"""Deterministic planning calculation engine.

All calculations are pure functions with no side effects.
No LLM involvement. No database access.
"""

from __future__ import annotations

from typing import Any

from planos.app.planning.engine import (
    CalculationResult,
    PlanningMetrics,
    ScenarioChanges,
)


class PlanningEngine:
    """Deterministic planning calculation engine."""

    @staticmethod
    def calculate_revenue(units: float, price: float) -> float:
        """Revenue = units x price"""
        return units * price

    @staticmethod
    def calculate_gross_profit(revenue: float, cost: float) -> float:
        """Gross profit = revenue - cost"""
        return revenue - cost

    @staticmethod
    def calculate_profit(revenue: float, cost: float, operating_expenses: float) -> float:
        """Profit = revenue - cost - operating_expenses"""
        return revenue - cost - operating_expenses

    @staticmethod
    def calculate_capacity_utilization(demand: float, available_capacity: float) -> float:
        """Capacity utilization = demand / available_capacity x 100"""
        if available_capacity == 0:
            return 0.0
        return (demand / available_capacity) * 100

    @staticmethod
    def calculate_inventory_requirement(
        forecast_demand: float,
        safety_factor: float = 1.2,
    ) -> float:
        """Inventory requirement = forecast_demand x safety_factor"""
        return forecast_demand * safety_factor

    @staticmethod
    def apply_scenario_changes(
        baseline: PlanningMetrics,
        changes: ScenarioChanges,
    ) -> PlanningMetrics:
        """Apply scenario changes to baseline metrics deterministically."""
        new_units = baseline.units * (1 + changes.demand_growth)
        new_price = baseline.price * (1 + changes.price_change)

        new_cost_per_unit = baseline.cost / baseline.units if baseline.units > 0 else 0
        new_cost_per_unit *= 1 + changes.cost_change
        new_cost = new_units * new_cost_per_unit if baseline.units > 0 else baseline.cost

        new_revenue = PlanningEngine.calculate_revenue(new_units, new_price)
        new_capacity = baseline.capacity * changes.supplier_capacity_multiplier
        new_marketing = baseline.marketing_budget * changes.marketing_budget_multiplier
        new_headcount = baseline.headcount * (1 + changes.headcount_change)
        new_inventory = PlanningEngine.calculate_inventory_requirement(new_units, safety_factor=1.2)

        return PlanningMetrics(
            units=new_units,
            price=new_price,
            cost=new_cost,
            revenue=new_revenue,
            headcount=new_headcount,
            capacity=new_capacity,
            inventory=new_inventory,
            marketing_budget=new_marketing,
            operating_expenses=baseline.operating_expenses
            + (new_marketing - baseline.marketing_budget),
        )

    @staticmethod
    def calculate_scenario_impact(
        baseline_metrics: list[PlanningMetrics],
        changes: ScenarioChanges,
        period_labels: list[str],
    ) -> list[CalculationResult]:
        """Calculate the impact of scenario changes across all periods."""
        results = []
        for i, baseline in enumerate(baseline_metrics):
            scenario = PlanningEngine.apply_scenario_changes(baseline, changes)
            label = period_labels[i] if i < len(period_labels) else f"period_{i + 1}"

            result = CalculationResult(
                period_label=label,
                baseline=baseline,
                scenario=scenario,
                delta_revenue=scenario.revenue - baseline.revenue,
                delta_profit=scenario.profit - baseline.profit,
                delta_units=scenario.units - baseline.units,
                delta_cost=scenario.cost - baseline.cost,
                delta_headcount=scenario.headcount - baseline.headcount,
                delta_inventory=scenario.inventory - baseline.inventory,
            )
            results.append(result)
        return results

    @staticmethod
    def aggregate_results(results: list[CalculationResult]) -> dict[str, Any]:
        """Aggregate calculation results into summary metrics."""
        if not results:
            return {}

        total_baseline_revenue = sum(r.baseline.revenue for r in results)
        total_scenario_revenue = sum(r.scenario.revenue for r in results)
        total_baseline_profit = sum(r.baseline.profit for r in results)
        total_scenario_profit = sum(r.scenario.profit for r in results)
        total_baseline_cost = sum(r.baseline.cost for r in results)
        total_scenario_cost = sum(r.scenario.cost for r in results)
        total_baseline_units = sum(r.baseline.units for r in results)
        total_scenario_units = sum(r.scenario.units for r in results)

        return {
            "total_baseline_revenue": total_baseline_revenue,
            "total_scenario_revenue": total_scenario_revenue,
            "total_revenue_delta": total_scenario_revenue - total_baseline_revenue,
            "total_revenue_delta_pct": (
                ((total_scenario_revenue - total_baseline_revenue) / total_baseline_revenue * 100)
                if total_baseline_revenue != 0
                else 0.0
            ),
            "total_baseline_profit": total_baseline_profit,
            "total_scenario_profit": total_scenario_profit,
            "total_profit_delta": total_scenario_profit - total_baseline_profit,
            "total_profit_delta_pct": (
                ((total_scenario_profit - total_baseline_profit) / abs(total_baseline_profit) * 100)
                if total_baseline_profit != 0
                else 0.0
            ),
            "total_baseline_cost": total_baseline_cost,
            "total_scenario_cost": total_scenario_cost,
            "total_cost_delta": total_scenario_cost - total_baseline_cost,
            "total_baseline_units": total_baseline_units,
            "total_scenario_units": total_scenario_units,
            "total_units_delta": total_scenario_units - total_baseline_units,
        }
