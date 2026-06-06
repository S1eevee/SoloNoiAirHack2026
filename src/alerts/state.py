import sqlite3
import json
import yaml
from datetime import datetime
from pathlib import Path

DB_PATH     = Path(__file__).parents[2] / "data" / "alerts.db"
CONFIG_PATH = Path(__file__).parents[2] / "config" / "thresholds.yaml"


def _baseline_desks() -> int:
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)["checkin"].get("baseline_desks", 1)
    except Exception:
        return 1


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
                desks_to_add INTEGER,
                desks_to_close INTEGER,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                acknowledged_by TEXT
            )
        """)
        for col in ("desks_to_add INTEGER", "desks_to_close INTEGER"):
            try:
                conn.execute(f"ALTER TABLE alerts ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS desk_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                desks_open INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("INSERT OR IGNORE INTO desk_state (id, desks_open) VALUES (1, ?)", (_baseline_desks(),))
        conn.commit()


def get_desks_open() -> int:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT desks_open FROM desk_state WHERE id = 1").fetchone()
    return row["desks_open"] if row else 0


def set_desks_open(count: int):
    init_db()
    with _connect() as conn:
        conn.execute("UPDATE desk_state SET desks_open = ? WHERE id = 1", (max(0, count),))
        conn.commit()


def save_alerts(alerts: list[dict]) -> list[int]:
    init_db()
    ids = []
    with _connect() as conn:
        for alert in alerts:
            cur = conn.execute("""
                INSERT INTO alerts
                  (type, window_start, predicted_load, desks_to_open, desks_to_add, desks_to_close, message, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert["type"],
                alert["window_start"],
                alert.get("predicted_load"),
                alert.get("desks_to_open"),
                alert.get("desks_to_add"),
                alert.get("desks_to_close"),
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
        alert = conn.execute(
            "SELECT id, status, type, desks_to_open FROM alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        if not alert:
            return False
        conn.execute("""
            UPDATE alerts
            SET status = 'ACKNOWLEDGED', acknowledged_at = ?, acknowledged_by = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), employee, alert_id))

        # sync desk counter to what this alert instructed
        if alert["desks_to_open"] is not None:
            conn.execute(
                "UPDATE desk_state SET desks_open = ? WHERE id = 1",
                (max(0, alert["desks_to_open"]),)
            )

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
