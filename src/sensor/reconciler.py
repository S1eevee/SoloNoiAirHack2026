"""
Reconcile XGBoost predictions against real VS133-P sensor counts.

For each 30-min window:
  - actual >= 1.2 × predicted  → escalated  (sensor sees more than forecast)
  - actual >= 0.8 × predicted  → confirmed  (forecast validated)
  - actual <  0.5 × predicted  → overestimated (open fewer desks)
  - otherwise                  → within_range (blend actual + predicted)

corrected_load is what the alert engine should act on when sensor data exists.
"""
from datetime import datetime, timedelta

import pandas as pd

from src.sensor.store import get_window_counts

ESCALATE_RATIO = 1.2
CONFIRM_RATIO = 0.8
OVERESTIMATE_RATIO = 0.5


def reconcile_window(window_start: datetime, predicted_load: int) -> dict:
    df = get_window_counts(window_start)

    base = {
        "window_start": window_start.isoformat(),
        "predicted_load": predicted_load,
    }

    if df.empty:
        return {**base, "actual_count": None, "ratio": None,
                "status": "no_sensor_data", "corrected_load": predicted_load}

    actual = int(df["count_in"].sum())
    ratio = actual / predicted_load if predicted_load > 0 else float("inf")

    if ratio >= ESCALATE_RATIO:
        status = "escalated"
        corrected = actual
    elif ratio >= CONFIRM_RATIO:
        status = "confirmed"
        corrected = actual
    elif ratio < OVERESTIMATE_RATIO:
        status = "overestimated"
        corrected = actual
    else:
        status = "within_range"
        corrected = round((predicted_load + actual) / 2)

    return {
        **base,
        "actual_count": actual,
        "ratio": round(ratio, 2),
        "status": status,
        "corrected_load": corrected,
    }


def reconcile_all(predictions: pd.DataFrame) -> list[dict]:
    results = []
    for _, row in predictions.iterrows():
        ws = pd.Timestamp(row["window_start"]).to_pydatetime()
        results.append(reconcile_window(ws, int(row["predicted_load"])))
    return results
