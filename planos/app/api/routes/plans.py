"""Plan routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import (
    AuthenticatedUser,
    get_current_user,
    require_permission_factory,
)
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session
from planos.app.schemas.common import PaginationParams
from planos.app.schemas.plan import (
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
)
from planos.app.services.plan import PlanService

router = APIRouter(prefix="/plans", tags=["Plans"])

require_plan_read = require_permission_factory(Permission.PLAN_READ)
require_plan_create = require_permission_factory(Permission.PLAN_CREATE)
require_plan_update = require_permission_factory(Permission.PLAN_UPDATE)


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: PlanCreate,
    current_user: Annotated[AuthenticatedUser, Depends(require_plan_create)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlanResponse:
    """Create a new plan."""
    service = PlanService(session)
    plan = await service.create(data, current_user.organization_id, current_user.user_id)
    return PlanResponse.model_validate(plan)


@router.get("", response_model=PlanListResponse)
async def list_plans(
    current_user: Annotated[AuthenticatedUser, Depends(require_plan_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
    pagination: Annotated[PaginationParams, Query()] = None,
    status_filter: str | None = Query(None, alias="status"),
) -> PlanListResponse:
    """List plans for the current organization."""
    if pagination is None:
        pagination = PaginationParams()
    service = PlanService(session)
    plans, total = await service.list_plans(
        current_user.organization_id,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status_filter,
    )
    return PlanListResponse(
        items=[PlanResponse.model_validate(p) for p in plans],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_plan_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlanResponse:
    """Get a plan by ID."""
    service = PlanService(session)
    plan = await service.get_by_id(plan_id, current_user.organization_id)
    return PlanResponse.model_validate(plan)


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: str,
    data: PlanUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(require_plan_update)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlanResponse:
    """Update a plan with optimistic concurrency control."""
    service = PlanService(session)
    plan = await service.update(plan_id, data, current_user.organization_id, current_user.user_id)
    return PlanResponse.model_validate(plan)
