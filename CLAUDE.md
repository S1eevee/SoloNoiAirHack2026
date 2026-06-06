# CLAUDE.md — Session Context for SoloNoiAirHack2026

Read this file at the start of every session to resume work without re-explaining context.

---

## Project

**Passenger Flow Predictor** for AirHack 2026.  
Built for **Iași International Airport (IAS)**, check-in operations only (security gates are out of scope).  
Team: **SoloNoi**

GitHub: https://github.com/S1eevee/SoloNoiAirHack2026

---

## What Is Built (Current State)

A fully working MVP with:
- **XGBoost** regression model predicting passenger load per 30-min window
- **Bell curve passenger spreading** — pax arrive normally distributed, mean = departure − 2h, σ = 30 min
- **Synthetic congestion delay** — EMA of excess passengers shifted one window forward, capped at 60 min
- **FastAPI** backend (port 8000) with REST endpoints
- **Streamlit** employee dashboard (port 8501) with **5 navigation tabs**
- **SQLite** alert persistence with OPEN → ACKNOWLEDGED → RESOLVED lifecycle
- **Time-evolving desk simulation** — desk state carries forward window-by-window
- **Percentile-based threshold auto-detection** (p50/p75/p90 from training data)
- **Multi-file CSV upload** with JSON manifest tracking
- **Agent-based visual simulation** tab with full-day playback

---

## How to Run

```bash
# Terminal 1 — API
python3.14 -m uvicorn src.api.app:app --reload --port 8000

# Terminal 2 — Dashboard
python3.14 -m streamlit run src/dashboard/app.py
```

Dashboard: http://localhost:8501  
API docs: http://localhost:8000/docs

> **Always use `python3.14`** — bare `python3` or `uvicorn` are not in PATH on this machine.

---

## Dashboard Navigation (5 tabs)

1. **Train Model** — upload historical CSVs (multi-file), train XGBoost, view MAE/RMSE/MAPE
2. **Forecast** — upload schedule CSV, run forecast, view bar chart with threshold reference lines
3. **Alerts** — acknowledge desk open/close alerts; desk counter updates on acknowledgement
4. **Simulation** — visual agent-based simulation (see below)
5. **Settings** — auto-detect thresholds from data, manual override

> AI Insights tab was removed — it was not useful.

---

## Simulation Tab (major feature)

Canvas-based agent simulation in `src/dashboard/app.py` embedded via `st.components.v1.html()`.

**Features:**
- **3 passenger types**: Solo (blue, 1×), Family (orange, 1.9×), Business (cyan, 0.55×)
- **Balk mechanic** — passengers leave if best queue ≥ 9 deep (counted in "Turned Away" stat)
- **Forecast-driven** — auto-fetches forecast + alerts on load; no manual input needed
- **Timeline** — scrollable horizontal strip of all 30-min windows, colored by load level, alert dots
- **Window card** — click any block to see time, predicted pax, recommended desks, alert message
- **"Simulate this window"** — sets desks from alert history, compresses 30 min into ~90 sec
- **Speed slider** (1x–30x) — scales both spawn rate and check-in time proportionally
- **"Simulate Entire Day"** — runs all windows in sequence, auto-advancing between them
- **Canvas overlay** — top-right HUD shows current window, pax progress, desk count, speed, day index
- **6-stat bar**: In System, In Queue, Processed, Turned Away, Open Desks, Avg Wait
- **Progress bar** — shows X/N pax spawned for current window

**Desk count logic**: replays all alerts up to the selected window to compute running desk state.  
**Spawn compression**: `spawnRate = FPS × 90 / predicted_load / simSpeed`

---

## Key Technical Details

### Bell Curve (features.py)
- `CHECKIN_LEAD_HOURS = 2.0` — pax arrive 2h before departure on average
- `CHECKIN_SIGMA_MIN = 30.0` — std dev 30 min
- `CHECKIN_TAIL_SIGMA = 2.5` — spread ±2.5σ
- Arrival flights (_ARR suffix) are excluded — arrivals don't use check-in
- Each departure splits into ~5 window rows weighted by normal PDF

### Alert Engine (alerts/engine.py)
- Desk state starts from `get_desks_open()` (SQLite `desk_state` table)
- Evolves window-by-window: `checkin_open` (delta > 0) and `checkin_close` (delta < 0)
- Acknowledging an alert syncs `desk_state.desks_open` to `alert.desks_to_open`

### Thresholds (config/thresholds.yaml)
```yaml
checkin:
  baseline_desks: 1
  level_1: { threshold: 75,  desks_to_open: 2 }
  level_2: { threshold: 125, desks_to_open: 3 }
  level_3: { threshold: 200, desks_to_open: 4 }
```

