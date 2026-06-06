# data/sample/

Sample and demo flight data. Safe to use for testing without real airport data.

## Files

### `sample_flights.csv`
38 departures across a single day (2026-06-06). Covers 05:30–22:00 with realistic pax counts (120–310 per flight). Useful for:
- Testing the upload → train → forecast → alerts pipeline end-to-end
- Demonstrating the dashboard when no real data is available

## Columns
```
flight_id, scheduled_time, pax_count, delay_min, checkin_desks
```

## Limitations
Training XGBoost on a single day produces flat predictions with little variance. For meaningful fluctuations the model needs at least 2 weeks of data across different days of the week. Use real historical data from the airport administration for production.
