"""Agent evaluation framework for PlanOS."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel


class EvalCase(BaseModel):
    """Single evaluation case."""
    id: str
    name: str
    description: str
    input: str
    expected_tools: list[str]
    expected_output_properties: dict[str, Any] = {}
    allowed_tools: list[str] = []
    tags: list[str] = []
    difficulty: str = "medium"


class EvalResult(BaseModel):
    """Result of running a single evaluation case."""
    case_id: str
    success: bool
    tools_selected: list[str]
    tools_correct: bool
    output_valid: bool
    policy_violations: int = 0
    latency_ms: float = 0.0
    tokens_used: int = 0
    error: Optional[str] = None
    details: dict[str, Any] = {}


class EvalReport(BaseModel):
    """Complete evaluation report."""
    run_id: str
    agent_name: str
    model: str
    prompt_version: str
    timestamp: str
    total_cases: int
    successful_cases: int
    failed_cases: int
    task_success_rate: float
    tool_accuracy: float
    policy_violation_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_tokens: float
    results: list[EvalResult] = []
