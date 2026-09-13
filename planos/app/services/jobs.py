"""Job service: durable async records + idempotent enqueue (Phases 8+9)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import ConflictError, NotFoundError
from planos.app.models import IdempotencyRecord, Job

TERMINAL = {"success", "failed", "cancelled"}


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, job_id: str, organization_id: str) -> Job:
        job = await self.session.get(Job, job_id)
        if job is None:
            raise NotFoundError("Job", job_id)
        if job.organization_id != organization_id:
            raise NotFoundError("Job", job_id)
        return job

    async def find_idempotent(
        self, organization_id: str, scope: str, key: str
    ) -> IdempotencyRecord | None:
        row = await self.session.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == organization_id,
                IdempotencyRecord.scope == scope,
                IdempotencyRecord.key == key,
            )
        )
        return row.scalar_one_or_none()

    async def enqueue_scenario_run(
        self,
        scenario_id: str,
        organization_id: str,
        user_id: str,
        idempotency_key: str | None = None,
    ) -> tuple[Job, bool, dict[str, Any] | None]:
        """Returns (job, replayed, cached_response). Same key -> same job, no dup task."""
        from planos.app.models import Scenario
        from planos.app.workers.scenario_tasks import execute_scenario

        scope = f"scenario_run:{scenario_id}"
        if idempotency_key:
            record = await self.find_idempotent(organization_id, scope, idempotency_key)
            if record is not None:
                job = await self.session.get(Job, (record.response or {}).get("job_id", ""))
                if job is not None:
                    return job, True, record.response
            # Reserve BEFORE dispatch so concurrent retries collide on unique index.
            record = IdempotencyRecord(
                organization_id=organization_id,
                scope=scope,
                key=idempotency_key,
                status_code=202,
                response={"status": "queued"},
            )
            self.session.add(record)
            try:
                await self.session.flush()
            except Exception as exc:
                await self.session.rollback()
                raise ConflictError("Duplicate idempotent request in flight") from exc
        row = await self.session.execute(
            select(Scenario).where(
                Scenario.id == scenario_id, Scenario.organization_id == organization_id
            )
        )
        scenario = row.scalar_one_or_none()
        if scenario is None:
            raise NotFoundError("Scenario", scenario_id)
        scenario.status = "running"
        job = Job(
            organization_id=organization_id,
            kind="scenario_run",
            status="queued",
            ref_type="scenario",
            ref_id=scenario_id,
            idempotency_key=idempotency_key,
            created_by=user_id,
            payload={"scenario_id": scenario_id},
        )
        self.session.add(job)
        await self.session.flush()
        task = execute_scenario.delay(scenario_id, organization_id, job.id)
        job.celery_task_id = task.id
        await self.session.commit()
        await self.session.refresh(job)
        body = {"job_id": job.id, "status": "queued", "celery_task_id": task.id}
        if idempotency_key:
            record = await self.find_idempotent(organization_id, scope, idempotency_key)
            if record is not None:
                record.response = body
                await self.session.commit()
        return job, False, None

    async def mark(
        self,
        job_id: str,
        status: str,
        result: dict | None = None,
        error: str | None = None,
        attempts: int | None = None,
    ) -> Job:
        job = await self.session.get(Job, job_id)
        if job is None:
            raise NotFoundError("Job", job_id)
        job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error[:2000]
        if attempts is not None:
            job.attempts = attempts
        job.updated_at = datetime.now(UTC)
        if status in ("success", "failed", "cancelled"):
            job.completed_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(job)
        return job
