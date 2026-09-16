from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import suppliers

app = FastAPI(
    title="Supplier Cash-Flow Predictor",
    description="Ranks suppliers by cash-flow risk so intervention (early payment / "
    "reduce dependency) happens before a shortfall disrupts the supply chain. "
    "All data is synthetic — see README for generation assumptions.",
    version="0.1.0",
)

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
