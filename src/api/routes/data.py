import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from src.data.loader import load_flights_from_bytes
from src.data.cleaner import clean_flights

router = APIRouter(prefix="/data", tags=["data"])

TRAINING_PATH = Path("data/processed/training_data.csv")
SCHEDULE_PATH = Path("data/processed/uploaded_schedule.csv")


def _process_upload(content: bytes) -> pd.DataFrame:
    try:
        df = load_flights_from_bytes(content, "upload.csv")
        return clean_flights(df)
    except Exception as e:
        try:
            preview = pd.read_csv(io.BytesIO(content), nrows=1)
            found = list(preview.columns)
        except Exception:
            found = "unknown"
        raise HTTPException(422, f"Invalid flight data: {e}. Columns found: {found}")


@router.post("/upload/training")
async def upload_training(file: UploadFile = File(...)):
    """Upload historical flight data to train the model."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files accepted")

    content = await file.read()
    df = _process_upload(content)

    TRAINING_PATH.parent.mkdir(parents=True, exist_ok=True)

    # append to existing training data if present
    if TRAINING_PATH.exists():
        existing = pd.read_csv(TRAINING_PATH, parse_dates=["scheduled_time"])
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=["flight_id"]).sort_values("scheduled_time").reset_index(drop=True)

    df.to_csv(TRAINING_PATH, index=False)

    return {
        "status": "ok",
        "flights_loaded": len(df),
        "date_range": {
            "from": str(df["scheduled_time"].min()),
            "to": str(df["scheduled_time"].max()),
        },
    }


@router.post("/upload/training/clear")
async def clear_training():
    if TRAINING_PATH.exists():
        TRAINING_PATH.unlink()
    return {"status": "cleared"}


@router.post("/upload/schedule")
async def upload_schedule(file: UploadFile = File(...)):
    """Upload upcoming flight schedule for prediction."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files accepted")

    content = await file.read()
    df = _process_upload(content)

    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SCHEDULE_PATH, index=False)

    return {
        "status": "ok",
        "flights_loaded": len(df),
        "date_range": {
            "from": str(df["scheduled_time"].min()),
            "to": str(df["scheduled_time"].max()),
        },
    }


# keep old endpoint working
@router.post("/upload")
async def upload_schedule_legacy(file: UploadFile = File(...)):
    return await upload_schedule(file)


@router.get("/training/info")
async def training_info():
    if not TRAINING_PATH.exists():
        return {"loaded": False}
    df = pd.read_csv(TRAINING_PATH)
    return {
        "loaded": True,
        "flights": len(df),
        "date_from": str(pd.to_datetime(df["scheduled_time"]).min()),
        "date_to": str(pd.to_datetime(df["scheduled_time"]).max()),
    }


@router.get("/schedule/info")
async def schedule_info():
    if not SCHEDULE_PATH.exists():
        return {"loaded": False}
    df = pd.read_csv(SCHEDULE_PATH)
    return {
        "loaded": True,
        "flights": len(df),
        "date_from": str(pd.to_datetime(df["scheduled_time"]).min()),
        "date_to": str(pd.to_datetime(df["scheduled_time"]).max()),
    }
