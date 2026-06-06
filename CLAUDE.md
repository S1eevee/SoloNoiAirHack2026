# CLAUDE.md — Session Context for SoloNoiAirHack2026

Read this file at the start of every session to resume work without re-explaining context.

---

## Project

**Passenger Flow Predictor** for AirHack 2026.  
Built for **Iași International Airport (IAS)**, check-in operations only (security gates are out of scope).  
Team: **SoloNoi**

---

## What Is Built (Current State)

A fully working MVP with:
- **XGBoost** regression model predicting passenger load per 30-min window
- **FastAPI** backend (port 8000) with REST endpoints
- **Streamlit** employee dashboard (port 8501) with 5 tabs
- **Claude claude-opus-4-8** LLM layer for natural language insights (with fallback if no API key)
- **SQLite** alert persistence with OPEN → ACKNOWLEDGED → RESOLVED lifecycle
- Configurable alert thresholds in `config/thresholds.yaml`

---

## How to Run

```bash
# Terminal 1 — API
python3 -m uvicorn src.api.app:app --reload --port 8000

# Terminal 2 — Dashboard
python3 -m streamlit run src/dashboard/app.py
```

Dashboard: http://localhost:8501  
API docs: http://localhost:8000/docs

---

## Workflow

1. **Train Model tab** → upload historical flights CSV → click Train Model
2. **Forecast tab** → upload tomorrow's schedule → click Run Forecast & Generate Alerts
3. **Alerts tab** → employees acknowledge check-in desk alerts
4. **AI Insights tab** → Claude or fallback summary
5. **Settings tab** → configure thresholds

---

## Key Decisions Made

- **XGBoost only** — no linear regression, no SVR
- **Check-in desks only** — security gates explicitly removed from all layers
- **YOLOv8 deferred** — Phase 2, not in MVP
- **Claude fallback** — works without API key, returns rule-based summary
- **Two upload types** — training data (historical, appends) vs schedule (upcoming, overwrites)
- **Real data source** — Iași Airport T4 administration (do not use synthetic data in production)

---

## CSV Input

The system auto-detects delimiter and column names. Supported naming:

| Data | Accepted names |
|---|---|
| Departure flight | `dep_flight`, `departure_flight`, `flight_id` |
| Departure time | `dep_time`, `departure_time`, `scheduled_time`, `etd`, `std` |
| Departure pax | `dep_pax`, `departure_pax`, `pax_count` |
| Arrival flight | `arr_flight`, `arrival_flight` |
| Arrival time | `arr_time`, `arrival_time`, `eta`, `sta` |
| Arrival pax | `arr_pax`, `arrival_pax` |

Time formats handled: `2026-06-06 14:30`, `14:30`, `14:30/06`, `23:50/31`

---

## File Map

```
pipeline.py              — CLI: train / predict / run / insights
config/thresholds.yaml   — alert thresholds (editable via UI)
src/data/loader.py       — CSV → DataFrame (auto-detects format)
src/data/cleaner.py      — normalise columns, parse times
src/data/features.py     — aggregate into 30-min window features
src/model/train.py       — XGBoost fit + save to models/model.pkl
src/model/predict.py     — load model + infer
src/model/evaluate.py    — MAE / RMSE / MAPE
src/alerts/engine.py     — predictions vs thresholds → alerts
src/alerts/state.py      — SQLite CRUD for alert lifecycle
src/llm/insights.py      — Claude API + rule-based fallback
src/api/app.py           — FastAPI app
src/api/routes/data.py   — /data/upload/training, /data/upload/schedule
src/api/routes/forecast.py — /forecast/train, /forecast/run
src/api/routes/alerts.py — /alerts GET/POST
src/api/routes/thresholds.py — /thresholds GET/POST
src/api/routes/insights.py   — /insights POST
src/dashboard/app.py     — Streamlit UI (5 tabs)
```

---

## Phase 2 (Not Built Yet)

- YOLOv8 live camera feed for real-time passenger counting
- Feed live pax counts back into XGBoost alongside schedule data

---

## Environment

- Python 3.14, macOS
- Working directory: `/Users/Admin/SoloNoiAirHack2026`
- GitHub: https://github.com/S1eevee/SoloNoiAirHack2026
- `pip3` / `python3` — use `python3 -m uvicorn` not bare `uvicorn` (not in PATH)
- Anthropic API key: enter in dashboard sidebar or set `ANTHROPIC_API_KEY` env var

---

## Known Issues Fixed

- CSV column names auto-detected via keyword matching (not exact match)
- Time format `HH:MM/DD` (e.g. `23:50/31`) parsed correctly, day clamped to month max
- `uvicorn` not in PATH on this machine — always use `python3 -m uvicorn`
- Model trained on single-day data gives flat predictions — need 2+ weeks of data
