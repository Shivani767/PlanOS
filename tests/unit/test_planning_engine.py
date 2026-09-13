"""Tests for the deterministic planning engine."""

from __future__ import annotations

import pytest

from planos.app.planning.calculator import PlanningEngine
from planos.app.planning.engine import PlanningMetrics, ScenarioChanges


class TestPlanningEngine:
    """Test deterministic planning calculations."""

    def test_calculate_revenue(self):
        assert PlanningEngine.calculate_revenue(100, 50) == 5000
        assert PlanningEngine.calculate_revenue(0, 100) == 0
        assert PlanningEngine.calculate_revenue(200, 25.5) == 5100

    def test_calculate_gross_profit(self):
        assert PlanningEngine.calculate_gross_profit(10000, 6000) == 4000
        assert PlanningEngine.calculate_gross_profit(5000, 5000) == 0
        assert PlanningEngine.calculate_gross_profit(3000, 4000) == -1000

    def test_calculate_profit(self):
        assert PlanningEngine.calculate_profit(10000, 6000, 2000) == 2000
        assert PlanningEngine.calculate_profit(10000, 8000, 2500) == -500

    def test_calculate_capacity_utilization(self):
        assert PlanningEngine.calculate_capacity_utilization(80, 100) == 80.0
        assert PlanningEngine.calculate_capacity_utilization(100, 100) == 100.0
        assert PlanningEngine.calculate_capacity_utilization(50, 0) == 0.0

    def test_calculate_inventory_requirement(self):
        assert PlanningEngine.calculate_inventory_requirement(100, 1.2) == 120
        assert PlanningEngine.calculate_inventory_requirement(200) == 240
        assert PlanningEngine.calculate_inventory_requirement(0) == 0
