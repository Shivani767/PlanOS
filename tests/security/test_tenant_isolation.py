"""Security tests for tenant isolation."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from planos.app.main import create_app
from planos.app.db.session import async_session_factory
from planos.app.models import Organization, User
from planos.app.core.security import hash_password, create_access_token


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def two_orgs():
    async with async_session_factory() as session:
        org_a = Organization(name="Org A", slug="org-a-sec")
        org_b = Organization(name="Org B", slug="org-b-sec")
        session.add_all([org_a, org_b])
        await session.flush()

        user_a = User(organization_id=org_a.id, email="admin@org-a.com",
                      hashed_password=hash_password("password123"),
                      full_name="Admin A", role="ADMIN")
        user_b = User(organization_id=org_b.id, email="admin@org-b.com",
                      hashed_password=hash_password("password123"),
                      full_name="Admin B", role="ADMIN")
        session.add_all([user_a, user_b])
        await session.commit()

        token_a = create_access_token(user_a.id)
        token_b = create_access_token(user_b.id)
        yield {"org_a": org_a.id, "org_b": org_b.id, "token_a": token_a, "token_b": token_b}
        await session.close()


async def _create_plan(client, headers: dict) -> str:
    resp = await client.post("/api/v1/plans", headers=headers, json={"name": "Test Plan"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_cross_tenant_plan_access(client, two_orgs):
    headers_a = {"Authorization": f"Bearer {two_orgs['token_a']}"}
    headers_b = {"Authorization": f"Bearer {two_orgs['token_b']}"}
    plan_id = await _create_plan(client, headers_a)
    resp = await client.get(f"/api/v1/plans/{plan_id}", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_update_denied(client, two_orgs):
    headers_a = {"Authorization": f"Bearer {two_orgs['token_a']}"}
    headers_b = {"Authorization": f"Bearer {two_orgs['token_b']}"}
    plan_id = await _create_plan(client, headers_a)
    resp = await client.patch(
        f"/api/v1/plans/{plan_id}", headers=headers_b,
        json={"name": "Hacked", "expected_version": 1},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_delete_denied(client, two_orgs):
    headers_a = {"Authorization": f"Bearer {two_orgs['token_a']}"}
    headers_b = {"Authorization": f"Bearer {two_orgs['token_b']}"}
    plan_id = await _create_plan(client, headers_a)
    resp = await client.delete(f"/api/v1/plans/{plan_id}", headers=headers_b)
    assert resp.status_code == 404
    verify = await client.get(f"/api/v1/plans/{plan_id}", headers=headers_a)
    assert verify.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_create_plan(client, two_orgs):
    async with async_session_factory() as session:
        viewer = User(organization_id=two_orgs["org_a"], email="viewer@org-a.com",
                      hashed_password=hash_password("password123"),
                      full_name="Viewer", role="VIEWER")
        session.add(viewer)
        await session.commit()
        token = create_access_token(viewer.id)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/plans", headers=headers, json={"name": "Test"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_denied(client):
    resp = await client.get("/api/v1/plans")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    headers = {"Authorization": "Bearer invalid.token"}
    resp = await client.get("/api/v1/plans", headers=headers)
    assert resp.status_code == 401
