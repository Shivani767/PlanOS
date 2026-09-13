"""Organization service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError, ValidationError
from planos.app.models import Organization
from planos.app.schemas.auth import OrganizationCreate


class OrganizationService:
    """Service for organization operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: OrganizationCreate) -> Organization:
        """Create a new organization."""
        # Check slug uniqueness
        existing = await self.session.execute(
            select(Organization).where(Organization.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Organization slug '{data.slug}' already exists")

        org = Organization(name=data.name, slug=data.slug)
        self.session.add(org)
        await self.session.commit()
        await self.session.refresh(org)
        return org

    async def get_by_id(self, org_id: str) -> Organization:
        """Get organization by ID."""
        result = await self.session.execute(select(Organization).where(Organization.id == org_id))
        org = result.scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization", org_id)
        return org

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Get organization by slug."""
        result = await self.session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()
