from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    issue_date: date
    due_date: date
    paid_date: Optional[date]
    status: str


class RevenueSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str
    period_index: int
    revenue: float


class SupplierListItem(BaseModel):
    id: int
    name: str
    industry: str
    order_volume: float
    dependency_weight: float
    risk_level: str
    score: float
    recommended_action: str


class RiskDriver(BaseModel):
    factor: str
    label: str
    value: float
    impact: float
    direction: str

class DependencyBreakdown(BaseModel):
    weight: float
    level: str
    replaceability: str


class InterventionDecision(BaseModel):
    action: str
    priority: str
    reason: str


class RiskBreakdown(BaseModel):
    risk_level: str
    score: float
    top_factors: List[str]
    risk_drivers: List[RiskDriver]
    dependency: DependencyBreakdown
    forecast_next_period: float
    recommended_action: str
    intervention: InterventionDecision


class SupplierProfile(BaseModel):
    id: int
    name: str
    industry: str
    order_volume: float
    dependency_weight: float
    invoices: List[InvoiceOut]
    revenue_history: List[RevenueSnapshotOut]
    risk: Optional[RiskBreakdown]


class ForecastOut(BaseModel):
    supplier_id: int
    history: List[RevenueSnapshotOut]
    forecast_next_period: float
