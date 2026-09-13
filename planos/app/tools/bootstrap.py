"""Bind handlers to registry (single call site, idempotent)."""

from __future__ import annotations

from planos.app.core.permissions import Permission
from planos.app.tools.read_tools import (
    handle_create_scenario,
    handle_get_metrics,
    handle_get_plan,
)
from planos.app.tools.registry import (
    CompareScenariosInput,
    CreateChangeRequestInput,
    CreateScenarioInput,
    GetMetricsInput,
    GetPlanInput,
    RunScenarioInput,
    SearchKnowledgeInput,
    ToolDefinition,
    registry,
)
from planos.app.tools.write_tools import (
    handle_compare_scenarios,
    handle_create_change_request,
    handle_run_scenario,
    handle_search_knowledge,
)


def register_tools() -> None:
    if registry.get("get_plan") is not None:
        return
    registry.register(
        ToolDefinition(
            name="get_plan",
            description="Fetch plan metadata (tenant-scoped).",
            input_schema=GetPlanInput,
            required_permission=Permission.PLAN_READ,
            risk="low",
            handler=handle_get_plan,
        )
    )
    registry.register(
        ToolDefinition(
            name="get_metrics",
            description="Aggregate a planning metric for a plan.",
            input_schema=GetMetricsInput,
            required_permission=Permission.PLAN_READ,
            risk="low",
            handler=handle_get_metrics,
        )
    )
    registry.register(
        ToolDefinition(
            name="create_scenario",
            description="Create scenario from assumptions.",
            input_schema=CreateScenarioInput,
            required_permission=Permission.SCENARIO_CREATE,
            risk="medium",
            handler=handle_create_scenario,
        )
    )
    registry.register(
        ToolDefinition(
            name="run_scenario",
            description="Run deterministic scenario calculation.",
            input_schema=RunScenarioInput,
            required_permission=Permission.SCENARIO_RUN,
            risk="medium",
            handler=handle_run_scenario,
        )
    )
    registry.register(
        ToolDefinition(
            name="compare_scenarios",
            description="Compare two scenarios' results.",
            input_schema=CompareScenariosInput,
            required_permission=Permission.SCENARIO_READ,
            risk="low",
            handler=handle_compare_scenarios,
        )
    )
    registry.register(
        ToolDefinition(
            name="create_change_request",
            description="Propose governed ChangeSet + human approval.",
            input_schema=CreateChangeRequestInput,
            required_permission=Permission.APPROVAL_REQUEST,
            risk="high",
            handler=handle_create_change_request,
        )
    )
    registry.register(
        ToolDefinition(
            name="search_knowledge",
            description="Tenant-scoped enterprise knowledge search.",
            input_schema=SearchKnowledgeInput,
            required_permission=Permission.PLAN_READ,
            risk="low",
            handler=handle_search_knowledge,
        )
    )
