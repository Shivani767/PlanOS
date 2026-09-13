"""Deterministic NL -> assumptions parsing (planner's interpreter)."""

from __future__ import annotations

import re

METRIC_PATTERNS = [
    (re.compile(r"demand\s*(?:by|\+)?\s*(\d+(?:\.\d+)?)\s*%"), "demand_growth", lambda v: v / 100),
    (
        re.compile(r"marketing\s*(?:by|\-)?\s*(\d+(?:\.\d+)?)\s*%"),
        "marketing_budget_multiplier",
        lambda v: 1 - v / 100,
    ),
    (re.compile(r"price\s*(?:by)?\s*(\d+(?:\.\d+)?)\s*%"), "price_change", lambda v: v / 100),
    (re.compile(r"cost\s*(?:by)?\s*(\d+(?:\.\d+)?)\s*%"), "cost_change", lambda v: v / 100),
]
HEADCOUNT_PIN = re.compile(
    r"keep headcount unchanged|headcount (?:fixed|unchanged)|no headcount change"
)
AGENT_SEQUENCE = ["planner", "analyst", "executor", "reviewer"]


def parse_assumptions(text: str) -> dict[str, float]:
    lowered = text.lower()
    out: dict[str, float] = {}
    for pattern, key, convert in METRIC_PATTERNS:
        match = pattern.search(lowered)
        if match:
            try:
                out[key] = round(convert(float(match.group(1))), 4)
            except ValueError:
                continue
    if HEADCOUNT_PIN.search(lowered):
        out["headcount_change"] = 0.0
    return out
