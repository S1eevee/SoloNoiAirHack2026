import pandas as pd
from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.model.train import load_model
from src.model.predict import predict_next_day

router = APIRouter(prefix="/forecast", tags=["forecast"])

TRAINING_PATH    = Path("data/processed/training_data.csv")
SCHEDULE_PATH    = Path("data/processed/uploaded_schedule.csv")
PREDICTIONS_PATH = Path("data/processed/checkin_predictions.csv")


@router.post("/train")
async def train_model():
    """Train XGBoost on uploaded historical data, augmented with sensor-validated rows."""
    if not TRAINING_PATH.exists():
        raise HTTPException(404, "No training data uploaded. POST /data/upload/training first.")

    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix
    from src.model.train import train
    from src.model.evaluate import evaluate

    df = pd.read_csv(TRAINING_PATH, parse_dates=["scheduled_time"])
    features = build_feature_matrix(clean_flights(df))

    # Merge in sensor-validated rows if available — sensor failure never blocks training
    sensor_window_count = 0
    try:
        from src.sensor.training import load_sensor_training
        sensor_rows = load_sensor_training()
        if sensor_rows is not None:
            features = pd.concat([features, sensor_rows], ignore_index=True)
            features = features.drop_duplicates(subset=["window_start"], keep="last")
            sensor_window_count = len(sensor_rows)
    except Exception:
        pass

    model = train(features, save=True)
    metrics = evaluate(model, features)

    return {
        "status": "trained",
        "training_flights": len(df),
        "windows": len(features),
        "sensor_validated_windows": sensor_window_count,
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

    predictions.to_csv(PREDICTIONS_PATH, index=False)

    return {
        "windows_predicted": len(predictions),
        "alerts_generated": len(alerts),
        "predictions": predictions.to_dict(orient="records"),
    }


@router.get("")
async def get_forecast():
    # Return cached predictions if available — avoids re-running the model on every page load
    if PREDICTIONS_PATH.exists():
        preds = pd.read_csv(PREDICTIONS_PATH)
        return preds.to_dict(orient="records")

    if not SCHEDULE_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload/schedule first.")
    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
    predictions = predict_next_day(model, df)
    predictions.to_csv(PREDICTIONS_PATH, index=False)
    return predictions.to_dict(orient="records")
