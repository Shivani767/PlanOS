"""Deterministic planning engine for business calculations.

This module contains ALL business-critical calculations.
The LLM must NEVER perform these calculations.
All formulas are deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PlanningMetrics:
    """Core planning metrics for a single dimension combination."""
    units: float = 0.0
    price: float = 0.0
    cost: float = 0.0
    revenue: float = 0.0
    headcount: float = 0.0
    capacity: float = 0.0
    inventory: float = 0.0
    marketing_budget: float = 0.0
    operating_expenses: float = 0.0

    @property
    def gross_profit(self) -> float:
        return self.revenue - self.cost

    @property
    def profit(self) -> float:
        return self.gross_profit - self.operating_expenses

    @property
    def margin_pct(self) -> float:
        if self.revenue == 0:
            return 0.0
        return (self.profit / self.revenue) * 100

    @property
    def capacity_utilization(self) -> float:
        if self.capacity == 0:
            return 0.0
        return (self.units / self.capacity) * 100


@dataclass
class ScenarioChanges:
    """Changes to apply in a scenario."""
    demand_growth: float = 0.0
    marketing_budget_multiplier: float = 1.0
    supplier_capacity_multiplier: float = 1.0
    price_change: float = 0.0
    cost_change: float = 0.0
    headcount_change: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScenarioChanges:
        return cls(
            demand_growth=data.get("demand_growth", 0.0),
            marketing_budget_multiplier=data.get("marketing_budget_multiplier", 1.0),
            supplier_capacity_multiplier=data.get("supplier_capacity_multiplier", 1.0),
            price_change=data.get("price_change", 0.0),
            cost_change=data.get("cost_change", 0.0),
            headcount_change=data.get("headcount_change", 0.0),
        )


@dataclass
class CalculationResult:
    """Result of a scenario calculation."""
    period_label: str
    baseline: PlanningMetrics
    scenario: PlanningMetrics
    delta_revenue: float = 0.0
    delta_profit: float = 0.0
    delta_units: float = 0.0
    delta_cost: float = 0.0
    delta_headcount: float = 0.0
    delta_inventory: float = 0.0
