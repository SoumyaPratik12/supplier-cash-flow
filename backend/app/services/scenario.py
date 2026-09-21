"""Scenario simulation built on the existing risk and intervention services."""

from dataclasses import dataclass
from typing import Dict, Literal, Optional

from app.services.intervention import intervention_for
from app.services.scoring import (
    FEATURE_NAMES,
    RiskModel,
    risk_level_from_score,
    score_supplier,
)

ScenarioType = Literal["early_payment", "dependency_reduction"]

EARLY_PAYMENT = "early_payment"
DEPENDENCY_REDUCTION = "dependency_reduction"


@dataclass(frozen=True)
class ScenarioState:
    risk_level: str
    score: float
    dependency: float
    intervention: Dict[str, str]


@dataclass(frozen=True)
class ScenarioResult:
    scenario: ScenarioType
    baseline: ScenarioState
    simulated: ScenarioState


def simulate_scenario(
    model: RiskModel,
    current_features: Dict[str, float],
    current_dependency: float,
    scenario: ScenarioType,
    *,
    target_payment_days: Optional[float] = None,
    target_dependency: Optional[float] = None,
) -> ScenarioResult:
    """Simulate one intervention without changing persisted risk scores.

    Early payment changes average payment time and removes a worsening payment
    trend. Dependency reduction changes only the dependency input. All other
    financial features remain unchanged in both scenarios.
    """
    _validate_features(current_features)
    _validate_dependency(current_dependency)

    baseline_score, _ = score_supplier(model, current_features)
    baseline_level = risk_level_from_score(baseline_score)
    baseline = ScenarioState(
        risk_level=baseline_level,
        score=baseline_score,
        dependency=current_dependency,
        intervention=intervention_for(baseline_level, current_dependency),
    )

    scenario_features, scenario_dependency = apply_scenario(
        current_features,
        current_dependency,
        scenario,
        target_payment_days=target_payment_days,
        target_dependency=target_dependency,
    )

    scenario_score, _ = score_supplier(model, scenario_features)
    scenario_level = risk_level_from_score(scenario_score)
    simulated = ScenarioState(
        risk_level=scenario_level,
        score=scenario_score,
        dependency=scenario_dependency,
        intervention=intervention_for(scenario_level, scenario_dependency),
    )

    return ScenarioResult(
        scenario=scenario,
        baseline=baseline,
        simulated=simulated,
    )


def apply_scenario(
    current_features: Dict[str, float],
    current_dependency: float,
    scenario: ScenarioType,
    *,
    target_payment_days: Optional[float] = None,
    target_dependency: Optional[float] = None,
) -> tuple[Dict[str, float], float]:
    """Return simulated financial features and dependency without scoring."""
    _validate_features(current_features)
    _validate_dependency(current_dependency)

    scenario_features = current_features.copy()
    scenario_dependency = current_dependency

    if scenario == EARLY_PAYMENT:
        _validate_early_payment_target(
            target_payment_days,
            current_features["avg_days_to_payment"],
        )
        scenario_features["avg_days_to_payment"] = target_payment_days
        scenario_features["days_to_payment_trend"] = 0.0
    elif scenario == DEPENDENCY_REDUCTION:
        _validate_dependency_target(target_dependency, current_dependency)
        scenario_dependency = target_dependency
    else:
        raise ValueError(f"Unsupported scenario: {scenario}")

    return scenario_features, scenario_dependency


def _validate_features(features: Dict[str, float]) -> None:
    missing = set(FEATURE_NAMES) - features.keys()
    if missing:
        raise ValueError(f"Missing risk features: {sorted(missing)}")


def _validate_dependency(value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError("dependency must be between 0 and 1")


def _validate_early_payment_target(
    target_payment_days: Optional[float],
    current_payment_days: float,
) -> None:
    if target_payment_days is None:
        raise ValueError("target_payment_days is required for early payment")
    if target_payment_days <= 0:
        raise ValueError("target_payment_days must be greater than 0")
    if target_payment_days >= current_payment_days:
        raise ValueError(
            "target_payment_days must be lower than current payment days"
        )


def _validate_dependency_target(
    target_dependency: Optional[float],
    current_dependency: float,
) -> None:
    if target_dependency is None:
        raise ValueError(
            "target_dependency is required for dependency reduction"
        )
    _validate_dependency(target_dependency)
    if target_dependency >= current_dependency:
        raise ValueError(
            "target_dependency must be lower than current dependency"
        )