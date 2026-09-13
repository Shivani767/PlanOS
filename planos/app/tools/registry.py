"""Typed tool registry (Phase 5): the ONLY path from agents to domain services.

Every tool: Pydantic I/O, required permission, risk level, approval flag.
Pipeline per call: schema -> auth -> policy -> domain validation -> execution.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import ForbiddenError, PolicyDeniedError
from planos.app.core.logging import get_logger
from planos.app.core.permissions import Permission
from planos.app.observability.metrics import observe_tool
from planos.app.policies.engine import evaluate_tool

logger = get_logger(__name__)

ToolFn = Callable[..., Awaitable[dict[str, Any]]]


class GetPlanInput(BaseModel):
    plan_id: str = Field(min_length=1, max_length=36)


class GetMetricsInput(BaseModel):
    plan_id: str = Field(min_length=1, max_length=36)
    metric: str = Field(default="revenue", max_length=50)


class CreateScenarioInput(BaseModel):
    plan_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=255)
    assumptions: dict[str, Any] = Field(default_factory=dict)


class RunScenarioInput(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=36)


class CompareScenariosInput(BaseModel):
    baseline_id: str = Field(min_length=1, max_length=36)
    scenario_id: str = Field(min_length=1, max_length=36)


class CreateChangeRequestInput(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=36)
    summary: str = Field(default="", max_length=2000)


class SearchKnowledgeInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: type[BaseModel]
    required_permission: Permission
    risk: str = "low"  # low | medium | high
    requires_approval: bool = False
    handler: ToolFn | None = None
    extra_permissions: set[Permission] = field(default_factory=set)


class ToolRegistry:
    """Central registry; handlers bound to domain services at call time."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def for_role(self, permissions: set[Permission]) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.required_permission in permissions]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(
        self,
        name: str,
        raw_args: dict[str, Any],
        *,
        session: AsyncSession,
        organization_id: str,
        user_id: str,
        role: str,
        user_permissions: set[Permission],
        run_id: str | None = None,
    ) -> dict[str, Any]:
        from planos.app.models.tool_call import ToolCall

        tool = self.get(name)
        if tool is None:
            raise ForbiddenError(f"Unknown tool '{name}'")
        if tool.required_permission not in user_permissions:
            raise ForbiddenError(f"Permission denied: {tool.required_permission.value} required")
        validated = tool.input_schema(**raw_args)
        decision = evaluate_tool(name, role, validated.model_dump())
        if decision.verdict == "deny":
            raise PolicyDeniedError(decision.reason)
        if decision.verdict == "require_approval" or tool.requires_approval:
            raise PolicyDeniedError(decision.reason or "Approval required", requires_approval=True)
        assert tool.handler is not None, f"Tool '{name}' has no handler"
        started = time.perf_counter()
        try:
            result = await tool.handler(
                validated,
                session=session,
                organization_id=organization_id,
                user_id=user_id,
                role=role,
            )
            ok, payload, err = True, result, None
        except Exception as exc:  # record then re-raise
            ok, payload, err = False, {}, str(exc)
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            observe_tool(name, ok)
            try:
                session.add(
                    ToolCall(
                        organization_id=organization_id,
                        run_id=run_id,
                        tool_name=name,
                        arguments=validated.model_dump(),
                        result=payload if ok else None,
                        status="success" if ok else "error",
                        error_message=err,
                        duration_ms=duration_ms,
                        invoked_by=user_id,
                    )
                )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.warning("tool_call_audit_failed", tool=name)
            logger.info(
                "tool_executed",
                tool=name,
                ok=ok,
                duration_ms=round(duration_ms, 2),
            )
        return payload


registry = ToolRegistry()
