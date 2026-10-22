"""
AquaMediAI — FastAPI Application Entry Point
============================================
Registers routers, middleware, lifespan events, and health endpoints.
"""

from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import check_db_connection

# ─── Logging setup ────────────────────────────────────────────────────────────
settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown lifecycle handler.
    Creates required data directories on startup.
    """
    logger.info("AquaMediAI backend starting up (env=%s)", settings.app_env)

    # Ensure data directories exist
    for directory in [settings.model_dir_path, settings.data_dir_path]:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory exists: %s", directory)

    # Log DB connectivity (non-fatal if DB is not yet ready)
    if check_db_connection():
        logger.info("Database connection: OK")
    else:
        logger.warning(
            "Database connection: FAILED — "
            "run 'alembic upgrade head' and ensure PostgreSQL is running."
        )

    yield  # Application runs here

    logger.info("AquaMediAI backend shutting down.")


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AquaMediAI API",
    description=(
        "Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System. "
        "**IMPORTANT**: All data in this system is synthetically generated for "
        "academic demonstration purposes. No real farmer data is used."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── CORS Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
# Phase 8: FastAPI Integration Layer

from app.api.health import router as health_router
from app.api.scenario_routes import router as scenario_router

app.include_router(health_router, prefix="/api/v1", tags=["System"])
app.include_router(scenario_router, prefix="/api/v1", tags=["Pipeline"])


# ─── Core Endpoints ───────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check() -> JSONResponse:
    """
    Liveness / readiness probe.
    Returns system status and database connectivity.
    """
    db_ok = check_db_connection()
    status_code = 200 if db_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if db_ok else "degraded",
            "service": "AquaMediAI API",
            "version": "1.0.0",
            "environment": settings.app_env,
            "database": "connected" if db_ok else "unreachable",
            "disclaimer": (
                "All data is synthetically generated for academic purposes. "
                "No real farmer data is used."
            ),
        },
    )


@app.get("/", tags=["System"])
def root() -> dict:
    """Root endpoint — brief project description."""
    return {
        "project": "AquaMediAI",
        "tagline": "Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation",
        "docs": "/docs",
        "health": "/api/v1/health",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "version": "1.0.0",
        "api_base": "/api/v1",
        "disclaimer": (
            "All data in this system is synthetically generated for "
            "academic demonstration purposes. No real farmer data is used."
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=settings.app_debug)

