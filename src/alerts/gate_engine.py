"""
Gate (boarding ticket scan) checkpoint forecasting.

Gate load is derived from security predictions:
  - shifted forward by `security_to_gate_delay_min` (passengers walk from
    security to the gate — typically 25-35 minutes at a small airport)
  - multiplied by `flow_factor` (~0.98 — almost everyone who clears security
    reaches their gate; a small fraction miss flights or go to wrong gate)

Generates separate gate agent alerts with their own lifecycle.
Also supports reconciliation against VS133-P sensor data at the gate,
and empirical flow_factor calibration from matched security vs gate counts.
"""
import yaml
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def derive_gate_predictions(security_predictions: pd.DataFrame) -> pd.DataFrame:
    """
    Shift security predictions forward by the configured delay and scale by
    flow_factor to produce gate load per 30-min window.
    """
    cfg = _load_config()["gate"]
    delay = timedelta(minutes=cfg.get("security_to_gate_delay_min", 30))
    factor = cfg.get("flow_factor", 0.98)

    df = security_predictions.copy()
    df["window_start"] = pd.to_datetime(df["window_start"]) + delay
    df["security_load"] = df["predicted_load"]
    df["predicted_load"] = (df["predicted_load"] * factor).round().astype(int)
    df["zone"] = "gate"
    return df


def generate_gate_alerts(gate_predictions: pd.DataFrame, running_agents: int) -> list[dict]:
    """
    Simulate gate agent state evolving through the day, firing alerts only
    when the required agent count changes.
    """
    cfg = _load_config()["gate"]
    baseline = cfg.get("baseline_agents", 1)

    sorted_levels = sorted(
        [v for v in cfg.values() if isinstance(v, dict)],
        key=lambda l: l["threshold"],
        reverse=True,
    )

    alerts = []
    for _, row in gate_predictions.sort_values("window_start").iterrows():
        load = int(row["predicted_load"])
        window = row["window_start"]
        time_str = pd.Timestamp(window).strftime("%H:%M")

        agents_needed = baseline
        for level in sorted_levels:
            if load >= level["threshold"]:
                agents_needed = level["agents_to_open"]
                break

        delta = agents_needed - running_agents

        if delta > 0:
            alerts.append({
                "type": "gate_open",
                "zone": "gate",
                "window_start": str(window),
                "predicted_load": load,
                "agents_to_open": agents_needed,
                "agents_to_add": delta,
                "agents_to_close": 0,
                "message": f"🎫 GATE {time_str} — {load} pax — deploy {delta} more agent(s) (currently {running_agents}, need {agents_needed})",
                "status": "OPEN",
            })
            running_agents = agents_needed

        elif delta < 0:
            agents_to_close = abs(delta)
            alerts.append({
                "type": "gate_close",
                "zone": "gate",
                "window_start": str(window),
                "predicted_load": load,
                "agents_to_open": agents_needed,
                "agents_to_add": 0,
                "agents_to_close": agents_to_close,
                "message": f"🎫 GATE {time_str} — {load} pax — release {agents_to_close} agent(s) (currently {running_agents}, only {agents_needed} needed)",
                "status": "OPEN",
            })
            running_agents = agents_needed

    return alerts


def reconcile_gate(gate_predictions: pd.DataFrame) -> list[dict]:
    """Compare actual gate sensor counts vs derived predictions per window."""
    from src.sensor.store import get_window_counts
    results = []
    for _, row in gate_predictions.iterrows():
        ws = pd.Timestamp(row["window_start"]).to_pydatetime()
        predicted = int(row["predicted_load"])
        df = get_window_counts(ws, zone="gate")

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


def calibrate_gate_flow_factor() -> dict:
    """
    Compare security sensor totals vs gate sensor totals (offset by delay)
    to derive an empirical flow_factor. Saves to thresholds.yaml if ≥5 windows matched.
    """
    from src.sensor.store import get_recent_counts
    cfg = _load_config()
    delay_min = cfg["gate"].get("security_to_gate_delay_min", 30)

    security_counts = get_recent_counts(hours=48, zone="security")
    gate_counts = get_recent_counts(hours=48, zone="gate")

    if security_counts.empty or gate_counts.empty:
        return {"status": "insufficient_data", "flow_factor": cfg["gate"]["flow_factor"]}

    security_counts["window_start"] = pd.to_datetime(security_counts["window_start"])
    gate_counts["window_start"] = pd.to_datetime(gate_counts["window_start"])
    security_counts["gate_window"] = (
        security_counts["window_start"] + timedelta(minutes=delay_min)
    ).dt.floor("30min")

    merged = security_counts.merge(
        gate_counts.rename(columns={"total_in": "gate_in", "window_start": "gate_window"}),
        on="gate_window", how="inner",
    )

    if len(merged) < 5:
        return {"status": "insufficient_data", "windows_matched": len(merged),
                "flow_factor": cfg["gate"]["flow_factor"]}

    empirical = (merged["gate_in"] / merged["total_in"].replace(0, float("nan"))).dropna()
    new_factor = round(float(empirical.median()), 3)

    cfg["gate"]["flow_factor"] = new_factor
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

    return {
        "status": "calibrated",
        "windows_matched": len(merged),
        "old_flow_factor": cfg["gate"].get("flow_factor"),
        "new_flow_factor": new_factor,
    }
