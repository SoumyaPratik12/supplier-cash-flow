import pytest

from app.services.data_generator import generate_suppliers
from app.services.scoring import extract_features, score_supplier, train_risk_model
from app.services.scenario import (
    DEPENDENCY_REDUCTION,
    EARLY_PAYMENT,
    apply_scenario,
    simulate_scenario,
)


@pytest.fixture
def scenario_context():
    suppliers, invoices, snapshots = generate_suppliers(
        n_suppliers=40,
        seed=42,
    )
    invoices_by_supplier = {}
    revenue_by_supplier = {}
    for invoice in invoices:
        invoices_by_supplier.setdefault(invoice["supplier_id"], []).append(invoice)
    for snapshot in snapshots:
        revenue_by_supplier.setdefault(snapshot["supplier_id"], []).append(
            snapshot["revenue"]
        )

    features = [
        extract_features(
            invoices_by_supplier[supplier["id"]],
            revenue_by_supplier[supplier["id"]],
        )
        for supplier in suppliers
    ]
    labels = [supplier["_ground_truth_label"] for supplier in suppliers]
    model = train_risk_model(features, labels)
    highest_risk_features = max(
        features,
        key=lambda item: score_supplier(model, item)[0],
    )
    return model, highest_risk_features


@pytest.fixture
def risk_model(scenario_context):
    return scenario_context[0]


@pytest.fixture
def features(scenario_context):
    return scenario_context[1]


def test_early_payment_changes_only_payment_features(risk_model, features):
    scenario_features, scenario_dependency = apply_scenario(
        features,
        0.72,
        EARLY_PAYMENT,
        target_payment_days=20.0,
    )

    assert scenario_features["avg_days_to_payment"] == 20.0
    assert scenario_features["days_to_payment_trend"] == 0.0
    assert scenario_dependency == 0.72

    result = simulate_scenario(
        risk_model,
        features,
        0.72,
        EARLY_PAYMENT,
        target_payment_days=20.0,
    )

    assert result.baseline.dependency == 0.72
    assert result.simulated.dependency == 0.72
    assert result.baseline.intervention["action"] == "Offer early payment"
    assert 0.0 <= result.simulated.score <= 1.0
    assert result.simulated.risk_level in {"Low", "Medium", "High"}


def test_dependency_reduction_does_not_change_financial_score(
    risk_model,
    features,
):
    result = simulate_scenario(
        risk_model,
        features,
        0.72,
        DEPENDENCY_REDUCTION,
        target_dependency=0.45,
    )

    assert result.baseline.score == result.simulated.score
    assert result.baseline.dependency == 0.72
    assert result.simulated.dependency == 0.45
    assert result.simulated.intervention["action"] == (
        "Reduce dependency on this supplier"
    )


def test_scenario_requires_an_improvement(risk_model, features):
    with pytest.raises(ValueError):
        simulate_scenario(
            risk_model,
            features,
            0.72,
            EARLY_PAYMENT,
            target_payment_days=72.0,
        )

    with pytest.raises(ValueError):
        simulate_scenario(
            risk_model,
            features,
            0.72,
            DEPENDENCY_REDUCTION,
            target_dependency=0.72,
        )