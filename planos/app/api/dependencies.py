"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import ForbiddenError, UnauthorizedError
from planos.app.core.logging import get_logger
from planos.app.core.permissions import Permission, has_permission
from planos.app.core.security import decode_token
from planos.app.db.session import get_session
from planos.app.models import User

logger = get_logger(__name__)

security_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents the authenticated user context."""

    def __init__(self, user_id: str, organization_id: str, role: str, email: str):
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role
        self.email = email

    def has_permission(self, permission: Permission) -> bool:
        return has_permission(self.role, permission)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthenticatedUser:
    """Extract and validate the current user from JWT token."""
    if not credentials:
        raise UnauthorizedError("Authentication required")

    payload = decode_token(credentials.credentials)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token: no subject")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")

    return AuthenticatedUser(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role,
        email=user.email,
    )


async def require_permission(
    permission: Permission,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """Require a specific permission for the current user."""
    if not current_user.has_permission(permission):
        logger.warning(
            "permission_denied",
            user_id=current_user.user_id,
            required_permission=permission.value,
            role=current_user.role,
        )
        raise ForbiddenError(f"Permission denied: {permission.value} required")
    return current_user


def require_permission_factory(permission: Permission) -> Callable[..., Any]:
    """Create a dependency that requires a specific permission."""

    async def _dependency(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        return await require_permission(permission, current_user)

    return _dependency


async def get_request_id(request: Request) -> str:
    """Get or generate a request ID for tracing."""
    return request.headers.get("x-request-id", "") or ""
