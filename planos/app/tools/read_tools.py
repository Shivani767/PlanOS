"""Read + scenario tool handlers (thin adapters over domain services)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError
from planos.app.models import Plan, PlanningData
from planos.app.schemas.scenario import ScenarioCreate
from planos.app.services.scenario import ScenarioService
from planos.app.tools.registry import (
    CreateScenarioInput,
    GetMetricsInput,
    GetPlanInput,
)

ALLOWED_METRICS = {
    "units",
    "price",
    "cost",
    "revenue",
    "headcount",
    "capacity",
    "inventory",
    "marketing_budget",
}


async def handle_get_plan(validated: GetPlanInput, **ctx: Any) -> dict[str, Any]:
    session: AsyncSession = ctx["session"]
    org: str = ctx["organization_id"]
    row = await session.execute(
        select(Plan).where(Plan.id == validated.plan_id, Plan.organization_id == org)
    )
    plan = row.scalar_one_or_none()
    if plan is None:
        raise NotFoundError("Plan", validated.plan_id)
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "status": plan.status,
        "current_version": plan.current_version,
    }


async def handle_get_metrics(validated: GetMetricsInput, **ctx: Any) -> dict[str, Any]:
    session: AsyncSession = ctx["session"]
    org: str = ctx["organization_id"]
    metric = validated.metric if validated.metric in ALLOWED_METRICS else "revenue"
    total = await session.execute(
        select(func.coalesce(func.sum(getattr(PlanningData, metric)), 0)).where(
            PlanningData.plan_id == validated.plan_id, PlanningData.organization_id == org
        )
    )
    count = await session.execute(
        select(func.count(PlanningData.id)).where(
            PlanningData.plan_id == validated.plan_id, PlanningData.organization_id == org
        )
    )
    return {
        "plan_id": validated.plan_id,
        "metric": metric,
        "total": float(total.scalar() or 0),
        "records": int(count.scalar() or 0),
    }


async def handle_create_scenario(validated: CreateScenarioInput, **ctx: Any) -> dict[str, Any]:
    service = ScenarioService(ctx["session"])
    scenario = await service.create(
        ScenarioCreate(
            name=validated.name,
            base_plan_id=validated.plan_id,
            description=f"Agent-created from plan {validated.plan_id}",
            changes=validated.assumptions,
        ),
        ctx["organization_id"],
        ctx["user_id"],
    )
    return {"scenario_id": scenario.id, "name": scenario.name, "status": scenario.status}
