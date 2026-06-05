from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.data import router as data_router
from src.api.routes.forecast import router as forecast_router
from src.api.routes.alerts import router as alerts_router
from src.api.routes.thresholds import router as thresholds_router
from src.api.routes.insights import router as insights_router

app = FastAPI(
    title="Passenger Flow Predictor API",
    description="AirHack 2026 — XGBoost-powered check-in demand forecasting",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)
app.include_router(forecast_router)
app.include_router(alerts_router)
app.include_router(thresholds_router)
app.include_router(insights_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "passenger-flow-predictor"}
