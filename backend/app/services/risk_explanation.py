"""Quantitative risk-driver explanation for supplier risk scores.

This module turns the model's feature importances and each supplier's deviation
from the training population into a compact, product-readable explanation.

The explanation is a heuristic based on standardized deviation and model
feature importance. It does not claim causal relationships.
"""
from typing import Dict, List

import numpy as np

from app.services.scoring import FEATURE_NAMES, RiskModel

FACTOR_LABELS = {
    "revenue_slope": "Revenue trend",
    "avg_days_to_payment": "Average payment time",
    "days_to_payment_trend": "Payment deterioration",
    "outstanding_ratio": "Outstanding invoice ratio",
    "overdue_ratio": "Overdue invoice ratio",
    "on_time_rate": "On-time payment rate",
}


def _direction_for_feature(factor: str, z_score: float) -> str:
    """Return the business meaning of a feature's deviation.

    negative = deviation increases risk
    positive = deviation decreases risk
    neutral = close to population baseline
    """
    if abs(z_score) < 0.25:
        return "neutral"

    high_is_risky = {
        "revenue_slope": False,
        "avg_days_to_payment": True,
        "days_to_payment_trend": True,
        "outstanding_ratio": True,
        "overdue_ratio": True,
        "on_time_rate": False,
    }

    if high_is_risky[factor]:
        return "negative" if z_score > 0 else "positive"
    return "negative" if z_score < 0 else "positive"


def explain_risk(
    model: RiskModel,
    features: Dict[str, float],
    top_n: int = 3,
) -> List[Dict]:
    """Generate ranked quantitative risk drivers for one supplier.

    Impact is based on:

        abs(z-score) × model feature importance

    The resulting impacts are normalized across all features.

    This is an explanation heuristic, not a causal attribution.
    """
    if top_n <= 0:
        return []

    values = np.array(
        [features[f] for f in FEATURE_NAMES],
        dtype=float,
    )

    means = np.asarray(model.feature_means, dtype=float)
    stds = np.asarray(model.feature_stds, dtype=float)

    # Prevent division by zero when a feature has no training-set variance.
    safe_stds = np.where(stds > 0, stds, 1.0)

    z_scores = (values - means) / safe_stds

    importances = np.asarray(
        model.clf.feature_importances_,
        dtype=float,
    )

    raw_contributions = np.abs(z_scores) * importances

    total = float(raw_contributions.sum())

    if total > 0:
        normalized = raw_contributions / total
    else:
        normalized = np.zeros_like(raw_contributions)

    drivers = []

    for index, factor in enumerate(FEATURE_NAMES):
        z = float(z_scores[index])

        drivers.append(
            {
                "factor": factor,
                "label": FACTOR_LABELS[factor],
                "value": round(float(values[index]), 4),
                "impact": round(float(normalized[index]), 4),
                "direction": _direction_for_feature(factor, z),
            }
        )

    drivers.sort(
        key=lambda item: item["impact"],
        reverse=True,
    )

    return drivers[:top_n]
