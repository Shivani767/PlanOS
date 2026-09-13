"""Role-Based Access Control definitions."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    PLANNER = "PLANNER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class Permission(str, Enum):
    # Plan permissions
    PLAN_READ = "plan:read"
    PLAN_CREATE = "plan:create"
    PLAN_UPDATE = "plan:update"
    PLAN_DELETE = "plan:delete"

    # Scenario permissions
    SCENARIO_READ = "scenario:read"
    SCENARIO_CREATE = "scenario:create"
    SCENARIO_RUN = "scenario:run"
    SCENARIO_DELETE = "scenario:delete"

    # Baseline permissions
    BASELINE_MODIFY = "baseline:modify"

    # Approval permissions
    APPROVAL_REQUEST = "approval:request"
    APPROVAL_APPROVE = "approval:approve"

    # Import permissions
    IMPORT_CREATE = "import:create"
    IMPORT_READ = "import:read"

    # Agent permissions
    AGENT_EXECUTE = "agent:execute"
    AGENT_READ = "agent:read"

    # User management
    USER_MANAGE = "user:manage"
    ORG_MANAGE = "org:manage"


# Role-to-permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        Permission.PLAN_READ,
        Permission.PLAN_CREATE,
        Permission.PLAN_UPDATE,
        Permission.PLAN_DELETE,
        Permission.SCENARIO_READ,
        Permission.SCENARIO_CREATE,
        Permission.SCENARIO_RUN,
        Permission.SCENARIO_DELETE,
        Permission.BASELINE_MODIFY,
        Permission.APPROVAL_REQUEST,
        Permission.APPROVAL_APPROVE,
        Permission.IMPORT_CREATE,
        Permission.IMPORT_READ,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_READ,
        Permission.USER_MANAGE,
        Permission.ORG_MANAGE,
    },
    Role.PLANNER: {
        Permission.PLAN_READ,
        Permission.PLAN_CREATE,
        Permission.PLAN_UPDATE,
        Permission.SCENARIO_READ,
        Permission.SCENARIO_CREATE,
        Permission.SCENARIO_RUN,
        Permission.SCENARIO_DELETE,
        Permission.BASELINE_MODIFY,
        Permission.APPROVAL_REQUEST,
        Permission.IMPORT_CREATE,
        Permission.IMPORT_READ,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_READ,
    },
    Role.ANALYST: {
        Permission.PLAN_READ,
        Permission.SCENARIO_READ,
        Permission.SCENARIO_CREATE,
        Permission.SCENARIO_RUN,
        Permission.APPROVAL_REQUEST,
        Permission.IMPORT_READ,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_READ,
    },
    Role.VIEWER: {
        Permission.PLAN_READ,
        Permission.SCENARIO_READ,
        Permission.AGENT_READ,
    },
}


def has_permission(role: str | Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    try:
        role_enum = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(role_enum, set())


def get_role_permissions(role: str | Role) -> set[Permission]:
    """Get all permissions for a role."""
    try:
        role_enum = Role(role)
    except ValueError:
        return set()
    return ROLE_PERMISSIONS.get(role_enum, set())
