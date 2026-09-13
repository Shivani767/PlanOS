"""Plan schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class PlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(None, pattern=r"^(draft|active|archived)$")
    expected_version: int = Field(..., ge=1)


class PlanVersionCreate(BaseModel):
    data: dict[str, Any]


class PlanVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    version: int
    data: dict[str, Any]
    created_at: datetime


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    description: str | None
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class PlanListResponse(BaseModel):
    items: list[PlanResponse]
    total: int
    page: int
    page_size: int
