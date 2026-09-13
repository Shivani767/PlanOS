"""Scenario routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import (
    AuthenticatedUser,
    require_permission_factory,
)
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session
from planos.app.schemas.common import PaginationParams
from planos.app.schemas.scenario import (
    ScenarioCompareRequest,
    ScenarioCreate,
    ScenarioListResponse,
    ScenarioResponse,
    ScenarioRunResponse,
)
from planos.app.services.scenario import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

require_scenario_read = require_permission_factory(Permission.SCENARIO_READ)
require_scenario_create = require_permission_factory(Permission.SCENARIO_CREATE)
require_scenario_run = require_permission_factory(Permission.SCENARIO_RUN)
require_scenario_delete = require_permission_factory(Permission.SCENARIO_DELETE)


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: ScenarioCreate,
    current_user: Annotated[AuthenticatedUser, Depends(require_scenario_create)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScenarioResponse:
    """Create a new scenario from a baseline plan."""
    service = ScenarioService(session)
    scenario = await service.create(data, current_user.organization_id, current_user.user_id)
    return ScenarioResponse.model_validate(scenario)


@router.get("", response_model=ScenarioListResponse)
async def list_scenarios(
    current_user: Annotated[AuthenticatedUser, Depends(require_scenario_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
    pagination: Annotated[PaginationParams, Query()] = None,
) -> ScenarioListResponse:
    """List scenarios for the current organization."""
    if pagination is None:
        pagination = PaginationParams()
    service = ScenarioService(session)
    scenarios, total = await service.list_scenarios(
        current_user.organization_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return ScenarioListResponse(
        items=[ScenarioResponse.model_validate(s) for s in scenarios],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_scenario_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScenarioResponse:
    """Get a scenario by ID."""
    service = ScenarioService(session)
    scenario = await service.get_by_id(scenario_id, current_user.organization_id)
    return ScenarioResponse.model_validate(scenario)


@router.post(
    "/{scenario_id}/run", response_model=ScenarioRunResponse, status_code=status.HTTP_202_ACCEPTED
)
async def run_scenario(
    scenario_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_scenario_run)],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ScenarioRunResponse:
    """Queue a scenario for execution (durable Job + idempotent)."""
    from planos.app.services.jobs import JobService

    job, replayed, cached = await JobService(session).enqueue_scenario_run(
        scenario_id,
        current_user.organization_id,
        current_user.user_id,
        idempotency_key=idempotency_key,
    )
    if replayed and cached:
        return ScenarioRunResponse(
            job_id=cached.get("job_id", job.id), status=cached.get("status", "queued")
        )
    return ScenarioRunResponse(job_id=job.id, status="queued")


@router.post("/compare")
async def compare_scenarios(
    data: ScenarioCompareRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_scenario_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Deterministic comparison (backend math, never the LLM)."""
    from planos.app.core.permissions import get_role_permissions
    from planos.app.tools.bootstrap import register_tools
    from planos.app.tools.registry import registry

    register_tools()
    return await registry.execute(
        "compare_scenarios",
        data.model_dump(),
        session=session,
        organization_id=current_user.organization_id,
        user_id=current_user.user_id,
        role=current_user.role,
        user_permissions=get_role_permissions(current_user.role),
    )


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_scenario_delete)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete a scenario (tenant-scoped, 204 No Content)."""
    service = ScenarioService(session)
    await service.delete(scenario_id, current_user.organization_id, current_user.user_id)
