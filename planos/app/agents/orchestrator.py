"""Orchestrator part 1: planner + analyst + executor."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.agents.interpreter import AGENT_SEQUENCE, parse_assumptions
from planos.app.core.exceptions import PlanOSError
from planos.app.core.logging import get_logger
from planos.app.core.permissions import get_role_permissions
from planos.app.models import AgentRun, AgentStep
from planos.app.tools.bootstrap import register_tools
from planos.app.tools.registry import registry

logger = get_logger(__name__)


class Orchestrator:
    """Flagship workflow with persisted state at every step (see reviewer.py)."""

    def __init__(self, session: AsyncSession):
        register_tools()
        self.session = session

    async def _step(
        self,
        run: AgentRun,
        number: int,
        agent: str,
        step_type: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        tool_name: str | None = None,
        tool_args: dict | None = None,
        tool_result: dict | None = None,
        policy: str | None = None,
        duration_ms: float = 0.0,
    ) -> AgentStep:
        step = AgentStep(
            run_id=run.id,
            step_number=number,
            step_type=step_type,
            input_data=input_data,
            output_data=output_data,
            tool_name=tool_name,
            tool_arguments=tool_args,
            tool_result=tool_result,
            policy_decision=policy,
            duration_ms=duration_ms,
        )
        self.session.add(step)
        await self.session.commit()
        return step

    def _ctx(
        self, organization_id: str, user_id: str, role: str, permissions: set, run_id: str
    ) -> dict[str, Any]:
        return {
            "session": self.session,
            "organization_id": organization_id,
            "user_id": user_id,
            "role": role,
            "user_permissions": permissions,
            "run_id": run_id,
        }

    async def run_full_workflow(
        self,
        *,
        plan_id: str,
        goal_text: str,
        organization_id: str,
        user_id: str,
        role: str,
        agent_run: AgentRun,
    ) -> dict[str, Any]:
        permissions = get_role_permissions(role)
        started = time.perf_counter()
        trace: list[dict[str, Any]] = []
        assumptions = parse_assumptions(goal_text) or {"demand_growth": 0.05}
        await self._step(
            agent_run,
            1,
            "planner",
            "plan",
            {"goal": goal_text},
            {"assumptions": assumptions, "agents": AGENT_SEQUENCE},
        )
        trace.append({"agent": "planner", "assumptions": assumptions})
        ctx = self._ctx(organization_id, user_id, role, permissions, agent_run.id)
        t0 = time.perf_counter()
        baseline = await registry.execute("get_metrics", {"plan_id": plan_id}, **ctx)
        cost = await registry.execute("get_metrics", {"plan_id": plan_id, "metric": "cost"}, **ctx)
        await self._step(
            agent_run,
            2,
            "analyst",
            "tool",
            {"plan_id": plan_id},
            {"baseline": baseline, "cost": cost},
            "get_metrics",
            {"plan_id": plan_id},
            baseline,
            "allow",
            (time.perf_counter() - t0) * 1000,
        )
        trace.append({"agent": "analyst", "baseline": baseline})
        variants = {
            "conservative": {
                k: (v * 0.5 if isinstance(v, float) else v) for k, v in assumptions.items()
            },
            "baseline": dict(assumptions),
            "aggressive": {
                k: (v * 1.5 if isinstance(v, float) else v) for k, v in assumptions.items()
            },
        }
        scenarios: dict[str, dict[str, Any]] = {}
        step_no = 3
        for label, variant in variants.items():
            created = await registry.execute(
                "create_scenario",
                {"plan_id": plan_id, "name": f"{label}-{agent_run.id[:8]}", "assumptions": variant},
                **ctx,
            )
            try:
                ran: dict[str, Any] = await registry.execute(
                    "run_scenario", {"scenario_id": created["scenario_id"]}, **ctx
                )
            except PlanOSError as exc:
                ran = {"status": "approval_required", "detail": str(exc)}
            scenarios[label] = {"created": created, "run": ran}
            await self._step(
                agent_run,
                step_no,
                "executor",
                "tool",
                {"variant": label, "assumptions": variant},
                ran,
                "run_scenario",
                {"scenario_id": created["scenario_id"]},
                ran,
                "allow",
            )
            step_no += 1
        trace.append({"agent": "executor", "scenarios": list(scenarios)})
        from planos.app.agents.reviewer import review_and_recommend

        return await review_and_recommend(
            self, agent_run, step_no, started, trace, scenarios, goal_text, organization_id, ctx
        )
