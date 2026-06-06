"""
SQLite store for VS133-P sensor readings.
Each reading is bucketed into the 30-min window it falls in,
matching the XGBoost prediction windows exactly.
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/processed/sensor.db")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            device_eui   TEXT    NOT NULL,
            zone         TEXT    NOT NULL DEFAULT 'checkin',
            timestamp    TEXT    NOT NULL,
            window_start TEXT    NOT NULL,
            count_in     INTEGER NOT NULL,
            count_out    INTEGER NOT NULL
        )
    """)
    # migrate existing rows that predate the zone column
    try:
        conn.execute("ALTER TABLE sensor_readings ADD COLUMN zone TEXT NOT NULL DEFAULT 'checkin'")
    except Exception:
        pass
    conn.commit()
    return conn


def _window_for(ts: datetime) -> datetime:
    return ts.replace(minute=0 if ts.minute < 30 else 30, second=0, microsecond=0)


def save_reading(device_eui: str, timestamp: datetime, count_in: int, count_out: int,
                 zone: str = "checkin") -> None:
    window = _window_for(timestamp)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO sensor_readings "
            "(device_eui, zone, timestamp, window_start, count_in, count_out) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (device_eui, zone, timestamp.isoformat(), window.isoformat(), count_in, count_out),
        )


def get_window_counts(window_start: datetime, zone: str = "checkin") -> pd.DataFrame:
    window_end = window_start + timedelta(minutes=30)
    with _conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM sensor_readings "
            "WHERE zone = ? AND window_start >= ? AND window_start < ?",
            conn,
            params=(zone, window_start.isoformat(), window_end.isoformat()),
        )


def get_recent_counts(hours: int = 24, zone: str = "checkin") -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(
            """
            SELECT window_start,
                   SUM(count_in)  AS total_in,
                   SUM(count_out) AS total_out,
                   COUNT(*)       AS readings
            FROM sensor_readings
            WHERE zone = ? AND timestamp >= datetime('now', ?)
            GROUP BY window_start
            ORDER BY window_start
            """,
            conn,
            params=(zone, f"-{hours} hours"),
        )
