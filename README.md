# Supplier Cash-Flow Predictor

Predicts which suppliers are likely to face a cash-flow shortfall before it
disrupts the supply chain — and, more importantly, ranks *which* supplier
deserves intervention first and *what* intervention makes sense (offer early
payment vs. reduce dependency). Supply Chain + FinTech, not invoice
financing.

No LLM anywhere in the scoring path — this is a small, explainable
statistical/ML model on purpose.

## Status: Phase 0 complete
- Synthetic data generator (5 supplier archetypes, deterministic, with
  ground-truth labels) — verified with 9 passing unit tests
- Risk scoring model (GradientBoostingClassifier) — **5-fold CV precision
  ~0.95, recall ~0.83–0.93** depending on random seed, validated against a
  real Postgres instance
- Forecasting (linear trend regression per supplier)
- FastAPI backend with all MVP endpoints — manually verified live against a
  seeded Postgres database, including the 404 case
- React + Vite + Recharts frontend — ranked dashboard + supplier detail view
  with forecast chart — builds clean

## Why the data is synthetic
Real supplier financial + supply-chain datasets at invoice-level granularity
aren't publicly available — this was the #1 stated risk for this project
going in. Rather than generating arbitrary numbers, `data_generator.py`
builds each supplier from a named archetype (stable / growing / slipping /
distressed / volatile) where revenue trend, payment behavior, and invoice
aging move together the way they plausibly would for a real business in that
situation. A subset gets an explicit ground-truth label so the model has
something real to learn from — see the docstring at the top of
`backend/app/services/data_generator.py` for the full design rationale.

**This is a demo dataset. Forecast horizons and risk thresholds are tuned
for demo clarity, not calibrated against real-world default rates.**

## Architecture
Monolith, not microservices — this is a single-team demo. Scoring runs as an
offline batch job (`app/seed.py`), not live per-request, which is realistic
for supplier risk (doesn't need to be real-time) and keeps things simple.

```
supplier-cash-flow/
├── .devcontainer/       # Codespaces config — postgres + python, auto-detected
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + CORS
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # suppliers, invoices, revenue_snapshots, risk_scores
│   │   ├── schemas.py         # Pydantic response models
│   │   ├── seed.py            # generate data -> train model -> persist scores
│   │   ├── routers/suppliers.py
│   │   └── services/
│   │       ├── data_generator.py   # the most-documented file in the repo — read this first
│   │       ├── scoring.py          # feature engineering + risk classifier
│   │       └── forecasting.py      # trend-based revenue forecast
│   └── tests/test_scoring.py  # 9 tests covering generator, forecast, scoring
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js
        └── components/{SupplierList,SupplierDetail}.jsx
```

## Running in GitHub Codespaces
1. Push this repo, then on GitHub: **Code → Codespaces → Create codespace on
   main**. The devcontainer (Python + Postgres via docker-compose) builds
   automatically — no manual setup needed.
2. Once the codespace is ready, seed the database:
   ```bash
   cd backend
   python -m app.seed
   ```
3. Start the API:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. In a second terminal, start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. Codespaces will prompt to forward ports 8000 and 5173 — open the 5173
   preview.

## Running locally (without Codespaces)
Same steps as above, but you'll need Postgres running locally first and a
`backend/.env` (copy `backend/.env.example`) pointing `DATABASE_URL` at it.

## Testing
```bash
cd backend
pytest tests/ -v
```

## Next (post-Phase 0)
- On-demand re-scoring ("what if this supplier's biggest customer delays
  payment?")
- Multi-tier supply chain visibility (your supplier's supplier)
- Alerting/notification integration
- Deploy demo to Render/Railway (API+DB) and Vercel/Netlify (frontend)
