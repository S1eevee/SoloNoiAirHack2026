import pandas as pd
import numpy as np
from datetime import datetime, timedelta


REQUIRED_COLUMNS = {"flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"}
AIRPORT_SCHEMA = {"departure_flight", "departure_time", "departure_pax"}


def _parse_time_column(series: pd.Series) -> pd.Series:
    """
    Parse time strings in any format into full datetimes.
    Handles: '23:50/31', '06:30', '2026-06-06 06:30', '06:30:00', etc.
    Uses today as the base date when only a time (or time/day) is given.
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    results = []

    for val in series:
        val = str(val).strip() if pd.notna(val) else ""
        if not val or val in ("nan", "None", ""):
            results.append(pd.NaT)
            continue

        dt = None

        # try pandas first (handles full ISO datetimes)
        try:
            dt = pd.to_datetime(val)
            results.append(dt)
            continue
        except Exception:
            pass

        # format: HH:MM/DD  e.g. "23:50/31" or "06:30/01"
        if "/" in val:
            try:
                time_part, day_part = val.split("/")
                day = int(day_part.strip())
                h, m = [int(x) for x in time_part.strip().split(":")]
                # keep current month/year, use the given day
                try:
                    dt = today.replace(day=day, hour=h, minute=m)
                except ValueError:
                    # day out of range for current month — use last valid day
                    import calendar
                    last_day = calendar.monthrange(today.year, today.month)[1]
                    dt = today.replace(day=min(day, last_day), hour=h, minute=m)
                results.append(pd.Timestamp(dt))
                continue
            except Exception:
                pass

        # format: HH:MM or HH:MM:SS (time only, no date)
        if ":" in val and len(val) <= 8:
            try:
                parts = val.split(":")
                h, m = int(parts[0]), int(parts[1])
                dt = today.replace(hour=h, minute=m)
                results.append(pd.Timestamp(dt))
                continue
            except Exception:
                pass

        results.append(pd.NaT)

    return pd.Series(results)


def _normalize_airport_schema(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    if "departure_flight" in df.columns and "departure_time" in df.columns:
        dep = df[df["departure_flight"].notna()].copy()
        dep = dep.rename(columns={
            "departure_flight": "flight_id",
            "departure_time": "scheduled_time",
            "departure_pax": "pax_count",
        })
        rows.append(dep)

    if "arrival_flight" in df.columns and "arrival_time" in df.columns:
        arr = df[df["arrival_flight"].notna()].copy()
        arr = arr.rename(columns={
            "arrival_flight": "flight_id",
            "arrival_time": "scheduled_time",
            "arrival_pax": "pax_count",
        })
        arr["flight_id"] = arr["flight_id"].astype(str) + "_ARR"
        rows.append(arr)

    if not rows:
        raise ValueError("No departure_flight or arrival_flight columns found.")

    out = pd.concat(rows, ignore_index=True)

    if "pax_count" not in out.columns:
        out["pax_count"] = 150

    out["delay_min"] = 0
    out["checkin_desks"] = 3

    return out[["flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"]]


def _detect_schema(df: pd.DataFrame) -> str:
    if REQUIRED_COLUMNS.issubset(set(df.columns)):
        return "internal"
    if "departure_flight" in df.columns or "arrival_flight" in df.columns:
        return "airport"
    return "unknown"


def clean_flights(df: pd.DataFrame) -> pd.DataFrame:
    schema = _detect_schema(df)

    if schema == "airport":
        df = _normalize_airport_schema(df)
    elif schema == "unknown":
        missing = REQUIRED_COLUMNS - set(df.columns)
        raise ValueError(
            f"Unrecognised CSV format. Columns found: {list(df.columns)}. "
            f"Expected columns: {sorted(REQUIRED_COLUMNS)}"
        )

    df = df.copy()
    df["scheduled_time"] = _parse_time_column(df["scheduled_time"])

    # drop rows where time couldn't be parsed
    before = len(df)
    df = df[df["scheduled_time"].notna()].reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"Warning: dropped {dropped} rows with unparseable times")

    df["pax_count"] = pd.to_numeric(df["pax_count"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    df["delay_min"] = pd.to_numeric(df["delay_min"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    df["checkin_desks"] = pd.to_numeric(df["checkin_desks"], errors="coerce").fillna(1).clip(lower=1).astype(int)

    df["effective_time"] = df["scheduled_time"] + pd.to_timedelta(df["delay_min"], unit="m")

    df = df.drop_duplicates(subset=["flight_id"])
    df = df.sort_values("scheduled_time").reset_index(drop=True)
    return df
