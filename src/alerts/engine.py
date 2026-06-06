import yaml
import pandas as pd
from pathlib import Path

from src.alerts.state import get_desks_open

CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _desks_needed_for_load(load: int, sorted_levels: list, baseline: int) -> int:
    for level in sorted_levels:
        if load >= level["threshold"]:
            return level["desks_to_open"]
    return baseline


def generate_alerts(predictions: pd.DataFrame) -> list[dict]:
    """
    Simulate desk state evolving through the day window by window.

    Starting from the current open desk count, each window that requires more
    or fewer desks than are currently open fires an alert and updates the
    running desk count. This means a desk opened at 03:00 is still open at
    03:30, and gets closed when load drops — mirroring real operations.
    """
    cfg = _load_config()
    levels = cfg["checkin"]
    baseline = cfg["checkin"].get("baseline_desks", 1)

    sorted_levels = sorted(
        [v for v in levels.values() if isinstance(v, dict)],
        key=lambda l: l["threshold"],
        reverse=True,
    )

    # simulate desk state through the day
    running_desks = get_desks_open()

    alerts = []
    for _, row in predictions.sort_values("window_start").iterrows():
        load = int(row["predicted_load"])
        window = row["window_start"]
        time_str = pd.Timestamp(window).strftime("%H:%M")
        desks_needed = _desks_needed_for_load(load, sorted_levels, baseline)
        delta = desks_needed - running_desks

        if delta > 0:
            alerts.append({
                "type": "checkin_open",
                "window_start": str(window),
                "predicted_load": load,
                "desks_to_open": desks_needed,
                "desks_to_add": delta,
                "desks_to_close": 0,
                "message": f"🔺 {time_str} — {load} pax — open {delta} more desk(s) (currently {running_desks}, need {desks_needed})",
                "status": "OPEN",
            })
            running_desks = desks_needed  # desks are now open

        elif delta < 0:
            desks_to_close = abs(delta)
            alerts.append({
                "type": "checkin_close",
                "window_start": str(window),
                "predicted_load": load,
                "desks_to_open": desks_needed,
                "desks_to_add": 0,
                "desks_to_close": desks_to_close,
                "message": f"🔻 {time_str} — {load} pax — close {desks_to_close} desk(s) (currently {running_desks}, only {desks_needed} needed)",
                "status": "OPEN",
            })
            running_desks = desks_needed  # desks are now closed

    return alerts
