"""
AquaMediAI — Agronomy, Weather & Diagnostic API Routes
======================================================
Exposes endpoints for:
1. Hyper-local weather telemetry and 7-day agricultural forecast.
2. Crop health diagnosis and stress screening.
3. Conformal prediction interval calculations for water demand.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import require_farmer_or_expert
from app.ml.conformal_predictor import conformal_predictor
from app.services.crop_health_service import crop_health_service
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agricultural Intelligence"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class DiagnosticRequest(BaseModel):
    crop_type: str = Field(..., description="Crop name (e.g. sugarcane, cotton, soybean, wheat)")
    symptom_key: str = Field(..., description="Observed symptom identifier")
    soil_moisture_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    growth_stage: Optional[str] = None


class ConformalIntervalRequest(BaseModel):
    predicted_demand_m3: float = Field(..., ge=0.0, description="Point water demand in m³")
    farm_area_ha: float = Field(1.0, ge=0.05, le=100.0, description="Farm area in hectares")
    growth_stage: str = Field("vegetative", description="Crop growth stage")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/weather/current",
    summary="Get current agro-meteorological telemetry",
    description="Returns real-time or cached weather conditions for Ahmednagar district with agricultural parameters.",
)
def get_current_weather(
    lat: float = Query(19.0948, description="Latitude"),
    lon: float = Query(74.7480, description="Longitude"),
) -> Dict[str, Any]:
    return weather_service.get_current_and_forecast(lat=lat, lon=lon)


@router.post(
    "/agronomy/diagnose",
    summary="Screen crop health symptoms",
    description="Agronomic diagnostic screening for crop deficiencies, disease symptoms, and moisture stress.",
)
def diagnose_crop_health(
    payload: DiagnosticRequest,
    identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    return crop_health_service.diagnose_symptoms(
        crop_type=payload.crop_type,
        symptom_key=payload.symptom_key,
        soil_moisture_pct=payload.soil_moisture_pct,
        growth_stage=payload.growth_stage,
    )


@router.post(
    "/predictions/conformal-interval",
    summary="Calculate conformal prediction interval for water demand",
    description="Produces mathematically guaranteed 90% confidence lower and upper bounds around predicted demand.",
)
def compute_conformal_interval(
    payload: ConformalIntervalRequest,
    identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    return conformal_predictor.predict_interval(
        point_prediction_m3=payload.predicted_demand_m3,
        farm_area_ha=payload.farm_area_ha,
        growth_stage=payload.growth_stage,
    )
