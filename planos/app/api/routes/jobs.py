"""Jobs routes: durable async execution records."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import AuthenticatedUser, require_permission_factory
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session
from planos.app.services.jobs import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])

require_read = require_permission_factory(Permission.SCENARIO_READ)


@router.get("")
async def list_jobs(
    current_user: Annotated[AuthenticatedUser, Depends(require_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    from planos.app.models import Job

    query = select(Job).where(Job.organization_id == current_user.organization_id)
    if status_filter:
        query = query.where(Job.status == status_filter)
    rows = (
        (await session.execute(query.order_by(Job.created_at.desc()).limit(limit))).scalars().all()
    )
    return [
        {
            "job_id": j.id,
            "kind": j.kind,
            "status": j.status,
            "ref_type": j.ref_type,
            "ref_id": j.ref_id,
            "attempts": j.attempts,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in rows
    ]


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_read)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    job = await JobService(session).get(job_id, current_user.organization_id)
    return {
        "job_id": job.id,
        "kind": job.kind,
        "status": job.status,
        "ref_type": job.ref_type,
        "ref_id": job.ref_id,
        "attempts": job.attempts,
        "result": job.result,
        "error": job.error,
        "celery_task_id": job.celery_task_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
