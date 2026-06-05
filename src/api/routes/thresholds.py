import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

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

    cfg["checkin"] = {
        "level_1": body.level_1.model_dump(),
        "level_2": body.level_2.model_dump(),
        "level_3": body.level_3.model_dump(),
    }

    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(cfg, f)

    return {"status": "updated", "config": cfg}
