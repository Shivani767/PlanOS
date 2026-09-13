"""Test configuration and fixtures.

Environment is pinned BEFORE any PlanOS import so the global app engine
(planos.app.db.session) and the test fixture engine both target planos_test.
"""

from __future__ import annotations

import os
import uuid

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://planos:planos@localhost:5433/planos_test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://planos:planos@localhost:5433/planos_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LLM_PROVIDER", "mock")

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from planos.app.core.security import create_access_token, hash_password
from planos.app.db.session import Base, get_session
from planos.app.main import create_app
from planos.app.models import Organization, User

if TYPE_CHECKING:
    from httpx import AsyncClient

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://planos:planos@localhost:5433/planos_test"
TEST_DATABASE_URL_SYNC = "postgresql://planos:planos@localhost:5433/planos_test"


@pytest.fixture(scope="session", autouse=True)
def db_schema():
    """Drop + recreate the test schema once per session (sync, no event-loop leaks)."""
    engine = create_engine(TEST_DATABASE_URL_SYNC)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()
    yield


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped async session over its own engine (loop-safe)."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Loop-safe ASGI client: routes resolve to the per-test session fixture.

    Overriding get_session avoids the global engine, whose pooled asyncpg
    connections break when pytest-asyncio opens a fresh event loop per test.
    """
    from httpx import ASGITransport, AsyncClient

    app = create_app()

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def unique_org_user(session: AsyncSession) -> dict:
    """Fresh org + admin user with unique slug/email (collision-free in shared DB)."""
    slug = f"org-{uuid.uuid4().hex[:10]}"
    org = Organization(name=f"Org {slug}", slug=slug)
    session.add(org)
    await session.flush()
    user = User(organization_id=org.id, email=f"u-{uuid.uuid4().hex[:8]}@example.com",
                hashed_password=hash_password("password123"),
                full_name="Test User", role="ADMIN")
    session.add(user)
    await session.commit()
    await session.refresh(org)
    await session.refresh(user)
    return {"org": org, "user": user, "token": create_access_token(user.id)}


@pytest_asyncio.fixture
async def test_organization(session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(name="Test Org", slug="test-org")
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_admin(session: AsyncSession, test_organization: Organization) -> User:
    """Create a test admin user."""
    user = User(
        organization_id=test_organization.id,
        email="admin@test.org",
        hashed_password=hash_password("testpassword123"),
        full_name="Test Admin",
        role="ADMIN",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_viewer(session: AsyncSession, test_organization: Organization) -> User:
    """Create a test viewer user."""
    user = User(
        organization_id=test_organization.id,
        email="viewer@test.org",
        hashed_password=hash_password("testpassword123"),
        full_name="Test Viewer",
        role="VIEWER",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
def app():
    """Create test application."""
    return create_app()
