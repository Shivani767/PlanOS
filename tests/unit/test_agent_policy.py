"""Deterministic agent evaluation tests (Phase 24): mock LLM, test orchestration."""

from __future__ import annotations

import pytest

from planos.app.agents.interpreter import parse_assumptions
from planos.app.policies.engine import evaluate_assumptions, evaluate_tool


class TestInterpreter:
    def test_parses_demand_and_marketing(self):
        out = parse_assumptions("Increase demand by 15% and reduce marketing by 10%.")
        assert out["demand_growth"] == pytest.approx(0.15)
        assert "marketing_budget_multiplier" in out

    def test_headcount_pin(self):
        out = parse_assumptions("Keep headcount unchanged while growing demand 10%.")
        assert out["headcount_change"] == 0.0

    def test_empty_text_gives_empty(self):
        assert parse_assumptions("hello world") == {}


class TestPolicyEngine:
    def test_viewer_is_read_only(self):
        d = evaluate_tool("create_scenario", "VIEWER", {"assumptions": {}})
        assert d.verdict == "deny"

    def test_analyst_cannot_request_changes(self):
        d = evaluate_tool("create_change_request", "ANALYST", {})
        assert d.verdict == "deny"

    def test_large_assumption_needs_approval(self):
        d = evaluate_assumptions({"demand_growth": 0.8}, "PLANNER")
        assert d.verdict == "require_approval"
        assert d.requires_approval is True

    def test_out_of_bounds_denied(self):
        d = evaluate_assumptions({"demand_growth": 50.0}, "ADMIN")
        assert d.verdict == "deny"

    def test_small_assumption_allowed(self):
        d = evaluate_assumptions({"demand_growth": 0.05}, "PLANNER")
        assert d.verdict == "allow"

    def test_high_risk_tool_needs_approval(self):
        d = evaluate_tool("apply_change_set", "ADMIN", {})
        assert d.verdict == "require_approval"
