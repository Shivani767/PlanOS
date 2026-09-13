"""Tests for scenario changes application."""

from __future__ import annotations

import pytest

from planos.app.planning.calculator import PlanningEngine
from planos.app.planning.engine import PlanningMetrics, ScenarioChanges


class TestScenarioChanges:
    """Test scenario changes application."""

    def test_apply_demand_growth(self):
        baseline = PlanningMetrics(units=100, price=50, cost=3000, revenue=5000)
        changes = ScenarioChanges(demand_growth=0.15)
        result = PlanningEngine.apply_scenario_changes(baseline, changes)
        assert round(result.units, 2) == 115
        assert round(result.revenue, 2) == 5750

    def test_apply_marketing_multiplier(self):
        baseline = PlanningMetrics(units=100, marketing_budget=10000, operating_expenses=5000)
        changes = ScenarioChanges(marketing_budget_multiplier=1.10)
        result = PlanningEngine.apply_scenario_changes(baseline, changes)
        assert result.marketing_budget == 11000
        assert result.operating_expenses == 6000

    def test_apply_supplier_capacity(self):
        baseline = PlanningMetrics(capacity=1000, units=800)
        changes = ScenarioChanges(supplier_capacity_multiplier=0.90)
        result = PlanningEngine.apply_scenario_changes(baseline, changes)
        assert result.capacity == 900

    def test_apply_combined_changes(self):
        baseline = PlanningMetrics(
            units=100, price=50, cost=3000, revenue=5000,
            marketing_budget=10000, capacity=1000, operating_expenses=5000,
        )
        changes = ScenarioChanges(
            demand_growth=0.15,
            marketing_budget_multiplier=1.10,
            supplier_capacity_multiplier=0.90,
        )
        result = PlanningEngine.apply_scenario_changes(baseline, changes)
        assert round(result.units, 2) == 115
        assert round(result.revenue, 2) == 5750
        assert result.capacity == 900
        assert result.marketing_budget == 11000

    def test_scenario_changes_from_dict(self):
        data = {
            "demand_growth": 0.15,
            "marketing_budget_multiplier": 1.10,
            "supplier_capacity_multiplier": 0.90,
        }
        changes = ScenarioChanges.from_dict(data)
        assert changes.demand_growth == 0.15
        assert changes.marketing_budget_multiplier == 1.10
        assert changes.supplier_capacity_multiplier == 0.90

    def test_scenario_impact_calculation(self):
        baseline_metrics = [
            PlanningMetrics(units=100, price=50, cost=3000, revenue=5000),
            PlanningMetrics(units=120, price=50, cost=3600, revenue=6000),
        ]
        changes = ScenarioChanges(demand_growth=0.10)
        results = PlanningEngine.calculate_scenario_impact(
            baseline_metrics, changes, ["Jan", "Feb"]
        )
        assert len(results) == 2
        assert results[0].period_label == "Jan"
        assert round(results[0].scenario.units, 2) == 110
        assert round(results[0].delta_units, 2) == 10

    def test_aggregate_results(self):
        baseline_metrics = [
            PlanningMetrics(units=100, price=50, cost=3000, revenue=5000, headcount=10),
            PlanningMetrics(units=200, price=50, cost=6000, revenue=10000, headcount=20),
        ]
        changes = ScenarioChanges(demand_growth=0.10)
        results = PlanningEngine.calculate_scenario_impact(
            baseline_metrics, changes, ["Jan", "Feb"]
        )
        aggregated = PlanningEngine.aggregate_results(results)
        assert round(aggregated["total_baseline_revenue"], 2) == 15000
        assert round(aggregated["total_scenario_revenue"], 2) == 16500
        assert round(aggregated["total_revenue_delta"], 2) == 1500


class TestPlanningMetrics:
    """Test PlanningMetrics computed properties."""

    def test_gross_profit(self):
        m = PlanningMetrics(revenue=10000, cost=6000)
        assert m.gross_profit == 4000

    def test_profit(self):
        m = PlanningMetrics(revenue=10000, cost=6000, operating_expenses=2000)
        assert m.profit == 2000

    def test_margin_pct(self):
        m = PlanningMetrics(revenue=10000, cost=6000, operating_expenses=2000)
        assert m.margin_pct == 20.0

    def test_margin_pct_zero_revenue(self):
        m = PlanningMetrics(revenue=0)
        assert m.margin_pct == 0.0

    def test_capacity_utilization(self):
        m = PlanningMetrics(units=80, capacity=100)
        assert m.capacity_utilization == 80.0

    def test_capacity_utilization_zero_capacity(self):
        m = PlanningMetrics(units=80, capacity=0)
        assert m.capacity_utilization == 0.0
