# config/

Contains runtime configuration files loaded at startup. No code lives here — only declarative settings.

## Files

### `thresholds.yaml`
Defines the passenger load thresholds that trigger check-in desk alerts.

```yaml
checkin:
  level_1: { threshold: 150, desks_to_open: 1, message: "Open 1 extra check-in desk" }
  level_2: { threshold: 300, desks_to_open: 2, message: "Open 2 extra check-in desks" }
  level_3: { threshold: 500, desks_to_open: 4, message: "Open 4 extra check-in desks — HIGH LOAD" }
peak_hours: [6, 7, 8, 17, 18, 19]
alert_cooldown_minutes: 30
```

## How to change thresholds
- **Via UI:** Settings tab in the Streamlit dashboard
- **Via API:** `POST /thresholds` with updated level objects
- **Manually:** Edit `thresholds.yaml` directly and restart the API

## Notes
- Thresholds apply per 30-minute window, not per flight
- The alert engine (`src/alerts/engine.py`) reads this file at runtime — changes take effect on the next forecast run
- `peak_hours` is used by the feature builder to add an `is_peak_hour` binary feature to the XGBoost model
