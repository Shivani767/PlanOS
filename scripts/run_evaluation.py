"""Run agent evaluation and generate report."""

from __future__ import annotations

import asyncio
import json
import os
import sys

from planos.app.evaluation.datasets import get_all_eval_cases, get_planning_agent_cases
from planos.app.evaluation.evaluator import Evaluator


def mock_planning_agent(input_text: str) -> dict:
    """Mock planning agent for evaluation (no LLM needed)."""
    tools_used = []
    output = {}

    input_lower = input_text.lower()
    if "create" in input_lower and "scenario" in input_lower:
        tools_used = ["create_scenario"]
        output = {"scenario_id": "mock-scenario-123", "status": "created"}
    elif "run" in input_lower and "scenario" in input_lower:
        tools_used = ["run_scenario"]
        output = {"job_id": "mock-job-456", "status": "queued"}
    elif "compare" in input_lower:
        tools_used = ["compare_scenarios"]
        output = {"comparison_id": "mock-comp-789", "deltas": {"revenue": 0.15}}
    elif "plan" in input_lower or "details" in input_lower:
        tools_used = ["get_plan"]
        output = {"plan_id": "mock-plan", "name": "2024 Annual Plan", "status": "active"}
    else:
        tools_used = ["get_plan"]
        output = {"plan_id": "mock-plan"}

    return {
        "tools_used": tools_used,
        "output": output,
        "tokens_used": len(input_text) * 2,  # Rough estimate
    }


def main():
    """Run evaluation."""
    print("Running PlanOS Agent Evaluation...")
    print("=" * 50)

    evaluator = Evaluator(
        agent_name="Planning Agent",
        model="mock",
        prompt_version="v1",
    )

    cases = get_planning_agent_cases()
    print(f"\nEvaluating {len(cases)} cases...")

    report = evaluator.run_evaluation(cases, mock_planning_agent)

    # Print summary
    print(f"\nResults:")
    print(f"  Total Cases:       {report.total_cases}")
    print(f"  Successful:        {report.successful_cases}")
    print(f"  Failed:            {report.failed_cases}")
    print(f"  Task Success Rate: {report.task_success_rate:.1%}")
    print(f"  Tool Accuracy:     {report.tool_accuracy:.1%}")
    print(f"  Avg Latency:       {report.avg_latency_ms:.1f}ms")
    print(f"  P95 Latency:       {report.p95_latency_ms:.1f}ms")

    # Generate reports
    os.makedirs("evaluation/reports", exist_ok=True)

    # JSON report
    json_path = f"evaluation/reports/{report.run_id}.json"
    with open(json_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"\nJSON report saved: {json_path}")

    # Markdown report
    md_path = f"evaluation/reports/{report.run_id}.md"
    with open(md_path, "w") as f:
        f.write(evaluator.generate_markdown(report))
    print(f"Markdown report saved: {md_path}")

    # Return non-zero if success rate too low
    if report.task_success_rate < 0.5:
        print("\nWARNING: Success rate below 50%!")
        sys.exit(1)

    print("\nEvaluation complete!")
    return report


if __name__ == "__main__":
    main()
