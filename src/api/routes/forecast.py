import pandas as pd
from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.model.train import load_model
from src.model.predict import predict_next_day

router = APIRouter(prefix="/forecast", tags=["forecast"])

TRAINING_PATH = Path("data/processed/training_data.csv")
SCHEDULE_PATH = Path("data/processed/uploaded_schedule.csv")


@router.post("/train")
async def train_model():
    """Train XGBoost on uploaded historical data."""
    if not TRAINING_PATH.exists():
        raise HTTPException(404, "No training data uploaded. POST /data/upload/training first.")

    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.model.train import train
    from src.model.evaluate import evaluate

    df = pd.read_csv(TRAINING_PATH, parse_dates=["scheduled_time"])
    features = build_feature_matrix(df)

    model = train(features, save=True)
    metrics = evaluate(model, features)

    return {
        "status": "trained",
        "training_flights": len(df),
        "windows": len(features),
        "metrics": metrics,
    }


@router.post("/run")
async def run_forecast():
    """Predict load on uploaded schedule and generate alerts."""
    if not SCHEDULE_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")

    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.model.predict import predict
    from src.alerts.engine import generate_alerts
    from src.alerts.state import save_alerts, clear_alerts

    df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    features = build_feature_matrix(df)
    predictions = predict(model, features)

    clear_alerts()
    alerts = generate_alerts(predictions)
    save_alerts(alerts)

    return {
        "windows_predicted": len(predictions),
        "alerts_generated": len(alerts),
        "predictions": predictions.to_dict(orient="records"),
    }


@router.get("")
async def get_forecast():
    if not SCHEDULE_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")
    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    predictions = predict_next_day(model, df)
    return predictions.to_dict(orient="records")
