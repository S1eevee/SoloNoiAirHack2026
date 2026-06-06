# src/alerts/

Converts XGBoost predictions into actionable check-in desk alerts and persists their lifecycle in SQLite.

## Files

### `engine.py`
Compares `predicted_load` per 30-min window to the thresholds in `config/thresholds.yaml`. Fires the highest matching alert level per window (only one alert per window).

**Output alert structure:**
```python
{
  "type": "checkin",
  "window_start": "2026-06-06 07:30:00",
  "predicted_load": 511,
  "desks_to_open": 4,
  "message": "Open 4 extra check-in desks — HIGH LOAD at 07:30 (expected 511 pax)",
  "status": "OPEN"
}
```

**Key function:** `generate_alerts(predictions_df)` → `list[dict]`

### `state.py`
SQLite persistence layer for alerts. Database is created automatically at `data/alerts.db` on first use.

**Alert lifecycle:**
```
OPEN → ACKNOWLEDGED → RESOLVED
```

**Key functions:**
| Function | Description |
|---|---|
| `init_db()` | Create table if not exists |
| `save_alerts(alerts)` | Insert new alerts, return list of IDs |
| `get_alerts(status=None)` | Fetch all or filtered by status |
| `acknowledge_alert(id, employee)` | Mark ACKNOWLEDGED, record who and when |
| `resolve_alert(id)` | Mark RESOLVED |
| `clear_alerts()` | Delete all alerts (called before each new forecast) |

## Alert Schema (SQLite)
```sql
id, type, window_start, predicted_load, desks_to_open, message,
status, created_at, acknowledged_at, acknowledged_by
```

## Notes
- Alerts are cleared and regenerated on every `POST /forecast/run`
- Acknowledgement creates an audit trail (employee name + timestamp)
- Security gates are explicitly out of scope — check-in desks only
