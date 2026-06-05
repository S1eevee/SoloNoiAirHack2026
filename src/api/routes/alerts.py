import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from src.alerts.state import get_alerts, acknowledge_alert, resolve_alert, init_db

router = APIRouter(prefix="/alerts", tags=["alerts"])

init_db()


class AcknowledgeRequest(BaseModel):
    employee: Optional[str] = "employee"


@router.get("")
async def list_alerts(status: Optional[str] = Query(None, enum=["OPEN", "ACKNOWLEDGED", "RESOLVED"])):
    return get_alerts(status=status)


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
