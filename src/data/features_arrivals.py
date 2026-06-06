"""
Arrivals bell curve feature engineering.

Passengers from an arriving flight reach baggage/passport ~20 min after landing.
Because they all land together, the spread is tight (σ = 12 min).
"""
import numpy as np
import pandas as pd
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"

ARRIVAL_DELAY_MIN  = 20.0   # minutes after STA passengers reach baggage/passport
ARRIVAL_SIGMA_MIN  = 12.0   # tight cluster — everyone from same flight arrives together
ARRIVAL_TAIL_SIGMA = 2.5


def _load_peak_hours() -> list[int]:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("peak_hours", [6, 7, 8, 17, 18, 19])


def _spread_arrivals(df: pd.DataFrame, freq: str = "30min") -> pd.DataFrame:
    arr = df[df["flight_id"].str.endswith("_ARR", na=False)].copy()
    if arr.empty:
        return arr

    sigma_s  = ARRIVAL_SIGMA_MIN * 60.0
    half_win = pd.Timedelta(freq) / 2
    tail     = pd.Timedelta(seconds=sigma_s * ARRIVAL_TAIL_SIGMA)

    rows = []
    for _, flight in arr.iterrows():
        # center is AFTER arrival (passengers walk out, reach passport/baggage)
        mean_t    = flight["scheduled_time"] + pd.Timedelta(minutes=ARRIVAL_DELAY_MIN)
        win_start = (mean_t - tail).floor(freq)
        win_end   = (mean_t + tail).floor(freq)

        windows = pd.date_range(win_start, win_end, freq=freq)
        if len(windows) == 0:
            continue

        centres  = np.array([(w + half_win).timestamp() for w in windows])
        mean_ts  = mean_t.timestamp()
        weights  = np.exp(-0.5 * ((centres - mean_ts) / sigma_s) ** 2)
        weights /= weights.sum()

        for win, w in zip(windows, weights):
            pax = int(round(flight["pax_count"] * w))
            if pax < 1:
                continue
            r = flight.copy()
            r["scheduled_time"] = win
            r["pax_count"]      = pax
            r["flight_id"]      = f"{flight['flight_id']}_w{win.strftime('%H%M')}"
            rows.append(r)

    if not rows:
        return pd.DataFrame(columns=arr.columns)
    return pd.DataFrame(rows).reset_index(drop=True)


def build_arrivals_feature_matrix(df: pd.DataFrame, freq: str = "30min") -> pd.DataFrame:
    peak_hours = _load_peak_hours()

    df = _spread_arrivals(df, freq=freq)
    if df.empty:
        return pd.DataFrame(columns=ARRIVALS_FEATURE_COLS + ["window_start", TARGET_COL])

    df["window_start"] = df["scheduled_time"].dt.floor(freq)

    agg = df.groupby("window_start").agg(
        total_pax=("pax_count", "sum"),
        num_flights=("flight_id", "count"),
        avg_delay=("delay_min", "mean"),
        max_delay=("delay_min", "max"),
    ).reset_index()

    agg["hour"]         = agg["window_start"].dt.hour
    agg["minute"]       = agg["window_start"].dt.minute
    agg["day_of_week"]  = agg["window_start"].dt.dayofweek
    agg["is_peak_hour"] = agg["hour"].isin(peak_hours).astype(int)
    agg["time_of_day"]  = agg["hour"] + agg["minute"] / 60.0

    agg["hour_sin"] = np.sin(2 * np.pi * agg["hour"] / 24)
    agg["hour_cos"] = np.cos(2 * np.pi * agg["hour"] / 24)
    agg["dow_sin"]  = np.sin(2 * np.pi * agg["day_of_week"] / 7)
    agg["dow_cos"]  = np.cos(2 * np.pi * agg["day_of_week"] / 7)

    agg = agg.sort_values("window_start").reset_index(drop=True)

    agg["pax_lag1"]  = agg["total_pax"].shift(1).fillna(0)
    agg["pax_lag2"]  = agg["total_pax"].shift(2).fillna(0)
    agg["pax_roll3"] = agg["total_pax"].shift(1).rolling(3, min_periods=1).mean().fillna(0)

    return agg


ARRIVALS_FEATURE_COLS = [
    "num_flights",
    "avg_delay",
    "max_delay",
    "hour",
    "minute",
    "day_of_week",
    "is_peak_hour",
    "time_of_day",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "pax_lag1",
    "pax_lag2",
    "pax_roll3",
]

TARGET_COL = "total_pax"
