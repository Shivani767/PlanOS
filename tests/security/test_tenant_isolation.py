"""Security tests for tenant isolation."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.security import create_access_token, hash_password
from planos.app.models import Organization, User


@pytest_asyncio.fixture
async def two_orgs(session: AsyncSession) -> dict:
    """Two isolated organizations with unique slugs (collision-free across runs)."""
    import uuid

    slug_a = f"org-a-{uuid.uuid4().hex[:10]}"
    slug_b = f"org-b-{uuid.uuid4().hex[:10]}"
    org_a = Organization(name="Org A", slug=slug_a)
    org_b = Organization(name="Org B", slug=slug_b)
    session.add_all([org_a, org_b])
    await session.flush()

    user_a = User(organization_id=org_a.id, email=f"admin-{uuid.uuid4().hex[:8]}@org-a.com",
                  hashed_password=hash_password("password123"),
                  full_name="Admin A", role="ADMIN")
    user_b = User(organization_id=org_b.id, email=f"admin-{uuid.uuid4().hex[:8]}@org-b.com",
                  hashed_password=hash_password("password123"),
                  full_name="Admin B", role="ADMIN")
    session.add_all([user_a, user_b])
    await session.commit()
    await session.refresh(org_a)
    await session.refresh(org_b)
    await session.refresh(user_a)
    await session.refresh(user_b)

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)
    yield {"org_a": org_a.id, "org_b": org_b.id, "token_a": token_a, "token_b": token_b}


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
async def test_viewer_cannot_create_plan(client, session, two_orgs):
    viewer = User(organization_id=two_orgs["org_a"], email="viewer@org-a.com",
                  hashed_password=hash_password("password123"),
                  full_name="Viewer", role="VIEWER")
    session.add(viewer)
    await session.commit()
    await session.refresh(viewer)
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
