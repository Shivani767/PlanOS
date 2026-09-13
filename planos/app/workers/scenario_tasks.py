"""Celery tasks for scenario execution."""

from __future__ import annotations

import asyncio
from typing import Any

from celery.utils.log import get_task_logger

from planos.app.core.config import settings
from planos.app.db.session import async_session_factory
from planos.app.models import PlanningData, Scenario
from planos.app.planning.calculator import PlanningEngine
from planos.app.planning.engine import PlanningMetrics, ScenarioChanges
from planos.app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="planos.app.workers.scenario_tasks.execute_scenario")
def execute_scenario(self, scenario_id: str, organization_id: str) -> dict[str, Any]:
    """Execute scenario calculation asynchronously.

    This runs in a Celery worker, not in the web process.
    Uses asyncio to run async DB operations.
    """
    return asyncio.run(_execute_scenario_async(scenario_id, organization_id))


async def _execute_scenario_async(scenario_id: str, organization_id: str) -> dict[str, Any]:
    """Async implementation of scenario execution."""
    logger.info("Starting scenario execution", scenario_id=scenario_id)

    async with async_session_factory() as session:
        try:
            # Fetch scenario
            from sqlalchemy import select
            result = await session.execute(
                __import__("sqlalchemy").select(Scenario).where(
                    Scenario.id == scenario_id,
                    Scenario.organization_id == organization_id,
                )
            )
            scenario = result.scalar_one_or_none()
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")

            # Fetch planning data for the base plan
            data_result = await session.execute(
                __import__("sqlalchemy").select(PlanningData).where(
                    PlanningData.plan_id == scenario.base_plan_id,
                    PlanningData.organization_id == organization_id,
                )
            )
            planning_data = data_result.scalars().all()

            if not planning_data:
                # No data to calculate
                scenario.status = "completed"
                scenario.results = {"message": "No planning data available"}
                await session.commit()
                return scenario.results

            # Group by period
            from collections import defaultdict
            period_data: dict[str, list[PlanningData]] = defaultdict(list)
            period_labels: dict[str, str] = {}

            for pd in planning_data:
                period_key = pd.period_id
                period_data[period_key].append(pd)
                # We'll use period_id as key, fetch labels separately
                period_labels[period_key] = period_key

            # Aggregate metrics per period
            from sqlalchemy import select
            from planos.app.models import TimePeriod

            period_result = await session.execute(
                select(TimePeriod).where(
                    TimePeriod.organization_id == organization_id
                )
            )
            periods = {p.id: p.label for p in period_result.scalars().all()}

            baseline_metrics = []
            sorted_period_ids = sorted(period_data.keys())

            for period_id in sorted_period_ids:
                records = period_data[period_id]
                total_units = sum(r.units for r in records)
                avg_price = sum(r.price for r in records) / len(records) if records else 0
                total_cost = sum(r.cost for r in records)
                total_revenue = sum(r.revenue for r in records)
                total_headcount = sum(r.headcount for r in records)
                total_capacity = sum(r.capacity for r in records)
                total_inventory = sum(r.inventory for r in records)
                total_marketing = sum(r.marketing_budget for r in records)

                metrics = PlanningMetrics(
                    units=total_units,
                    price=avg_price,
                    cost=total_cost,
                    revenue=total_revenue,
                    headcount=total_headcount,
                    capacity=total_capacity,
                    inventory=total_inventory,
                    marketing_budget=total_marketing,
                    operating_expenses=total_cost * 0.3,  # Simplified
                )
                baseline_metrics.append(metrics)

            # Apply scenario changes
            changes = ScenarioChanges.from_dict(scenario.changes)
            period_label_list = [periods.get(pid, f"period_{i+1}") for i, pid in enumerate(sorted_period_ids)]

            calc_results = PlanningEngine.calculate_scenario_impact(
                baseline_metrics, changes, period_label_list
            )

            # Aggregate and store results
            aggregated = PlanningEngine.aggregate_results(calc_results)
            scenario.results = aggregated
            scenario.status = "completed"
            await session.commit()

            logger.info("Scenario execution completed", scenario_id=scenario_id)
            return aggregated

        except Exception as e:
            logger.error("Scenario execution failed", scenario_id=scenario_id, error=str(e))
            async with async_session_factory() as error_session:
                result = await error_session.execute(
                    __import__("sqlalchemy").select(Scenario).where(Scenario.id == scenario_id)
                )
                error_scenario = result.scalar_one_or_none()
                if error_scenario:
                    error_scenario.status = "failed"
                    await error_session.commit()
            raise
