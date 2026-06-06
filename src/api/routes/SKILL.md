# src/api/routes/

One file per domain area. Each file defines a FastAPI `APIRouter` mounted in `src/api/app.py`.

## Files

### `data.py` — `/data`
Handles CSV uploads. Validates, cleans, and saves to `data/processed/`.
- Training uploads **append** to existing data (multiple files stack)
- Schedule uploads **overwrite** (always the latest upcoming schedule)

### `forecast.py` — `/forecast`
- `POST /forecast/train` — trains XGBoost on `training_data.csv`, returns metrics
- `POST /forecast/run` — predicts on `uploaded_schedule.csv`, saves alerts to SQLite
- `GET /forecast` — returns latest predictions without re-running

### `alerts.py` — `/alerts`
CRUD for alert lifecycle. Initialises the SQLite DB on import.
- Supports status filter: `?status=OPEN|ACKNOWLEDGED|RESOLVED`
- Acknowledge endpoint accepts `employee` name for audit trail

### `thresholds.py` — `/thresholds`
Read/write `config/thresholds.yaml`. Changes take effect on the next forecast run.

### `insights.py` — `/insights`
Accepts optional `question` and `api_key` in request body. Delegates to `src/llm/insights.py`.
