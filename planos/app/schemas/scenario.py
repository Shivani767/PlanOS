"""Scenario schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    base_plan_id: str
    description: Optional[str] = None
    changes: dict[str, Any] = Field(default_factory=dict)


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    base_plan_id: str
    name: str
    description: Optional[str]
    status: str
    changes: dict[str, Any]
    results: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ScenarioRunResponse(BaseModel):
    job_id: str
    status: str


class ScenarioCompareRequest(BaseModel):
    scenario_a_id: str
    scenario_b_id: str


class ScenarioCompareResponse(BaseModel):
    scenario_a: ScenarioResponse
    scenario_b: ScenarioResponse
    comparison: dict[str, Any]


class ScenarioListResponse(BaseModel):
    items: list[ScenarioResponse]
    total: int
    page: int
    page_size: int
