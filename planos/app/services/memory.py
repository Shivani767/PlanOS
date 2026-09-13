"""Memory service: short-term / organizational / episodic tiers (Phase 11)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.models import MemoryEntry

TIERS = {"short_term", "organizational", "episodic"}
TTL = {"short_term": timedelta(hours=24), "organizational": None, "episodic": timedelta(days=90)}


class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def remember(
        self,
        organization_id: str,
        tier: str,
        key: str,
        value: dict,
        relevance: float = 1.0,
        run_id: str | None = None,
        created_by: str | None = None,
    ) -> MemoryEntry:
        assert tier in TIERS, f"unknown tier {tier}"
        ttl = TTL[tier]
        entry = MemoryEntry(
            organization_id=organization_id,
            tier=tier,
            key=key,
            value=value,
            relevance=relevance,
            run_id=run_id,
            created_by=created_by,
            expires_at=datetime.now(UTC) + ttl if ttl else None,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def recall(
        self,
        organization_id: str,
        tier: str | None = None,
        key: str | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        now = datetime.now(UTC)
        query = select(MemoryEntry).where(MemoryEntry.organization_id == organization_id)
        if tier:
            query = query.where(MemoryEntry.tier == tier)
        if key:
            query = query.where(MemoryEntry.key == key)
        query = query.order_by(MemoryEntry.relevance.desc(), MemoryEntry.updated_at.desc()).limit(
            limit
        )
        rows = (await self.session.execute(query)).scalars().all()
        live = [r for r in rows if r.expires_at is None or r.expires_at > now]
        return live

    async def record_episode(
        self,
        organization_id: str,
        task: str,
        decision: str,
        tools_used: list[str],
        result: dict,
        feedback: str | None = None,
        run_id: str | None = None,
    ) -> MemoryEntry:
        return await self.remember(
            organization_id,
            "episodic",
            f"episode:{run_id or task[:40]}",
            {
                "task": task,
                "decision": decision,
                "tools_used": tools_used,
                "result": result,
                "feedback": feedback,
            },
            run_id=run_id,
        )

    async def prune_expired(self, organization_id: str) -> int:
        now = datetime.now(UTC)
        res = await self.session.execute(
            delete(MemoryEntry).where(
                MemoryEntry.organization_id == organization_id,
                MemoryEntry.expires_at.is_not(None),
                MemoryEntry.expires_at < now,
            )
        )
        await self.session.commit()
        return res.rowcount or 0
