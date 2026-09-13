"""Run/compare/change/knowledge tool handlers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError
from planos.app.models import PlanningData, Scenario
from planos.app.planning.calculator import PlanningEngine
from planos.app.planning.engine import PlanningMetrics, ScenarioChanges
from planos.app.tools.registry import (
    CompareScenariosInput,
    CreateChangeRequestInput,
    RunScenarioInput,
    SearchKnowledgeInput,
)


async def handle_run_scenario(validated: RunScenarioInput, **ctx: Any) -> dict[str, Any]:
    session: AsyncSession = ctx["session"]
    org: str = ctx["organization_id"]
    row = await session.execute(
        select(Scenario).where(
            Scenario.id == validated.scenario_id, Scenario.organization_id == org
        )
    )
    scenario = row.scalar_one_or_none()
    if scenario is None:
        raise NotFoundError("Scenario", validated.scenario_id)
    data = (
        (
            await session.execute(
                select(PlanningData).where(
                    PlanningData.plan_id == scenario.base_plan_id,
                    PlanningData.organization_id == org,
                )
            )
        )
        .scalars()
        .all()
    )
    if not data:
        return {
            "scenario_id": scenario.id,
            "status": "completed",
            "summary": {"message": "no data"},
        }
    totals = PlanningMetrics(
        units=sum(r.units for r in data),
        price=sum(r.price for r in data) / max(len(data), 1),
        cost=sum(r.cost for r in data),
        revenue=sum(r.revenue for r in data),
        headcount=sum(r.headcount for r in data),
        capacity=sum(r.capacity for r in data),
        inventory=sum(r.inventory for r in data),
        marketing_budget=sum(r.marketing_budget for r in data),
        operating_expenses=sum(r.cost for r in data) * 0.3,
    )
    changes = ScenarioChanges.from_dict(scenario.changes or {})
    results = PlanningEngine.calculate_scenario_impact([totals], changes, ["all"])
    summary = PlanningEngine.aggregate_results(results)
    # Per-period margins so the reviewer agent (and API consumers) can reason
    # about margin movement without re-deriving it from totals.
    summary["periods"] = [
        {
            "period_label": r.period_label,
            "baseline_margin_pct": round(r.baseline.margin_pct, 2),
            "scenario_margin_pct": round(r.scenario.margin_pct, 2),
        }
        for r in results
    ]
    scenario.results = summary
    scenario.status = "completed"
    await session.commit()
    return {"scenario_id": scenario.id, "status": "completed", "summary": summary}


async def handle_compare_scenarios(validated: CompareScenariosInput, **ctx: Any) -> dict[str, Any]:
    session: AsyncSession = ctx["session"]
    org: str = ctx["organization_id"]
    rows = (
        (
            await session.execute(
                select(Scenario).where(
                    Scenario.id.in_([validated.baseline_id, validated.scenario_id]),
                    Scenario.organization_id == org,
                )
            )
        )
        .scalars()
        .all()
    )
    by_id = {s.id: s for s in rows}
    if validated.baseline_id not in by_id or validated.scenario_id not in by_id:
        raise NotFoundError("Scenario", "baseline or scenario")
    base, other = by_id[validated.baseline_id], by_id[validated.scenario_id]
    b, o = base.results or {}, other.results or {}
    return {
        "baseline": {"id": base.id, "name": base.name, "results": b},
        "scenario": {"id": other.id, "name": other.name, "results": o},
        "delta_revenue": float(o.get("total_scenario_revenue", 0))
        - float(b.get("total_scenario_revenue", 0)),
        "delta_profit": float(o.get("total_scenario_profit", 0))
        - float(b.get("total_scenario_profit", 0)),
    }


async def handle_create_change_request(
    validated: CreateChangeRequestInput, **ctx: Any
) -> dict[str, Any]:
    from planos.app.services.approvals import ApprovalService

    service = ApprovalService(ctx["session"])
    cs, approval = await service.propose_from_scenario(
        validated.scenario_id, ctx["organization_id"], ctx["user_id"], validated.summary
    )
    return {"change_set_id": cs.id, "approval_id": approval.id, "status": approval.status}


async def handle_search_knowledge(validated: SearchKnowledgeInput, **ctx: Any) -> dict[str, Any]:
    from planos.app.services.knowledge import KnowledgeService

    service = KnowledgeService(ctx["session"])
    chunks = await service.search(ctx["organization_id"], validated.query, validated.top_k)
    return {"chunks": chunks}
