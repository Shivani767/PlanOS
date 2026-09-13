"""Celery application configuration."""

from __future__ import annotations

from celery import Celery

from planos.app.core.config import settings

celery_app = Celery(
    "planos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["planos.app.workers.scenario_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_default_queue="planos",
    task_routes={
        "planos.app.workers.scenario_tasks.execute_scenario": {"queue": "planning"},
    },
)
