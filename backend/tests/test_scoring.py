import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.data_generator import generate_suppliers
from app.services.forecasting import forecast_next_period, revenue_slope
from app.services.risk_explanation import explain_risk
from app.services.scoring import (
    extract_features,
    recommended_action,
    risk_level_from_score,
    score_supplier,
    train_risk_model,
)


def test_generator_produces_expected_counts():
    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=20, seed=1)
    assert len(suppliers) == 20
    assert len(snapshots) == 20 * 8  # N_PERIODS
    assert all("_ground_truth_label" in s for s in suppliers)
    assert all(s["_ground_truth_label"] in (0, 1) for s in suppliers)


def test_generator_is_deterministic_with_seed():
    s1, _, _ = generate_suppliers(n_suppliers=10, seed=99)
    s2, _, _ = generate_suppliers(n_suppliers=10, seed=99)
    assert [s["name"] for s in s1] == [s["name"] for s in s2]
    assert [s["_ground_truth_label"] for s in s1] == [s["_ground_truth_label"] for s in s2]


def test_forecast_flat_series_returns_same_value():
    assert forecast_next_period([100.0, 100.0, 100.0]) == 100.0


def test_forecast_growing_series_projects_upward():
    forecast = forecast_next_period([100.0, 110.0, 120.0, 130.0])
    assert forecast > 130.0


def test_revenue_slope_sign_matches_trend():
    assert revenue_slope([100, 90, 80, 70]) < 0
    assert revenue_slope([100, 110, 120, 130]) > 0


def test_extract_features_handles_supplier_with_no_invoices():
    features = extract_features([], [100.0, 105.0])
    assert features["outstanding_ratio"] == 0.0
    assert features["on_time_rate"] == 1.0


def test_risk_level_buckets():
    assert risk_level_from_score(0.1) == "Low"
    assert risk_level_from_score(0.5) == "Medium"
    assert risk_level_from_score(0.9) == "High"


def test_recommended_action_depends_on_dependency_weight():
    assert recommended_action("High", 0.8) == "Offer early payment"
    assert recommended_action("High", 0.2) == "Reduce dependency on this supplier"
    assert recommended_action("Low", 0.9) == "Monitor"


def test_model_recovers_signal_on_synthetic_labels():
    """The model should do meaningfully better than chance on its own
    training distribution — this is a smoke test, not a rigorous eval
    (see app/seed.py output for real cross-validated precision/recall)."""
    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=60, seed=7)
    inv_by_supplier, rev_by_supplier = {}, {}
    for inv in invoices:
        inv_by_supplier.setdefault(inv["supplier_id"], []).append(inv)
    for snap in snapshots:
        rev_by_supplier.setdefault(snap["supplier_id"], []).append(snap["revenue"])

    feature_rows = [extract_features(inv_by_supplier[s["id"]], rev_by_supplier[s["id"]]) for s in suppliers]
    labels = [s["_ground_truth_label"] for s in suppliers]

    model = train_risk_model(feature_rows, labels)
    assert model.cv_precision > 0.5
    assert model.cv_recall > 0.5


def test_explain_risk_returns_structured_driver_details():
    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=30, seed=11)
    inv_by_supplier, rev_by_supplier = {}, {}
    for inv in invoices:
        inv_by_supplier.setdefault(inv["supplier_id"], []).append(inv)
    for snap in snapshots:
        rev_by_supplier.setdefault(snap["supplier_id"], []).append(snap["revenue"])

    feature_rows = [extract_features(inv_by_supplier[s["id"]], rev_by_supplier[s["id"]]) for s in suppliers]
    labels = [s["_ground_truth_label"] for s in suppliers]
    model = train_risk_model(feature_rows, labels)

    supplier_features = feature_rows[0]
    drivers = explain_risk(model, supplier_features, top_n=3)

    assert len(drivers) > 0
    assert len(drivers) <= 3
    for driver in drivers:
        assert {"factor", "label", "value", "impact", "direction"}.issubset(driver.keys())
        assert driver["factor"] in supplier_features
        assert isinstance(driver["value"], (int, float))
        assert isinstance(driver["impact"], (int, float))
        assert driver["direction"] in {"positive", "negative", "neutral"}


def test_risk_explanation_returns_ranked_drivers():
    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=40, seed=42)

    inv_by_supplier, rev_by_supplier = {}, {}

    for inv in invoices:
        inv_by_supplier.setdefault(inv["supplier_id"], []).append(inv)

    for snap in snapshots:
        rev_by_supplier.setdefault(snap["supplier_id"], []).append(snap["revenue"])

    feature_rows = [
        extract_features(
            inv_by_supplier[s["id"]],
            rev_by_supplier[s["id"]],
        )
        for s in suppliers
    ]

    labels = [s["_ground_truth_label"] for s in suppliers]

    model = train_risk_model(feature_rows, labels)

    drivers = explain_risk(model, feature_rows[0])

    assert len(drivers) == 3
    assert all("factor" in driver for driver in drivers)
    assert all("label" in driver for driver in drivers)
    assert all("value" in driver for driver in drivers)
    assert all("impact" in driver for driver in drivers)
    assert all("direction" in driver for driver in drivers)

    impacts = [driver["impact"] for driver in drivers]

    assert impacts == sorted(impacts, reverse=True)
    assert all(0.0 <= impact <= 1.0 for impact in impacts)


def test_risk_explanation_direction_changes_with_feature_deviation():
    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=40, seed=42)

    inv_by_supplier, rev_by_supplier = {}, {}

    for inv in invoices:
        inv_by_supplier.setdefault(inv["supplier_id"], []).append(inv)

    for snap in snapshots:
        rev_by_supplier.setdefault(snap["supplier_id"], []).append(snap["revenue"])

    feature_rows = [
        extract_features(
            inv_by_supplier[s["id"]],
            rev_by_supplier[s["id"]],
        )
        for s in suppliers
    ]

    labels = [s["_ground_truth_label"] for s in suppliers]

    model = train_risk_model(feature_rows, labels)

    features = feature_rows[0].copy()

    features["avg_days_to_payment"] = (
        model.feature_means[1] + 3 * model.feature_stds[1]
    )

    drivers = explain_risk(model, features)

    payment_driver = next(
        driver
        for driver in drivers
        if driver["factor"] == "avg_days_to_payment"
    )

    assert payment_driver["direction"] == "negative"


def test_risk_explanation_handles_population_baseline():
    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=40, seed=42)

    inv_by_supplier, rev_by_supplier = {}, {}

    for inv in invoices:
        inv_by_supplier.setdefault(inv["supplier_id"], []).append(inv)

    for snap in snapshots:
        rev_by_supplier.setdefault(snap["supplier_id"], []).append(snap["revenue"])

    feature_rows = [
        extract_features(
            inv_by_supplier[s["id"]],
            rev_by_supplier[s["id"]],
        )
        for s in suppliers
    ]

    labels = [s["_ground_truth_label"] for s in suppliers]

    model = train_risk_model(feature_rows, labels)

    baseline_features = {
        factor: float(model.feature_means[index])
        for index, factor in enumerate(
            [
                "revenue_slope",
                "avg_days_to_payment",
                "days_to_payment_trend",
                "outstanding_ratio",
                "overdue_ratio",
                "on_time_rate",
            ]
        )
    }

    drivers = explain_risk(model, baseline_features)

    assert len(drivers) == 3
    assert all(driver["impact"] == 0.0 for driver in drivers)
