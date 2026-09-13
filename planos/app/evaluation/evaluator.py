"""Evaluator implementation."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from planos.app.evaluation.models import EvalCase, EvalReport, EvalResult


@dataclass
class Evaluator:
    """Evaluates agent performance against fixed datasets."""

    agent_name: str
    model: str
    prompt_version: str = "v1"
    results: list[EvalResult] = field(default_factory=list)

    def evaluate_case(self, case: EvalCase, agent_fn: Callable) -> EvalResult:
        """Run a single evaluation case."""
        start_time = time.time()
        try:
            response = agent_fn(case.input)
            tools_selected = response.get("tools_used", [])
            tools_correct = all(t in case.expected_tools for t in tools_selected)

            expected = case.expected_output_properties
            props = list(expected.keys()) if isinstance(expected, dict) else list(expected)
            output_valid = True
            for prop in props:
                if prop not in response.get("output", {}):
                    output_valid = False
                    break

            policy_violations = 0
            for tool in tools_selected:
                if case.allowed_tools and tool not in case.allowed_tools:
                    policy_violations += 1

            latency_ms = (time.time() - start_time) * 1000

            return EvalResult(
                case_id=case.id,
                success=tools_correct and output_valid and policy_violations == 0,
                tools_selected=tools_selected,
                tools_correct=tools_correct,
                output_valid=output_valid,
                policy_violations=policy_violations,
                latency_ms=latency_ms,
                tokens_used=response.get("tokens_used", 0),
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return EvalResult(
                case_id=case.id,
                success=False,
                tools_selected=[],
                tools_correct=False,
                output_valid=False,
                latency_ms=latency_ms,
                error=str(e),
            )

    def run_evaluation(self, cases: list[EvalCase], agent_fn: Callable) -> EvalReport:
        """Run full evaluation suite."""
        results = [self.evaluate_case(case, agent_fn) for case in cases]
        latencies = sorted(r.latency_ms for r in results)
        total = len(results)
        successful = sum(1 for r in results if r.success)

        def percentile(data: list[float], p: float) -> float:
            if not data:
                return 0.0
            idx = int(len(data) * p)
            return data[min(idx, len(data) - 1)]

        return EvalReport(
            run_id=str(uuid.uuid4()),
            agent_name=self.agent_name,
            model=self.model,
            prompt_version=self.prompt_version,
            timestamp=datetime.now(UTC).isoformat(),
            total_cases=total,
            successful_cases=successful,
            failed_cases=total - successful,
            task_success_rate=successful / total if total > 0 else 0,
            tool_accuracy=sum(1 for r in results if r.tools_correct) / total if total > 0 else 0,
            policy_violation_rate=sum(r.policy_violations for r in results) / total
            if total > 0
            else 0,
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
            p50_latency_ms=percentile(latencies, 0.5),
            p95_latency_ms=percentile(latencies, 0.95),
            p99_latency_ms=percentile(latencies, 0.99),
            avg_tokens=sum(r.tokens_used for r in results) / total if total > 0 else 0,
            results=results,
        )

    def generate_markdown(self, report: EvalReport) -> str:
        """Generate markdown report."""
        lines = [
            f"# Evaluation Report: {report.agent_name}",
            "",
            f"**Model**: {report.model} | **Prompt**: {report.prompt_version} | **Date**: {report.timestamp}",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Cases | {report.total_cases} |",
            f"| Successful | {report.successful_cases} |",
            f"| Failed | {report.failed_cases} |",
            f"| Task Success Rate | {report.task_success_rate:.1%} |",
            f"| Tool Accuracy | {report.tool_accuracy:.1%} |",
            f"| Policy Violation Rate | {report.policy_violation_rate:.2%} |",
            f"| Avg Latency | {report.avg_latency_ms:.0f}ms |",
            f"| P50 Latency | {report.p50_latency_ms:.0f}ms |",
            f"| P95 Latency | {report.p95_latency_ms:.0f}ms |",
            f"| P99 Latency | {report.p99_latency_ms:.0f}ms |",
            f"| Avg Tokens | {report.avg_tokens:.0f} |",
        ]
        return "\n".join(lines)
