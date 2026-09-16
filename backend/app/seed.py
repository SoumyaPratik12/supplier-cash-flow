"""Run this once to (re)build the demo database:
    python -m app.seed
Generates synthetic suppliers/invoices/revenue, trains the risk model on the
synthetic ground truth, and persists risk scores + forecasts per supplier.
This mirrors the "offline batch job" design from the kickoff doc — scoring
is not computed live per request."""

from app.database import Base, SessionLocal, engine
from app.models import Invoice, RevenueSnapshot, RiskScore, Supplier
from app.services.data_generator import generate_suppliers
from app.services.forecasting import forecast_next_period
from app.services.scoring import (
    extract_features,
    recommended_action,
    risk_level_from_score,
    score_supplier,
    train_risk_model,
)


def seed(n_suppliers: int = 50, seed_value: int = 42):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    suppliers, invoices, snapshots = generate_suppliers(n_suppliers=n_suppliers, seed=seed_value)

    invoices_by_supplier = {}
    for inv in invoices:
        invoices_by_supplier.setdefault(inv["supplier_id"], []).append(inv)

    revenue_by_supplier = {}
    for snap in snapshots:
        revenue_by_supplier.setdefault(snap["supplier_id"], []).append(snap["revenue"])

    feature_rows, labels = [], []
    for s in suppliers:
        feats = extract_features(invoices_by_supplier[s["id"]], revenue_by_supplier[s["id"]])
        feature_rows.append(feats)
        labels.append(s["_ground_truth_label"])

    model = train_risk_model(feature_rows, labels)
    print(f"Trained risk model — 5-fold CV precision={model.cv_precision:.2f}, recall={model.cv_recall:.2f}")

    db = SessionLocal()
    try:
        for s, feats in zip(suppliers, feature_rows):
            db.add(
                Supplier(
                    id=s["id"],
                    name=s["name"],
                    industry=s["industry"],
                    order_volume=s["order_volume"],
                    dependency_weight=s["dependency_weight"],
                )
            )
        db.flush()

        for inv in invoices:
            db.add(Invoice(**inv))

        for snap in snapshots:
            db.add(RevenueSnapshot(**snap))

        for s, feats in zip(suppliers, feature_rows):
            score, top_factors = score_supplier(model, feats)
            level = risk_level_from_score(score)
            action = recommended_action(level, s["dependency_weight"])
            rev_series = revenue_by_supplier[s["id"]]

            db.add(
                RiskScore(
                    supplier_id=s["id"],
                    period="2026-current",
                    risk_level=level,
                    score=score,
                    top_factors=",".join(top_factors),
                    forecast_next_period=forecast_next_period(rev_series),
                    recommended_action=action,
                    ground_truth_label=s["_ground_truth_label"],
                )
            )

        db.commit()
        print(f"Seeded {len(suppliers)} suppliers, {len(invoices)} invoices, {len(snapshots)} revenue snapshots")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
