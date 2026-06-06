"""
VS133-P sensor integration routes.

POST /sensor/ingest           — VS133-P pushes a reading here (HTTP mode)
GET  /sensor/counts           — recent 30-min window totals from sensor
POST /sensor/reconcile        — compare latest forecast vs actual sensor counts
POST /sensor/simulate         — inject fake readings for a full day (demo mode)
POST /sensor/simulate/window  — inject one fake reading for the current window
POST /sensor/mqtt/start       — start background MQTT subscriber
POST /sensor/mqtt/stop        — stop MQTT subscriber
"""
import json
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.sensor.vs133 import VS133Payload
from src.sensor.store import save_reading, get_recent_counts

router = APIRouter(prefix="/sensor", tags=["sensor"])

_mqtt_client = None  # module-level singleton


class MQTTConfig(BaseModel):
    broker: str
    port: int = 1883
    topic: str
    username: Optional[str] = None
    password: Optional[str] = None


# ---------------------------------------------------------------------------
# HTTP ingest
# ---------------------------------------------------------------------------

@router.post("/ingest")
async def ingest(payload: VS133Payload):
    """
    Configure the VS133-P in HTTP push mode and point it at:
        POST http://<your-server>:8000/sensor/ingest
    """
    data = payload.normalize()
    save_reading(
        device_eui=data["device_eui"],
        timestamp=data["timestamp"],
        count_in=data["count_in"],
        count_out=data["count_out"],
    )
    return {
        "status": "ok",
        "device": data["device_eui"],
        "window": data["timestamp"].strftime("%H:%M"),
        "count_in": data["count_in"],
        "count_out": data["count_out"],
    }


# ---------------------------------------------------------------------------
# Query stored counts
# ---------------------------------------------------------------------------

@router.get("/counts")
async def counts(hours: int = 24):
    """Return sensor totals per 30-min window for the last N hours."""
    df = get_recent_counts(hours=hours)
    if df.empty:
        return []
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Reconcile forecast vs sensor
# ---------------------------------------------------------------------------

@router.post("/reconcile")
async def reconcile():
    """
    For each predicted window, compare XGBoost forecast against real sensor
    counts and return corrected_load + status (confirmed / escalated / etc.).
    """
    from pathlib import Path
    import pandas as pd
    from src.model.train import load_model
    from src.model.predict import predict
    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.sensor.reconciler import reconcile_all

    schedule_path = Path("data/processed/uploaded_schedule.csv")
    if not schedule_path.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")

    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    df = pd.read_csv(schedule_path, parse_dates=["scheduled_time"])
    features = build_feature_matrix(clean_flights(df))
    predictions = predict(model, features)

    return reconcile_all(predictions)


# ---------------------------------------------------------------------------
# Simulation (demo without hardware)
# ---------------------------------------------------------------------------

SIM_DEVICE_EUI = "SIMULATOR-VS133P"

# Base check-in arrival rate by hour (fraction of daily total)
_HOUR_WEIGHTS = {
    0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.01, 5: 0.03,
    6: 0.08, 7: 0.10, 8: 0.09, 9: 0.06, 10: 0.04, 11: 0.04,
    12: 0.04, 13: 0.04, 14: 0.05, 15: 0.05, 16: 0.06, 17: 0.08,
    18: 0.09, 19: 0.07, 20: 0.04, 21: 0.02, 22: 0.01, 23: 0.00,
}


def _pax_for_window(window_start: datetime, schedule_pax: int = 0) -> tuple[int, int]:
    """
    Return (count_in, count_out) for a 30-min window.
    Uses schedule pax if available, otherwise falls back to time-of-day curve.
    Adds ±15% noise so it looks like a real sensor.
    """
    hour = window_start.hour
    if schedule_pax > 0:
        base = schedule_pax
    else:
        base = int(_HOUR_WEIGHTS.get(hour, 0.02) * 800)

    noise = random.uniform(0.85, 1.15)
    count_in = max(0, round(base * noise))
    count_out = max(0, round(count_in * random.uniform(0.6, 0.9)))
    return count_in, count_out


def _schedule_pax_by_window() -> dict:
    """Load uploaded schedule and return {window_start: total_pax} mapping."""
    from pathlib import Path
    import pandas as pd
    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix

    schedule_path = Path("data/processed/uploaded_schedule.csv")
    if not schedule_path.exists():
        return {}
    try:
        df = pd.read_csv(schedule_path, parse_dates=["scheduled_time"])
        features = build_feature_matrix(clean_flights(df))
        return {
            str(row["window_start"]): int(row["total_pax"])
            for _, row in features.iterrows()
        }
    except Exception:
        return {}


