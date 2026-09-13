"""Seed data script for PlanOS.

Creates realistic seed data for development and demo.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from planos.app.core.config import settings
from planos.app.core.security import hash_password
from planos.app.db.session import Base
from planos.app.models import Organization, User
from planos.app.models.dimension import Product, Region, Department, TimePeriod
from planos.app.models.plan import Plan, PlanVersion
from planos.app.models.planning_data import PlanningData
from planos.app.models.scenario import Scenario

# Sample data
PRODUCT_NAMES = [
    ("Widget A", "WDG-001", "Widgets", 45.0, 22.0),
    ("Widget B", "WDG-002", "Widgets", 55.0, 28.0),
    ("Widget C", "WDG-003", "Widgets", 35.0, 18.0),
    ("Gadget X", "GDG-001", "Gadgets", 120.0, 65.0),
    ("Gadget Y", "GDG-002", "Gadgets", 95.0, 50.0),
    ("Gadget Z", "GDG-003", "Gadgets", 150.0, 80.0),
    ("Tool Pro", "TOL-001", "Tools", 200.0, 110.0),
    ("Tool Lite", "TOL-002", "Tools", 85.0, 45.0),
    ("Component Alpha", "CMP-001", "Components", 15.0, 8.0),
    ("Component Beta", "CMP-002", "Components", 22.0, 12.0),
    ("Component Gamma", "CMP-003", "Components", 18.0, 10.0),
    ("Assembly 101", "ASM-001", "Assemblies", 350.0, 190.0),
    ("Assembly 102", "ASM-002", "Assemblies", 420.0, 230.0),
    ("Assembly 103", "ASM-003", "Assemblies", 380.0, 205.0),
    ("Module X1", "MOD-001", "Modules", 75.0, 40.0),
    ("Module X2", "MOD-002", "Modules", 88.0, 48.0),
    ("Module X3", "MOD-003", "Modules", 110.0, 60.0),
    ("Service Pack A", "SVC-001", "Services", 500.0, 250.0),
    ("Service Pack B", "SVC-002", "Services", 750.0, 375.0),
    ("Service Pack C", "SVC-003", "Services", 1000.0, 500.0),
    ("Premium Suite", "PRM-001", "Premium", 1500.0, 750.0),
    ("Enterprise Bundle", "ENT-001", "Enterprise", 2500.0, 1250.0),
]

REGION_NAMES = [
    ("North America", "NA"),
    ("Europe", "EU"),
    ("Asia Pacific", "APAC"),
    ("Latin America", "LATAM"),
    ("Middle East & Africa", "MEA"),
    ("Oceania", "OCE"),
]

DEPARTMENT_NAMES = [
    ("Sales", "SALES"),
    ("Marketing", "MKT"),
    ("Operations", "OPS"),
    ("Finance", "FIN"),
    ("HR", "HR"),
    ("Engineering", "ENG"),
]

YEARMONTHS = [(2024, m) for m in range(1, 13)]


async def create_organizations(session: AsyncSession) -> tuple[Organization, Organization]:
    """Create test organizations."""
    acme = Organization(name="Acme Corp", slug="acme-corp")
    globex = Organization(name="Globex Inc", slug="globex-inc")
    session.add_all([acme, globex])
    await session.flush()
    return acme, globex


async def create_users(session: AsyncSession, acme: Organization, globex: Organization) -> list[User]:
    """Create test users."""
    users = [
        User(organization_id=acme.id, email="admin@acme.com",
             hashed_password=hash_password("password123"), full_name="Alice Admin", role="ADMIN"),
        User(organization_id=acme.id, email="planner@acme.com",
             hashed_password=hash_password("password123"), full_name="Paul Planner", role="PLANNER"),
        User(organization_id=acme.id, email="analyst@acme.com",
             hashed_password=hash_password("password123"), full_name="Anna Analyst", role="ANALYST"),
        User(organization_id=acme.id, email="viewer@acme.com",
             hashed_password=hash_password("password123"), full_name="Vince Viewer", role="VIEWER"),
        User(organization_id=globex.id, email="admin@globex.com",
             hashed_password=hash_password("password123"), full_name="Gina Admin", role="ADMIN"),
    ]
    session.add_all(users)
    await session.flush()
    return users


async def create_dimensions(session: AsyncSession, org_ids: list[str]) -> dict:
    """Create dimension data for organizations."""
    products, regions, departments, periods = [], [], [], []
    for org_id in org_ids:
        for name, sku, category, price, cost in PRODUCT_NAMES:
            products.append(Product(organization_id=org_id, name=name, sku=sku,
                                    category=category, unit_price=price, unit_cost=cost))
        for name, code in REGION_NAMES:
            regions.append(Region(organization_id=org_id, name=name, code=code))
        for name, code in DEPARTMENT_NAMES:
            departments.append(Department(organization_id=org_id, name=name, code=code))
        for year, month in YEARMONTHS:
            quarter = (month - 1) // 3 + 1
            periods.append(TimePeriod(organization_id=org_id, year=year, month=month,
                                     quarter=quarter, label=f"{year}-{month:02d}"))
    session.add_all(products + regions + departments + periods)
    await session.flush()
    return {"products": products, "regions": regions, "departments": departments, "periods": periods}


async def create_planning_data(session: AsyncSession, acme: Organization,
                                dimensions: dict, admin_user: User) -> None:
    """Create plans and planning data."""
    acme_products = [p for p in dimensions["products"] if p.organization_id == acme.id][:8]
    acme_regions = [r for r in dimensions["regions"] if r.organization_id == acme.id][:3]
    acme_depts = [d for d in dimensions["departments"] if d.organization_id == acme.id][:3]
    acme_periods = [p for p in dimensions["periods"] if p.organization_id == acme.id]

    plan1 = Plan(organization_id=acme.id, name="2024 Annual Plan",
                 description="Main annual operating plan", status="active",
                 current_version=1, created_by=admin_user.id)
    plan2 = Plan(organization_id=acme.id, name="Q4 Adjusted Forecast",
                 description="Updated Q4 forecast", status="draft",
                 current_version=1, created_by=admin_user.id)
    session.add_all([plan1, plan2])
    await session.flush()

    session.add_all([PlanVersion(plan_id=plan1.id, version=1, data={}, created_by=admin_user.id),
                     PlanVersion(plan_id=plan2.id, version=1, data={}, created_by=admin_user.id)])

    random.seed(42)
    planning_data = []
    for prod in acme_products:
        for region in acme_regions:
            for dept in acme_depts:
                for period in acme_periods:
                    units = float(random.randint(50, 500))
                    price = prod.unit_price
                    cost = prod.unit_cost * units
                    revenue = price * units
                    planning_data.append(PlanningData(
                        organization_id=acme.id, plan_id=plan1.id,
                        product_id=prod.id, region_id=region.id,
                        department_id=dept.id, period_id=period.id,
                        units=units, price=price, cost=cost, revenue=revenue,
                        headcount=float(random.randint(5, 50)),
                        capacity=float(int(units * 1.3)),
                        inventory=float(int(units * 0.4)),
                        marketing_budget=float(random.randint(5000, 50000)),
                    ))
    session.add_all(planning_data)
    await session.flush()

    scenario1 = Scenario(organization_id=acme.id, base_plan_id=plan1.id,
                         name="Q4 Demand Surge", description="15% demand increase",
                         changes={"demand_growth": 0.15, "marketing_budget_multiplier": 1.10},
                         status="draft", created_by=admin_user.id)
    scenario2 = Scenario(organization_id=acme.id, base_plan_id=plan1.id,
                         name="Supply Chain Disruption", description="Reduced capacity",
                         changes={"supplier_capacity_multiplier": 0.85, "cost_change": 0.10},
                         status="draft", created_by=admin_user.id)
    session.add_all([scenario1, scenario2])
    await session.commit()
    print(f"Seed data created: 2 orgs, 5 users, {len(planning_data)} records")


async def seed_database() -> None:
    """Seed the database with realistic test data."""
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        acme, globex = await create_organizations(session)
        users = await create_users(session, acme, globex)
        dims = await create_dimensions(session, [acme.id, globex.id])
        await create_planning_data(session, acme, dims, users[0])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())

