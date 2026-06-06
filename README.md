# SoloNoiAirHack2026 — Passenger Flow Predictor

**AirHack 2026** — An AI-powered passenger load forecasting system for airport check-in operations. Built for Iași Airport (T4). Predicts how many passengers will arrive at check-in per 30-minute window and automatically alerts staff when extra desks need to be opened.

---

## What It Does

1. **Airport admin uploads** a historical flight schedule CSV (past weeks/months)
2. **XGBoost model trains** on that data, learning peak hours, day-of-week patterns, and delay impacts
3. **Admin uploads** tomorrow's scheduled flights
4. **Model predicts** passenger load per 30-minute window for the upcoming day
5. **Alert engine** compares predictions to configurable thresholds → generates check-in desk alerts
6. **Employees see** alerts on the dashboard and acknowledge them (audit trail)
7. **Claude AI** summarises the forecast in natural language and answers manager questions

---

## Architecture

```
Flight CSV (historical)
        │
        ▼
  src/data/loader.py       ← auto-detects CSV format, delimiter, encoding
        │
        ▼
  src/data/cleaner.py      ← normalises any airport column naming to internal schema
        │
        ▼
  src/data/features.py     ← aggregates flights into 30-min window feature matrix
        │
        ▼
  src/model/train.py       ← trains XGBoost regressor → models/model.pkl
        │
Flight CSV (upcoming)
        │
        ▼
  src/model/predict.py     ← predicts passenger load per window
        │
        ▼
  src/alerts/engine.py     ← threshold comparison → alert list
        │
        ▼
  src/alerts/state.py      ← persists alerts to SQLite (OPEN→ACK→RESOLVED)
        │
        ▼
  src/api/app.py           ← FastAPI REST backend (port 8000)
        │
        ├──────────────────────────────┐
        ▼                              ▼
src/dashboard/app.py        src/llm/insights.py
  Streamlit UI (8501)         Claude claude-opus-4-8
  Employee alerts             Natural language summary
  Forecast chart
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Prediction | XGBoost (regression) | Non-linear, handles tabular data, feature importance |
| Backend | FastAPI + uvicorn | Async, fast, auto-generated docs at `/docs` |
| Frontend | Streamlit | Rapid UI, no frontend build step |
| LLM | Claude claude-opus-4-8 (Anthropic SDK) | Adaptive thinking, natural language insights |
| Database | SQLite | Zero-config, embedded, sufficient for airport scale |
| Config | thresholds.yaml | Human-readable, editable via UI or directly |

---

## Quick Start

### 1. Clone and install
```bash
git clone https://github.com/S1eevee/SoloNoiAirHack2026.git
cd SoloNoiAirHack2026
pip3 install -r requirements.txt
```

### 2. Start the API (Terminal 1)
```bash
python3 -m uvicorn src.api.app:app --reload --port 8000
```

### 3. Start the dashboard (Terminal 2)
```bash
python3 -m streamlit run src/dashboard/app.py
```

### 4. Open the dashboard
Go to **http://localhost:8501**

### 5. Load data and run
1. **Train Model tab** → upload historical flight CSV → click **Train Model**
2. **Forecast tab** → upload tomorrow's schedule → click **Run Forecast & Generate Alerts**
3. **Alerts tab** → employees see and acknowledge check-in desk alerts

---

## Terminal Check-In Flow Simulation

A **real-time interactive simulation** showing passenger flow through check-in desks, integrated with ML predictions.

### Run the Simulation

#### Option A: Web-based (no special setup)
```bash
# Start the web server (already running in dev container)
python3 -m http.server 8000
```
Then visit: **http://localhost:8000**

#### Option B: With API predictions (full integration)
```bash
# Terminal 1: Start the API
python3 -m uvicorn src.api.app:app --reload --port 8000

