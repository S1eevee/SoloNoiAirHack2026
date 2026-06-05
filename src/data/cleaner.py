import pandas as pd
import numpy as np


REQUIRED_COLUMNS = {"flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"}

# columns from the real airport export format
AIRPORT_SCHEMA = {
    "departure_flight", "departure_time", "departure_pax"
}


def _normalize_airport_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Convert real airport CSV columns → internal schema."""
    rows = []

    # departures (check-in relevant)
    if "departure_flight" in df.columns and "departure_time" in df.columns:
        dep = df[df["departure_flight"].notna()].copy()
        dep = dep.rename(columns={
            "departure_flight": "flight_id",
            "departure_time": "scheduled_time",
            "departure_pax": "pax_count",
        })
        dep["type"] = "departure"
        rows.append(dep)

    # arrivals (optional — still counts toward queue/desk load)
    if "arrival_flight" in df.columns and "arrival_time" in df.columns:
        arr = df[df["arrival_flight"].notna()].copy()
        arr = arr.rename(columns={
            "arrival_flight": "flight_id",
            "arrival_time": "scheduled_time",
            "arrival_pax": "pax_count",
        })
        arr["flight_id"] = arr["flight_id"].astype(str) + "_ARR"
        arr["type"] = "arrival"
        rows.append(arr)

    if not rows:
        raise ValueError("No departure_flight or arrival_flight columns found.")

    out = pd.concat(rows, ignore_index=True)

    if "pax_count" not in out.columns:
        out["pax_count"] = 150  # sensible default if pax column missing

    out["delay_min"] = 0
    out["checkin_desks"] = 3

    return out[["flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"]]


def _detect_schema(df: pd.DataFrame) -> str:
    if REQUIRED_COLUMNS.issubset(set(df.columns)):
        return "internal"
    if AIRPORT_SCHEMA.issubset(set(df.columns)) or (
        "departure_flight" in df.columns or "arrival_flight" in df.columns
    ):
        return "airport"
    return "unknown"


def clean_flights(df: pd.DataFrame) -> pd.DataFrame:
    schema = _detect_schema(df)

    if schema == "airport":
        df = _normalize_airport_schema(df)
    elif schema == "unknown":
        missing = REQUIRED_COLUMNS - set(df.columns)
        raise ValueError(
            f"Unrecognised CSV format. Missing columns: {missing}. "
            f"Expected either the internal schema {sorted(REQUIRED_COLUMNS)} "
            f"or an airport export with departure_flight / departure_time / departure_pax."
        )

    df = df.copy()
    df["scheduled_time"] = pd.to_datetime(df["scheduled_time"], infer_datetime_format=True)

    df["pax_count"] = pd.to_numeric(df["pax_count"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    df["delay_min"] = pd.to_numeric(df["delay_min"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    df["checkin_desks"] = pd.to_numeric(df["checkin_desks"], errors="coerce").fillna(1).clip(lower=1).astype(int)

    df["effective_time"] = df["scheduled_time"] + pd.to_timedelta(df["delay_min"], unit="m")

    df = df.drop_duplicates(subset=["flight_id"])
    df = df.sort_values("scheduled_time").reset_index(drop=True)
    return df
