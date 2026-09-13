"""Run (job) routes."""

from __future__ import annotations

from typing import Annotated

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
    current_user: Annotated[AuthenticatedUser, Depends(require_permission_factory(Permission.SCENARIO_READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Get the status of an async job."""
    from celery.result import AsyncResult
    from planos.app.workers.celery_app import celery_app

    result = AsyncResult(job_id, app=celery_app)

    response = {
        "job_id": job_id,
        "status": result.state,
    }

    if result.state == "SUCCESS":
        response["result"] = result.get()
    elif result.state == "FAILURE":
        response["error"] = str(result.info)

    return response
