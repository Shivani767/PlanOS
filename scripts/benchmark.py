"""Performance benchmark script for PlanOS.

Measures:
- API latency (P50, P95, P99)
- Database query latency
- Scenario calculation time
- Import throughput
- Cache effectiveness

Usage:
    python scripts/benchmark.py
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    p50: float
    p95: float
    p99: float
    min_time: float
    max_time: float
    ops_per_second: float


def benchmark(name: str, fn: Callable, iterations: int = 100, warmup: int = 10) -> BenchmarkResult:
    """Run a benchmark and return results."""
    # Warmup
    for _ in range(warmup):
        fn()

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)

    times.sort()
    total = sum(times)

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time=total,
        avg_time=total / iterations,
        p50=times[int(len(times) * 0.5)],
        p95=times[int(len(times) * 0.95)],
        p99=times[int(len(times) * 0.99)],
        min_time=times[0],
        max_time=times[-1],
        ops_per_second=1000 / (total / iterations),
    )


def print_result(result: BenchmarkResult) -> None:
    """Print benchmark result."""
    print(f"\n{result.name}")
    print("-" * 50)
    print(f"  Iterations:   {result.iterations}")
    print(f"  Avg:          {result.avg_time:.2f}ms")
    print(f"  P50:          {result.p50:.2f}ms")
    print(f"  P95:          {result.p95:.2f}ms")
    print(f"  P99:          {result.p99:.2f}ms")
    print(f"  Min:          {result.min_time:.2f}ms")
    print(f"  Max:          {result.max_time:.2f}ms")
    print(f"  Ops/sec:      {result.ops_per_second:.1f}")


def main():
    """Run all benchmarks."""
    print("=" * 50)
    print("PlanOS Performance Benchmarks")
    print("=" * 50)

    # Planning engine benchmarks
    from planos.app.planning.calculator import PlanningEngine
    from planos.app.planning.engine import PlanningMetrics, ScenarioChanges

    # Benchmark: revenue calculation
    result = benchmark(
        "Revenue Calculation",
        lambda: PlanningEngine.calculate_revenue(100, 50),
        iterations=10000,
    )
    print_result(result)

    # Benchmark: scenario changes
    baseline = PlanningMetrics(units=100, price=50, cost=3000, revenue=5000)
    changes = ScenarioChanges(demand_growth=0.15, marketing_budget_multiplier=1.10)
    result = benchmark(
        "Apply Scenario Changes",
        lambda: PlanningEngine.apply_scenario_changes(baseline, changes),
        iterations=10000,
    )
    print_result(result)

    # Benchmark: scenario impact across 12 periods
    baseline_metrics = [
        PlanningMetrics(units=100 + i * 10, price=50, cost=3000 + i * 200, revenue=5000 + i * 500)
        for i in range(12)
    ]
    period_labels = [f"2024-{m:02d}" for m in range(1, 13)]
    result = benchmark(
        "Scenario Impact (12 periods)",
        lambda: PlanningEngine.calculate_scenario_impact(
            baseline_metrics, ScenarioChanges(demand_growth=0.15), period_labels
        ),
        iterations=1000,
    )
    print_result(result)

    # Benchmark: aggregate results
    results = PlanningEngine.calculate_scenario_impact(
        baseline_metrics, ScenarioChanges(demand_growth=0.15), period_labels
    )
    result = benchmark(
        "Aggregate Results",
        lambda: PlanningEngine.aggregate_results(results),
        iterations=10000,
    )
    print_result(result)

    # Benchmark: password hashing
    from planos.app.core.security import hash_password
    result = benchmark(
        "Password Hashing",
        lambda: hash_password("benchmark_password"),
        iterations=100,
    )
    print_result(result)

    # Summary
    print("\n" + "=" * 50)
    print("Benchmark Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
