"""Common schemas."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


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
    error_summary: Optional[str] = None


class ApprovalCreateRequest(BaseModel):
    action_type: str
    action_details: dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision_reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    organization_id: str
    action_type: str
    action_details: dict[str, Any]
    status: str
    reason: Optional[str] = None
    decision_reason: Optional[str] = None
    created_at: str
