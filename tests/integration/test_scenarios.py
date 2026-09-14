"""Integration tests for scenario operations."""

from __future__ import annotations

import uuid

import pytest


async def _create_plan(client, headers: dict) -> str:
    """Create a baseline plan and return its ID."""
    resp = await client.post(
        "/api/v1/plans", headers=headers, json={"name": f"Baseline {uuid.uuid4().hex[:6]}"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_scenario(client, unique_org_user):
    """Test scenario creation."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}
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
async def test_list_scenarios(client, unique_org_user):
    """Test listing scenarios."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}
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
async def test_get_scenario(client, unique_org_user):
    """Test getting a specific scenario."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}
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
async def test_run_scenario_returns_job_id(client, unique_org_user):
    """Test scenario run returns job ID immediately."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}
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
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_run_scenario_invalid_plan(client, unique_org_user):
    """Test scenario creation with non-existent plan fails."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}

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
async def test_delete_scenario(client, unique_org_user):
    """Test scenario deletion."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}
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
