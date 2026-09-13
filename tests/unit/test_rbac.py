"""Tests for Role-Based Access Control."""

from __future__ import annotations

from planos.app.core.permissions import (
    Permission,
    Role,
    get_role_permissions,
    has_permission,
)


class TestRBAC:
    """Test role-based access control."""

    def test_admin_has_all_permissions(self):
        """ADMIN role should have all permissions."""
        admin_perms = get_role_permissions(Role.ADMIN)
        all_perms = set(Permission)
        assert admin_perms == all_perms

    def test_viewer_limited_permissions(self):
        """VIEWER should only have read permissions."""
        viewer_perms = get_role_permissions(Role.VIEWER)
        assert Permission.PLAN_READ in viewer_perms
        assert Permission.SCENARIO_READ in viewer_perms
        assert Permission.AGENT_READ in viewer_perms
        assert Permission.PLAN_CREATE not in viewer_perms
        assert Permission.BASELINE_MODIFY not in viewer_perms

    def test_planner_permissions(self):
        """PLANNER should have planning permissions."""
        planner_perms = get_role_permissions(Role.PLANNER)
        assert Permission.PLAN_CREATE in planner_perms
        assert Permission.PLAN_UPDATE in planner_perms
        assert Permission.SCENARIO_CREATE in planner_perms
        assert Permission.SCENARIO_RUN in planner_perms
        assert Permission.BASELINE_MODIFY in planner_perms
        assert Permission.ORG_MANAGE not in planner_perms

    def test_analyst_permissions(self):
        """ANALYST should have read and scenario permissions."""
        analyst_perms = get_role_permissions(Role.ANALYST)
        assert Permission.PLAN_READ in analyst_perms
        assert Permission.SCENARIO_CREATE in analyst_perms
        assert Permission.SCENARIO_RUN in analyst_perms
        assert Permission.PLAN_UPDATE not in analyst_perms
        assert Permission.BASELINE_MODIFY not in analyst_perms

    def test_has_permission_valid_role(self):
        """Test has_permission with valid roles."""
        assert has_permission("ADMIN", Permission.PLAN_DELETE) is True
        assert has_permission("VIEWER", Permission.PLAN_READ) is True
        assert has_permission("VIEWER", Permission.PLAN_CREATE) is False

    def test_has_permission_invalid_role(self):
        """Test has_permission with invalid role."""
        assert has_permission("INVALID_ROLE", Permission.PLAN_READ) is False

    def test_approval_permissions(self):
        """Test approval-related permissions."""
        assert has_permission("ADMIN", Permission.APPROVAL_APPROVE) is True
        assert has_permission("PLANNER", Permission.APPROVAL_REQUEST) is True
        assert has_permission("VIEWER", Permission.APPROVAL_REQUEST) is False

    def test_import_permissions(self):
        """Test import-related permissions."""
        assert has_permission("ADMIN", Permission.IMPORT_CREATE) is True
        assert has_permission("PLANNER", Permission.IMPORT_CREATE) is True
        assert has_permission("ANALYST", Permission.IMPORT_READ) is True
        assert has_permission("ANALYST", Permission.IMPORT_CREATE) is False