# Terminal 2: Start the web server  
python3 -m http.server 8001
```
Then visit: **http://localhost:8001** (simulation with live predictions)

### What It Shows

- **20 check-in desks** (10 open/green, 10 closed/red)
- **Real-time passenger flow** — blue circles spawn, queue, check in, exit
- **Dynamic desk allocation** — simulation recommends which desks to open based on **ML predictions**
- **Live statistics** — passengers in system, queue length, processed count, FPS
- **Predicted load graph** — next 24 hours of passenger volume (from XGBoost model)

### How It Works

1. Simulation fetches **24-hour predictions** from the FastAPI backend (`/forecast/run`)
2. Shows **predicted peak windows** on the right panel
3. Recommends how many desks should be **open at each time**
4. Spawns passengers at the **predicted flowrate** for the current window
5. Updates in real-time as simulation progresses

### Controls

- **Start** — Begin simulation
- **Pause** — Pause/resume
- **Reset** — Clear all passengers and restart

---

## Mobile Employee App

An **Android native app** (Kotlin) for check-in staff to receive **push notifications** when the predictor recommends opening more desks.

### Features

- **Employee Registration** — Create account with employee ID + email
- **Push Notifications** — Firebase Cloud Messaging alerts
- **Real-time Dashboard** — Live stats + alert list
- **Alert Acknowledgement** — Tap to confirm you've opened desks
- **Offline Support** — Works even if app is in background

### Setup

```bash
cd mobile
# 1. Add Firebase credentials → mobile/app/google-services.json
# 2. Open in Android Studio
# 3. Run on emulator or device
```

See [mobile/README.md](mobile/README.md) for detailed setup.

### Push Notification Flow

```
XGBoost Predicts High Load
       ↓
Alert Generated
       ↓
Backend sends Firebase Message to all registered employee devices
       ↓
Employee receives notification on home screen
       ↓
Notification includes: load, recommended desks, time window
       ↓
Employee taps notification → opens app → Dashboard
```

### API Endpoints (Mobile Auth)

| Method | Endpoint | Usage |
|---|---|---|
| POST | `/auth/register` | Register: `{employee_id, name, email, password}` |
| POST | `/auth/login` | Login: `{email, password}` → returns JWT token |
| POST | `/auth/fcm-token` | Save device token: `{fcm_token}` (on app launch) |
| GET | `/auth/me` | Verify token + get user info |

---

## Dashboard Tabs

| Tab | Who uses it | What it does |
|---|---|---|
| **Train Model** | Airport admin | Upload historical data, train XGBoost, view MAE/RMSE/MAPE |
| **Forecast** | Operations manager | Upload upcoming schedule, run prediction, view load chart |
| **Alerts** | Check-in supervisors | See OPEN alerts, acknowledge with name (audit trail) |
| **AI Insights** | Manager | Ask Claude questions about the forecast in natural language |
| **Settings** | Admin | Configure passenger load thresholds for all 3 alert levels |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Register new employee account |
| POST | `/auth/login` | Login with email/password → JWT token |
| POST | `/auth/fcm-token` | Register device for push notifications |
| GET | `/auth/me` | Get current user info |
| POST | `/data/upload/training` | Upload historical CSV (appends + deduplicates) |
| POST | `/data/upload/schedule` | Upload upcoming schedule |
| GET | `/data/training/info` | Training dataset stats |
| GET | `/data/schedule/info` | Schedule dataset stats |
| POST | `/forecast/train` | Train XGBoost on historical data |
| POST | `/forecast/run` | Predict on schedule + generate alerts |
| GET | `/forecast` | Get latest predictions |
| GET | `/alerts` | List alerts (`?status=OPEN\|ACKNOWLEDGED\|RESOLVED`) |
| POST | `/alerts/{id}/acknowledge` | Acknowledge an alert (pass `employee` name) |
| POST | `/alerts/{id}/resolve` | Resolve an alert |
| GET | `/thresholds` | Get current thresholds |
| POST | `/thresholds` | Update thresholds |
| POST | `/insights` | Get Claude AI operational summary |

Full interactive docs: **http://localhost:8000/docs**

---

## Alert Thresholds

| Level | Trigger | Action |
|---|---|---|
| 1 | ≥ 150 pax in window | Open 1 extra check-in desk |
| 2 | ≥ 300 pax in window | Open 2 extra check-in desks |
| 3 | ≥ 500 pax in window | Open 4 extra check-in desks — HIGH LOAD |

Configurable via **Settings tab** or `config/thresholds.yaml`.

---

## Input CSV Format

The system accepts any airport CSV with flight data. Supported column names:

| Data | Accepted column names |
|---|---|
| Departure flight ID | `dep_flight`, `departure_flight`, `flight_id` |
| Departure time | `dep_time`, `departure_time`, `scheduled_time`, `etd`, `std` |
| Departure pax | `dep_pax`, `departure_pax`, `pax_count` |
| Arrival flight ID | `arr_flight`, `arrival_flight` |
| Arrival time | `arr_time`, `arrival_time`, `eta`, `sta` |
| Arrival pax | `arr_pax`, `arrival_pax` |

Supported time formats: `2026-06-06 14:30:00`, `14:30`, `14:30/06`, `23:50/31`  
Supported delimiters: comma, semicolon, tab, pipe (auto-detected)

---

## CLI Usage

```bash
# Train on historical data
python3 pipeline.py train --schedule data/sample/sample_flights.csv

