"""Integration tests for scenario operations."""

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
        org = Organization(name="Test Org Scenarios", slug="test-org-scenarios")
        session.add(org)
        await session.flush()

        user = User(
            organization_id=org.id,
            email="scenarios@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Scenarios User",
            role="ADMIN",
        )
        session.add(user)
        await session.commit()

        token = create_access_token(user.id)
        yield {"org": org, "user": user, "token": token}
        await session.close()


async def _create_plan(client, headers: dict) -> str:
    """Helper to create a plan and return its ID."""
    resp = await client.post(
        "/api/v1/plans",
        headers=headers,
        json={"name": "Base Plan for Scenario"},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_scenario(client, test_org_and_user):
    """Test scenario creation."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    plan_id = await _create_plan(client, headers)

    response = await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "Test Scenario",
            "base_plan_id": plan_id,
            "changes": {"demand_growth": 0.15},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Scenario"
    assert data["status"] == "draft"
    assert data["changes"]["demand_growth"] == 0.15


@pytest.mark.asyncio
async def test_list_scenarios(client, test_org_and_user):
    """Test listing scenarios."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    plan_id = await _create_plan(client, headers)

    await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "Scenario 1",
            "base_plan_id": plan_id,
            "changes": {"demand_growth": 0.10},
        },
    )

    response = await client.get("/api/v1/scenarios", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_scenario(client, test_org_and_user):
    """Test getting a specific scenario."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    plan_id = await _create_plan(client, headers)

    create_resp = await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "Get Test Scenario",
            "base_plan_id": plan_id,
            "changes": {"demand_growth": 0.20},
        },
    )
    scenario_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/scenarios/{scenario_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == scenario_id


@pytest.mark.asyncio
async def test_run_scenario_returns_job_id(client, test_org_and_user):
    """Test scenario run returns job ID immediately."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    plan_id = await _create_plan(client, headers)

    scenario_resp = await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "Run Scenario",
            "base_plan_id": plan_id,
            "changes": {"demand_growth": 0.10},
        },
    )
    scenario_id = scenario_resp.json()["id"]

    response = await client.post(
        f"/api/v1/scenarios/{scenario_id}/run",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_run_scenario_invalid_plan(client, test_org_and_user):
    """Test scenario creation with non-existent plan fails."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}

    response = await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "Invalid Scenario",
            "base_plan_id": "non-existent-id",
            "changes": {"demand_growth": 0.10},
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scenario(client, test_org_and_user):
    """Test scenario deletion."""
    headers = {"Authorization": f"Bearer {test_org_and_user['token']}"}
    plan_id = await _create_plan(client, headers)

    create_resp = await client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "name": "Delete Scenario",
            "base_plan_id": plan_id,
            "changes": {"demand_growth": 0.05},
        },
    )
    scenario_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/scenarios/{scenario_id}", headers=headers)
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/scenarios/{scenario_id}", headers=headers)
    assert get_resp.status_code == 404
