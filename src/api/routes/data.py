import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from src.data.loader import load_flights_from_bytes
from src.data.cleaner import clean_flights

router = APIRouter(prefix="/data", tags=["data"])

UPLOAD_PATH = Path("data/processed/uploaded_schedule.csv")


@router.post("/upload")
async def upload_schedule(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files accepted")

    content = await file.read()
    try:
        df = load_flights_from_bytes(content, file.filename)
        df = clean_flights(df)
    except Exception as e:
        raise HTTPException(422, f"Invalid flight data: {e}")

    UPLOAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(UPLOAD_PATH, index=False)

    return {
        "status": "ok",
        "flights_loaded": len(df),
        "date_range": {
            "from": str(df["scheduled_time"].min()),
            "to": str(df["scheduled_time"].max()),
        },
    }


@router.get("/schedule")
async def get_schedule():
    if not UPLOAD_PATH.exists():
        raise HTTPException(404, "No schedule uploaded yet")
    df = pd.read_csv(UPLOAD_PATH)
    return df.to_dict(orient="records")
