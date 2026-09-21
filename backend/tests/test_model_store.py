from pathlib import Path

import numpy as np

from app.services.model_store import load_model, save_model
from app.services.scoring import FEATURE_NAMES, RiskModel


def test_model_round_trip(tmp_path: Path):
    classifier = object()

    model = RiskModel(
        clf=classifier,
        feature_means=np.array([1.0, 2.0, 3.0]),
        feature_stds=np.array([4.0, 5.0, 6.0]),
        cv_precision=0.95,
        cv_recall=0.93,
    )

    model.feature_means = np.arange(len(FEATURE_NAMES), dtype=float)
    model.feature_stds = np.arange(
        1,
        len(FEATURE_NAMES) + 1,
        dtype=float,
    )

    path = tmp_path / "risk_model.joblib"

    save_model(model, path)
    loaded = load_model(path)

    assert loaded.clf is not None
    assert list(loaded.feature_means) == list(model.feature_means)
    assert list(loaded.feature_stds) == list(model.feature_stds)
    assert loaded.cv_precision == 0.0
    assert loaded.cv_recall == 0.0


def test_model_artifact_creates_parent_directory(tmp_path: Path):
    classifier = object()

    model = RiskModel(
        clf=classifier,
        feature_means=np.zeros(len(FEATURE_NAMES)),
        feature_stds=np.ones(len(FEATURE_NAMES)),
        cv_precision=0.95,
        cv_recall=0.93,
    )

    path = tmp_path / "nested" / "model.joblib"

    save_model(model, path)

    assert path.exists()