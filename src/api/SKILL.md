# src/api/

FastAPI REST backend. The single source of truth between the data pipeline and the dashboard.

## Entry Point
```bash
python3 -m uvicorn src.api.app:app --reload --port 8000
```
Docs available at: http://localhost:8000/docs

## Files

### `app.py`
Creates the FastAPI app, registers CORS middleware, and mounts all routers.

### `routes/`

| File | Prefix | Purpose |
|---|---|---|
| `data.py` | `/data` | Upload historical training data and upcoming schedules |
| `forecast.py` | `/forecast` | Train model and run predictions |
| `alerts.py` | `/alerts` | List, acknowledge, and resolve check-in alerts |
| `thresholds.py` | `/thresholds` | Get and update alert threshold config |
| `insights.py` | `/insights` | Claude LLM natural language insights |

## Full Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/data/upload/training` | Upload historical flights (appends, deduplicates) |
| POST | `/data/upload/training/clear` | Wipe all training data |
| POST | `/data/upload/schedule` | Upload upcoming schedule for prediction |
| GET | `/data/training/info` | Training dataset stats |
| GET | `/data/schedule/info` | Schedule dataset stats |
| POST | `/forecast/train` | Train XGBoost on uploaded historical data |
| POST | `/forecast/run` | Predict on schedule + generate alerts |
| GET | `/forecast` | Return latest predictions |
| GET | `/alerts` | List alerts (filter: `?status=OPEN\|ACKNOWLEDGED\|RESOLVED`) |
| POST | `/alerts/{id}/acknowledge` | Employee acknowledges an alert |
| POST | `/alerts/{id}/resolve` | Mark alert resolved |
| GET | `/thresholds` | Get current thresholds from YAML |
| POST | `/thresholds` | Update thresholds (persisted to YAML) |
| POST | `/insights` | Get Claude LLM operational insights |

## Notes
- The dashboard (`src/dashboard/app.py`) communicates exclusively through these endpoints
- CORS is open (`allow_origins=["*"]`) — restrict in production
- All file paths are relative to the repo root (run uvicorn from there)
