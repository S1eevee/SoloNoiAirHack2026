"""
Departures gate routes (model-trained, independent of check-in chain).

POST /departures/train          — train XGBoost on departures gate training data
POST /departures/run            — predict gate load + generate boarding agent alerts
GET  /departures/forecast       — latest departures gate predictions
GET  /departures/alerts         — departures gate agent alerts
POST /departures/alerts/{id}/acknowledge
GET  /departures/agents         — current open agent count
POST /departures/agents         — set agent count
"""
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.alerts.state import (
    get_departures_gate_agents_open, set_departures_gate_agents_open,
    save_departures_gate_alerts, get_departures_gate_alerts,
    clear_departures_gate_alerts, acknowledge_departures_gate_alert,
)

router = APIRouter(prefix="/departures", tags=["departures"])

DEPARTURES_TRAINING_PATH     = Path("data/processed/training_data_departures.csv")
SCHEDULE_PATH                = Path("data/processed/uploaded_schedule.csv")
DEPARTURES_PREDICTIONS_PATH  = Path("data/processed/departures_gate_predictions.csv")
DEPARTURES_MODEL_PATH        = Path("models/departures_gate_model.pkl")


class AgentStateRequest(BaseModel):
    agents_open: int


class AcknowledgeRequest(BaseModel):
    employee: Optional[str] = "employee"


@router.post("/train")
async def train_departures_gate_model():
    """Train XGBoost on departures gate historical data (STD - 45 min bell curve)."""
    if not DEPARTURES_TRAINING_PATH.exists():
        raise HTTPException(404, "No departures training data found at data/processed/training_data_departures.csv.")

    from src.data.cleaner import clean_flights
    from src.data.features_departures_gate import (
        build_departures_gate_feature_matrix,
        DEPARTURES_GATE_FEATURE_COLS,
        TARGET_COL,
    )
    from src.model.train import train
    from src.model.evaluate import evaluate

    df = pd.read_csv(DEPARTURES_TRAINING_PATH, parse_dates=["scheduled_time"])
    features = build_departures_gate_feature_matrix(clean_flights(df))

    if features.empty:
        raise HTTPException(422, "No departure windows could be built from the training data.")

    model = train(
        features,
        save=True,
        model_path=DEPARTURES_MODEL_PATH,
        feature_cols=DEPARTURES_GATE_FEATURE_COLS,
    )
    metrics = evaluate(model, features, feature_cols=DEPARTURES_GATE_FEATURE_COLS)

    return {
        "status": "trained",
        "training_flights": len(df),
        "windows": len(features),
        "metrics": metrics,
    }


@router.post("/run")
async def run_departures_gate_forecast():
    """Predict departures gate load from uploaded schedule and generate boarding agent alerts."""
    if not SCHEDULE_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")
    if not DEPARTURES_MODEL_PATH.exists():
        raise HTTPException(503, "Departures gate model not trained. POST /departures/train first.")

    from src.data.cleaner import clean_flights
    from src.data.features_departures_gate import (
        build_departures_gate_feature_matrix,
        DEPARTURES_GATE_FEATURE_COLS,
    )
    from src.model.train import load_model
    from src.alerts.departures_gate_engine import generate_departures_gate_alerts

    df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    features = build_departures_gate_feature_matrix(clean_flights(df))

    if features.empty:
        raise HTTPException(422, "No departure flights found in the uploaded schedule.")

    model = load_model(DEPARTURES_MODEL_PATH)
    import numpy as np
    preds = np.clip(model.predict(features[DEPARTURES_GATE_FEATURE_COLS]), 0, None).round().astype(int)
    predictions = features[["window_start"]].copy()
    predictions["predicted_load"] = preds

    DEPARTURES_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(DEPARTURES_PREDICTIONS_PATH, index=False)

    clear_departures_gate_alerts()
    alerts = generate_departures_gate_alerts(predictions, running_agents=get_departures_gate_agents_open())
    save_departures_gate_alerts(alerts)

    return {
        "windows_predicted": len(predictions),
        "alerts_generated": len(alerts),
        "predictions": predictions.to_dict(orient="records"),
    }


@router.get("/forecast")
async def get_departures_gate_forecast():
    """Return latest departures gate predictions."""
    if not DEPARTURES_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No departures gate forecast yet. POST /departures/run first.")
    df = pd.read_csv(DEPARTURES_PREDICTIONS_PATH)
    return df[["window_start", "predicted_load"]].to_dict(orient="records")


@router.get("/alerts")
async def list_departures_gate_alerts(status: Optional[str] = None):
    return get_departures_gate_alerts(status=status)


@router.post("/alerts/{alert_id}/acknowledge")
async def ack_departures_gate_alert(alert_id: int, body: AcknowledgeRequest = AcknowledgeRequest()):
    ok = acknowledge_departures_gate_alert(alert_id, employee=body.employee)
    if not ok:
        raise HTTPException(404, f"Departures gate alert {alert_id} not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/agents")
async def get_departures_gate_agent_state():
    return {"agents_open": get_departures_gate_agents_open()}


@router.post("/agents")
async def update_departures_gate_agent_state(body: AgentStateRequest):
    set_departures_gate_agents_open(body.agents_open)
    return {"agents_open": body.agents_open}
