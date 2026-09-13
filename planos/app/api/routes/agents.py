"""Agent routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
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
async def run_agent(
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
    )
    return AgentRunResponse.model_validate(run)


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_permission_factory(Permission.AGENT_READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentRunResponse:
    """Get an agent run by ID."""
    from planos.app.services.agent import AgentService

    service = AgentService(session)
    run = await service.get_run(run_id, current_user.organization_id)
    return AgentRunResponse.model_validate(run)
