"""Integration tests for plan CRUD operations."""

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
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_org_and_user():
    async with async_session_factory() as session:
        org = Organization(name="Test Org Plans", slug="test-org-plans")
        session.add(org)
        await session.flush()

        user = User(
            organization_id=org.id,
            email="plans@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Plans User",
            role="ADMIN",
        )
        session.add(user)
        await session.commit()

        token = create_access_token(user.id)
        yield {"org": org, "user": user, "token": token}
        await session.close()


@pytest.mark.asyncio
async def test_create_plan(client, test_org_and_user):
    """Test plan creation."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    response = await client.post(
        "/api/v1/plans",
        headers=headers,
        json={"name": "Test Plan", "description": "A test plan"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Plan"
    assert data["status"] == "draft"
    assert data["current_version"] == 1


@pytest.mark.asyncio
async def test_list_plans(client, test_org_and_user):
    """Test listing plans."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}

    # Create a plan first
    await client.post(
        "/api/v1/plans",
        headers=headers,
        json={"name": "Plan 1"},
    )

    response = await client.get("/api/v1/plans", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_plan(client, test_org_and_user):
    """Test getting a specific plan."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}

    create_resp = await client.post(
        "/api/v1/plans",
        headers=headers,
        json={"name": "Get Test Plan"},
    )
    plan_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == plan_id


@pytest.mark.asyncio
async def test_update_plan_optimistic_lock(client, test_org_and_user):
    """Test optimistic concurrency control on plan updates."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}

    create_resp = await client.post(
        "/api/v1/plans",
        headers=headers,
        json={"name": "Lock Test Plan"},
    )
    plan_id = create_resp.json()["id"]

    # First update with correct version
    response1 = await client.patch(
        f"/api/v1/plans/{plan_id}",
        headers=headers,
        json={"name": "Updated Plan", "expected_version": 1},
    )
    assert response1.status_code == 200
    assert response1.json()["current_version"] == 2

    # Second update with stale version should fail
    response2 = await client.patch(
        f"/api/v1/plans/{plan_id}",
        headers=headers,
        json={"name": "Stale Update", "expected_version": 1},
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_delete_plan(client, test_org_and_user):
    """Test plan deletion."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}

    create_resp = await client.post(
        "/api/v1/plans",
        headers=headers,
        json={"name": "Delete Test Plan"},
    )
    plan_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/plans/{plan_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's gone
    get_resp = await client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    assert get_resp.status_code == 404
