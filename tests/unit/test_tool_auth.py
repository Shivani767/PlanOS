"""Tool authorization matrix tests (Phases 5-6): permission + policy gates."""

from __future__ import annotations

import pytest

from planos.app.core.permissions import Permission, get_role_permissions
from planos.app.tools.bootstrap import register_tools
from planos.app.tools.registry import registry

register_tools()


@pytest.mark.parametrize(
    ("role", "tool", "allowed"),
    [
        ("ADMIN", "get_plan", True),
        ("ADMIN", "create_change_request", True),
        ("PLANNER", "create_scenario", True),
        ("PLANNER", "get_plan", True),
        ("ANALYST", "create_scenario", True),
        # ANALYST holds approval:request permission (RBAC) ...
        ("ANALYST", "create_change_request", True),
        # ... but the policy engine additionally denies execution (see test_agent_policy).
        ("VIEWER", "get_plan", True),
        ("VIEWER", "compare_scenarios", True),
        ("VIEWER", "create_scenario", False),
        ("VIEWER", "run_scenario", False),
    ],
)
def test_permission_matrix(role: str, tool: str, allowed: bool) -> None:
    permitted = get_role_permissions(role)
    definition = registry.get(tool)
    assert definition is not None
    assert (definition.required_permission in permitted) is allowed


def test_all_tools_have_metadata() -> None:
    for tool in registry.list_definitions():
        assert tool.name and tool.description and tool.input_schema is not None
        assert isinstance(tool.required_permission, Permission)
        assert tool.risk in {"low", "medium", "high"}
