"""Supplier dependency classification and explanation."""

import math
from typing import Dict


def dependency_level_from_weight(weight: float) -> str:
    """Classify supplier replacement difficulty on a 0-1 scale."""
    if not math.isfinite(weight):
        raise ValueError("dependency_weight must be finite")

    if not 0 <= weight <= 1:
        raise ValueError("dependency_weight must be between 0 and 1")

    if weight < 0.33:
        return "Low"

    if weight < 0.66:
        return "Medium"

    return "High"


def dependency_breakdown(weight: float) -> Dict:
    """Return a product-readable dependency assessment."""
    level = dependency_level_from_weight(weight)

    replaceability = {
        "Low": "Easy to replace",
        "Medium": "Moderately difficult to replace",
        "High": "Difficult to replace",
    }[level]

    return {
        "weight": round(float(weight), 4),
        "level": level,
        "replaceability": replaceability,
    }
