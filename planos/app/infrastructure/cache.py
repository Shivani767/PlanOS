"""Redis cache-aside helper (Phase 17): tenant-safe keys, TTL, invalidation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as aioredis

from planos.app.core.config import settings
from planos.app.core.logging import get_logger

logger = get_logger(__name__)

_client: aioredis.Redis | None = None
_hits = 0
_misses = 0


def get_client() -> aioredis.Redis | None:
    global _client
    if _client is None:
        try:
            _client = aioredis.from_url(settings.redis_url, decode_responses=True)
        except Exception as exc:
            logger.warning("redis_unavailable", error=str(exc))
            return None
    return _client


def cache_key(*parts: str) -> str:
    raw = ":".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{raw}:{digest}"


def stats() -> dict[str, int]:
    return {"hits": _hits, "misses": _misses}


async def cached(
    key: str, ttl_seconds: int, loader: Callable[[], Awaitable[Any]]
) -> tuple[Any, bool]:
    """Return (value, from_cache). Falls back to loader on any Redis error."""
    global _hits, _misses
    client = get_client()
    if client is None:
        return await loader(), False
    try:
        raw = await client.get(key)
        if raw is not None:
            _hits += 1
            return json.loads(raw), True
    except Exception as exc:
        logger.warning("cache_read_failed", error=str(exc))
    value = await loader()
    _misses += 1
    try:
        await client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("cache_write_failed", error=str(exc))
    return value, False


async def invalidate(pattern: str) -> int:
    client = get_client()
    if client is None:
        return 0
    try:
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
    except Exception as exc:
        logger.warning("cache_invalidate_failed", error=str(exc))
    return 0
