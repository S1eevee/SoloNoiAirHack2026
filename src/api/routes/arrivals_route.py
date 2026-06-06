"""
Arrivals checkpoint routes.

POST /arrivals/train            — train XGBoost on arrivals training data
POST /arrivals/run              — predict arrivals load + generate staff alerts
GET  /arrivals/forecast         — latest arrivals predictions
GET  /arrivals/alerts           — arrivals staff alerts
POST /arrivals/alerts/{id}/acknowledge
GET  /arrivals/agents           — current open staff count
POST /arrivals/agents           — set staff count
"""
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.alerts.state import (
    get_arrivals_agents_open, set_arrivals_agents_open,
    save_arrivals_alerts, get_arrivals_alerts,
    clear_arrivals_alerts, acknowledge_arrivals_alert,
)

router = APIRouter(prefix="/arrivals", tags=["arrivals"])

ARRIVALS_TRAINING_PATH  = Path("data/processed/training_data_arrivals.csv")
SCHEDULE_PATH           = Path("data/processed/uploaded_schedule.csv")
ARRIVALS_PREDICTIONS_PATH = Path("data/processed/arrivals_predictions.csv")
ARRIVALS_MODEL_PATH     = Path("models/arrivals_model.pkl")


class AgentStateRequest(BaseModel):
    agents_open: int


class AcknowledgeRequest(BaseModel):
    employee: Optional[str] = "employee"


@router.post("/train")
async def train_arrivals_model():
    """Train XGBoost on arrivals historical data."""
    if not ARRIVALS_TRAINING_PATH.exists():
        raise HTTPException(404, "No arrivals training data found at data/processed/training_data_arrivals.csv.")

    from src.data.cleaner import clean_flights
    from src.data.features_arrivals import build_arrivals_feature_matrix, ARRIVALS_FEATURE_COLS, TARGET_COL
    from src.model.train import train
    from src.model.evaluate import evaluate

    df = pd.read_csv(ARRIVALS_TRAINING_PATH, parse_dates=["scheduled_time"])
    features = build_arrivals_feature_matrix(clean_flights(df))

    if features.empty:
        raise HTTPException(422, "No arrival windows could be built from the training data.")

    model = train(features, save=True, model_path=ARRIVALS_MODEL_PATH, feature_cols=ARRIVALS_FEATURE_COLS)
    metrics = evaluate(model, features, feature_cols=ARRIVALS_FEATURE_COLS)

    return {
        "status": "trained",
        "training_flights": len(df),
        "windows": len(features),
        "metrics": metrics,
    }


@router.post("/run")
async def run_arrivals_forecast():
    """Predict arrivals load from the uploaded schedule and generate staff alerts."""
    if not SCHEDULE_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")
    if not ARRIVALS_MODEL_PATH.exists():
        raise HTTPException(503, "Arrivals model not trained. POST /arrivals/train first.")

    from src.data.cleaner import clean_flights
    from src.data.features_arrivals import build_arrivals_feature_matrix, ARRIVALS_FEATURE_COLS
    from src.model.train import load_model
    from src.alerts.arrivals_engine import generate_arrivals_alerts

    df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    features = build_arrivals_feature_matrix(clean_flights(df))

    if features.empty:
        raise HTTPException(422, "No arrival flights found in the uploaded schedule.")

    model = load_model(ARRIVALS_MODEL_PATH)
    import numpy as np
    preds = np.clip(model.predict(features[ARRIVALS_FEATURE_COLS]), 0, None).round().astype(int)
    predictions = features[["window_start"]].copy()
    predictions["predicted_load"] = preds

    ARRIVALS_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(ARRIVALS_PREDICTIONS_PATH, index=False)

    clear_arrivals_alerts()
    alerts = generate_arrivals_alerts(predictions, running_agents=get_arrivals_agents_open())
    save_arrivals_alerts(alerts)

    return {
        "windows_predicted": len(predictions),
        "alerts_generated": len(alerts),
        "predictions": predictions.to_dict(orient="records"),
    }


@router.get("/forecast")
async def get_arrivals_forecast():
    """Return latest arrivals load predictions."""
    if not ARRIVALS_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No arrivals forecast yet. POST /arrivals/run first.")
    df = pd.read_csv(ARRIVALS_PREDICTIONS_PATH)
    return df[["window_start", "predicted_load"]].to_dict(orient="records")


@router.get("/alerts")
async def list_arrivals_alerts(status: Optional[str] = None):
    return get_arrivals_alerts(status=status)


@router.post("/alerts/{alert_id}/acknowledge")
async def ack_arrivals_alert(alert_id: int, body: AcknowledgeRequest = AcknowledgeRequest()):
    ok = acknowledge_arrivals_alert(alert_id, employee=body.employee)
    if not ok:
        raise HTTPException(404, f"Arrivals alert {alert_id} not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/agents")
async def get_arrivals_agent_state():
    return {"agents_open": get_arrivals_agents_open()}


@router.post("/agents")
async def update_arrivals_agent_state(body: AgentStateRequest):
    set_arrivals_agents_open(body.agents_open)
    return {"agents_open": body.agents_open}
