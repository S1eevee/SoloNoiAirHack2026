import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from src.model.threshold_detector import detect_thresholds

router = APIRouter(prefix="/thresholds", tags=["thresholds"])

CONFIG_PATH = Path("config/thresholds.yaml")


@router.get("")
async def get_thresholds():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


class ThresholdLevel(BaseModel):
    threshold: int
    desks_to_open: int
    message: str


class ThresholdsUpdate(BaseModel):
    level_1: ThresholdLevel
    level_2: ThresholdLevel
    level_3: ThresholdLevel


@router.post("")
async def update_thresholds(body: ThresholdsUpdate):
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    cfg["checkin"]["level_1"] = body.level_1.model_dump()
    cfg["checkin"]["level_2"] = body.level_2.model_dump()
    cfg["checkin"]["level_3"] = body.level_3.model_dump()

    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(cfg, f)

    return {"status": "updated", "config": cfg}


@router.post("/auto-detect")
async def auto_detect_thresholds(apply: bool = False):
    """
    Analyse uploaded training data and return recommended thresholds.
    Pass ?apply=true to also write them to thresholds.yaml immediately.
    """
    try:
        result = detect_thresholds()
    except FileNotFoundError as e:
        raise HTTPException(400, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))

    if apply:
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)

        rec = result["recommended"]
        cfg["checkin"]["baseline_desks"] = rec["baseline_desks"]
        cfg["checkin"]["level_1"] = rec["level_1"]
        cfg["checkin"]["level_2"] = rec["level_2"]
        cfg["checkin"]["level_3"] = rec["level_3"]

        with open(CONFIG_PATH, "w") as f:
            yaml.safe_dump(cfg, f)

        result["applied"] = True

    return result
