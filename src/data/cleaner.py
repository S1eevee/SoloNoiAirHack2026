import pandas as pd
import numpy as np


REQUIRED_COLUMNS = {"flight_id", "scheduled_time", "pax_count", "delay_min", "checkin_desks"}


def clean_flights(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()
    df["scheduled_time"] = pd.to_datetime(df["scheduled_time"])

    # fill numeric nulls
    df["pax_count"] = df["pax_count"].fillna(0).clip(lower=0).astype(int)
    df["delay_min"] = df["delay_min"].fillna(0).clip(lower=0).astype(int)
    df["checkin_desks"] = df["checkin_desks"].fillna(1).clip(lower=1).astype(int)

    # effective departure time accounts for delay
    df["effective_time"] = df["scheduled_time"] + pd.to_timedelta(df["delay_min"], unit="m")

    df = df.drop_duplicates(subset=["flight_id"])
    df = df.sort_values("scheduled_time").reset_index(drop=True)
    return df
