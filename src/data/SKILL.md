# src/data/

Responsible for ingesting raw CSV files and transforming them into a clean feature matrix ready for XGBoost.

## Files

### `loader.py`
Reads a CSV from a file path or raw bytes. Uses `sep=None, engine="python"` so pandas auto-detects the delimiter (comma, semicolon, tab, pipe). Lowercases and strips all column names.

**Key functions:**
- `load_flights(path)` — load from file path
- `load_flights_from_bytes(content, filename)` — load from uploaded bytes

### `cleaner.py`
Normalises any airport CSV format into the internal schema. Handles multiple naming conventions via keyword detection.

**Key functions:**
- `clean_flights(df)` — detects schema, maps columns, parses times, fills nulls
- `_find_col(df, *keywords)` — finds a column by keyword match (e.g. "dep", "pax")
- `_parse_time_column(series)` — handles full datetimes, `HH:MM/DD`, `HH:MM` time-only strings

**Supported input schemas:**
| Column type | Accepted names |
|---|---|
| Departure flight | `dep_flight`, `departure_flight`, `flight_id` |
| Departure time | `dep_time`, `departure_time`, `scheduled_time`, `etd`, `std` |
| Departure pax | `dep_pax`, `departure_pax`, `pax_count` |
| Arrival flight | `arr_flight`, `arrival_flight` |
| Arrival time | `arr_time`, `arrival_time`, `eta`, `sta` |
| Arrival pax | `arr_pax`, `arrival_pax` |

### `features.py`
Aggregates cleaned flight rows into 30-minute time windows for XGBoost.

**Output columns per window:**
```
window_start | total_pax | num_flights | avg_delay | max_delay | checkin_desks
hour | minute | day_of_week | is_peak_hour | time_of_day
```

**Key constants:**
- `FEATURE_COLS` — list of input features fed to XGBoost
- `TARGET_COL` — `"total_pax"` (what the model predicts)

## Pipeline Order
`loader.py` → `cleaner.py` → `features.py` → `src/model/train.py`
