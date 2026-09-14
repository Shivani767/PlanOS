"""Policy / guardrail engine (Phase 14): evaluated BEFORE any tool executes."""

from __future__ import annotations

from dataclasses import dataclass

FAIL = "deny"
REQUIRE_APPROVAL = "require_approval"
ALLOW = "allow"

# Assumptions that always need a human (fractional, e.g. 0.5 = 50%).
ASSUMPTION_APPROVAL_THRESHOLD = 0.5
# Budget deltas above this need approval.
BUDGET_DELTA_APPROVAL_THRESHOLD = 1_000_000.0
# Absolute bounds for assumptions (guardrail).
ASSUMPTION_BOUNDS: dict[str, tuple[float, float]] = {
    "demand_growth": (-0.9, 5.0),
    "price_change": (-0.9, 5.0),
    "cost_change": (-0.9, 5.0),
    "headcount_change": (-0.9, 5.0),
    "marketing_budget_multiplier": (0.0, 10.0),
    "supplier_capacity_multiplier": (0.0, 10.0),
}


@dataclass
class PolicyDecision:
    verdict: str  # allow | require_approval | deny
    reason: str = ""
    requires_approval: bool = False

    @classmethod
    def allow(cls, reason: str = "allowed") -> PolicyDecision:
        return cls(ALLOW, reason, False)

    @classmethod
    def needs_approval(cls, reason: str) -> PolicyDecision:
        return cls(REQUIRE_APPROVAL, reason, True)

    @classmethod
    def deny(cls, reason: str) -> PolicyDecision:
        return cls(FAIL, reason, False)


def evaluate_assumptions(changes: dict, role: str) -> PolicyDecision:
    """Guardrail: bounds-check every assumption, approval for large/risky ones."""
    if role == "VIEWER":
        return PolicyDecision.deny("VIEWER role is read-only")
    for key, value in (changes or {}).items():
        if not isinstance(value, (int, float)):
            continue
        bounds = ASSUMPTION_BOUNDS.get(key)
        if bounds and not (bounds[0] <= float(value) <= bounds[1]):
            return PolicyDecision.deny(f"Assumption '{key}={value}' outside bounds {bounds}")
        magnitude = abs(float(value) if "multiplier" not in key else float(value) - 1.0)
        if magnitude >= ASSUMPTION_APPROVAL_THRESHOLD:
            return PolicyDecision.needs_approval(
                f"Assumption '{key}={value}' exceeds ±{ASSUMPTION_APPROVAL_THRESHOLD:.0%}; approval required"
            )
    return PolicyDecision.allow("assumptions within policy")


def evaluate_tool(tool_name: str, role: str, args: dict | None = None) -> PolicyDecision:
    """Central pre-execution gate for every typed tool."""
    args = args or {}
    if role == "ADMIN":
        pass  # admins pass role gates; assumption gates below still apply
    elif role == "VIEWER":
        if not (
            tool_name.startswith("get_") or tool_name in {"compare_scenarios", "search_knowledge"}
        ):
            return PolicyDecision.deny(f"VIEWER cannot execute '{tool_name}'")
    elif role == "ANALYST" and tool_name in {
        "create_change_request",
        "delete_plan",
        "apply_change_set",
    }:
        return PolicyDecision.deny(f"ANALYST cannot execute '{tool_name}'")
    if tool_name in {"create_scenario", "run_scenario", "create_change_request"}:
        return evaluate_assumptions(args.get("assumptions") or args.get("changes") or {}, role)
    if tool_name in {"apply_change_set", "approve_change", "delete_plan"}:
        return PolicyDecision.needs_approval(f"'{tool_name}' is high-risk; approval required")
    return PolicyDecision.allow(f"'{tool_name}' permitted for {role}")
