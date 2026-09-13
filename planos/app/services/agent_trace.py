"""Agent run trace queries (Phase 21): run + ordered steps + tool calls."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.models import AgentRun, AgentStep, ToolCall


async def get_trace(session: AsyncSession, run: AgentRun) -> dict:
    steps = (
        (
            await session.execute(
                select(AgentStep)
                .where(AgentStep.run_id == run.id)
                .order_by(AgentStep.step_number.asc())
            )
        )
        .scalars()
        .all()
    )
    calls = (
        (
            await session.execute(
                select(ToolCall)
                .where(ToolCall.run_id == run.id)
                .order_by(ToolCall.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    return {
        "run": {
            "id": run.id,
            "status": run.status,
            "input": run.input_text,
            "output": run.output_text,
            "error": run.error_message,
            "duration_ms": run.duration_ms,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        },
        "steps": [
            {
                "n": s.step_number,
                "agent": s.step_type,
                "type": s.step_type,
                "tool": s.tool_name,
                "args": s.tool_arguments,
                "result": s.tool_result,
                "policy": s.policy_decision,
                "duration_ms": s.duration_ms,
            }
            for s in steps
        ],
        "tool_calls": [
            {
                "tool": c.tool_name,
                "args": c.arguments,
                "status": c.status,
                "error": c.error_message,
                "duration_ms": c.duration_ms,
            }
            for c in calls
        ],
    }


async def steps_for_run(session: AsyncSession, run_id: str) -> list[dict]:
    steps = (
        (
            await session.execute(
                select(AgentStep)
                .where(AgentStep.run_id == run_id)
                .order_by(AgentStep.step_number.asc())
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": s.id,
            "run_id": s.run_id,
            "step_number": s.step_number,
            "step_type": s.step_type,
            "input_data": s.input_data,
            "output_data": s.output_data,
            "tool_name": s.tool_name,
            "tool_arguments": s.tool_arguments,
            "tool_result": s.tool_result,
            "policy_decision": s.policy_decision,
            "duration_ms": s.duration_ms,
            "created_at": s.created_at,
        }
        for s in steps
    ]
