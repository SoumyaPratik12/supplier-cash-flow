"""Deterministic supplier intervention decision engine.

The engine preserves the existing recommended_action() behavior while adding
structured priority and an explanation for product use.

This is a rule-based decision aid, not a causal prediction.
"""

import math
from typing import Dict

VALID_RISK_LEVELS = {"Low", "Medium", "High"}

MONITOR_ACTION = "Monitor"
EARLY_PAYMENT_ACTION = "Offer early payment"
REDUCE_DEPENDENCY_ACTION = "Reduce dependency on this supplier"


def intervention_for(
    risk_level: str,
    dependency_weight: float,
) -> Dict[str, str]:
    """Return a structured intervention decision."""
    if risk_level not in VALID_RISK_LEVELS:
        raise ValueError(
            f"risk_level must be one of {sorted(VALID_RISK_LEVELS)}"
        )

    if not math.isfinite(dependency_weight):
        raise ValueError("dependency_weight must be finite")

    if not 0 <= dependency_weight <= 1:
        raise ValueError(
            "dependency_weight must be between 0 and 1"
        )

    if risk_level != "High":
        return {
            "action": MONITOR_ACTION,
            "priority": risk_level,
            "reason": (
                f"{risk_level} financial risk does not currently "
                "trigger a high-risk intervention."
            ),
        }

    if dependency_weight >= 0.5:
        return {
            "action": EARLY_PAYMENT_ACTION,
            "priority": "High",
            "reason": (
                "High financial risk combined with high supplier dependency."
            ),
        }

    return {
        "action": REDUCE_DEPENDENCY_ACTION,
        "priority": "High",
        "reason": (
            "High financial risk combined with lower supplier dependency."
        ),
    }
