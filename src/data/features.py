import pandas as pd
import numpy as np
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _load_peak_hours() -> list[int]:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("peak_hours", [6, 7, 8, 17, 18, 19])


def build_feature_matrix(df: pd.DataFrame, freq: str = "30min") -> pd.DataFrame:
    """Aggregate flights into time-window feature rows for XGBoost."""
    peak_hours = _load_peak_hours()

    df = df.copy()
    df["window_start"] = df["scheduled_time"].dt.floor(freq)

    agg = df.groupby("window_start").agg(
        total_pax=("pax_count", "sum"),
        num_flights=("flight_id", "count"),
        avg_delay=("delay_min", "mean"),
        max_delay=("delay_min", "max"),
        checkin_desks=("checkin_desks", "max"),
    ).reset_index()

    agg["hour"] = agg["window_start"].dt.hour
    agg["minute"] = agg["window_start"].dt.minute
    agg["day_of_week"] = agg["window_start"].dt.dayofweek
    agg["is_peak_hour"] = agg["hour"].isin(peak_hours).astype(int)
    agg["time_of_day"] = agg["hour"] + agg["minute"] / 60.0

    agg = agg.sort_values("window_start").reset_index(drop=True)
    return agg


FEATURE_COLS = [
    "num_flights",
    "avg_delay",
    "max_delay",
    "checkin_desks",
    "hour",
    "minute",
    "day_of_week",
    "is_peak_hour",
    "time_of_day",
]

TARGET_COL = "total_pax"
