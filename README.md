# SoloNoiAirHack2026 — Passenger Flow Predictor

AirHack 2026 MVP: XGBoost-powered passenger load forecasting with check-in desk alerts, a FastAPI backend, and a Streamlit employee dashboard.

## Architecture

```
Flight CSV → Cleaner → Feature Builder → XGBoost → Predictions
                                                         ↓
                                                  Alert Engine → SQLite
                                                         ↓
                                               FastAPI (REST API)
                                                    ↙       ↘
                                          Streamlit        Claude LLM
                                          Dashboard        Insights
```

## Stack

| Layer | Technology |
|---|---|
| Prediction | XGBoost (regression) |
| Backend | FastAPI + uvicorn |
| Frontend | Streamlit |
| LLM | Claude claude-opus-4-8 (Anthropic SDK) |
| Persistence | SQLite |
| Config | thresholds.yaml |

## Input Schema

`flight_schedule.csv`:
```
flight_id | scheduled_time       | pax_count | delay_min | checkin_desks
AA101     | 2026-06-06 06:00:00  | 210       | 10        | 4
```

## Predicted Output

```
window_start  | predicted_load
07:00         | 340
07:30         | 210
08:00         | 480
```

## Alert Output

```
id | type    | message                                    | status
1  | checkin | Open 2 extra check-in desks at 07:00 ...  | OPEN
2  | checkin | Open 4 extra check-in desks at 08:00 ...  | OPEN
```

## Quick Start

### 1. Install dependencies

```bash
cd SoloNoiAirHack2026
pip install -r requirements.txt
```

### 2. Set Anthropic API key (for LLM insights)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Train + predict + generate alerts (CLI)

```bash
python pipeline.py run --schedule data/sample/sample_flights.csv
```

### 4. Start the API server

```bash
uvicorn src.api.app:app --reload --port 8000
```

### 5. Start the employee dashboard

```bash
streamlit run src/dashboard/app.py
```

Open http://localhost:8501 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/data/upload` | Upload flight schedule CSV |
| GET | `/forecast` | Get predictions for uploaded schedule |
| POST | `/forecast/run` | Train + predict + generate alerts |
| GET | `/alerts` | List alerts (filter by `?status=OPEN`) |
| POST | `/alerts/{id}/acknowledge` | Employee acknowledges an alert |
| POST | `/alerts/{id}/resolve` | Mark alert resolved |
| GET | `/thresholds` | Get current alert thresholds |
| POST | `/thresholds` | Update thresholds (manager) |
| POST | `/insights` | Get Claude LLM operational insights |
| GET | `/health` | Health check |

## CLI Commands

```bash
# Train model only
python pipeline.py train --schedule data/sample/sample_flights.csv

# Predict (model must exist)
python pipeline.py predict --schedule data/sample/sample_flights.csv

# Full pipeline: train + predict + alerts
python pipeline.py run --schedule data/sample/sample_flights.csv

# Get AI insights
python pipeline.py insights --schedule data/sample/sample_flights.csv --question "Which hour needs most desks?"
```

## Project Structure

```
SoloNoiAirHack2026/
├── data/
│   ├── processed/          # uploaded schedules land here
│   └── sample/
│       └── sample_flights.csv
├── src/
│   ├── data/
│   │   ├── loader.py       # read CSV
│   │   ├── cleaner.py      # validate + normalize
│   │   └── features.py     # 30-min window aggregation
│   ├── model/
│   │   ├── train.py        # XGBoost training
│   │   ├── predict.py      # inference
│   │   └── evaluate.py     # MAE / RMSE / MAPE
│   ├── alerts/
│   │   ├── engine.py       # threshold logic → alerts
│   │   └── state.py        # SQLite persistence
│   ├── llm/
│   │   └── insights.py     # Claude API integration
│   ├── api/
│   │   ├── app.py          # FastAPI app
│   │   └── routes/         # data, forecast, alerts, thresholds, insights
│   └── dashboard/
│       └── app.py          # Streamlit employee dashboard
├── models/
│   └── model.pkl           # trained XGBoost (generated)
├── config/
│   └── thresholds.yaml     # alert thresholds config
├── pipeline.py             # CLI entry point
└── requirements.txt
```

## Alert Thresholds (configurable via UI or API)

| Level | Passenger Load | Action |
|---|---|---|
| 1 | ≥ 150 pax | Open 1 extra check-in desk |
| 2 | ≥ 300 pax | Open 2 extra check-in desks |
| 3 | ≥ 500 pax | Open 4 extra check-in desks (HIGH LOAD) |

## YOLOv8 Live Feed (Phase 2)

Real-time camera feed integration is planned for Phase 2. The XGBoost prediction and Claude LLM layers are already designed to receive live pax counts as additional input alongside the schedule-based predictions.
