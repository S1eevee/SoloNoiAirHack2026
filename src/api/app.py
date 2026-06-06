from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.data import router as data_router
from src.api.routes.forecast import router as forecast_router
from src.api.routes.alerts import router as alerts_router
from src.api.routes.thresholds import router as thresholds_router
from src.api.routes.auth import router as auth_router
from src.api.routes.demo import router as demo_router

try:
    from src.api.routes.sensor import router as sensor_router
    _sensor_available = True
except Exception:
    _sensor_available = False

app = FastAPI(
    title="Passenger Flow Predictor API",
    description="AirHack 2026 — XGBoost-powered check-in demand forecasting + Mobile Employee Alerts",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(data_router)
app.include_router(forecast_router)
app.include_router(alerts_router)
app.include_router(thresholds_router)
app.include_router(demo_router)
if _sensor_available:
    app.include_router(sensor_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "passenger-flow-predictor"}
