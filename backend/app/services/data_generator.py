"""
Synthetic supplier data generator.

WHY THIS EXISTS
----------------
Real supplier financial + supply-chain datasets at invoice-level granularity
are not publicly available (this was the stated #1 risk for this project).
Instead of faking numbers arbitrarily, this generator builds each supplier
from a named "archetype" with an internally consistent story: revenue trend,
payment behavior, and invoice aging all move together the way they plausibly
would for a real business in that situation. A subset of suppliers gets an
explicit ground-truth label (`will_face_shortfall`) so the risk model has
something real to learn from and you can measure precision/recall instead of
eyeballing plausibility.

ARCHETYPES
----------
- stable:      flat/slightly growing revenue, reliable payments -> label 0
- growing:     clearly growing revenue, reliable payments -> label 0
- slipping:    flat-to-declining revenue, days-to-payment creeping up,
               invoice aging worsening -> label 1 (the target class)
- distressed:  clearly declining revenue, chronically late payments,
               heavy overdue balance -> label 1
- volatile:    noisy revenue with no clear trend, inconsistent payments ->
               label is derived from the actual generated trend, not fixed,
               so the model has to work for the ambiguous middle case too

This file is intentionally the most-documented part of the codebase, per the
project's own risk assessment: if this generator is unrealistic, everything
downstream (forecast, risk score, ranking) looks arbitrary no matter how good
the model is.
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Tuple

import numpy as np
from faker import Faker

fake = Faker()

INDUSTRIES = [
    "Electronics Components",
    "Packaging",
    "Raw Materials",
    "Logistics",
    "Textiles",
    "Industrial Equipment",
    "Chemicals",
    "Contract Manufacturing",
]

N_PERIODS = 8  # quarters of history
PERIOD_LABELS = [f"2024-Q{i%4+1}" if i < 4 else f"2025-Q{i%4+1}" for i in range(N_PERIODS)]


@dataclass
class ArchetypeConfig:
    name: str
    revenue_drift: Tuple[float, float]  # (mean, std) quarter-over-quarter % change
    revenue_noise: float  # std of noise on top of drift
    on_time_payment_prob: Tuple[float, float]  # (start, end) probability of paying on time
    days_to_payment_range: Tuple[int, int]  # (start_avg, end_avg) trending between these
    overdue_bias: float  # 0-1, extra chance an outstanding invoice becomes overdue
    label: int  # 1 = will face cash-flow shortfall next period, 0 = will not


ARCHETYPES = [
    ArchetypeConfig("stable", (0.01, 0.02), 0.03, (0.92, 0.90), (25, 27), 0.05, 0),
    ArchetypeConfig("growing", (0.06, 0.02), 0.04, (0.95, 0.93), (22, 20), 0.03, 0),
    ArchetypeConfig("slipping", (-0.02, 0.03), 0.05, (0.85, 0.60), (28, 45), 0.30, 1),
    ArchetypeConfig("distressed", (-0.08, 0.04), 0.06, (0.70, 0.35), (35, 65), 0.55, 1),
    ArchetypeConfig("volatile", (0.0, 0.08), 0.10, (0.80, 0.70), (30, 38), 0.25, None),
]

# archetype mix — weighted so "at risk" suppliers are a meaningful but
# realistic minority, matching the project's framing (early warning for a
# subset, not "half your suppliers are failing")
ARCHETYPE_WEIGHTS = {
    "stable": 0.35,
    "growing": 0.25,
    "slipping": 0.15,
    "distressed": 0.10,
    "volatile": 0.15,
}


def _pick_archetype(rng: random.Random) -> ArchetypeConfig:
    names = list(ARCHETYPE_WEIGHTS.keys())
    weights = list(ARCHETYPE_WEIGHTS.values())
    chosen = rng.choices(names, weights=weights, k=1)[0]
    return next(a for a in ARCHETYPES if a.name == chosen)


def _generate_revenue_series(archetype: ArchetypeConfig, base_revenue: float, rng: np.random.Generator) -> List[float]:
    series = [base_revenue]
    mean_drift, drift_std = archetype.revenue_drift
    for _ in range(1, N_PERIODS):
        drift = rng.normal(mean_drift, drift_std)
        noise = rng.normal(0, archetype.revenue_noise)
        next_val = series[-1] * (1 + drift + noise)
        series.append(max(next_val, base_revenue * 0.1))  # floor so it never goes absurdly negative
    return series


def _generate_invoices(
    supplier_id: int,
    archetype: ArchetypeConfig,
    order_volume: float,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> List[dict]:
    """Generate ~1 invoice per month for the trailing 12 months, with payment
    behavior that trends from archetype.on_time_payment_prob[0] toward [1]
    and days_to_payment_range[0] toward [1] as time progresses — i.e. the
    most recent invoices reflect where the supplier is heading, which is
    exactly the signal a real early-warning system would have to pick up."""
    invoices = []
    today = date(2026, 1, 1)
    n_months = 12
    start_prob, end_prob = archetype.on_time_payment_prob
    start_days, end_days = archetype.days_to_payment_range

    monthly_amount = order_volume / 12

    for m in range(n_months):
        progress = m / (n_months - 1)
        on_time_prob = start_prob + (end_prob - start_prob) * progress
        avg_days = start_days + (end_days - start_days) * progress

        issue_date = today - timedelta(days=(n_months - m) * 30)
        due_date = issue_date + timedelta(days=30)
        amount = max(monthly_amount * np_rng.normal(1.0, 0.15), 100)

        paid_on_time = rng.random() < on_time_prob
        days_taken = max(int(np_rng.normal(avg_days, 8)), 1)
        paid_date = issue_date + timedelta(days=days_taken)

        # most recent 1-2 invoices may still be genuinely outstanding/overdue
        is_recent = m >= n_months - 2
        if is_recent and rng.random() < 0.6:
            status = "overdue" if (due_date < today and rng.random() < archetype.overdue_bias) else "outstanding"
            paid_date = None
        else:
            status = "paid"

        invoices.append(
            {
                "supplier_id": supplier_id,
                "amount": round(float(amount), 2),
                "issue_date": issue_date,
                "due_date": due_date,
                "paid_date": paid_date,
                "status": status,
            }
        )
    return invoices


def generate_suppliers(n_suppliers: int = 40, seed: int = 42) -> Tuple[List[dict], List[dict], List[dict]]:
    """Returns (suppliers, invoices, revenue_snapshots) as plain dicts ready
    for insertion, plus each supplier dict carries a `_ground_truth_label`
    key (0/1/None) for use by the training/eval step — strip it before
    inserting into the `suppliers` table."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    fake.seed_instance(seed)

    suppliers, all_invoices, all_snapshots = [], [], []

    for i in range(1, n_suppliers + 1):
        archetype = _pick_archetype(rng)
        base_revenue = float(np_rng.lognormal(mean=12.5, sigma=0.6))  # ~ tens of thousands to a few million
        order_volume = base_revenue * float(np_rng.uniform(0.05, 0.25))  # this supplier is a fraction of their total revenue
        dependency_weight = round(
            float(min(max(np_rng.beta(2, 5) + (0.2 if archetype.name in ("stable", "growing") else 0), 0), 1)), 2
        )

        revenue_series = _generate_revenue_series(archetype, base_revenue, np_rng)

        label = archetype.label
        if label is None:
            # volatile archetype: derive the label from the actual generated
            # trend rather than a fixed archetype rule, so the model sees a
            # genuinely ambiguous case, not just five clean clusters
            slope = np.polyfit(range(N_PERIODS), revenue_series, 1)[0]
            label = 1 if slope < 0 else 0

        supplier = {
            "id": i,
            "name": fake.company(),
            "industry": rng.choice(INDUSTRIES),
            "order_volume": round(order_volume, 2),
            "dependency_weight": dependency_weight,
            "_archetype": archetype.name,
            "_ground_truth_label": label,
        }
        suppliers.append(supplier)

        for idx, (period_label, revenue) in enumerate(zip(PERIOD_LABELS, revenue_series)):
            all_snapshots.append(
                {
                    "supplier_id": i,
                    "period": period_label,
                    "period_index": idx,
                    "revenue": round(float(revenue), 2),
                }
            )

        all_invoices.extend(_generate_invoices(i, archetype, order_volume, rng, np_rng))

    return suppliers, all_invoices, all_snapshots


if __name__ == "__main__":
    suppliers, invoices, snapshots = generate_suppliers()
    label_counts = {}
    for s in suppliers:
        label_counts[s["_archetype"]] = label_counts.get(s["_archetype"], 0) + 1
    print(f"Generated {len(suppliers)} suppliers, {len(invoices)} invoices, {len(snapshots)} revenue snapshots")
    print("Archetype mix:", label_counts)
    print("Positive label rate:", sum(s["_ground_truth_label"] for s in suppliers) / len(suppliers))
