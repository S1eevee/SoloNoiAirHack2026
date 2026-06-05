import pandas as pd
from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.model.train import load_model
from src.model.predict import predict_next_day
from src.data.cleaner import clean_flights

router = APIRouter(prefix="/forecast", tags=["forecast"])

UPLOAD_PATH = Path("data/processed/uploaded_schedule.csv")


def _load_schedule() -> pd.DataFrame:
    if not UPLOAD_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload first.")
    return pd.read_csv(UPLOAD_PATH, parse_dates=["scheduled_time"])


@router.get("")
async def get_forecast():
    df = _load_schedule()
    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    predictions = predict_next_day(model, df)
    return predictions.to_dict(orient="records")


@router.post("/run")
async def run_forecast():
    """Train model on uploaded schedule, then predict."""
    df = _load_schedule()
    from src.data.features import build_feature_matrix
    from src.model.train import train
    from src.model.predict import predict
    from src.alerts.engine import generate_alerts
    from src.alerts.state import save_alerts, clear_alerts

    clean = clean_flights(df)
    features = build_feature_matrix(clean)

    model = train(features, save=True)

    predictions = predict(model, features)

    clear_alerts()
    alerts = generate_alerts(predictions)
    save_alerts(alerts)

    return {
        "windows_predicted": len(predictions),
        "alerts_generated": len(alerts),
        "predictions": predictions.to_dict(orient="records"),
    }
