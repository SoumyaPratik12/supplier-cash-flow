import pytest

from app.services.dependency import (
    dependency_breakdown,
    dependency_level_from_weight,
)


@pytest.mark.parametrize(
    ("weight", "expected"),
    [
        (0.00, "Low"),
        (0.32, "Low"),
        (0.33, "Medium"),
        (0.65, "Medium"),
        (0.66, "High"),
        (1.00, "High"),
    ],
)
def test_dependency_level_boundaries(weight, expected):
    assert dependency_level_from_weight(weight) == expected


@pytest.mark.parametrize(
    "weight",
    [
        -0.01,
        1.01,
        -1.0,
        2.0,
    ],
)
def test_dependency_weight_rejects_out_of_range_values(weight):
    with pytest.raises(ValueError):
        dependency_level_from_weight(weight)


@pytest.mark.parametrize(
    "weight",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_dependency_weight_rejects_non_finite_values(weight):
    with pytest.raises(ValueError):
        dependency_level_from_weight(weight)


def test_dependency_breakdown_contains_expected_fields():
    result = dependency_breakdown(0.73)

    assert result == {
        "weight": 0.73,
        "level": "High",
        "replaceability": "Difficult to replace",
    }


def test_dependency_breakdown_rounds_weight():
    result = dependency_breakdown(0.73649)

    assert result["weight"] == 0.7365


def test_dependency_breakdown_preserves_classification_at_boundaries():
    assert dependency_breakdown(0.32)["level"] == "Low"
    assert dependency_breakdown(0.33)["level"] == "Medium"
    assert dependency_breakdown(0.66)["level"] == "High"
