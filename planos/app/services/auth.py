"""Authentication service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from planos.app.core.exceptions import UnauthorizedError, ValidationError
from planos.app.core.logging import get_logger
from planos.app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from planos.app.models import Organization, User
from planos.app.schemas.auth import LoginRequest, TokenResponse, UserRegister

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, data: UserRegister) -> User:
        """Register a new user in an existing organization."""
        # Check if organization exists
        org_result = await self.session.execute(
            select(Organization).where(Organization.slug == data.organization_slug)
        )
        organization = org_result.scalar_one_or_none()
        if not organization:
            raise ValidationError(f"Organization '{data.organization_slug}' not found")

        # Check if email already exists
        existing = await self.session.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValidationError("Email already registered")

        user = User(
            organization_id=organization.id,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role="VIEWER",
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info("user_registered", user_id=user.id, email=user.email)
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return tokens."""
        result = await self.session.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        scopes = [f"org:{user.organization_id}", f"role:{user.role}"]
        access_token = create_access_token(user.id, scopes=scopes)
        refresh_token = create_refresh_token(user.id)

        logger.user_id = user.id
        logger.info("user_login", user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using a valid refresh token."""
        from planos.app.core.security import decode_token, verify_token_type

        payload = decode_token(refresh_token)
        if not payload or not verify_token_type(payload, "refresh"):
            raise UnauthorizedError("Invalid refresh token")

        user_id = payload.get("sub")
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        scopes = [f"org:{user.organization_id}", f"role:{user.role}"]
        new_access_token = create_access_token(user.id, scopes=scopes)
        new_refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=30 * 60,
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID with organization eagerly loaded."""
        result = await self.session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.organization))
        )
        return result.scalar_one_or_none()
