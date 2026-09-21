import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice, RevenueSnapshot, RiskScore, Supplier
from app.schemas import (
    ForecastOut,
    InvoiceOut,
    InterventionDecision,
    RevenueSnapshotOut,
    RiskBreakdown,
    ScenarioRequest,
    ScenarioResponse,
    ScenarioStateResponse,
    SupplierListItem,
    SupplierProfile,
)
from app.services.dependency import dependency_breakdown
from app.services.intervention import intervention_for
from app.services.scenario import (
    DEPENDENCY_REDUCTION,
    EARLY_PAYMENT,
    simulate_scenario,
)
from app.services.scoring import extract_features

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _latest_risk(db: Session, supplier_id: int):
    return (
        db.query(RiskScore)
        .filter(RiskScore.supplier_id == supplier_id)
        .order_by(RiskScore.id.desc())
        .first()
    )


@router.get("", response_model=list[SupplierListItem])
def list_suppliers(db: Session = Depends(get_db)):
    """Ranked risk dashboard: sorted by risk score x dependency weight, so the
    highest-priority intervention surfaces first — this ranking, not the raw
    score, is the actual PM differentiator per the kickoff doc."""
    suppliers = db.query(Supplier).all()
    items = []
    for s in suppliers:
        risk = _latest_risk(db, s.id)
        if not risk:
            continue
        items.append(
            SupplierListItem(
                id=s.id,
                name=s.name,
                industry=s.industry,
                order_volume=s.order_volume,
                dependency_weight=s.dependency_weight,
                risk_level=risk.risk_level.value,
                score=risk.score,
                recommended_action=risk.recommended_action.value,
            )
        )
    items.sort(key=lambda i: i.score * i.dependency_weight, reverse=True)
    return items


@router.post("/{supplier_id}/scenario", response_model=ScenarioResponse)
def run_supplier_scenario(
    supplier_id: int,
    payload: ScenarioRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ScenarioResponse:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    risk_model = getattr(request.app.state, "risk_model", None)
    if risk_model is None:
        raise HTTPException(
            status_code=503,
            detail="Risk model is not available",
        )

    invoices = (
        db.query(Invoice)
        .filter(Invoice.supplier_id == supplier_id)
        .all()
    )
    revenue_snapshots = (
        db.query(RevenueSnapshot)
        .filter(RevenueSnapshot.supplier_id == supplier_id)
        .all()
    )
    invoice_data = [
        {
            "status": invoice.status.value,
            "paid_date": invoice.paid_date,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
        }
        for invoice in invoices
    ]
    features = extract_features(
        invoice_data,
        [snapshot.revenue for snapshot in revenue_snapshots],
    )

    if payload.scenario == "early_payment":
        if payload.payment_days_reduction is None:
            raise HTTPException(
                status_code=422,
                detail="payment_days_reduction is required for early_payment",
            )
        scenario_type = EARLY_PAYMENT
        target_payment_days = (
            features["avg_days_to_payment"] - payload.payment_days_reduction
        )
        target_dependency = None
    elif payload.scenario == "reduce_dependency":
        if payload.dependency_weight is None:
            raise HTTPException(
                status_code=422,
                detail="dependency_weight is required for reduce_dependency",
            )
        scenario_type = DEPENDENCY_REDUCTION
        target_payment_days = None
        target_dependency = payload.dependency_weight
    else:
        raise HTTPException(
            status_code=422,
            detail="scenario must be one of: early_payment, reduce_dependency",
        )

    try:
        result = simulate_scenario(
            model=risk_model,
            current_features=features,
            current_dependency=supplier.dependency_weight,
            scenario=scenario_type,
            target_payment_days=target_payment_days,
            target_dependency=target_dependency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def state_to_response(state) -> ScenarioStateResponse:
        return ScenarioStateResponse(
            risk_level=state.risk_level,
            score=state.score,
            dependency=dependency_breakdown(state.dependency),
            intervention=InterventionDecision(**state.intervention),
        )

    return ScenarioResponse(
        scenario=payload.scenario,
        baseline=state_to_response(result.baseline),
        simulated=state_to_response(result.simulated),
    )


@router.get("/{supplier_id}", response_model=SupplierProfile)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")

    risk = _latest_risk(db, supplier_id)
    risk_out = None
    if risk:
        risk_out = RiskBreakdown(
            risk_level=risk.risk_level.value,
            score=risk.score,
            top_factors=risk.top_factors.split(","),
            risk_drivers=json.loads(risk.risk_drivers),
            dependency=dependency_breakdown(s.dependency_weight),
            forecast_next_period=risk.forecast_next_period,
            recommended_action=risk.recommended_action.value,
            intervention=InterventionDecision(
                **intervention_for(
                    risk.risk_level.value,
                    s.dependency_weight,
                )
            ),
        )

    invoices = db.query(Invoice).filter(Invoice.supplier_id == supplier_id).order_by(Invoice.issue_date).all()
    revenue = (
        db.query(RevenueSnapshot)
        .filter(RevenueSnapshot.supplier_id == supplier_id)
        .order_by(RevenueSnapshot.period_index)
        .all()
    )

    return SupplierProfile(
        id=s.id,
        name=s.name,
        industry=s.industry,
        order_volume=s.order_volume,
        dependency_weight=s.dependency_weight,
        invoices=[InvoiceOut.model_validate(i) for i in invoices],
        revenue_history=[RevenueSnapshotOut.model_validate(r) for r in revenue],
        risk=risk_out,
    )


@router.get("/{supplier_id}/forecast", response_model=ForecastOut)
def get_forecast(supplier_id: int, db: Session = Depends(get_db)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")

    revenue = (
        db.query(RevenueSnapshot)
        .filter(RevenueSnapshot.supplier_id == supplier_id)
        .order_by(RevenueSnapshot.period_index)
        .all()
    )
    risk = _latest_risk(db, supplier_id)

    return ForecastOut(
        supplier_id=supplier_id,
        history=[RevenueSnapshotOut.model_validate(r) for r in revenue],
        forecast_next_period=risk.forecast_next_period if risk else 0.0,
    )


@router.get("/{supplier_id}/risk-breakdown", response_model=RiskBreakdown)
def get_risk_breakdown(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    risk = _latest_risk(db, supplier_id)
    if not risk:
        raise HTTPException(status_code=404, detail="No risk score for this supplier")

    return RiskBreakdown(
        risk_level=risk.risk_level.value,
        score=risk.score,
        top_factors=risk.top_factors.split(","),
        risk_drivers=json.loads(risk.risk_drivers),
        dependency=dependency_breakdown(supplier.dependency_weight),
        forecast_next_period=risk.forecast_next_period,
        recommended_action=risk.recommended_action.value,
        intervention=InterventionDecision(
            **intervention_for(
                risk.risk_level.value,
                supplier.dependency_weight,
            )
        ),
    )
