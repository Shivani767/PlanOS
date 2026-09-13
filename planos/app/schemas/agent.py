"""Agent schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., pattern=r"^(planning|finance|workforce|analyst)$")
    input_text: str = Field(..., min_length=1, max_length=10000)


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    step_number: int
    step_type: str
    content: dict[str, Any]
    created_at: datetime


class AgentToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: Optional[dict[str, Any]]
    status: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    agent_id: str
    status: str
    input_text: str
    output_text: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    steps: list[AgentStepResponse] = []