### Upload & Deduplication
- Training: multi-file, appends to store, manifest at `data/training_manifest.json`
- Schedule: single file, overwrites previous
- Dedup key: `["flight_id", "scheduled_time"]` (not just flight_id)

---

## CSV Input

Auto-detects delimiter and column names. Supported:

| Data | Accepted names |
|---|---|
| Departure flight | `dep_flight`, `departure_flight`, `flight_id`, `flt dep` |
| Departure time | `dep_time`, `departure_time`, `scheduled_time`, `etd`, `std` |
| Departure pax | `dep_pax`, `departure_pax`, `pax_count`, `pax` |
| Arrival flight | `arr_flight`, `arrival_flight`, `flt arr` |
| Arrival time | `arr_time`, `arrival_time`, `eta`, `sta` |
| Arrival pax | `arr_pax`, `arrival_pax` |
| Romanian format | `numar zbor`, `ora`, `type` / `tip` |

Time formats: `2026-06-06 14:30`, `14:30`, `14:30/06`, `23:50/31`

---

## File Map

```
config/thresholds.yaml          — alert thresholds + baseline_desks
src/data/loader.py              — CSV → DataFrame (auto-detects format)
src/data/cleaner.py             — normalise columns, parse times, Romanian fallback
src/data/features.py            — bell curve spreading + 30-min window aggregation
src/model/train.py              — XGBoost fit + save to models/model.pkl
src/model/predict.py            — load model + infer
src/model/evaluate.py           — MAE / RMSE / MAPE
src/model/threshold_detector.py — auto-detect thresholds from training data
src/alerts/engine.py            — time-evolving desk simulation → alerts
src/alerts/state.py             — SQLite CRUD: alerts + desk_state tables
src/api/app.py                  — FastAPI app
src/api/routes/data.py          — /data/upload/training (multi), /data/upload/schedule
src/api/routes/forecast.py      — /forecast/train, /forecast/run
src/api/routes/alerts.py        — /alerts, /alerts/desks
src/api/routes/thresholds.py    — /thresholds, /thresholds/auto-detect
src/dashboard/app.py            — Streamlit UI (5 tabs + simulation HTML)
```

---

## API Endpoints

```
GET  /health
GET  /forecast                  — latest predictions
POST /forecast/train            — train XGBoost
POST /forecast/run              — run forecast + generate alerts
GET  /data/training/info        — flight count, date range, file list
POST /data/upload/training      — multi-file CSV upload
POST /data/upload/training/clear
GET  /data/schedule/info
POST /data/upload/schedule
GET  /alerts                    — all alerts (status filter via ?status=OPEN)
POST /alerts/{id}/acknowledge
GET  /alerts/desks              — current desk count
POST /alerts/desks              — set desk count
GET  /thresholds
POST /thresholds
POST /thresholds/auto-detect    — analyse training data (?apply=true to save)
```

---

## Environment

- Python 3.14, macOS
- Working directory: `/Users/Admin/SoloNoiAirHack2026`
- **Always use `python3.14`** and `python3.14 -m uvicorn` (not bare `uvicorn`)
- Streamlit: `python3.14 -m streamlit run ...`

---

## Known Issues Fixed (do not re-introduce)

- CSV: `flt dep`, `flt arr`, `pax` columns now recognised
- CSV: Romanian format (`numar zbor`, `ora`, `type`) has fallback branch in cleaner.py
- Dedup: key is `["flight_id", "scheduled_time"]` — changing to just `flight_id` collapses flights
- Forecast button disappearing: session state key prevents re-upload on Streamlit rerun
- Navigation IndexError: use dict mapping, not `.split("  ")[1]`
- Desk count defaulting to 0: `init_db()` seeds from `baseline_desks` in thresholds.yaml
- Old alerts showing "already covered": `desks_to_add = NULL` — fixed, re-run forecast clears them
- Congestion delay too high: capped at 60 min via `.clip(upper=60.0)`
- FutureWarning dtype: `agg["avg_delay"] = agg["avg_delay"].astype(float)` before assignment

---

## Phase 2 (Not Built Yet)

- YOLOv8 live camera feed for real-time passenger counting
- Feed live pax counts back into XGBoost alongside schedule data

---

## Session Instructions

After every bug fix or significant feature, update this file and the memory files at:
`/Users/Admin/.claude/projects/-Users-Admin/memory/`

Memory files to keep current:
- `MEMORY.md` — index
- `project_solonoiairhack.md` — project state
- `feedback_solonoiairhack.md` — user preferences and corrections
