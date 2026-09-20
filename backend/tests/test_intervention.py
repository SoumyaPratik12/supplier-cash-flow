import math

import pytest

from app.services.intervention import intervention_for


@pytest.mark.parametrize(
    "risk_level,dependency_weight,expected_action,expected_priority",
    [
        ("Low", 0.00, "Monitor", "Low"),
        ("Low", 1.00, "Monitor", "Low"),
        ("Medium", 0.00, "Monitor", "Medium"),
        ("Medium", 1.00, "Monitor", "Medium"),
        (
            "High",
            0.00,
            "Reduce dependency on this supplier",
            "High",
        ),
        (
            "High",
            0.49,
            "Reduce dependency on this supplier",
            "High",
        ),
        (
            "High",
            0.50,
            "Offer early payment",
            "High",
        ),
        (
            "High",
            1.00,
            "Offer early payment",
            "High",
        ),
    ],
)
def test_intervention_matrix(
    risk_level,
    dependency_weight,
    expected_action,
    expected_priority,
):
    result = intervention_for(risk_level, dependency_weight)

    assert result["action"] == expected_action
    assert result["priority"] == expected_priority
    assert result["reason"]


@pytest.mark.parametrize("risk_level", ["Low", "Medium", "High"])
def test_intervention_rejects_invalid_dependency(
    risk_level,
):
    with pytest.raises(ValueError):
        intervention_for(risk_level, -0.01)

    with pytest.raises(ValueError):
        intervention_for(risk_level, 1.01)


@pytest.mark.parametrize(
    "dependency_weight",
    [math.nan, math.inf, -math.inf],
)
def test_intervention_rejects_non_finite_dependency(
    dependency_weight,
):
    with pytest.raises(ValueError):
        intervention_for("High", dependency_weight)


@pytest.mark.parametrize(
    "risk_level",
    ["low", "medium", "high", "", "Unknown", None],
)
def test_intervention_rejects_invalid_risk_level(
    risk_level,
):
    with pytest.raises((ValueError, TypeError)):
        intervention_for(risk_level, 0.5)


def test_dependency_boundary_is_exactly_preserved():
    below = intervention_for("High", 0.499999)
    boundary = intervention_for("High", 0.5)

    assert below["action"] == "Reduce dependency on this supplier"
    assert boundary["action"] == "Offer early payment"


def test_reasons_match_intervention_logic():
    low = intervention_for("Low", 0.4)
    medium = intervention_for("Medium", 0.4)
    early_payment = intervention_for("High", 0.8)
    reduce_dependency = intervention_for("High", 0.2)

    assert (
        low["reason"]
        == "Low financial risk does not currently trigger a high-risk intervention."
    )

    assert (
        medium["reason"]
        == "Medium financial risk does not currently trigger a high-risk intervention."
    )

    assert (
        early_payment["reason"]
        == "High financial risk combined with high supplier dependency."
    )

    assert (
        reduce_dependency["reason"]
        == "High financial risk combined with lower supplier dependency."
    )
