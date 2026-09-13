"""Integration tests for API endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_returns_tokens(client, unique_org_user):
    """Test login returns valid tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": unique_org_user["user"].email,
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"  # noqa: S105


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, unique_org_user):
    """Test login fails with wrong password."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": unique_org_user["user"].email,
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
async def test_get_me(client, unique_org_user):
    """Test /auth/me returns current user."""
    headers = {"Authorization": f"Bearer {unique_org_user['token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == unique_org_user["user"].email
    assert data["full_name"] == "Test User"
    assert data["role"] == "ADMIN"
