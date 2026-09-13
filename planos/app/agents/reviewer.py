"""Reviewer phase: pick best margin gain >= 2pts, propose approval."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from planos.app.core.exceptions import PlanOSError
from planos.app.core.logging import get_logger
from planos.app.models import AgentRun
from planos.app.observability.metrics import observe_agent_run
from planos.app.services.memory import MemoryService
from planos.app.tools.registry import registry

logger = get_logger(__name__)


async def review_and_recommend(
    orchestrator: Any,
    agent_run: AgentRun,
    step_no: int,
    started: float,
    trace: list[dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    goal_text: str,
    organization_id: str,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    best_label, best_gain = None, 0.0
    for label, payload in scenarios.items():
        periods = ((payload.get("run") or {}).get("summary") or {}).get("periods") or []
        if periods:
            gain = sum(
                p.get("scenario_margin_pct", 0) - p.get("baseline_margin_pct", 0) for p in periods
            ) / len(periods)
            if gain > best_gain:
                best_label, best_gain = label, gain
    recommendation, approval_id, change_set_id = None, None, None
    if best_label and best_gain >= 2.0:
        created_id = scenarios[best_label]["created"]["scenario_id"]
        try:
            req = await registry.execute(
                "create_change_request",
                {
                    "scenario_id": created_id,
                    "summary": f"Recommend '{best_label}' (+{best_gain:.2f}pts margin)",
                },
                **ctx,
            )
            recommendation = best_label
            change_set_id = req.get("change_set_id")
            approval_id = req.get("approval_id")
        except PlanOSError as exc:
            recommendation = f"{best_label} (approval blocked: {exc.message})"
    await orchestrator._step(
        agent_run,
        step_no,
        "reviewer",
        "review",
        {"candidates": list(scenarios)},
        {
            "recommendation": recommendation,
            "margin_gain_pts": round(best_gain, 2),
            "change_set_id": change_set_id,
            "approval_id": approval_id,
        },
    )
    trace.append({"agent": "reviewer", "recommendation": recommendation})
    try:
        await MemoryService(orchestrator.session).record_episode(
            organization_id,
            goal_text,
            recommendation or "no recommendation",
            ["get_metrics", "create_scenario", "run_scenario"],
            {"scenarios": list(scenarios), "margin_gain": best_gain},
            run_id=agent_run.id,
        )
    except Exception as exc:
        logger.warning("episode_record_failed", error=str(exc))
    agent_run.output_text = (
        f"Recommendation: {recommendation or 'none meets the 2% margin bar'} "
        f"(margin gain {best_gain:.2f}pts across {', '.join(scenarios)})."
    )
    agent_run.status = "completed"
    agent_run.completed_at = datetime.now(UTC)
    agent_run.duration_ms = (time.perf_counter() - started) * 1000
    await orchestrator.session.commit()
    observe_agent_run("completed")
    return {
        "recommendation": recommendation,
        "margin_gain_pts": round(best_gain, 2),
        "scenarios": scenarios,
        "change_set_id": change_set_id,
        "approval_id": approval_id,
        "trace": trace,
    }
