"""Plan service with optimistic concurrency control."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError, OptimisticLockError
from planos.app.core.logging import get_logger
from planos.app.models import Plan, PlanVersion
from planos.app.schemas.plan import PlanCreate, PlanUpdate

logger = get_logger(__name__)


class PlanService:
    """Service for plan operations with optimistic locking."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: PlanCreate, organization_id: str, user_id: str) -> Plan:
        """Create a new plan."""
        plan = Plan(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            status="draft",
            current_version=1,
            created_by=user_id,
        )
        self.session.add(plan)
        # Flush so plan.id exists before referencing it in the version row.
        await self.session.flush()

        # Create initial version
        version = PlanVersion(
            plan_id=plan.id,
            version=1,
            data={},
            created_by=user_id,
        )
        self.session.add(version)

        await self.session.commit()
        await self.session.refresh(plan)

        logger.info("plan_created", plan_id=plan.id, org_id=organization_id)
        return plan

    async def get_by_id(self, plan_id: str, organization_id: str) -> Plan:
        """Get plan by ID with tenant isolation check."""
        result = await self.session.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundError("Plan", plan_id)
        if plan.organization_id != organization_id:
            raise NotFoundError("Plan", plan_id)
        return plan

    async def list_plans(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Plan], int]:
        """List plans for an organization with pagination."""
        query = select(Plan).where(Plan.organization_id == organization_id)
        count_query = select(Plan.id).where(Plan.organization_id == organization_id)

        if status:
            query = query.where(Plan.status == status)
            count_query = count_query.where(Plan.status == status)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.order_by(Plan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        result = await self.session.execute(query)
        plans = list(result.scalars().all())

        return plans, total

    async def update(
        self,
        plan_id: str,
        data: PlanUpdate,
        organization_id: str,
        user_id: str,
    ) -> Plan:
        """Update a plan with database-level optimistic concurrency control.

        The version guard is a single conditional UPDATE: it only succeeds when
        current_version still equals the caller's expected_version, so two
        concurrent updates can never both win (no read-check-write race).
        """
        plan = await self.get_by_id(plan_id, organization_id)

        update_data = data.model_dump(exclude_unset=True, exclude={"expected_version"})
        set_fields = {k: v for k, v in update_data.items() if v is not None}
        new_version_num = plan.current_version + 1

        # Atomic guard: bump version + apply fields only if version is unchanged.
        stmt = (
            update(Plan)
            .where(
                Plan.id == plan_id,
                Plan.current_version == data.expected_version,
            )
            .values(current_version=new_version_num, **set_fields)
        )
        result = await self.session.execute(stmt)
        rowcount = getattr(result, "rowcount", 0)
        if rowcount != 1:
            # Either stale version (409) or concurrent winner committed first.
            await self.session.rollback()
            fresh = await self.get_by_id(plan_id, organization_id)
            raise OptimisticLockError(data.expected_version, fresh.current_version)

        # Create version snapshot
        version = PlanVersion(
            plan_id=plan.id,
            version=new_version_num,
            data=update_data,
            created_by=user_id,
        )
        self.session.add(version)

        await self.session.commit()
        await self.session.refresh(plan)

        logger.info(
            "plan_updated",
            plan_id=plan.id,
            new_version=new_version_num,
            org_id=organization_id,
        )
        return plan

    async def delete(self, plan_id: str, organization_id: str, user_id: str) -> None:
        """Delete a plan (hard delete; DB cascades versions + planning data)."""
        plan = await self.get_by_id(plan_id, organization_id)
        await self.session.delete(plan)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        logger.info("plan_deleted", plan_id=plan_id, org_id=organization_id, user_id=user_id)
