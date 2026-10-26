"""
AquaMediAI — Health & System Routes
=====================================

Provides GET /api/v1/health and system status endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    pipeline: str
    disclaimer: str


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> Dict[str, Any]:
    """
    Liveness / readiness probe.

    Returns system status and pipeline availability.
    Does NOT require a database connection.
    """
    # Check if model artifacts are available
    from app.config import get_settings
    model_dir = get_settings().model_dir_path
    pipeline_available = (model_dir / "encoders.joblib").exists()

    return {
        "status": "healthy",
        "service": "AquaMediAI",
        "version": "1.0.0",
        "pipeline": "available" if pipeline_available else "degraded",
        "disclaimer": (
            "All data in this system is synthetically generated for "
            "academic demonstration purposes. No real farmer data is used."
        ),
    }
