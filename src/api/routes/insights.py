import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from src.alerts.state import get_alerts

router = APIRouter(prefix="/insights", tags=["insights"])

UPLOAD_PATH = Path("data/processed/uploaded_schedule.csv")


class InsightRequest(BaseModel):
    question: Optional[str] = None
    api_key: Optional[str] = None


@router.post("")
async def get_insights(body: InsightRequest = InsightRequest()):
    from src.model.train import load_model
    from src.model.predict import predict_next_day
    from src.llm.insights import get_insights as llm_insights

    if not UPLOAD_PATH.exists():
        raise HTTPException(404, "No schedule uploaded. POST /data/upload first.")

    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    df = pd.read_csv(UPLOAD_PATH, parse_dates=["scheduled_time"])
    predictions = predict_next_day(model, df)
    alerts = get_alerts(status="OPEN")

    insight_text = llm_insights(
        predictions, alerts,
        question=body.question,
        api_key=body.api_key,
    )
    return {"insight": insight_text}
