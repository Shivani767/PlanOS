"""Integration tests for agentic + governance APIs (flagship workflow, Phases 4-14)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.security import create_access_token, hash_password
from planos.app.models import ApprovalRequest, ChangeSet, Organization, Plan, PlanVersion, User

if TYPE_CHECKING:
    from httpx import AsyncClient


async def _make_org_user(
    session: AsyncSession, role: str = "ADMIN"
) -> tuple[Organization, User, str]:
    """Fresh org + user (uuid slug/email: collision-free across runs)."""
    suffix = uuid.uuid4().hex[:10]
    org = Organization(name=f"Org {suffix}", slug=f"agent-{suffix}")
    session.add(org)
    await session.flush()
    user = User(
        organization_id=org.id,
        email=f"agent-{suffix}@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test User",
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(org)
    await session.refresh(user)
    return org, user, create_access_token(user.id)


async def _seed_plan_with_data(session: AsyncSession, org_id: str, user_id: str) -> Plan:
    """Plan with 4 identical rows -> deterministic 35% baseline margin."""
    from planos.app.models.dimension import Department, Product, Region, TimePeriod
    from planos.app.models.planning_data import PlanningData

    plan = Plan(organization_id=org_id, name="2025 Plan", status="active",
                current_version=1, created_by=user_id)
    session.add(plan)
    await session.flush()
    session.add(PlanVersion(plan_id=plan.id, version=1, data={}, created_by=user_id))
    suffix = uuid.uuid4().hex[:8]
    prod = Product(organization_id=org_id, name="P", sku=f"SKU-{suffix}",
                   unit_price=50, unit_cost=25)
    reg = Region(organization_id=org_id, name="NA", code=f"NA-{suffix}")
    dept = Department(organization_id=org_id, name="Sales", code=f"SALES-{suffix}")
    period = TimePeriod(organization_id=org_id, year=2025, month=1,
                        quarter=1, label="2025-Q1")
    session.add_all([prod, reg, dept, period])
    await session.flush()
    for _ in range(4):
        session.add(PlanningData(
            organization_id=org_id, plan_id=plan.id, product_id=prod.id,
            region_id=reg.id, department_id=dept.id, period_id=period.id,
            units=100, price=50, cost=2500, revenue=5000, headcount=10,
            capacity=130, inventory=40, marketing_budget=1000))
    await session.commit()
    return plan


@pytest.mark.asyncio
async def test_agent_workflow_end_to_end(client: AsyncClient, session: AsyncSession) -> None:
    """Flagship demo: planner -> analyst -> executor -> reviewer -> approval -> commit."""
    org, user, token = await _make_org_user(session)
    plan = await _seed_plan_with_data(session, org.id, user.id)
    plan_id = plan.id
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/agents/plan", headers=headers,
        json={"plan_id": plan_id,
              "goal": "Increase demand by 30% and keep headcount unchanged."})
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["run_id"]
    assert body["status"] == "completed"

    step_types = {s["agent"] for s in body["trace"]["steps"]}
    assert {"plan", "review"} <= step_types
    tool_names = {c["tool"] for c in body["trace"]["tool_calls"]}
    assert {"get_metrics", "create_scenario", "run_scenario"} <= tool_names
    # aggressive variant (demand x1.5) wins: +4.66pts margin, above the 2pt bar
    assert "Recommendation: aggressive" in (body["output"] or "")

    approvals = (
        await session.execute(
            select(ApprovalRequest).where(ApprovalRequest.organization_id == org.id)
        )
    ).scalars().all()
    change_sets = (
        await session.execute(
            select(ChangeSet).where(ChangeSet.organization_id == org.id)
        )
    ).scalars().all()
    assert len(approvals) == 1, "expected exactly one approval request for this org"
    assert len(change_sets) == 1, "expected exactly one change set for this org"
    assert approvals[0].status == "pending"

    resp = await client.post(
        f"/api/v1/approvals/{approvals[0].id}/approve",
        headers=headers, json={"reason": "recommended scenario meets the bar"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"

    cs = await session.get(ChangeSet, change_sets[0].id)
    plan_after = await session.get(Plan, plan_id)
    assert cs is not None and cs.status == "applied"
    assert plan_after is not None and plan_after.current_version >= 2


@pytest.mark.asyncio
async def test_small_change_does_not_trigger_approval(
    client: AsyncClient, session: AsyncSession
) -> None:
    """+1% demand stays under the 2pt margin bar: no ChangeSet, no approval."""
    org, user, token = await _make_org_user(session)
    plan = await _seed_plan_with_data(session, org.id, user.id)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/agents/plan", headers=headers,
        json={"plan_id": plan.id, "goal": "Increase demand by 1%."})
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert "none meets the 2% margin bar" in (body["output"] or "")
    approvals = (
        await session.execute(
            select(ApprovalRequest).where(ApprovalRequest.organization_id == org.id)
        )
    ).scalars().all()
    assert approvals == []


@pytest.mark.asyncio
async def test_knowledge_is_tenant_scoped(client: AsyncClient, session: AsyncSession) -> None:
    """RAG respects tenant boundaries: org B must not retrieve org A's documents."""
    _, _, token_a = await _make_org_user(session)
    _, _, token_b = await _make_org_user(session)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = await client.post(
        "/api/v1/knowledge/documents", headers=headers_a,
        json={"title": "Pricing Policy",
              "content": "Enterprise pricing policy: minimum margin 20%.",
              "document_type": "policy"})
    assert resp.status_code == 201, resp.text
    resp_a = await client.get("/api/v1/knowledge/search", headers=headers_a,
                              params={"q": "pricing"})
    assert resp_a.status_code == 200
    assert resp_a.json()["chunks"]
    resp_b = await client.get("/api/v1/knowledge/search", headers=headers_b,
                              params={"q": "pricing"})
    assert resp_b.status_code == 200
    assert resp_b.json()["chunks"] == []


@pytest.mark.asyncio
async def test_tools_list_per_role(client: AsyncClient, session: AsyncSession) -> None:
    """Tool registry visibility follows the caller's role (Phase 6)."""
    _, _, token = await _make_org_user(session, role="VIEWER")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/agents/tools", headers=headers)
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()}
    assert "get_plan" in names
    assert "create_scenario" not in names
