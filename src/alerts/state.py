import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "alerts.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                window_start TEXT NOT NULL,
                predicted_load INTEGER,
                desks_to_open INTEGER,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                acknowledged_by TEXT
            )
        """)
        conn.commit()


def save_alerts(alerts: list[dict]) -> list[int]:
    init_db()
    ids = []
    with _connect() as conn:
        for alert in alerts:
            cur = conn.execute("""
                INSERT INTO alerts
                  (type, window_start, predicted_load, desks_to_open, message, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert["type"],
                alert["window_start"],
                alert.get("predicted_load"),
                alert.get("desks_to_open"),
                alert["message"],
                alert.get("status", "OPEN"),
                datetime.utcnow().isoformat(),
            ))
            ids.append(cur.lastrowid)
        conn.commit()
    return ids


def get_alerts(status: str | None = None) -> list[dict]:
    init_db()
    with _connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alerts ORDER BY created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def acknowledge_alert(alert_id: int, employee: str = "employee") -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "SELECT id, status FROM alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        if not cur:
            return False
        conn.execute("""
            UPDATE alerts
            SET status = 'ACKNOWLEDGED', acknowledged_at = ?, acknowledged_by = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), employee, alert_id))
        conn.commit()
    return True


def resolve_alert(alert_id: int) -> bool:
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE alerts SET status = 'RESOLVED' WHERE id = ?", (alert_id,)
        )
        conn.commit()
    return True


def clear_alerts():
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM alerts")
        conn.commit()
