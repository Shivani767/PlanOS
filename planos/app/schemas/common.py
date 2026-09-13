"""Common schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ImportStatusResponse(BaseModel):
    id: str
    filename: str
    status: str
    records_received: int
    records_valid: int
    records_invalid: int
    error_summary: str | None = None


class ApprovalCreateRequest(BaseModel):
    action_type: str
    action_details: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision_reason: str | None = None


class ApprovalResponse(BaseModel):
    id: str
    organization_id: str
    action_type: str
    action_details: dict[str, Any]
    status: str
    reason: str | None = None
    decision_reason: str | None = None
    created_at: str
