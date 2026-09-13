"""Agent routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import (
    AuthenticatedUser,
    require_permission_factory,
)
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session
from planos.app.schemas.agent import AgentRunRequest, AgentRunResponse

router = APIRouter(prefix="/agents", tags=["Agents"])

require_agent_execute = require_permission_factory(Permission.AGENT_EXECUTE)


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_agent_legacy(
    data: AgentRunRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_agent_execute)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentRunResponse:
    """Execute an agent run."""
    from planos.app.services.agent import AgentService

    service = AgentService(session)
    run = await service.execute_run(
        agent_type=data.agent_type,
        input_text=data.input_text,
        organization_id=current_user.organization_id,
        user_id=current_user.user_id,
        role=current_user.role,
        plan_id=data.plan_id,
    )
    payload = AgentRunResponse.model_validate(run).model_dump()
    payload["steps"] = await service.steps_for_run(run.id)
    return payload  # type: ignore[return-value]


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_permission_factory(Permission.AGENT_READ))
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentRunResponse:
    """Get an agent run by ID."""
    from planos.app.services.agent import AgentService

    service = AgentService(session)
    run = await service.get_run(run_id, current_user.organization_id)
    return AgentRunResponse.model_validate(run)


class PlanWorkflowRequest(BaseModel):
    plan_id: str = Field(min_length=1, max_length=36)
    goal: str = Field(min_length=1, max_length=5000)


@router.post("/plan", status_code=status.HTTP_202_ACCEPTED)
async def run_plan_workflow(
    data: PlanWorkflowRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_agent_execute)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Flagship demo: planner -> analyst -> executor -> reviewer."""
    from planos.app.services.agent import AgentService

    service = AgentService(session)
    run = await service.execute_run(
        agent_type="planner",
        input_text=data.goal,
        organization_id=current_user.organization_id,
        user_id=current_user.user_id,
        role=current_user.role,
        plan_id=data.plan_id,
    )
    trace = await service.trace(run.id, current_user.organization_id)
    return {"run_id": run.id, "status": run.status, "output": run.output_text, "trace": trace}


@router.get("/runs/{run_id}/trace")
async def get_agent_trace(
    run_id: str,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_permission_factory(Permission.AGENT_READ))
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Full execution trace for debugging."""
    from planos.app.services.agent import AgentService

    return await AgentService(session).trace(run_id, current_user.organization_id)


@router.get("/tools", response_model=list[dict[str, Any]])
async def list_tools(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_permission_factory(Permission.AGENT_READ))
    ],
) -> list[dict[str, Any]]:
    """Tools visible to the caller's role (from the central registry)."""
    from planos.app.core.permissions import get_role_permissions
    from planos.app.tools.bootstrap import register_tools
    from planos.app.tools.registry import registry

    register_tools()
    permitted = get_role_permissions(current_user.role)
    visible = [t for t in registry.list_definitions() if t.required_permission in permitted]
    return [
        {
            "name": t.name,
            "description": t.description,
            "risk": t.risk,
            "requires_approval": t.requires_approval,
            "input_schema": t.input_schema.model_json_schema(),
        }
        for t in visible
    ]
