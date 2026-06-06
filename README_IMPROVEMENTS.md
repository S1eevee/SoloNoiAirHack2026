# README improvements (proposed edits and additions)

Below are concrete sections and text you can add/merge into README.md to improve onboarding and clarity.

## 1) Quick Start (Add near top)
### Requirements
- Python 3.10+ (or whichever version repo targets)
- pip, virtualenv
- Install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

### Run locally
- Start API: `uvicorn src.api.app:app --reload`
- Start Dashboard: `streamlit run src/dashboard/app.py`
- CLI examples:
  - Train: `python3 pipeline.py train --data path/to/data.csv --out models/model.pkl`
  - Predict: `python3 pipeline.py predict --input path/to/data.csv --model models/model.pkl`
  - Run (end-to-end server + worker): `python3 pipeline.py run`
  - Insights (LLM): `python3 pipeline.py insights --model models/model.pkl`

## 2) Environment variables (new section)
- `CLAUDE_API_KEY` — required for src/llm/insights.py (LLM summaries).
- `FASTAPI_HOST` / `FASTAPI_PORT` — optional overrides for uvicorn.
- `ALERT_DB_PATH` — path to SQLite alerts DB (default: `./state/alerts.db`).
- `MODEL_PATH` — path to model artifact (default: `./models/model.pkl`).

Add example `.env` (do not commit):
```
CLAUDE_API_KEY=sk-...
ALERT_DB_PATH=./state/alerts.db
MODEL_PATH=./models/model.pkl
```

## 3) Architecture (link to ARCHITECTURE.md)
- Add a short "Architecture" section referencing ARCHITECTURE.md and the high-level diagram.

## 4) API Endpoints (concise)
Add a short enumerated list of key endpoints (update when routes change):
- `POST /upload` — upload CSV (incoming bytes → loader)
- `POST /predict` — return predictions for uploaded data
- `GET /alerts` — list persisted alerts
- `POST /alerts/{id}/ack` — acknowledge alert

(Replace with actual routes if different — confirm by scanning src/api/app.py.)

## 5) Data & Artifacts layout (explicit)
Recommend a small directory layout and where files are stored by default:
- `data/` — raw CSV examples, processed artifacts
- `models/` — model artifacts like model.pkl
- `state/` — sqlite DB and runtime state
- `logs/` — runtime logs

## 6) Development notes / testing
- Where to find main modules: `src/data/`, `src/model/`, `src/alerts/`, `src/api/`, `src/dashboard/`, `src/llm/`.
- Suggest adding unit tests for:
  - data loader/cleaner (edge cases, missing timestamps)
  - features (windowing correctness)
  - model.train (training run smoke test on small dataset)
  - alerts.engine (threshold logic)
- Add `pytest` to dev dependencies and a short CI job.

## 7) Security & credentials
- Call out that API keys (Claude) must never be committed.
- Recommend using environment variables or a secrets manager for CI.
- If the project will be deployed, document the minimal permissions needed.

## 8) Troubleshooting (short)
- If uvicorn fails: confirm `MODEL_PATH` and `ALERT_DB_PATH` are writable and exist.
- If LLM calls fail: verify `CLAUDE_API_KEY` and network access.

## 9) Contribution & Contact
- Add a short "How to contribute" linking to a CONTRIBUTING.md if the project grows. For now: fork → branch → PR → review.

---

Suggested small README patch you can paste into README.md (insert under current intro):

```md
## Quick Start

1. Create and activate a venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment variables (example `.env`):
   ```bash
   export CLAUDE_API_KEY="sk-..."
   export ALERT_DB_PATH="./state/alerts.db"
   export MODEL_PATH="./models/model.pkl"
   ```

3. Start the API:
   ```bash
   uvicorn src.api.app:app --reload
   ```

4. Start the dashboard in a separate terminal:
   ```bash
   streamlit run src/dashboard/app.py
   ```

See ARCHITECTURE.md for a high-level diagram and component interactions.
```
