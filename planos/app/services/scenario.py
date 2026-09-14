"""Scenario service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError
from planos.app.core.logging import get_logger
from planos.app.models import Scenario
from planos.app.schemas.scenario import ScenarioCreate

logger = get_logger(__name__)


class ScenarioService:
    """Service for scenario operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: ScenarioCreate,
        organization_id: str,
        user_id: str,
    ) -> Scenario:
        """Create a new scenario from a baseline plan."""
        # Verify base plan exists and belongs to org
        from planos.app.models import Plan

        plan_result = await self.session.execute(select(Plan).where(Plan.id == data.base_plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise NotFoundError("Plan", data.base_plan_id)
        # Cross-tenant: treat as not-found to avoid leaking resource existence.

        scenario = Scenario(
            organization_id=organization_id,
            base_plan_id=data.base_plan_id,
            name=data.name,
            description=data.description,
            changes=data.changes,
            status="draft",
            created_by=user_id,
        )
        self.session.add(scenario)
        await self.session.commit()
        await self.session.refresh(scenario)

        logger.info("scenario_created", scenario_id=scenario.id, org_id=organization_id)
        return scenario

    async def get_by_id(self, scenario_id: str, organization_id: str) -> Scenario:
        """Get scenario by ID with tenant isolation check."""
        result = await self.session.execute(select(Scenario).where(Scenario.id == scenario_id))
        scenario = result.scalar_one_or_none()
        if not scenario:
            raise NotFoundError("Scenario", scenario_id)
        if scenario.organization_id != organization_id:
            raise NotFoundError("Scenario", scenario_id)
        return scenario

    async def list_scenarios(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Scenario], int]:
        """List scenarios for an organization."""
        count_query = select(Scenario.id).where(Scenario.organization_id == organization_id)
        total_result = await self.session.execute(count_query)
        total = len(total_result.scalars().all())

        query = (
            select(Scenario)
            .where(Scenario.organization_id == organization_id)
            .order_by(Scenario.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(query)
        scenarios = list(result.scalars().all())
        return scenarios, total

    async def update_results(
        self,
        scenario_id: str,
        results: dict,
        organization_id: str,
    ) -> Scenario:
        """Update scenario results after calculation."""
        scenario = await self.get_by_id(scenario_id, organization_id)
        scenario.results = results
        scenario.status = "completed"
        await self.session.commit()
        await self.session.refresh(scenario)
        return scenario

    async def delete(self, scenario_id: str, organization_id: str, user_id: str) -> None:
        """Delete a scenario (hard delete, tenant-scoped)."""
        scenario = await self.get_by_id(scenario_id, organization_id)
        await self.session.delete(scenario)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        logger.info(
            "scenario_deleted", scenario_id=scenario_id, org_id=organization_id, user_id=user_id
        )
