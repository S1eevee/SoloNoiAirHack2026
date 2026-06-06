"""
Gate (ticket scan / boarding control) checkpoint routes.

POST /gate/run                  — derive gate predictions + generate alerts
GET  /gate/forecast             — latest gate load predictions
GET  /gate/alerts               — gate agent alerts
POST /gate/alerts/{id}/acknowledge
GET  /gate/agents               — current open agent count
POST /gate/agents               — set agent count
GET  /gate/sensor/counts        — real sensor counts from gate zone
POST /gate/sensor/reconcile     — compare sensor actuals vs predictions
POST /gate/sensor/calibrate     — auto-calibrate flow_factor from sensor data
POST /gate/sensor/simulate      — inject a full day of simulated gate readings
POST /gate/sensor/simulate/window — inject one reading for current window
"""
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.alerts.state import (
    get_agents_open, set_agents_open,
    save_gate_alerts, get_gate_alerts,
    clear_gate_alerts, acknowledge_gate_alert,
)

router = APIRouter(prefix="/gate", tags=["gate"])

SECURITY_PREDICTIONS_PATH = Path("data/processed/security_predictions.csv")
GATE_PREDICTIONS_PATH = Path("data/processed/gate_predictions.csv")


class AgentStateRequest(BaseModel):
    agents_open: int


class AcknowledgeRequest(BaseModel):
    employee: Optional[str] = "employee"


@router.post("/run")
async def run_gate_forecast():
    """
    Derive gate load from the latest security predictions and generate
    gate agent alerts. Requires security/run to have been called first.
    """
    if not SECURITY_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No security forecast yet. POST /security/run first.")

    from src.alerts.gate_engine import derive_gate_predictions, generate_gate_alerts

    sec_df = pd.read_csv(SECURITY_PREDICTIONS_PATH)
    gate_predictions = derive_gate_predictions(sec_df)

    GATE_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    gate_predictions.to_csv(GATE_PREDICTIONS_PATH, index=False)

    clear_gate_alerts()
    alerts = generate_gate_alerts(gate_predictions, running_agents=get_agents_open())
    save_gate_alerts(alerts)

    return {
        "windows_predicted": len(gate_predictions),
        "alerts_generated": len(alerts),
        "predictions": gate_predictions[["window_start", "security_load", "predicted_load"]].to_dict(orient="records"),
    }


@router.get("/forecast")
async def get_gate_forecast():
    """Return latest gate load predictions."""
    if not GATE_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No gate forecast yet. POST /gate/run first.")
    df = pd.read_csv(GATE_PREDICTIONS_PATH)
    return df[["window_start", "security_load", "predicted_load"]].to_dict(orient="records")


@router.get("/alerts")
async def list_gate_alerts(status: Optional[str] = None):
    """List gate agent alerts, optionally filtered by status."""
    return get_gate_alerts(status=status)


@router.post("/alerts/{alert_id}/acknowledge")
async def ack_gate_alert(alert_id: int, body: AcknowledgeRequest = AcknowledgeRequest()):
    ok = acknowledge_gate_alert(alert_id, employee=body.employee)
    if not ok:
        raise HTTPException(404, f"Gate alert {alert_id} not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/agents")
async def get_agent_state():
    return {"agents_open": get_agents_open()}


@router.post("/agents")
async def update_agent_state(body: AgentStateRequest):
    set_agents_open(body.agents_open)
    return {"agents_open": body.agents_open}


# ---------------------------------------------------------------------------
# Gate sensor data
# ---------------------------------------------------------------------------

@router.get("/sensor/counts")
async def gate_sensor_counts(hours: int = 24):
    """Real VS133-P counts from the gate zone."""
    from src.sensor.store import get_recent_counts
    df = get_recent_counts(hours=hours, zone="gate")
    return [] if df.empty else df.to_dict(orient="records")


@router.post("/sensor/reconcile")
async def gate_sensor_reconcile():
    """Compare actual gate sensor counts vs derived predictions."""
    if not GATE_PREDICTIONS_PATH.exists():
        raise HTTPException(404, "No gate forecast yet. POST /gate/run first.")
    from src.alerts.gate_engine import reconcile_gate
    df = pd.read_csv(GATE_PREDICTIONS_PATH)
    return reconcile_gate(df)


@router.post("/sensor/calibrate")
async def gate_sensor_calibrate():
    """
    Derive an empirical flow_factor from matched security vs gate sensor counts
    and persist it to thresholds.yaml.
    """
    from src.alerts.gate_engine import calibrate_gate_flow_factor
    result = calibrate_gate_flow_factor()
    return result


@router.post("/sensor/simulate")
async def gate_sensor_simulate(date: Optional[str] = None):
    """Inject simulated gate sensor readings for a full day (demo without hardware)."""
    import requests as _req
    url = "http://localhost:8000/sensor/simulate/gate"
    params = {"date": date} if date else {}
    r = _req.post(url, params=params, timeout=30)
    return r.json() if r.ok else {"error": r.text}


@router.post("/sensor/simulate/window")
async def gate_sensor_simulate_window():
    """Inject one simulated gate reading for the current window."""
    import requests as _req
    r = _req.post("http://localhost:8000/sensor/simulate/gate/window", timeout=10)
    return r.json() if r.ok else {"error": r.text}
