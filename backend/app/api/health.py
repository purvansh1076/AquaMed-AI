"""
AquaMediAI — Health & System Routes
=====================================

Provides GET /api/v1/health and readiness endpoints.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.version import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    pipeline: str
    disclaimer: str


def _readiness() -> bool:
    model_dir = get_settings().model_dir_path
    return (
        (model_dir / "encoders.joblib").exists()
        or (model_dir / "rf_model.joblib").exists()
        or (model_dir / "xgb_model.joblib").exists()
    )


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> Dict[str, Any]:
    pipeline_ok = _readiness()
    status_code = 200 if pipeline_ok else 503
    body = {
        "status": "healthy" if pipeline_ok else "not_ready",
        "service": "AquaMediAI",
        "version": __version__,
        "pipeline": "available" if pipeline_ok else "degraded",
        "disclaimer": (
            "All data in this system is synthetically generated for "
            "academic demonstration purposes. No real farmer data is used."
        ),
    }
    if not pipeline_ok:
        return JSONResponse(status_code=503, content=body)
    return body


@router.get("/health/ready", tags=["System"])
def readiness_check() -> JSONResponse:
    pipeline_ok = _readiness()
    if not pipeline_ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": "Model artifacts not available.", "status_code": 503},
        )
    return JSONResponse(status_code=200, content={"status": "ready", "version": __version__})