@router.post("/simulate")
async def simulate_day(date: Optional[str] = None):
    """
    Inject simulated VS133-P readings for every 30-min window of a day.
    Uses the uploaded schedule to make counts realistic.
    Pass ?date=2026-06-06 to simulate a specific date, defaults to today.
    """
    if date:
        try:
            base = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(400, "date must be YYYY-MM-DD")
    else:
        base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    schedule = _schedule_pax_by_window()
    injected = []

    for slot in range(48):  # 48 × 30 min = full day
        window = base + timedelta(minutes=30 * slot)
        sched_pax = schedule.get(str(window.replace(tzinfo=None)), 0)
        count_in, count_out = _pax_for_window(window, sched_pax)

        if count_in > 0:
            save_reading(SIM_DEVICE_EUI, window, count_in, count_out)
            injected.append({
                "window": window.strftime("%H:%M"),
                "count_in": count_in,
                "count_out": count_out,
                "based_on_schedule": sched_pax > 0,
            })

    return {
        "status": "ok",
        "device": SIM_DEVICE_EUI,
        "date": base.strftime("%Y-%m-%d"),
        "windows_injected": len(injected),
        "readings": injected,
    }


@router.post("/simulate/window")
async def simulate_window():
    """Inject one simulated reading for the current 30-min window (live demo tick)."""
    now = datetime.now(timezone.utc)
    window = now.replace(minute=0 if now.minute < 30 else 30, second=0, microsecond=0)

    schedule = _schedule_pax_by_window()
    sched_pax = schedule.get(str(window.replace(tzinfo=None)), 0)
    count_in, count_out = _pax_for_window(window, sched_pax)

    save_reading(SIM_DEVICE_EUI, window, count_in, count_out)

    return {
        "status": "ok",
        "device": SIM_DEVICE_EUI,
        "window": window.strftime("%H:%M"),
        "count_in": count_in,
        "count_out": count_out,
        "based_on_schedule": sched_pax > 0,
    }


# ---------------------------------------------------------------------------
# Sensor → training data export
# ---------------------------------------------------------------------------

@router.post("/export-training")
async def export_training(hours: int = 24):
    """
    Convert recent sensor readings into XGBoost training rows and append to
    data/processed/sensor_training.csv.  The next /forecast/train call will
    automatically include these validated windows so the model learns from
    real observed counts.
    """
    from src.sensor.training import export_sensor_training

    rows = export_sensor_training(hours=hours)
    return {
        "status": "ok",
        "rows_exported": rows,
        "note": "Call POST /forecast/train to retrain with these sensor observations.",
    }


# ---------------------------------------------------------------------------
# MQTT subscriber
# ---------------------------------------------------------------------------

def _mqtt_loop(config: MQTTConfig) -> None:
    import paho.mqtt.client as mqtt

    global _mqtt_client

    def on_message(client, userdata, msg):
        try:
            raw = json.loads(msg.payload.decode())
            p = VS133Payload(**raw)
            data = p.normalize()
            save_reading(data["device_eui"], data["timestamp"],
                         data["count_in"], data["count_out"])
        except Exception:
            pass

    client = mqtt.Client()
    if config.username:
        client.username_pw_set(config.username, config.password)
    client.on_message = on_message
    client.connect(config.broker, config.port, keepalive=60)
    client.subscribe(config.topic)
    _mqtt_client = client
    client.loop_forever()


@router.post("/mqtt/start")
async def mqtt_start(config: MQTTConfig, background_tasks: BackgroundTasks):
    """Start a background MQTT subscriber for the VS133-P topic."""
    try:
        import paho.mqtt.client  # noqa: F401
    except ImportError:
        raise HTTPException(503, "paho-mqtt not installed. Run: pip install paho-mqtt")

    global _mqtt_client
    if _mqtt_client is not None:
        return {"status": "already_running"}

    background_tasks.add_task(_mqtt_loop, config)
    return {"status": "started", "broker": config.broker, "topic": config.topic}


@router.post("/mqtt/stop")
async def mqtt_stop():
    """Stop the MQTT subscriber."""
    global _mqtt_client
    if _mqtt_client is not None:
        _mqtt_client.disconnect()
        _mqtt_client = None
    return {"status": "stopped"}
