"""
Security checkpoint forecasting.

Security load is derived from check-in predictions:
  - shifted forward by `checkin_to_security_delay_min` (passengers walk from
    check-in to security — typically 15-25 minutes at a small airport)
  - multiplied by `flow_factor` (fraction of check-in pax that pass through
    security — excludes already-airside passengers, connecting flights, etc.)

Generates separate lane alerts with their own open/close lifecycle,
completely independent of check-in desk alerts.
"""
import yaml
import pandas as pd
from datetime import timedelta
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def derive_security_predictions(checkin_predictions: pd.DataFrame) -> pd.DataFrame:
    """
    Shift check-in predictions forward by the configured delay and scale by
    flow_factor to produce security checkpoint load per 30-min window.
    """
    cfg = _load_config()["security"]
    delay = timedelta(minutes=cfg.get("checkin_to_security_delay_min", 20))
    factor = cfg.get("flow_factor", 0.90)

    df = checkin_predictions.copy()
    df["window_start"] = pd.to_datetime(df["window_start"]) + delay
    df["checkin_load"] = df["predicted_load"]
    df["predicted_load"] = (df["predicted_load"] * factor).round().astype(int)
    df["zone"] = "security"
    return df


def reconcile_security(security_predictions: pd.DataFrame) -> list[dict]:
    """
    Compare security sensor counts vs derived predictions for each window.
    Returns per-window reconciliation with status and corrected_load.
    """
    from src.sensor.store import get_window_counts
    results = []
    for _, row in security_predictions.iterrows():
        ws = pd.Timestamp(row["window_start"]).to_pydatetime()
        predicted = int(row["predicted_load"])
        df = get_window_counts(ws, zone="security")

        if df.empty:
            results.append({
                "window_start": str(row["window_start"]),
                "predicted_load": predicted,
                "actual_count": None,
                "ratio": None,
                "status": "no_sensor_data",
                "corrected_load": predicted,
            })
            continue

        actual = int(df["count_in"].sum())
        ratio = actual / predicted if predicted > 0 else float("inf")
        if ratio >= 1.2:
            status, corrected = "escalated", actual
        elif ratio >= 0.8:
            status, corrected = "confirmed", actual
        elif ratio < 0.5:
            status, corrected = "overestimated", actual
        else:
            status, corrected = "within_range", round((predicted + actual) / 2)

        results.append({
            "window_start": str(row["window_start"]),
            "predicted_load": predicted,
            "actual_count": actual,
            "ratio": round(ratio, 2),
            "status": status,
            "corrected_load": corrected,
        })
    return results


def calibrate_flow_factor(checkin_predictions: pd.DataFrame) -> dict:
    """
    Compare security sensor totals vs check-in sensor totals (offset by delay)
    to derive an empirical flow_factor. Saves result to thresholds.yaml if
    enough data is available (≥5 matched windows).
    """
    from src.sensor.store import get_recent_counts
    cfg = _load_config()
    delay_min = cfg["security"].get("checkin_to_security_delay_min", 20)

    checkin_counts = get_recent_counts(hours=48, zone="checkin")
    security_counts = get_recent_counts(hours=48, zone="security")

    if checkin_counts.empty or security_counts.empty:
        return {"status": "insufficient_data", "flow_factor": cfg["security"]["flow_factor"]}

    checkin_counts["window_start"] = pd.to_datetime(checkin_counts["window_start"])
    security_counts["window_start"] = pd.to_datetime(security_counts["window_start"])
    # shift checkin windows forward by delay to find matching security windows
    checkin_counts["security_window"] = checkin_counts["window_start"] + timedelta(minutes=delay_min)
    checkin_counts["security_window"] = checkin_counts["security_window"].dt.floor("30min")

    merged = checkin_counts.merge(
        security_counts.rename(columns={"total_in": "sec_in", "window_start": "security_window"}),
        on="security_window", how="inner",
    )

    if len(merged) < 5:
        return {"status": "insufficient_data", "windows_matched": len(merged),
                "flow_factor": cfg["security"]["flow_factor"]}

    empirical = (merged["sec_in"] / merged["total_in"].replace(0, float("nan"))).dropna()
    new_factor = round(float(empirical.median()), 3)

    # persist to thresholds.yaml
    import yaml
    cfg["security"]["flow_factor"] = new_factor
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

    return {
        "status": "calibrated",
        "windows_matched": len(merged),
        "old_flow_factor": cfg["security"].get("flow_factor"),
        "new_flow_factor": new_factor,
    }


def generate_security_alerts(security_predictions: pd.DataFrame, running_lanes: int) -> list[dict]:
    """
    Simulate security lane state evolving through the day, firing alerts only
    when the required lane count changes — same stateful logic as check-in desks.
    """
    cfg = _load_config()["security"]
    baseline = cfg.get("baseline_lanes", 1)

    sorted_levels = sorted(
        [v for v in cfg.values() if isinstance(v, dict)],
        key=lambda l: l["threshold"],
        reverse=True,
    )

    alerts = []
    for _, row in security_predictions.sort_values("window_start").iterrows():
        load = int(row["predicted_load"])
        window = row["window_start"]
        time_str = pd.Timestamp(window).strftime("%H:%M")

        lanes_needed = baseline
        for level in sorted_levels:
            if load >= level["threshold"]:
                lanes_needed = level["lanes_to_open"]
                break

        delta = lanes_needed - running_lanes

        if delta > 0:
            alerts.append({
                "type": "security_open",
                "zone": "security",
                "window_start": str(window),
                "predicted_load": load,
                "lanes_to_open": lanes_needed,
                "lanes_to_add": delta,
                "lanes_to_close": 0,
                "message": f"🔺 SECURITY {time_str} — {load} pax — open {delta} more lane(s) (currently {running_lanes}, need {lanes_needed})",
                "status": "OPEN",
            })
            running_lanes = lanes_needed

        elif delta < 0:
            lanes_to_close = abs(delta)
            alerts.append({
                "type": "security_close",
                "zone": "security",
                "window_start": str(window),
                "predicted_load": load,
                "lanes_to_open": lanes_needed,
                "lanes_to_add": 0,
                "lanes_to_close": lanes_to_close,
                "message": f"🔻 SECURITY {time_str} — {load} pax — close {lanes_to_close} lane(s) (currently {running_lanes}, only {lanes_needed} needed)",
                "status": "OPEN",
            })
            running_lanes = lanes_needed

    return alerts
