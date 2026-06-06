"""
Arrivals staff alert engine.

Generates alerts for baggage/passport handling staff based on predicted
arrival passenger load per 30-min window.
"""
import yaml
import pandas as pd
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def generate_arrivals_alerts(predictions: pd.DataFrame, running_agents: int) -> list[dict]:
    cfg = _load_config()["arrivals"]
    baseline = cfg.get("baseline_agents", 1)

    sorted_levels = sorted(
        [v for v in cfg.values() if isinstance(v, dict)],
        key=lambda l: l["threshold"],
        reverse=True,
    )

    alerts = []
    for _, row in predictions.sort_values("window_start").iterrows():
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
                "type": "arrivals_open",
                "zone": "arrivals",
                "window_start": str(window),
                "predicted_load": load,
                "agents_to_open": agents_needed,
                "agents_to_add": delta,
                "agents_to_close": 0,
                "message": f"✈️ ARR {time_str} — {load} pax — deploy {delta} more staff (currently {running_agents}, need {agents_needed})",
                "status": "OPEN",
            })
            running_agents = agents_needed

        elif delta < 0:
            close = abs(delta)
            alerts.append({
                "type": "arrivals_close",
                "zone": "arrivals",
                "window_start": str(window),
                "predicted_load": load,
                "agents_to_open": agents_needed,
                "agents_to_add": 0,
                "agents_to_close": close,
                "message": f"✈️ ARR {time_str} — {load} pax — release {close} staff (currently {running_agents}, only {agents_needed} needed)",
                "status": "OPEN",
            })
            running_agents = agents_needed

    return alerts
