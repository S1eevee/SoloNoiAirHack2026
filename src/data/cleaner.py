import pandas as pd
import numpy as np
from datetime import datetime
import calendar


REQUIRED_COLUMNS = {"flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"}


def _find_col(df: pd.DataFrame, *keywords) -> str | None:
    """Return first column whose name contains any of the keywords."""
    for col in df.columns:
        for kw in keywords:
            if kw in col:
                return col
    return None


def _parse_time_column(series: pd.Series) -> pd.Series:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    results = []

    for val in series:
        val = str(val).strip() if pd.notna(val) else ""
        if not val or val in ("nan", "None", ""):
            results.append(pd.NaT)
            continue

        # full datetime string
        try:
            results.append(pd.to_datetime(val))
            continue
        except Exception:
            pass

        # HH:MM/DD  e.g. "23:50/31"
        if "/" in val:
            try:
                time_part, day_part = val.split("/", 1)
                day = int(day_part.strip())
                h, m = [int(x) for x in time_part.strip().split(":")]
                last_day = calendar.monthrange(today.year, today.month)[1]
                dt = today.replace(day=min(day, last_day), hour=h, minute=m)
                results.append(pd.Timestamp(dt))
                continue
            except Exception:
                pass

        # HH:MM or HH:MM:SS
        if ":" in val:
            try:
                parts = val.split(":")
                h, m = int(parts[0]), int(parts[1])
                results.append(pd.Timestamp(today.replace(hour=h, minute=m)))
                continue
            except Exception:
                pass

        results.append(pd.NaT)

    return pd.Series(results, index=series.index)


def _normalize_to_internal(df: pd.DataFrame) -> pd.DataFrame:
    """Map any airport CSV column naming to internal schema using keyword detection."""
    rows = []

    # --- departures ---
    dep_flight = _find_col(df, "dep_flight", "departure_flight", "dep_flt", "flight_dep", "flt dep", "flt_dep")
    dep_time   = _find_col(df, "dep_time", "departure_time", "dep_sched", "etd", "std")
    dep_pax    = _find_col(df, "dep_pax", "departure_pax", "pax_dep", "dep_passengers", "pax")

    if dep_flight:
        dep = df[df[dep_flight].notna()].copy()
        dep["flight_id"]      = dep[dep_flight].astype(str)
        dep["scheduled_time"] = _parse_time_column(dep[dep_time]) if dep_time else pd.NaT
        dep["pax_count"]      = pd.to_numeric(dep[dep_pax], errors="coerce").fillna(150) if dep_pax else 150
        rows.append(dep[["flight_id", "scheduled_time", "pax_count"]])

    # --- arrivals ---
    arr_flight = _find_col(df, "arr_flight", "arrival_flight", "arr_flt", "flight_arr", "flt arr", "flt_arr")
    arr_time   = _find_col(df, "arr_time", "arrival_time", "arr_sched", "eta", "sta")
    arr_pax    = _find_col(df, "arr_pax", "arrival_pax", "pax_arr", "arr_passengers", "pax")

    if arr_flight:
        arr = df[df[arr_flight].notna()].copy()
        arr["flight_id"]      = arr[arr_flight].astype(str) + "_ARR"
        arr["scheduled_time"] = _parse_time_column(arr[arr_time]) if arr_time else pd.NaT
        arr["pax_count"]      = pd.to_numeric(arr[arr_pax], errors="coerce").fillna(150) if arr_pax else 150
        rows.append(arr[["flight_id", "scheduled_time", "pax_count"]])

    # --- fallback: single flight-id column + type/direction discriminator ---
    # handles formats like Romanian airport exports: "numar zbor", "ora", "type"
    if not rows:
        flight_col = _find_col(df, "numar zbor", "numar_zbor", "zbor", "flight_number", "flight no", "flight")
        time_col   = _find_col(df, "ora", "time", "scheduled", "hour")
        type_col   = _find_col(df, "type", "tip", "direction", "dir")
        pax_col    = _find_col(df, "pax", "pasageri", "passengers")

        if flight_col:
            sub = df[df[flight_col].notna()].copy()
            sub["flight_id"]      = sub[flight_col].astype(str)
            sub["scheduled_time"] = _parse_time_column(sub[time_col]) if time_col else pd.NaT
            sub["pax_count"]      = pd.to_numeric(sub[pax_col], errors="coerce").fillna(150) if pax_col else 150

            if type_col:
                # arrivals: type value contains 'a', 'arr', 'sosir' (Romanian)
                arr_mask = sub[type_col].astype(str).str.lower().str.contains(r"arr|sosi|^a$", regex=True, na=False)
                sub.loc[~arr_mask, "flight_id"] = sub.loc[~arr_mask, "flight_id"]
                sub.loc[arr_mask,  "flight_id"] = sub.loc[arr_mask,  "flight_id"] + "_ARR"

            rows.append(sub[["flight_id", "scheduled_time", "pax_count"]])

    if not rows:
        raise ValueError(
            f"Cannot find flight columns. Columns in your CSV: {list(df.columns)}. "
            "Need at least one column with 'dep_flight', 'departure_flight', 'arr_flight', or 'arrival_flight'."
        )

    out = pd.concat(rows, ignore_index=True)
    out["delay_min"]    = 0
    out["checkin_desks"] = 3
    return out[["flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"]]


def _is_internal_schema(df: pd.DataFrame) -> bool:
    return REQUIRED_COLUMNS.issubset(set(df.columns))


def clean_flights(df: pd.DataFrame) -> pd.DataFrame:
    if not _is_internal_schema(df):
        df = _normalize_to_internal(df)

    df = df.copy()
    df["scheduled_time"] = _parse_time_column(df["scheduled_time"])

    # if no times could be parsed, spread flights evenly across the day
    if df["scheduled_time"].isna().all():
        today = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        df["scheduled_time"] = pd.date_range(today, periods=len(df), freq="15min")
    else:
        df = df[df["scheduled_time"].notna()].reset_index(drop=True)

    df["pax_count"]      = pd.to_numeric(df["pax_count"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    df["delay_min"]      = pd.to_numeric(df["delay_min"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    df["checkin_desks"]  = pd.to_numeric(df["checkin_desks"], errors="coerce").fillna(1).clip(lower=1).astype(int)
    df["effective_time"] = df["scheduled_time"] + pd.to_timedelta(df["delay_min"], unit="m")

    df = df.drop_duplicates(subset=["flight_id", "scheduled_time"])
    df = df.sort_values("scheduled_time").reset_index(drop=True)
    return df
