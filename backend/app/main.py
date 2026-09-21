from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import suppliers
from app.services.model_store import load_model

app = FastAPI(
    title="Supplier Cash-Flow Predictor",
    description="Ranks suppliers by cash-flow risk so intervention (early payment / "
    "reduce dependency) happens before a shortfall disrupts the supply chain. "
    "All data is synthetic — see README for generation assumptions.",
    version="0.1.0",
)

MODEL_PATH = Path(__file__).resolve().parent / "risk_model.joblib"


@app.on_event("startup")
def load_risk_model() -> None:
    """Load the persisted risk model when available."""
    if MODEL_PATH.exists():
        app.state.risk_model = load_model(MODEL_PATH)
    else:
        app.state.risk_model = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"https://.*-5173\.app\.github\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(suppliers.router)


@app.get("/health")
def health():
    return {"status": "ok"}
