"""Run (job) routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import (
    AuthenticatedUser,
    require_permission_factory,
)
from planos.app.core.permissions import Permission
from planos.app.db.session import get_session

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/{job_id}")
async def get_run_status(
    job_id: str,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_permission_factory(Permission.SCENARIO_READ))
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Job status: durable DB record first, Celery result as fallback."""
    from planos.app.core.exceptions import NotFoundError
    from planos.app.services.jobs import JobService

    try:
        job = await JobService(session).get(job_id, current_user.organization_id)
        payload: dict[str, Any] = {
            "job_id": job.id,
            "status": job.status,
            "kind": job.kind,
            "attempts": job.attempts,
        }
        if job.result:
            payload["result"] = job.result
        if job.error:
            payload["error"] = job.error
        if job.celery_task_id:
            payload["celery_task_id"] = job.celery_task_id
        return payload
    except NotFoundError:
        pass
    # Back-compat: raw Celery task id
    from celery.result import AsyncResult

    from planos.app.workers.celery_app import celery_app

    result = AsyncResult(job_id, app=celery_app)
    response: dict[str, Any] = {"job_id": job_id, "status": result.state}
    if result.state == "SUCCESS":
        response["result"] = result.get()
    elif result.state == "FAILURE":
        response["error"] = str(result.info)
    return response
