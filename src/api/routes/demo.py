import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import timedelta

router = APIRouter(prefix="/demo", tags=["demo"])

SAMPLE_PATH   = Path("data/sample/sample_flights.csv")
TRAINING_PATH = Path("data/processed/training_data.csv")
SCHEDULE_PATH = Path("data/processed/uploaded_schedule.csv")
MANIFEST_PATH = Path("data/processed/training_manifest.json")


@router.post("/load")
async def load_demo():
    """
    Pre-populate training data (14 synthetic days) + today's schedule from
    the bundled sample, train the model, and run the forecast — one click.
    """
    if not SAMPLE_PATH.exists():
        raise HTTPException(404, "Sample file not found at data/sample/sample_flights.csv")

    base = pd.read_csv(SAMPLE_PATH, parse_dates=["scheduled_time"])
    base_date = base["scheduled_time"].dt.normalize().iloc[0]

    rng = np.random.default_rng(42)
    days = []
    for offset in range(1, 15):  # 14 historical days
        day = base.copy()
        day["scheduled_time"] = day["scheduled_time"] + timedelta(days=-offset)
        noise = rng.uniform(0.82, 1.18, size=len(day))
        day["pax_count"] = (day["pax_count"] * noise).round().astype(int).clip(lower=10)
        delay_noise = rng.integers(0, 15, size=len(day))
        day["delay_min"] = (day["delay_min"] + delay_noise).clip(0, 90)
        # suffix flight ids so they don't collide across days
        day["flight_id"] = day["flight_id"] + f"_d{offset}"
        days.append(day)

    training = pd.concat(days, ignore_index=True).sort_values("scheduled_time").reset_index(drop=True)

    TRAINING_PATH.parent.mkdir(parents=True, exist_ok=True)
    training.to_csv(TRAINING_PATH, index=False)

    # today's schedule = original sample file (no changes)
    base.to_csv(SCHEDULE_PATH, index=False)

    # train
    from src.data.features import build_feature_matrix
    from src.model.train import train
    from src.model.evaluate import evaluate

    features = build_feature_matrix(training)
    model = train(features, save=True)
    metrics = evaluate(model, features)

    # run forecast + generate alerts
    from src.data.features import build_feature_matrix as bfm
    from src.model.predict import predict
    from src.alerts.engine import generate_alerts
    from src.alerts.state import save_alerts, clear_alerts

    schedule_df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    sched_features = bfm(schedule_df)
    predictions = predict(model, sched_features)
    clear_alerts()
    alerts = generate_alerts(predictions)
    save_alerts(alerts)

    MANIFEST_PATH.write_text('[{"filename":"demo_data","flights":' + str(len(training)) +
                             ',"date_from":"' + str(training["scheduled_time"].min())[:10] +
                             '","date_to":"' + str(training["scheduled_time"].max())[:10] + '"}]')

    return {
        "status": "demo_loaded",
        "training_days": 14,
        "training_flights": len(training),
        "schedule_flights": len(base),
        "windows_predicted": len(predictions),
        "alerts_generated": len(alerts),
        "metrics": metrics,
    }


@router.post("/unload")
async def unload_demo():
    """Clear all demo data, model, and alerts to return to a clean state."""
    from src.alerts.state import clear_alerts

    for p in [TRAINING_PATH, SCHEDULE_PATH, MANIFEST_PATH]:
        p.unlink(missing_ok=True)

    model_path = Path("models/model.pkl")
    model_path.unlink(missing_ok=True)

    clear_alerts()

    return {"status": "demo_unloaded"}


@router.get("/status")
async def demo_status():
    """Returns whether demo data is currently loaded."""
    is_demo = False
    if MANIFEST_PATH.exists():
        import json
        manifest = json.loads(MANIFEST_PATH.read_text())
        is_demo = any(e.get("filename") == "demo_data" for e in manifest)
    return {"demo_active": is_demo}
