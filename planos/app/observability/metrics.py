"""Prometheus-compatible in-process metrics (no exporter dependency drift)."""

from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Any

_lock = Lock()
_request_counts: Counter[tuple[str, str, int]] = Counter()
_request_latency_ms: dict[tuple[str, str], list[float]] = {}
_tool_calls: Counter[str] = Counter()
_tool_errors: Counter[str] = Counter()
_agent_runs: Counter[str] = Counter()


def _route(path: str) -> str:
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 3 and parts[0] == "api":
        # /api/v1/<resource>[/...] -> /api/v1/<resource>
        return "/" + "/".join(parts[:3])
    return path or "/"


def observe_request(path: str, method: str, status: int, duration_ms: float) -> None:
    route = _route(path)
    with _lock:
        _request_counts[(route, method, status)] += 1
        bucket = _request_latency_ms.setdefault((route, method), [])
        bucket.append(duration_ms)
        if len(bucket) > 1024:
            del bucket[: len(bucket) - 1024]


def observe_tool(tool: str, ok: bool) -> None:
    with _lock:
        _tool_calls[tool] += 1
        if not ok:
            _tool_errors[tool] += 1


def observe_agent_run(status: str) -> None:
    with _lock:
        _agent_runs[status] += 1


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(int(len(ordered) * p), len(ordered) - 1)]


def snapshot() -> dict[str, Any]:
    with _lock:
        requests = [
            {"route": r, "method": m, "status": s, "count": c}
            for (r, m, s), c in _request_counts.items()
        ]
        latency = [
            {
                "route": r,
                "method": m,
                "count": len(v),
                "p50_ms": round(_pct(v, 0.5), 2),
                "p95_ms": round(_pct(v, 0.95), 2),
            }
            for (r, m), v in _request_latency_ms.items()
        ]
        return {
            "requests": requests,
            "latency": latency,
            "tools": dict(_tool_calls),
            "tool_errors": dict(_tool_errors),
            "agent_runs": dict(_agent_runs),
        }


def render_prometheus() -> str:
    snap = snapshot()
    lines = ["# HELP planos_requests_total HTTP requests", "# TYPE planos_requests_total counter"]
    for row in snap["requests"]:
        lines.append(
            f'planos_requests_total{{route="{row["route"]}",method="{row["method"]}",'
            f'status="{row["status"]}"}} {row["count"]}'
        )
    lines += ["# HELP planos_tool_calls_total Tool calls", "# TYPE planos_tool_calls_total counter"]
    for tool, count in snap["tools"].items():
        lines.append(f'planos_tool_calls_total{{tool="{tool}"}} {count}')
    return "\n".join(lines) + "\n"
