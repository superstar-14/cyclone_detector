"""
IMD Cyclone Detector – FastAPI Application

Main entrypoint for the backend API server.
"""
from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api import storms, layers, history, health, websocket_router, alerts, satellite


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with low-memory thread and GC tuning for Render."""
    import gc
    import asyncio
    import concurrent.futures

    # Restrict default thread pool to 4 workers (saves ~30-50MB RAM on container environments)
    try:
        loop = asyncio.get_running_loop()
        loop.set_default_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="cyclo_worker")
        )
    except Exception as e:
        logger.debug("ThreadPoolExecutor config note: %s", e)

    # Force initial garbage collection
    gc.collect()

    logger.info(
        "Starting IMD Cyclone Detector (DEMO_MODE=%s, ENV=%s, MEMORY_OPTIMIZED=true)",
        settings.DEMO_MODE,
        settings.APP_ENV,
    )
    yield
    gc.collect()
    logger.info("Shutting down IMD Cyclone Detector")


app = FastAPI(
    title="IMD Cyclone Detector API",
    description=(
        "Tropical Cyclone Identification, Classification & Prediction Platform "
        "for the North Indian Ocean. Ingests real-time satellite and environmental "
        "data, detects and tracks cyclones, and predicts track, intensity, and impact."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# CORS – allow frontend dev server and production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health Check (Render / Kubernetes zero-downtime monitoring) ──
@app.api_route("/healthz", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/api/healthz", methods=["GET", "HEAD"], tags=["Health"])
async def healthz():
    """Lightweight health check endpoint for Render zero-downtime monitoring."""
    return {
        "status": "ok",
        "service": "IMD Cyclone Detector",
        "demo_mode": settings.DEMO_MODE,
    }

# ── API Routes ──────────────────────────────────────────────
app.include_router(storms.router, prefix="/api/storms", tags=["Storms"])
app.include_router(layers.router, prefix="/api/layers", tags=["Map Layers"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Vulnerability Alerts"])
app.include_router(websocket_router.router, prefix="/ws", tags=["WebSocket"])
app.include_router(satellite.router, prefix="/api", tags=["Satellite"])

@app.get("/api/config", tags=["Config"])
async def get_config():
    """Public configuration for the frontend."""
    return {
        "demo_mode": settings.DEMO_MODE,
        "domain": {
            "lat_min": 0,
            "lat_max": 30,
            "lon_min": 45,
            "lon_max": 100,
        },
        "categories": [
            {
                "key": "LOW_PRESSURE",
                "label": "Low Pressure Area",
                "abbr": "LP",
                "min_kt": 0,
                "max_kt": 17,
                "color": "#808080",
            },
            {
                "key": "D",
                "label": "Depression",
                "abbr": "D",
                "min_kt": 17,
                "max_kt": 27,
                "color": "#5B9BD5",
            },
            {
                "key": "DD",
                "label": "Deep Depression",
                "abbr": "DD",
                "min_kt": 28,
                "max_kt": 33,
                "color": "#4472C4",
            },
            {
                "key": "CS",
                "label": "Cyclonic Storm",
                "abbr": "CS",
                "min_kt": 34,
                "max_kt": 47,
                "color": "#00B050",
            },
            {
                "key": "SCS",
                "label": "Severe Cyclonic Storm",
                "abbr": "SCS",
                "min_kt": 48,
                "max_kt": 63,
                "color": "#FFC000",
            },
            {
                "key": "VSCS",
                "label": "Very Severe Cyclonic Storm",
                "abbr": "VSCS",
                "min_kt": 64,
                "max_kt": 89,
                "color": "#FF6600",
            },
            {
                "key": "ESCS",
                "label": "Extremely Severe Cyclonic Storm",
                "abbr": "ESCS",
                "min_kt": 90,
                "max_kt": 119,
                "color": "#FF0000",
            },
            {
                "key": "SuCS",
                "label": "Super Cyclonic Storm",
                "abbr": "SuCS",
                "min_kt": 120,
                "max_kt": None,
                "color": "#990000",
            },
        ],
        "lead_times_hours": [0, 6, 12, 18, 24, 36, 48, 60, 72],
        "wind_thresholds_kt": [34, 50, 64],
    }


# ── Static SPA Serving (when built frontend is present) ──────
CANDIDATE_DIST_DIRS = [
    os.environ.get("FRONTEND_DIST"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "dist")),
    "/app/frontend/dist",
    "/app/dist",
]

FRONTEND_DIST = next(
    (d for d in CANDIDATE_DIST_DIRS if d and os.path.isdir(d) and os.path.isfile(os.path.join(d, "index.html"))),
    None,
)

if FRONTEND_DIST:
    logger.info("Serving built frontend SPA from %s", FRONTEND_DIST)
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.api_route("/", methods=["GET", "HEAD"], tags=["Root"], include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Exclude reserved routes from SPA fallback
        if full_path.startswith(("api", "ws", "docs", "redoc", "openapi.json", "healthz")):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/", tags=["Root"])
    async def root():
        """API root – basic info when frontend dist is not found."""
        return {
            "service": "IMD Cyclone Detector",
            "version": "0.1.0",
            "demo_mode": settings.DEMO_MODE,
            "docs": "/docs",
            "status": "operational",
        }
