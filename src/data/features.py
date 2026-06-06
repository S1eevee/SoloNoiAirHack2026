import pandas as pd
import numpy as np
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"

PAX_PER_DESK_CAPACITY = 50
DELAY_PER_EXCESS_PAX  = 0.3
CONGESTION_EMA_SPAN   = 3

CHECKIN_LEAD_HOURS = 2.0
CHECKIN_SIGMA_MIN  = 30.0
CHECKIN_TAIL_SIGMA = 2.5


def _load_peak_hours() -> list[int]:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("peak_hours", [6, 7, 8, 17, 18, 19])


def _spread_departures(df: pd.DataFrame, freq: str = "30min") -> pd.DataFrame:
    dep = df[~df["flight_id"].str.endswith("_ARR")].copy()
    if dep.empty:
        return dep

    sigma_s  = CHECKIN_SIGMA_MIN * 60.0
    half_win = pd.Timedelta(freq) / 2
    tail     = pd.Timedelta(seconds=sigma_s * CHECKIN_TAIL_SIGMA)

    rows = []
    for _, flight in dep.iterrows():
        mean_t    = flight["scheduled_time"] - pd.Timedelta(hours=CHECKIN_LEAD_HOURS)
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
        return pd.DataFrame(columns=dep.columns)
    return pd.DataFrame(rows).reset_index(drop=True)


def _add_congestion_delay(agg: pd.DataFrame) -> pd.DataFrame:
    agg      = agg.copy()
    capacity = agg["checkin_desks"] * PAX_PER_DESK_CAPACITY
    excess   = (agg["total_pax"] - capacity).clip(lower=0)

    ema_excess = excess.shift(1).fillna(0).ewm(span=CONGESTION_EMA_SPAN, adjust=False).mean()
    synthetic  = (ema_excess * DELAY_PER_EXCESS_PAX).round(1).clip(upper=60.0)

    agg["avg_delay"] = agg["avg_delay"].astype(float)
    agg["max_delay"] = agg["max_delay"].astype(float)
    no_real_delay    = agg["avg_delay"] == 0
    agg.loc[no_real_delay, "avg_delay"] = synthetic[no_real_delay]
    agg.loc[no_real_delay, "max_delay"] = (synthetic[no_real_delay] * 1.5).clip(upper=90.0)
    agg["congestion_delay"] = synthetic
    return agg


def build_feature_matrix(df: pd.DataFrame, freq: str = "30min") -> pd.DataFrame:
    peak_hours = _load_peak_hours()

    df = _spread_departures(df, freq=freq)
    if df.empty:
        return pd.DataFrame(columns=FEATURE_COLS + ["window_start", TARGET_COL])

    df["window_start"] = df["scheduled_time"].dt.floor(freq)

    agg = df.groupby("window_start").agg(
        total_pax=("pax_count", "sum"),
        num_flights=("flight_id", "count"),
        avg_delay=("delay_min", "mean"),
        max_delay=("delay_min", "max"),
        checkin_desks=("checkin_desks", "max"),
    ).reset_index()

    agg["hour"]        = agg["window_start"].dt.hour
    agg["minute"]      = agg["window_start"].dt.minute
    agg["day_of_week"] = agg["window_start"].dt.dayofweek
    agg["is_peak_hour"]= agg["hour"].isin(peak_hours).astype(int)
    agg["time_of_day"] = agg["hour"] + agg["minute"] / 60.0

    # cyclical encoding — avoids the artificial gap between hour 23 and hour 0
    agg["hour_sin"] = np.sin(2 * np.pi * agg["hour"] / 24)
    agg["hour_cos"] = np.cos(2 * np.pi * agg["hour"] / 24)
    agg["dow_sin"]  = np.sin(2 * np.pi * agg["day_of_week"] / 7)
    agg["dow_cos"]  = np.cos(2 * np.pi * agg["day_of_week"] / 7)

    agg = agg.sort_values("window_start").reset_index(drop=True)
    agg = _add_congestion_delay(agg)

    # lag / rolling features — previous windows are strong predictors
    agg["pax_lag1"]  = agg["total_pax"].shift(1).fillna(0)
    agg["pax_lag2"]  = agg["total_pax"].shift(2).fillna(0)
    agg["pax_roll3"] = agg["total_pax"].shift(1).rolling(3, min_periods=1).mean().fillna(0)

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
    "congestion_delay",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "pax_lag1",
    "pax_lag2",
    "pax_roll3",
]

TARGET_COL = "total_pax"
