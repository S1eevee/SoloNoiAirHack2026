import os
import hashlib
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes.data import router as data_router
from src.api.routes.forecast import router as forecast_router
from src.api.routes.alerts import router as alerts_router
from src.api.routes.thresholds import router as thresholds_router
from src.api.routes.auth import router as auth_router
from src.api.routes.demo import router as demo_router
from src.api.routes.security import router as security_router
from src.api.routes.gate import router as gate_router
from src.api.routes.arrivals_route import router as arrivals_router
from src.api.routes.departures_gate_route import router as departures_gate_router

try:
    from src.api.routes.sensor import router as sensor_router
    _sensor_available = True
except Exception:
    _sensor_available = False

# API key auth — set API_KEY in .env; algo used to hash the key is also configurable
_RAW_API_KEY    = os.getenv("API_KEY", "")
_KEY_HASH_ALGO  = os.getenv("API_KEY_HASH_ALGO", "sha256")  # crypto agility for key hashing
_STORED_KEY_HASH = hashlib.new(_KEY_HASH_ALGO, _RAW_API_KEY.encode()).hexdigest() if _RAW_API_KEY else ""

# Paths that don't require an API key
_PUBLIC_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc", "/auth/login", "/auth/register")

app = FastAPI(
    title="Passenger Flow Predictor API",
    description="AirHack 2026 — XGBoost-powered check-in demand forecasting + Mobile Employee Alerts",
    version="1.0.0",
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Reject requests missing a valid X-API-Key header (except public endpoints)."""
    if not _RAW_API_KEY:  # key not configured → open (dev mode)
        return await call_next(request)
    path = request.url.path
    if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)
    provided = request.headers.get("X-API-Key", "")
    provided_hash = hashlib.new(_KEY_HASH_ALGO, provided.encode()).hexdigest()
    if provided_hash != _STORED_KEY_HASH:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)

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
app.include_router(security_router)
app.include_router(gate_router)
app.include_router(arrivals_router)
app.include_router(departures_gate_router)
if _sensor_available:
    app.include_router(sensor_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "passenger-flow-predictor"}
