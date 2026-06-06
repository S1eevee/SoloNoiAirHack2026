"""
Export sensor-validated feature rows for XGBoost retraining.

For each 30-min window where the VS133-P recorded real counts:
  1. Look up flight-derived features for that window (from training_data.csv)
  2. Override total_pax with the actual sensor count (ground truth)
  3. Append the validated row to data/processed/sensor_training.csv

The result is a growing dataset of windows where the model knows exactly
how many people were at check-in, not just what the schedule predicted.
Deduplicated by window_start so re-exporting is safe.
"""
from pathlib import Path

import pandas as pd

from src.data.features import FEATURE_COLS, TARGET_COL, build_feature_matrix
from src.sensor.store import get_recent_counts

SENSOR_TRAINING_PATH = Path("data/processed/sensor_training.csv")
TRAINING_PATH = Path("data/processed/training_data.csv")

_PEAK_HOURS = [6, 7, 8, 17, 18, 19]


def _time_features(window_start: pd.Series) -> pd.DataFrame:
    ws = pd.to_datetime(window_start)
    return pd.DataFrame({
        "hour":        ws.dt.hour,
        "minute":      ws.dt.minute,
        "day_of_week": ws.dt.dayofweek,
        "is_peak_hour": ws.dt.hour.isin(_PEAK_HOURS).astype(int),
        "time_of_day": ws.dt.hour + ws.dt.minute / 60.0,
    })


SCHEDULE_PATH = Path("data/processed/uploaded_schedule.csv")


def _flight_features_for_windows(windows: pd.Series) -> pd.DataFrame:
    """
    Build a window-level feature DataFrame covering the given window_start values.
    Tries today's schedule first (most accurate for live sensor readings),
    then falls back to historical training data for older windows.
    """
    from src.data.cleaner import clean_flights

    frames = []

    # Today's schedule — the flights actually flying while the sensor is recording
    if SCHEDULE_PATH.exists():
        df = pd.read_csv(SCHEDULE_PATH, parse_dates=["scheduled_time"])
        frames.append(build_feature_matrix(clean_flights(df)))

    # Historical data — covers windows from past days
    if TRAINING_PATH.exists():
        df = pd.read_csv(TRAINING_PATH, parse_dates=["scheduled_time"])
        frames.append(build_feature_matrix(clean_flights(df)))

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["window_start"] = pd.to_datetime(combined["window_start"])
    # Where the same window appears in both sources, schedule wins (more recent)
    combined = combined.drop_duplicates(subset=["window_start"], keep="first")
    return combined


def export_sensor_training(hours: int = 24) -> int:
    """
    Build sensor-validated training rows and append to sensor_training.csv.
    Returns number of new rows written.
    """
    sensor_df = get_recent_counts(hours=hours)
    if sensor_df.empty:
        return 0

    sensor_df["window_start"] = pd.to_datetime(sensor_df["window_start"])

    # --- join with flight features (schedule first, then historical) ---
    flight_features = _flight_features_for_windows(sensor_df["window_start"])
    if not flight_features.empty:
        merged = sensor_df.merge(flight_features, on="window_start", how="left")
    else:
        merged = sensor_df.copy()

    # sensor count is the ground truth target
    merged[TARGET_COL] = merged["total_in"]

    # fill time-based features from window_start — used as baseline when no
    # flight data matched, or to fill NaN gaps in partially matched rows
    time_feats = _time_features(merged["window_start"])
    for col in ["hour", "minute", "day_of_week", "is_peak_hour", "time_of_day"]:
        if col not in merged.columns:
            merged[col] = time_feats[col]
        else:
            merged[col] = merged[col].fillna(time_feats[col])

    # fill flight-dependent features with safe defaults where missing
    defaults = {"num_flights": 0, "avg_delay": 0.0, "max_delay": 0.0, "checkin_desks": 3}
    for col, default in defaults.items():
        if col not in merged.columns:
            merged[col] = default
        else:
            merged[col] = merged[col].fillna(default)

    merged["source"] = "sensor"
    keep = ["window_start", TARGET_COL] + FEATURE_COLS + ["source"]
    merged = merged[[c for c in keep if c in merged.columns]].dropna(subset=[TARGET_COL])

    # --- deduplicate against existing sensor training data ---
    if SENSOR_TRAINING_PATH.exists():
        existing = pd.read_csv(SENSOR_TRAINING_PATH, parse_dates=["window_start"])
        combined = pd.concat([existing, merged], ignore_index=True)
        combined = combined.drop_duplicates(subset=["window_start"], keep="last")
    else:
        combined = merged

    SENSOR_TRAINING_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(SENSOR_TRAINING_PATH, index=False)
    return len(merged)


def load_sensor_training() -> pd.DataFrame | None:
    """Return sensor-validated feature rows, or None if none exist yet."""
    if not SENSOR_TRAINING_PATH.exists():
        return None
    df = pd.read_csv(SENSOR_TRAINING_PATH, parse_dates=["window_start"])
    return df if not df.empty else None
