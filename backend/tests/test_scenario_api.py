import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Supplier


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_early_payment_scenario(client):
    response = client.post(
        "/suppliers/1/scenario",
        json={
            "scenario": "early_payment",
            "payment_days_reduction": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["scenario"] == "early_payment"
    assert "baseline" in data
    assert "simulated" in data

    for state in (data["baseline"], data["simulated"]):
        assert "risk_level" in state
        assert "score" in state
        assert "dependency" in state
        assert "intervention" in state


def test_reduce_dependency_scenario(client):
    with SessionLocal() as db:
        supplier = (
            db.query(Supplier)
            .filter(Supplier.dependency_weight > 0.45)
            .order_by(Supplier.id)
            .first()
        )

    assert supplier is not None

    response = client.post(
        f"/suppliers/{supplier.id}/scenario",
        json={
            "scenario": "reduce_dependency",
            "dependency_weight": 0.45,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["scenario"] == "reduce_dependency"
    assert data["simulated"]["dependency"]["weight"] == 0.45


def test_scenario_unknown_supplier(client):
    response = client.post(
        "/suppliers/999999/scenario",
        json={
            "scenario": "reduce_dependency",
            "dependency_weight": 0.45,
        },
    )

    assert response.status_code == 404


def test_scenario_missing_model(client):
    original_model = getattr(client.app.state, "risk_model", None)
    client.app.state.risk_model = None
    try:
        response = client.post(
            "/suppliers/1/scenario",
            json={
                "scenario": "reduce_dependency",
                "dependency_weight": 0.45,
            },
        )
    finally:
        client.app.state.risk_model = original_model

    assert response.status_code == 503


def test_invalid_scenario_name(client):
    response = client.post(
        "/suppliers/1/scenario",
        json={
            "scenario": "dependency_reduction",
            "dependency_weight": 0.45,
        },
    )

    assert response.status_code == 422
