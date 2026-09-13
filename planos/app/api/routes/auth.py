"""Authentication routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.api.dependencies import AuthenticatedUser, get_current_user
from planos.app.core.exceptions import PlanOSError
from planos.app.db.session import get_session
from planos.app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserMeResponse,
    UserRegister,
    UserResponse,
)
from planos.app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """Register a new user in an existing organization."""
    service = AuthService(session)
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Authenticate and receive access/refresh tokens."""
    service = AuthService(session)
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    """Refresh access token."""
    service = AuthService(session)
    return await service.refresh(data.refresh_token)


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserMeResponse:
    """Get current user profile."""
    service = AuthService(session)
    user = await service.get_user_by_id(current_user.user_id)
    if not user:
        raise PlanOSError("User not found", "USER_NOT_FOUND")
    return UserMeResponse(
        id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_name=user.organization.name if user.organization else "",
    )
