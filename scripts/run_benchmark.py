"""Run a headless Locust load test and append results to docs/PERFORMANCE.md.

Usage:
    .venv/bin/python scripts/run_benchmark.py

Requires the API to be running (docker compose up) so numbers are real.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS_PERF = REPO / "docs" / "PERFORMANCE.md"
LOCUSTFILE = REPO / "tests" / "performance" / "locustfile.py"

HOST = "http://localhost:8000"
USERS = "50"
RATE = "10"
DURATION = "30s"


def main() -> int:
    if not LOCUSTFILE.exists():
        print(f"locustfile not found: {LOCUSTFILE}", file=sys.stderr)
        return 1

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(LOCUSTFILE),
        "--headless",
        "-u",
        USERS,
        "-r",
        RATE,
        "-t",
        DURATION,
        "--host",
        HOST,
        "--only-summary",
        "--csv",
        str(REPO / "tests" / "performance" / "benchmark"),
    ]
    print(f"Running benchmark: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(REPO))
    if result.returncode != 0:
        return result.returncode

    stats = REPO / "tests" / "performance" / "benchmark_stats.csv"
    content = stats.read_text() if stats.exists() else "(no stats captured)"
    DOCS_PERF.write_text(
        _render(ts, USERS, RATE, DURATION, content),
        encoding="utf-8",
    )
    print(f"Results written to {DOCS_PERF}")
    return 0


def _render(ts: str, users: str, rate: str, duration: str, csv_text: str) -> str:
    return (
        "# Performance\n\n"
        f"> Last real run: {ts}\n"
        f"> Config: {users} users, {rate}/s ramp, {duration} duration, host {HOST}\n\n"
        "## Locust summary (CSV)\n\n"
        "```csv\n"
        f"{csv_text}\n"
        "```\n\n"
        "## Interpretation\n\n"
        "- p50/p95/p99 are read latencies across plans, scenarios, metrics, health, knowledge/search.\n"
        "- Compare against the previous run to spot regressions.\n"
        "- Bottlenecks and fixes go here after each profiling pass.\n"
    )


if __name__ == "__main__":
    sys.exit(main())
