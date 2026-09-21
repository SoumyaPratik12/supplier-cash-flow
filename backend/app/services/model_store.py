"""Persistence helpers for the trained supplier risk model."""

from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np

from app.services.scoring import FEATURE_NAMES, RiskModel


def save_model(model: RiskModel, path: Path) -> None:
    """Persist the minimum model state required for serving and scenarios."""
    artifact: Dict[str, Any] = {
        "feature_names": FEATURE_NAMES,
        "classifier": model.clf,
        "feature_means": model.feature_means,
        "feature_stds": model.feature_stds,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)


def load_model(path: Path) -> RiskModel:
    """Load a persisted risk model artifact."""
    artifact = joblib.load(path)

    required_keys = {
        "feature_names",
        "classifier",
        "feature_means",
        "feature_stds",
    }

    missing = required_keys - artifact.keys()
    if missing:
        raise ValueError(
            f"Model artifact is missing required fields: {sorted(missing)}"
        )

    if list(artifact["feature_names"]) != list(FEATURE_NAMES):
        raise ValueError(
            "Model artifact feature_names do not match FEATURE_NAMES"
        )

    return RiskModel(
        clf=artifact["classifier"],
        feature_means=np.asarray(artifact["feature_means"]),
        feature_stds=np.asarray(artifact["feature_stds"]),
        cv_precision=0.0,
        cv_recall=0.0,
    )