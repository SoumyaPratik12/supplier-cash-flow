import enum

from sqlalchemy import (
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class InvoiceStatus(str, enum.Enum):
    paid = "paid"
    outstanding = "outstanding"
    overdue = "overdue"


class RiskLevel(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class RecommendedAction(str, enum.Enum):
    monitor = "Monitor"
    offer_early_payment = "Offer early payment"
    reduce_dependency = "Reduce dependency on this supplier"


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    order_volume = Column(Float, nullable=False)  # annualized spend with this supplier
    dependency_weight = Column(Float, nullable=False)  # 0-1, how hard this supplier is to replace

    invoices = relationship("Invoice", back_populates="supplier", cascade="all, delete-orphan")
    revenue_snapshots = relationship(
        "RevenueSnapshot", back_populates="supplier", cascade="all, delete-orphan"
    )
    risk_scores = relationship(
        "RiskScore", back_populates="supplier", cascade="all, delete-orphan"
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    status = Column(Enum(InvoiceStatus), nullable=False)

    supplier = relationship("Supplier", back_populates="invoices")


class RevenueSnapshot(Base):
    __tablename__ = "revenue_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    period = Column(String, nullable=False)  # e.g. "2026-Q1"
    period_index = Column(Integer, nullable=False)  # 0..N, for trend regression
    revenue = Column(Float, nullable=False)

    supplier = relationship("Supplier", back_populates="revenue_snapshots")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    period = Column(String, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    score = Column(Float, nullable=False)  # 0-1 probability of cash-flow shortfall
    top_factors = Column(String, nullable=False)  # comma-separated, ranked
    forecast_next_period = Column(Float, nullable=False)
    recommended_action = Column(Enum(RecommendedAction), nullable=False)
    ground_truth_label = Column(Integer, nullable=True)  # only set for synthetic labeled subset

    supplier = relationship("Supplier", back_populates="risk_scores")
