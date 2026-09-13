"""Integration tests for API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.main import create_app
from planos.app.db.session import async_session_factory, engine, Base
from planos.app.models import Organization, User
from planos.app.core.security import hash_password, create_access_token


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_org_and_user():
    """Create test organization and user directly in DB."""
    async with async_session_factory() as session:
        org = Organization(name="Test Org", slug="test-org-123")
        session.add(org)
        await session.flush()

        user = User(
            organization_id=org.id,
            email="test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Test User",
            role="ADMIN",
        )
        session.add(user)
        await session.commit()

        token = create_access_token(user.id)
        yield {"org": org, "user": user, "token": token}
        await session.close()


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_returns_tokens(client, test_org_and_user):
    """Test login returns valid tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login fails with wrong password."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client):
    """Test that protected endpoints require authentication."""
    response = await client.get("/api/v1/plans")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, test_org_and_user):
    """Test /auth/me returns current user."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "ADMIN"
