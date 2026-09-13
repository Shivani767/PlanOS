"""Scenario schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    base_plan_id: str
    description: str | None = None
    changes: dict[str, Any] = Field(default_factory=dict)


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    base_plan_id: str
    name: str
    description: str | None
    status: str
    changes: dict[str, Any]
    results: dict[str, Any] | None
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
