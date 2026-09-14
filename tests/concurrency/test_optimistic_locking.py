"""Database-level optimistic concurrency tests (Phase 15).

True concurrency: each contender gets its own session/connection, and the
winner/loser split is enforced by the conditional-UPDATE rowcount (not by a
Python read-check-write).
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from planos.app.core.exceptions import OptimisticLockError
from planos.app.core.security import create_access_token, hash_password
from planos.app.models import Organization, Plan, PlanVersion, User
from planos.app.schemas.plan import PlanUpdate
from planos.app.services.plan import PlanService

TEST_DB = "postgresql+asyncpg://planos:planos@localhost:5433/planos_test"


def _make_engine():
    return create_async_engine(TEST_DB, echo=False)


async def _setup() -> tuple[str, str, str, str]:
    """Fresh org + admin + one plan. Returns (plan_id, org_id, user_id, token)."""
    eng = _make_engine()
    sf = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with sf() as s:
        suffix = uuid.uuid4().hex[:10]
        org = Organization(name=f"Org {suffix}", slug=f"conc-{suffix}")
        s.add(org)
        await s.flush()
        user = User(
            organization_id=org.id,
            email=f"conc-{suffix}@example.com",
            hashed_password=hash_password("password123"),
            full_name="Conc User",
            role="ADMIN",
        )
        s.add(user)
        await s.flush()
        plan = Plan(
            organization_id=org.id,
            name="Race Plan",
            current_version=1,
            created_by=user.id,
        )
        s.add(plan)
        await s.flush()
        s.add(PlanVersion(plan_id=plan.id, version=1, data={}, created_by=user.id))
        await s.commit()
        plan_id, org_id, user_id = plan.id, org.id, user.id
    eng.dispose()
    return plan_id, org_id, user_id, create_access_token(user_id)


async def _attempt(
    plan_id: str, org_id: str, user_id: str, name: str, expected_version: int
) -> str:
    """Run one update attempt in its own session; returns win:<name> or lose."""
    eng = _make_engine()
    sf = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with sf() as s:
        svc = PlanService(s)
        try:
            updated = await svc.update(
                plan_id,
                PlanUpdate(name=name, description=None, expected_version=expected_version),
                org_id,
                user_id,
            )
            eng.dispose()
            return f"win:{updated.name}:{updated.current_version}"
        except OptimisticLockError:
            eng.dispose()
            return "lose"


@pytest.mark.asyncio
async def test_sequential_stale_version_loses() -> None:
    """Fresh version wins; the now-stale version loses."""
    plan_id, org_id, user_id, _ = await _setup()

    eng = _make_engine()
    sf = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with sf() as s:
        svc = PlanService(s)
        a = await svc.update(
            plan_id, PlanUpdate(name="A", expected_version=1), org_id, user_id
        )
        assert a.current_version == 2
        with pytest.raises(OptimisticLockError):
            await svc.update(
                plan_id, PlanUpdate(name="stale", expected_version=1), org_id, user_id
            )
        c = await svc.update(
            plan_id, PlanUpdate(name="C", expected_version=2), org_id, user_id
        )
        assert c.current_version == 3
    eng.dispose()


@pytest.mark.asyncio
async def test_concurrent_updates_only_one_wins() -> None:
    """Two contenders racing with the same expected_version: exactly one commits."""
    plan_id, org_id, user_id, _ = await _setup()

    results = await asyncio.gather(
        _attempt(plan_id, org_id, user_id, "Task-A", 1),
        _attempt(plan_id, org_id, user_id, "Task-B", 1),
    )
    winners = [r for r in results if r.startswith("win:")]
    losers = [r for r in results if r == "lose"]
    assert len(winners) == 1, f"expected exactly one winner, got {results}"
    assert len(losers) == 1, f"expected exactly one loser, got {results}"

    eng = _make_engine()
    sf = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with sf() as s:
        svc = PlanService(s)
        final = await svc.get_by_id(plan_id, org_id)
        assert final.current_version == 2
        assert final.name == winners[0].split(":")[1]
    eng.dispose()
