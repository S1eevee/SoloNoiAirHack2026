import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from src.alerts.state import (
    get_alerts, acknowledge_alert, resolve_alert, init_db,
    get_desks_open, set_desks_open,
    get_lanes_open, get_agents_open,
    get_security_alerts, get_gate_alerts,
    set_alert_note,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])

init_db()


class AcknowledgeRequest(BaseModel):
    employee: Optional[str] = "employee"


class DeskStateRequest(BaseModel):
    desks_open: int


@router.get("/status")
async def get_status():
    """Single consolidated endpoint for all sidebar state — one call instead of eight."""
    import json
    from pathlib import Path
    manifest_path = Path("data/processed/training_manifest.json")
    demo_active = False
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            demo_active = any(e.get("filename") == "demo_data" for e in manifest)
        except Exception:
            pass
    return {
        "desks_open":        get_desks_open(),
        "lanes_open":        get_lanes_open(),
        "agents_open":       get_agents_open(),
        "open_alert_count":  len(get_alerts(status="OPEN")),
        "open_sec_count":    len(get_security_alerts(status="OPEN")),
        "open_gate_count":   len(get_gate_alerts(status="OPEN")),
        "demo_active":       demo_active,
    }


@router.get("/desks")
async def get_desk_state():
    return {"desks_open": get_desks_open()}


@router.post("/desks")
async def update_desk_state(body: DeskStateRequest):
    set_desks_open(body.desks_open)
    return {"desks_open": body.desks_open}


@router.get("")
async def list_alerts(status: Optional[str] = Query(None, enum=["OPEN", "ACKNOWLEDGED", "RESOLVED"])):
    return get_alerts(status=status)


class NoteRequest(BaseModel):
    note: str


@router.patch("/{alert_id}/note")
async def set_note(alert_id: int, body: NoteRequest):
    """Set or update the admin note/label on any alert (by id, any zone)."""
    ok = set_alert_note(alert_id, body.note)
    if not ok:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return {"alert_id": alert_id, "note": body.note.strip()}


@router.post("/{alert_id}/acknowledge")
async def ack_alert(alert_id: int, body: AcknowledgeRequest = AcknowledgeRequest()):
    ok = acknowledge_alert(alert_id, employee=body.employee)
    if not ok:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
async def resolve(alert_id: int):
    ok = resolve_alert(alert_id)
    if not ok:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return {"status": "resolved", "alert_id": alert_id}
