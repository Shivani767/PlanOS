"""Agent schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., pattern=r"^(planning|finance|workforce|analyst|planner)$")
    input_text: str = Field(..., min_length=1, max_length=10000)
    plan_id: str | None = Field(default=None, min_length=1, max_length=36)


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    step_number: int
    step_type: str
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    policy_decision: str | None = None
    duration_ms: float = 0.0
    created_at: datetime


class AgentToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    status: str
    error_message: str | None
    duration_ms: int | None
    created_at: datetime


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    agent_id: str
    status: str
    input_text: str | None = None
    output_text: str | None = None
    error_message: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    created_at: datetime
    completed_at: datetime | None = None
    steps: list[AgentStepResponse] = []
