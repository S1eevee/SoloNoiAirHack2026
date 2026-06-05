import yaml
import pandas as pd
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def generate_alerts(predictions: pd.DataFrame) -> list[dict]:
    """
    Compare predicted_load per window to checkin thresholds.
    Returns list of alert dicts ready to persist.
    """
    cfg = _load_config()
    levels = cfg["checkin"]

    sorted_levels = sorted(
        levels.values(),
        key=lambda l: l["threshold"],
        reverse=True,
    )

    alerts = []
    for _, row in predictions.iterrows():
        load = int(row["predicted_load"])
        window = row["window_start"]

        for level in sorted_levels:
            if load >= level["threshold"]:
                alerts.append({
                    "type": "checkin",
                    "window_start": str(window),
                    "predicted_load": load,
                    "desks_to_open": level["desks_to_open"],
                    "message": f"{level['message']} at {pd.Timestamp(window).strftime('%H:%M')} "
                               f"(expected {load} pax)",
                    "status": "OPEN",
                })
                break  # only fire highest matching level per window

    return alerts
