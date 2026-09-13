"""Standard evaluation datasets for PlanOS agents."""

from __future__ import annotations

from planos.app.evaluation.models import EvalCase


def get_planning_agent_cases() -> list[EvalCase]:
    """Evaluation cases for the Planning Agent."""
    return [
        EvalCase(
            id="plan-001",
            name="Create basic scenario",
            description="User requests creating a scenario with demand growth",
            input="Create a Q4 scenario where demand increases by 15%",
            expected_tools=["create_scenario"],
            expected_output_properties=["scenario_id", "status"],
            allowed_tools=["create_scenario", "get_plan", "get_scenario", "run_scenario"],
            tags=["scenario", "creation"],
            difficulty="easy",
        ),
        EvalCase(
            id="plan-002",
            name="Multi-variable scenario",
            description="Complex scenario with multiple change variables",
            input="Create a scenario with 20% demand growth, 10% price reduction, and 5% cost increase",
            expected_tools=["create_scenario"],
            expected_output_properties=["scenario_id", "status"],
            allowed_tools=["create_scenario", "get_plan", "get_scenario"],
            tags=["scenario", "complex"],
            difficulty="medium",
        ),
        EvalCase(
            id="plan-003",
            name="Run scenario",
            description="Run an existing scenario",
            input="Run scenario 'Q4 Demand Surge'",
            expected_tools=["run_scenario"],
            expected_output_properties=["job_id", "status"],
            allowed_tools=["run_scenario", "get_scenario"],
            tags=["scenario", "execution"],
            difficulty="easy",
        ),
        EvalCase(
            id="plan-004",
            name="Compare scenarios",
            description="Compare two scenarios",
            input="Compare the 'Q4 Demand Surge' scenario with baseline",
            expected_tools=["compare_scenarios"],
            expected_output_properties=["comparison_id", "deltas"],
            allowed_tools=["compare_scenarios", "get_scenario"],
            tags=["scenario", "comparison"],
            difficulty="medium",
        ),
        EvalCase(
            id="plan-005",
            name="View plan details",
            description="Retrieve plan information",
            input="Show me the details of plan '2024 Annual Plan'",
            expected_tools=["get_plan"],
            expected_output_properties=["plan_id", "name", "status"],
            allowed_tools=["get_plan", "list_plans"],
            tags=["plan", "read"],
            difficulty="easy",
        ),
    ]


def get_finance_agent_cases() -> list[EvalCase]:
    """Evaluation cases for the Finance Agent."""
    return [
        EvalCase(
            id="fin-001",
            name="Revenue breakdown",
            description="Analyze revenue breakdown by product",
            input="What is the revenue breakdown by product for Q4?",
            expected_tools=["get_financial_breakdown"],
            expected_output_properties=["revenue_by_product", "total"],
            allowed_tools=["get_financial_breakdown", "get_plan"],
            tags=["finance", "revenue"],
            difficulty="easy",
        ),
        EvalCase(
            id="fin-002",
            name="Profit analysis",
            description="Analyze profit margins",
            input="Show me the profit margin trend over the last 4 quarters",
            expected_tools=["get_financial_breakdown"],
            expected_output_properties=["margins", "trend"],
            allowed_tools=["get_financial_breakdown"],
            tags=["finance", "profit"],
            difficulty="medium",
        ),
        EvalCase(
            id="fin-003",
            name="Cost drivers",
            description="Identify major cost drivers",
            input="What are the main cost drivers in our operations?",
            expected_tools=["get_financial_breakdown"],
            expected_output_properties=["cost_drivers", "breakdown"],
            allowed_tools=["get_financial_breakdown"],
            tags=["finance", "cost"],
            difficulty="medium",
        ),
    ]


def get_analyst_agent_cases() -> list[EvalCase]:
    """Evaluation cases for the Analyst Agent."""
    return [
        EvalCase(
            id="anl-001",
            name="Root cause analysis",
            description="Explain why a metric changed",
            input="Why did profit decrease in Scenario B?",
            expected_tools=["compare_scenarios", "get_financial_breakdown"],
            expected_output_properties=["root_causes", "impact"],
            allowed_tools=["compare_scenarios", "get_financial_breakdown", "get_scenario"],
            tags=["analysis", "root-cause"],
            difficulty="hard",
        ),
        EvalCase(
            id="anl-002",
            name="Major changes detection",
            description="Identify major changes between scenarios",
            input="What are the major changes between baseline and the demand surge scenario?",
            expected_tools=["compare_scenarios"],
            expected_output_properties=["major_changes", "affected_areas"],
            allowed_tools=["compare_scenarios", "get_scenario"],
            tags=["analysis", "changes"],
            difficulty="medium",
        ),
        EvalCase(
            id="anl-003",
            name="Impact summary",
            description="Summarize scenario impact",
            input="Summarize the overall business impact of the supply chain disruption scenario",
            expected_tools=["compare_scenarios", "get_financial_breakdown"],
            expected_output_properties=["summary", "key_impacts"],
            allowed_tools=[
                "compare_scenarios",
                "get_financial_breakdown",
                "get_workforce_capacity",
            ],
            tags=["analysis", "summary"],
            difficulty="hard",
        ),
    ]


def get_all_eval_cases() -> list[EvalCase]:
    """Get all evaluation cases."""
    return get_planning_agent_cases() + get_finance_agent_cases() + get_analyst_agent_cases()
