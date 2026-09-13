"""System routes: health detail, metrics, cache stats."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from planos.app.infrastructure.cache import stats as cache_stats
from planos.app.observability.metrics import render_prometheus, snapshot

router = APIRouter(tags=["System"])


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    return render_prometheus()


@router.get("/metrics/summary")
async def metrics_summary() -> dict:
    return {**snapshot(), "cache": cache_stats()}


@router.get("/health/detailed")
async def detailed_health() -> dict:
    from planos.app.infrastructure.cache import get_client

    redis_ok = False
    client = get_client()
    if client is not None:
        try:
            await client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False
    return {"status": "healthy", "redis": "up" if redis_ok else "down"}
