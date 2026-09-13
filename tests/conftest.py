"""Test configuration and fixtures."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session

from planos.app.core.config import settings
from planos.app.db.session import Base, get_session
from planos.app.main import create_app
from planos.app.models import Organization, User
from planos.app.core.security import hash_password


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://planos:planos@localhost:5432/planos_test"
TEST_DATABASE_URL_SYNC = "postgresql://planos:planos@localhost:5432/planos_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        # Clean up after test
        await session.rollback()


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
