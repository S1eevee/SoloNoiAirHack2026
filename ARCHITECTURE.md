# Architecture — SoloNoiAirHack2026

A concise component diagram and data flow for the application.

```mermaid
flowchart TD
  subgraph Ingest["Ingestion"]
    CSV[CSV Upload]
    CSV --> Loader[src.data.loader]
  end

  subgraph Preproc["Preprocessing / Features"]
    Loader --> Cleaner[src.data.cleaner]
    Cleaner --> Features[src.data.features]
  end

  subgraph Modeling["Model"]
    Features --> Train[src.model.train]
    Train --> ModelFile["model.pkl"]
    ModelFile --> Predict[src.model.predict]
  end

  subgraph Alerts["Alerts"]
    Predict --> AlertsEngine[src.alerts.engine]
    AlertsEngine --> AlertsState[src.alerts.state{SQLite}]
  end

  subgraph Services["Services"]
    Predict --> API[src.api.app (FastAPI)]
    AlertsState --> API
    API --> Dashboard[src.dashboard.app (Streamlit)]
    API --> Clients[External Clients / UI]
  end

  subgraph LLM["LLM Insights"]
    Predict --> LLM[src.llm.insights (Claude)]
    AlertsEngine --> LLM
    LLM --> API
  end

  subgraph Orchestration["CLI / Pipeline"]
    CLI[pipeline.py (train|predict|run|insights)] --> Train
    CLI --> Predict
    CLI --> LLM
  end

  %% Notes
  note["Tech highlights:\n- Model: XGBoost\n- DB: SQLite for alerts\n- API: FastAPI\n- UI: Streamlit\n- LLM: Claude (external API)\n- Entry points: uvicorn, streamlit, pipeline.py"]:::noteStyle

  classDef noteStyle fill:#f9f,stroke:#333,stroke-width:0.5
```

Key interactions:
- CSV upload -> loader -> cleaner -> features → training or prediction.
- Training produces model.pkl consumed by prediction and LLM insights.
- Alerts are produced by comparing predictions to thresholds and persisted in SQLite.
- FastAPI exposes upload, predict, and alert endpoints; Streamlit consumes the API for employee-facing UI.
- pipeline.py coordinates common workflows (train/predict/run/insights).

Operational notes:
- Keep model artifacts and sqlite file in a consistent config path (e.g., ./models/, ./data/, ./state/).
- Secrets: Claude API key must be stored as an environment variable (do not check into Git).
