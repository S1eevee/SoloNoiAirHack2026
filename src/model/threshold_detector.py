import numpy as np
import pandas as pd
from pathlib import Path

from src.data.features import build_feature_matrix

TRAINING_PATH = Path("data/processed/training_data.csv")


def _effective_load(row: pd.Series) -> float:
    """
    Adjust raw pax count upward when delays are present.
    Delayed flights bunch passengers into a shorter window, increasing queue pressure.
    Formula: effective = total_pax * (1 + 0.4 * avg_delay / 30)
    A 30-min average delay adds 40% to the effective load.
    """
    delay_factor = 0.4 * (row["avg_delay"] / 30.0) if row["avg_delay"] > 0 else 0.0
    return row["total_pax"] * (1.0 + delay_factor)


def detect_thresholds() -> dict:
    """
    Analyse training data windows and return recommended threshold config.
    """
    if not TRAINING_PATH.exists():
        raise FileNotFoundError("No training data found. Upload historical CSVs first.")

    df = pd.read_csv(TRAINING_PATH, parse_dates=["scheduled_time"])
    windows = build_feature_matrix(df)

    # drop near-empty windows (single stray flight, likely noise)
    windows = windows[windows["total_pax"] >= 10].copy()
    if len(windows) < 10:
        raise ValueError("Not enough data to detect thresholds — upload more historical flights.")

    windows["effective_load"] = windows.apply(_effective_load, axis=1)

    load = windows["effective_load"]
    total_pax = windows["total_pax"]

    # --- percentile breakpoints ---
    p25  = float(np.percentile(load, 25))
    p50  = float(np.percentile(load, 50))
    p75  = float(np.percentile(load, 75))
    p90  = float(np.percentile(load, 90))
    p_max = float(load.max())

    # round to nearest 25 for clean config values
    def r25(x): return max(10, int(round(x / 25.0)) * 25)

    t1 = r25(p50)   # level 1: median load
    t2 = r25(p75)   # level 2: 75th percentile
    t3 = r25(p90)   # level 3: 90th percentile
    baseline = max(1, r25(p25) // 150)  # baseline desks from low-load quartile

    # ensure levels are strictly increasing
    t2 = max(t2, t1 + 25)
    t3 = max(t3, t2 + 25)

    # --- desk counts ---
    # estimate how many pax one desk can comfortably handle per 30-min window
    # using 75th percentile load / 2 desks as the per-desk capacity baseline
    pax_per_desk = max(50, p75 / 2)
    def desks_for(threshold): return max(1, int(np.ceil(threshold / pax_per_desk)))

    d1 = desks_for(t1)
    d2 = desks_for(t2)
    d3 = desks_for(t3)

    # ensure desk counts are strictly increasing
    d2 = max(d2, d1 + 1)
    d3 = max(d3, d2 + 1)

    # --- delay stats for reporting ---
    delayed_windows = windows[windows["avg_delay"] > 0]
    avg_delay_overall = float(windows["avg_delay"].mean())
    pct_delayed = float(len(delayed_windows) / len(windows) * 100)

    return {
        "recommended": {
            "baseline_desks": baseline,
            "level_1": {"threshold": t1, "desks_to_open": d1, "message": f"Open {d1} check-in desk(s)"},
            "level_2": {"threshold": t2, "desks_to_open": d2, "message": f"Open {d2} check-in desks"},
            "level_3": {"threshold": t3, "desks_to_open": d3, "message": f"Open {d3} check-in desks — HIGH LOAD"},
        },
        "analysis": {
            "windows_analysed": int(len(windows)),
            "pax_min": int(total_pax.min()),
            "pax_p25": int(p25),
            "pax_p50": int(p50),
            "pax_p75": int(p75),
            "pax_p90": int(p90),
            "pax_max": int(p_max),
            "pax_per_desk_estimate": int(pax_per_desk),
            "avg_delay_min": round(avg_delay_overall, 1),
            "pct_windows_with_delay": round(pct_delayed, 1),
            "delay_adjusted": avg_delay_overall > 0,
        },
    }
