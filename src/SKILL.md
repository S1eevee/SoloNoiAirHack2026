# src/

All application source code. Each subdirectory is an independent Python package with a single responsibility.

## Package Map

```
src/
├── data/       — CSV ingestion, cleaning, feature engineering
├── model/      — XGBoost training, inference, evaluation
├── alerts/     — threshold logic, SQLite alert persistence
├── llm/        — Claude API integration for natural language insights
├── api/        — FastAPI REST backend
└── dashboard/  — Streamlit employee-facing UI
```

## Data Flow

```
CSV Upload
    │
    ▼
src/data/loader.py        — read raw bytes → DataFrame
    │
    ▼
src/data/cleaner.py       — normalise columns, parse times, fill nulls
    │
    ▼
src/data/features.py      — aggregate into 30-min windows → feature matrix
    │
    ▼
src/model/train.py        — fit XGBoost on feature matrix → model.pkl
    │
    ▼
src/model/predict.py      — load model, predict total_pax per window
    │
    ▼
src/alerts/engine.py      — compare predictions to thresholds → alert list
    │
    ▼
src/alerts/state.py       — persist alerts to SQLite (OPEN/ACK/RESOLVED)
    │
    ▼
src/api/app.py            — expose everything via REST endpoints
    │
    ▼
src/dashboard/app.py      — render for employees in browser
    │
    ▼
src/llm/insights.py       — Claude generates natural language summary
```

## Entry Points
- **API:** `uvicorn src.api.app:app`
- **Dashboard:** `streamlit run src/dashboard/app.py`
- **CLI:** `python3 pipeline.py [train|predict|run|insights]`
