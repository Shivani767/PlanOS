"""Plan service with optimistic concurrency control."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import (
    ConflictError,
    NotFoundError,
    OptimisticLockError,
    TenantIsolationError,
)
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
        result = await self.session.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundError("Plan", plan_id)
        if plan.organization_id != organization_id:
            raise TenantIsolationError()
        return plan

    async def list_plans(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
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
        query = query.order_by(Plan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
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
        """Update a plan with optimistic concurrency control."""
        plan = await self.get_by_id(plan_id, organization_id)

        # Optimistic locking check
        if plan.current_version != data.expected_version:
            raise OptimisticLockError(data.expected_version, plan.current_version)

        # Apply updates
        update_data = data.model_dump(exclude_unset=True, exclude={"expected_version"})
        for field, value in update_data.items():
            if value is not None:
                setattr(plan, field, value)

        # Increment version
        new_version_num = plan.current_version + 1
        plan.current_version = new_version_num

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
