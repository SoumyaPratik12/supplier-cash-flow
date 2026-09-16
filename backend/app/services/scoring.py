"""Risk classification: feature engineering + a gradient boosting classifier
trained on the synthetic labeled data. No LLM anywhere in this path, per
project scope — this is a small, explainable tabular model on purpose.

Explainability approach: rather than pulling in SHAP for a 40-row demo
dataset, we rank each supplier's own features by (feature_value - population
mean) / population_std, weighted by the model's global feature_importances_.
This gives an honest "why this supplier, specifically" without overstating
precision the underlying model doesn't have.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

from app.services.forecasting import revenue_slope

FEATURE_NAMES = [
    "revenue_slope",
    "avg_days_to_payment",
    "days_to_payment_trend",
    "outstanding_ratio",
    "overdue_ratio",
    "on_time_rate",
]


def extract_features(invoices: List[dict], revenue_series: List[float]) -> Dict[str, float]:
    paid = [inv for inv in invoices if inv["status"] == "paid" and inv["paid_date"]]
    days_to_payment = [(inv["paid_date"] - inv["issue_date"]).days for inv in paid]

    avg_days = float(np.mean(days_to_payment)) if days_to_payment else 30.0

    if len(days_to_payment) >= 2:
        x = np.arange(len(days_to_payment))
        dtp_trend = float(np.polyfit(x, days_to_payment, 1)[0])
    else:
        dtp_trend = 0.0

    total = len(invoices) or 1
    outstanding_ratio = sum(1 for inv in invoices if inv["status"] in ("outstanding", "overdue")) / total
    overdue_ratio = sum(1 for inv in invoices if inv["status"] == "overdue") / total
    on_time_rate = (
        sum(1 for inv in paid if (inv["paid_date"] - inv["due_date"]).days <= 0) / len(paid) if paid else 1.0
    )

    return {
        "revenue_slope": revenue_slope(revenue_series),
        "avg_days_to_payment": avg_days,
        "days_to_payment_trend": dtp_trend,
        "outstanding_ratio": outstanding_ratio,
        "overdue_ratio": overdue_ratio,
        "on_time_rate": on_time_rate,
    }


@dataclass
class RiskModel:
    clf: GradientBoostingClassifier
    feature_means: np.ndarray
    feature_stds: np.ndarray
    cv_precision: float
    cv_recall: float


def train_risk_model(feature_rows: List[Dict[str, float]], labels: List[int]) -> RiskModel:
    X = np.array([[row[f] for f in FEATURE_NAMES] for row in feature_rows])
    y = np.array(labels)

    clf = GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.1, random_state=42)

    # 5-fold CV for an honest read on a 40-row dataset — do not trust a
    # single train/test split at this sample size
    cv_precision = float(np.mean(cross_val_score(clf, X, y, cv=5, scoring="precision")))
    cv_recall = float(np.mean(cross_val_score(clf, X, y, cv=5, scoring="recall")))

    clf.fit(X, y)

    return RiskModel(
        clf=clf,
        feature_means=X.mean(axis=0),
        feature_stds=X.std(axis=0) + 1e-6,
        cv_precision=cv_precision,
        cv_recall=cv_recall,
    )


def score_supplier(model: RiskModel, features: Dict[str, float]) -> Tuple[float, List[str]]:
    x = np.array([[features[f] for f in FEATURE_NAMES]])
    score = float(model.clf.predict_proba(x)[0][1])

    z_scores = (x[0] - model.feature_means) / model.feature_stds
    importances = model.clf.feature_importances_
    weighted = np.abs(z_scores) * importances
    ranked_idx = np.argsort(-weighted)
    top_factors = [FEATURE_NAMES[i] for i in ranked_idx[:3]]

    return round(score, 3), top_factors


def risk_level_from_score(score: float) -> str:
    if score < 0.33:
        return "Low"
    if score < 0.66:
        return "Medium"
    return "High"


def recommended_action(risk_level: str, dependency_weight: float) -> str:
    if risk_level != "High":
        return "Monitor"
    return "Offer early payment" if dependency_weight >= 0.5 else "Reduce dependency on this supplier"
