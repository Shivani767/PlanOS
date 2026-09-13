"""Approval routes: human-in-the-loop for governed change sets."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import AuthenticatedUser, require_permission_factory
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session
from planos.app.services.approvals import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals"])

require_request = require_permission_factory(Permission.APPROVAL_REQUEST)
require_decide = require_permission_factory(Permission.APPROVAL_APPROVE)


class DecideRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


def _serialize(approval: Any) -> dict[str, Any]:
    return {
        "id": approval.id,
        "organization_id": approval.organization_id,
        "action_type": approval.action_type,
        "resource_type": approval.resource_type,
        "resource_id": approval.resource_id,
        "details": approval.details,
        "status": approval.status,
        "requested_by": approval.requested_by,
        "approved_by": approval.approved_by,
        "decision_reason": approval.decision_reason,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
    }


@router.get("")
async def list_approvals(
    current_user: Annotated[AuthenticatedUser, Depends(require_request)],
    session: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    from planos.app.models import ApprovalRequest

    query = (
        select(ApprovalRequest)
        .where(ApprovalRequest.organization_id == current_user.organization_id)
        .order_by(ApprovalRequest.created_at.desc())
        .limit(100)
    )
    if status_filter:
        query = query.where(ApprovalRequest.status == status_filter)
    rows = (await session.execute(query)).scalars().all()
    return [_serialize(a) for a in rows]


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_decide)],
    session: Annotated[AsyncSession, Depends(get_session)],
    data: DecideRequest | None = None,
) -> dict[str, Any]:
    approval = await ApprovalService(session).decide(
        approval_id,
        current_user.organization_id,
        current_user.user_id,
        True,
        (data.reason if data else None),
    )
    return _serialize(approval)


@router.post("/{approval_id}/reject", status_code=status.HTTP_200_OK)
async def reject(
    approval_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_decide)],
    session: Annotated[AsyncSession, Depends(get_session)],
    data: DecideRequest | None = None,
) -> dict[str, Any]:
    approval = await ApprovalService(session).decide(
        approval_id,
        current_user.organization_id,
        current_user.user_id,
        False,
        (data.reason if data else None),
    )
    return _serialize(approval)
