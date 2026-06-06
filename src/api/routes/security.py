"""
Security checkpoint routes.

POST /security/run                  — derive security predictions + generate alerts
GET  /security/forecast             — latest security load predictions
GET  /security/alerts               — security lane alerts
POST /security/alerts/{id}/acknowledge
GET  /security/lanes                — current open lane count
POST /security/lanes                — set lane count
GET  /security/sensor/counts        — real sensor counts from security checkpoint
POST /security/sensor/reconcile     — compare sensor actuals vs predictions
POST /security/sensor/calibrate     — auto-calibrate flow_factor from sensor data
POST /security/sensor/simulate      — inject a full day of simulated security readings
POST /security/sensor/simulate/window — inject one reading for current window
"""
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.alerts.state import (
    get_lanes_open, set_lanes_open,
    save_security_alerts, get_security_alerts,
    clear_security_alerts, acknowledge_security_alert,
)

router = APIRouter(prefix="/security", tags=["security"])

SCHEDULE_PATH = Path("data/processed/uploaded_schedule.csv")
SECURITY_PREDICTIONS_PATH = Path("data/processed/security_predictions.csv")


class LaneStateRequest(BaseModel):
    lanes_open: int


class AcknowledgeRequest(BaseModel):
    employee: Optional[str] = "employee"


@router.post("/run")
async def run_security_forecast():
    """
    Derive security load from the latest check-in predictions and generate
    security lane alerts. Requires a trained model and uploaded schedule.
    """
    if not SCHEDULE_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")

    from src.model.train import load_model
    from src.model.predict import predict
    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.alerts.security_engine import derive_security_predictions, generate_security_alerts

    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    features = build_feature_matrix(clean_flights(df))
    checkin_predictions = predict(model, features)

    security_predictions = derive_security_predictions(checkin_predictions)

    SECURITY_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    security_predictions.to_csv(SECURITY_PREDICTIONS_PATH, index=False)

    clear_security_alerts()
    alerts = generate_security_alerts(security_predictions, running_lanes=get_lanes_open())
    save_security_alerts(alerts)

    return {
        "windows_predicted": len(security_predictions),
        "alerts_generated": len(alerts),
        "predictions": security_predictions[["window_start", "checkin_load", "predicted_load"]].to_dict(orient="records"),
    }


@router.get("/forecast")
async def get_security_forecast():
    """Return latest security load predictions."""
    if not SECURITY_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No security forecast yet. POST /security/run first.")
    df = pd.read_csv(SECURITY_PREDICTIONS_PATH)
    return df[["window_start", "checkin_load", "predicted_load"]].to_dict(orient="records")


@router.get("/alerts")
async def list_security_alerts(status: Optional[str] = None):
    """List security lane alerts, optionally filtered by status."""
    return get_security_alerts(status=status)


@router.post("/alerts/{alert_id}/acknowledge")
async def ack_security_alert(alert_id: int, body: AcknowledgeRequest = AcknowledgeRequest()):
    ok = acknowledge_security_alert(alert_id, employee=body.employee)
    if not ok:
        raise HTTPException(404, f"Security alert {alert_id} not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/lanes")
async def get_lane_state():
    return {"lanes_open": get_lanes_open()}


@router.post("/lanes")
async def update_lane_state(body: LaneStateRequest):
    set_lanes_open(body.lanes_open)
    return {"lanes_open": body.lanes_open}


# ---------------------------------------------------------------------------
# Security sensor data
# ---------------------------------------------------------------------------

@router.get("/sensor/counts")
async def security_sensor_counts(hours: int = 24):
    """Real VS133-P counts from the security checkpoint."""
    from src.sensor.store import get_recent_counts
    df = get_recent_counts(hours=hours, zone="security")
    return [] if df.empty else df.to_dict(orient="records")


@router.post("/sensor/reconcile")
async def security_sensor_reconcile():
    """Compare actual security sensor counts vs derived predictions."""
    if not SECURITY_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No security forecast yet. POST /security/run first.")
    from src.alerts.security_engine import reconcile_security
    df = pd.read_csv(SECURITY_PREDICTIONS_PATH)
    return reconcile_security(df)


@router.post("/sensor/calibrate")
async def security_sensor_calibrate():
    """
    Derive an empirical flow_factor from matched check-in vs security sensor
    counts and persist it to thresholds.yaml.
    """
    from src.alerts.security_engine import calibrate_flow_factor
    if not SECURITY_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No security forecast yet. POST /security/run first.")
    df = pd.read_csv(SECURITY_PREDICTIONS_PATH)
    result = calibrate_flow_factor(df)
    return result


@router.post("/sensor/simulate")
async def security_sensor_simulate(date: Optional[str] = None):
    """Inject simulated security sensor readings for a full day (demo without hardware)."""
    import requests as _req
    url = f"http://localhost:8000/sensor/simulate/security"
    params = {"date": date} if date else {}
    r = _req.post(url, params=params, timeout=30)
    return r.json() if r.ok else {"error": r.text}


@router.post("/sensor/simulate/window")
async def security_sensor_simulate_window():
    """Inject one simulated security reading for the current window."""
    import requests as _req
    r = _req.post("http://localhost:8000/sensor/simulate/security/window", timeout=10)
    return r.json() if r.ok else {"error": r.text}
