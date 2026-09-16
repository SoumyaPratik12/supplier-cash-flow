"""Simple, explainable forecasting — deliberately not deep learning.
At 8 quarters of history per supplier, a linear trend is honestly about as
much signal as the data supports, and it's trivial to explain to a non-technical
user ("revenue has been declining ~4% a quarter"), which matters more here
than marginal forecast accuracy."""

from typing import List

import numpy as np


def forecast_next_period(revenue_series: List[float]) -> float:
    """Fit a linear trend to the revenue history and project one period ahead.
    Falls back to the last known value if there isn't enough history."""
    if len(revenue_series) < 2:
        return revenue_series[-1] if revenue_series else 0.0

    x = np.arange(len(revenue_series))
    slope, intercept = np.polyfit(x, revenue_series, 1)
    next_x = len(revenue_series)
    forecast = float(slope * next_x + intercept)
    return round(max(forecast, 0.0), 2)


def revenue_slope(revenue_series: List[float]) -> float:
    """Normalized slope (% change per period relative to series mean) — used
    as a model feature, not just for the forecast chart."""
    if len(revenue_series) < 2:
        return 0.0
    x = np.arange(len(revenue_series))
    slope, _ = np.polyfit(x, revenue_series, 1)
    mean_rev = np.mean(revenue_series) or 1.0
    return round(slope / mean_rev, 4)