# Predict (model must exist)
python3 pipeline.py predict --schedule data/sample/sample_flights.csv

# Full pipeline: train + predict + generate alerts
python3 pipeline.py run --schedule data/sample/sample_flights.csv

# Get AI insights (requires ANTHROPIC_API_KEY or uses fallback)
python3 pipeline.py insights --schedule data/sample/sample_flights.csv
python3 pipeline.py insights --schedule data/sample/sample_flights.csv --question "When is the busiest hour?"
```

---

## AI Insights (Claude)

The AI Insights tab works in two modes:

| Mode | Requirement | Output |
|---|---|---|
| **Claude mode** | Anthropic API key | Full natural language analysis with adaptive thinking |
| **Fallback mode** | Nothing | Auto-generated summary: top 3 windows, risk flags, staffing recs |

To use Claude: enter your API key in the sidebar (console.anthropic.com) or set `ANTHROPIC_API_KEY` environment variable. No key = fallback mode, which is fully presentable for demos.

---

## Project Structure

```
SoloNoiAirHack2026/
├── config/
│   ├── thresholds.yaml        # alert thresholds (editable via UI)
│   └── SKILL.md
├── data/
│   ├── processed/             # auto-generated, git-ignored
│   │   ├── training_data.csv  # accumulated historical flights
│   │   ├── uploaded_schedule.csv  # upcoming schedule
│   │   └── alerts.db          # SQLite alert store
│   ├── raw/                   # drop raw files here
│   ├── sample/
│   │   └── sample_flights.csv # 38-flight demo CSV
│   └── SKILL.md
├── models/
│   └── model.pkl              # trained XGBoost (git-ignored, regenerated locally)
├── src/
│   ├── data/
│   │   ├── loader.py          # CSV → DataFrame
│   │   ├── cleaner.py         # normalise columns + parse times
│   │   └── features.py        # 30-min window aggregation
│   ├── model/
│   │   ├── train.py           # XGBoost fit + save
│   │   ├── predict.py         # load model + infer
│   │   └── evaluate.py        # MAE / RMSE / MAPE
│   ├── alerts/
│   │   ├── engine.py          # predictions → alerts
│   │   └── state.py           # SQLite CRUD
│   ├── llm/
│   │   └── insights.py        # Claude API + fallback
│   ├── api/
│   │   ├── app.py             # FastAPI app
│   │   └── routes/
│   │       ├── data.py
│   │       ├── forecast.py
│   │       ├── alerts.py
│   │       ├── thresholds.py
│   │       └── insights.py
│   └── dashboard/
│       └── app.py             # Streamlit UI
├── pipeline.py                # CLI entry point
├── requirements.txt
└── README.md
```

---

## XGBoost Model Details

**Target:** `total_pax` — total passengers across all flights in a 30-min window

**Features:**
| Feature | Description |
|---|---|
| `num_flights` | Number of flights in the window |
| `avg_delay` | Average delay across flights (minutes) |
| `max_delay` | Maximum delay in the window |
| `checkin_desks` | Max desks available across flights |
| `hour` | Hour of day (0–23) |
| `minute` | Minute within the hour (0, 30) |
| `day_of_week` | Day of week (0=Monday, 6=Sunday) |
| `is_peak_hour` | 1 if hour is in peak_hours config, else 0 |
| `time_of_day` | Continuous: hour + minute/60 |

**Training data recommendation:** 2–4 weeks minimum, ideally from the target airport. More data = more variance in predictions = better alerts.

---

## Phase 2 (Planned)

- **YOLOv8 live camera feed** — real-time passenger counting at check-in queues
- Live pax counts fed back into XGBoost as additional features
- Computer vision layer integrated alongside schedule-based predictions

---

## AirHack 2026

Built by **SoloNoi** for AirHack 2026.  
Target airport: **Iași International Airport (IAS)**  
Scope: check-in desk operations (security gates explicitly out of scope for MVP)
