"""
AquaMediAI — Scenario Routes
===============================

Phase 8: Exposes the full AquaMediAI pipeline through FastAPI endpoints.

Primary endpoint: POST /api/v1/scenarios/run
This is the main end-to-end pipeline endpoint.

Design
------
- Routes are THIN — they validate input, call ScenarioService, and return output.
- No computational logic lives in routes.
- All domain logic is delegated to existing Phase 1–7 implementations.
- Error handling returns structured JSON errors.

DISCLAIMER: All data processed is SYNTHETIC.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_expert, require_farmer_or_expert

from app.schemas.api_models import (
    AllocationRequest,
    AllocationResponse,
    ConflictRequest,
    ErrorResponse,
    NegotiationRequest,
    NegotiationResponse,
    PredictionBatchRequest,
    PredictionBatchResponse,
    PredictionRequest,
    PredictionResponse,
    ScenarioConflictReportResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
    ScenarioType,
)
from app.services.scenario_service import ScenarioService, prediction_to_dict

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy-init service (avoids import-time DB connection)
_service: ScenarioService | None = None


def _get_service() -> ScenarioService:
    global _service
    if _service is None:
        _service = ScenarioService()
    return _service


@router.get(
    "/predictions/quick-et0",
    tags=["Predictions"],
    summary="Compute standardized FAO-56 Penman-Monteith reference ET0",
    description="Calculates standard FAO-56 ET0 (mm/day) using Penman-Monteith physical equations.",
)
def compute_quick_et0(
    temp: float = Query(..., ge=-50.0, le=60.0, description="Air temperature (C)"),
    humidity: float = Query(60.0, ge=0.0, le=100.0, description="Relative humidity (%)"),
    wind_speed: float = Query(2.0, ge=0.0, le=50.0, description="Wind speed (m/s)"),
    solar_radiation: float = Query(18.0, ge=0.0, le=40.0, description="Solar radiation (MJ/m2/day)"),
    elevation: float = Query(540.0, ge=-500.0, le=9000.0, description="Elevation (m)"),
    lat: float = Query(19.0948, ge=-90.0, le=90.0, description="Latitude"),
    day_of_year: int = Query(180, ge=1, le=366, description="Day of year"),
    _identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    from app.data.fao56_penman_monteith import calculate_fao56_et0

    try:
        t_min = max(0.0, temp - 5.0)
        t_max = temp + 5.0
        et0 = calculate_fao56_et0(
            lat_deg=lat,
            day_of_year=day_of_year,
            t_min=t_min,
            t_max=t_max,
            t_mean=temp,
            rh_mean=humidity,
            wind_2m=wind_speed,
            rs_mj=solar_radiation,
            elevation_m=elevation,
        )
        return {
            "et0_mm_day": round(et0, 2),
            "method": "FAO-56 Penman-Monteith",
            "inputs": {
                "temperature_c": temp,
                "humidity_pct": humidity,
                "wind_speed_ms": wind_speed,
                "solar_radiation_mj": solar_radiation,
                "elevation_m": elevation,
                "latitude": lat,
                "day_of_year": day_of_year,
            },
            "scientific_reference": "FAO Irrigation and Drainage Paper No. 56",
            "disclaimer": "Physical reference evapotranspiration calculated via FAO-56 Penman-Monteith formulation.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "et0_calculation_error", "detail": str(exc), "status_code": 500},
        )


@router.post(
    "/scenarios/run",
    response_model=ScenarioRunResponse,
    tags=["Scenarios"],
    summary="Run full AquaMediAI pipeline",
    description=(
        "Execute the complete AquaMediAI pipeline: synthetic data generation → "
        "ML water demand prediction → FarmerAgent construction → conflict detection → "
        "LP-based water allocation → multi-agent negotiation → explainability. "
        "Returns structured results from all pipeline phases."
    ),
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal pipeline error"},
    },
)
def run_scenario(
    request: ScenarioRunRequest,
    identity: Dict[str, Any] = Depends(require_expert),
) -> Dict[str, Any]:
    """
    Run the full AquaMediAI pipeline.

    This is the primary endpoint that orchestrates all phases.
    Restricted to verified Agricultural Experts.
    """
    try:
        service = _get_service()
        result = service.run_scenario(
            scenario_type=request.scenario_type.value,
            n_farmers=request.n_farmers,
            seed=request.seed,
            model_name=request.model_name,
            available_water_override_m3=request.available_water_override_m3,
        )
        return result
    except FileNotFoundError as exc:
        logger.error("Model artifacts not found: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "model_artifacts_missing",
                "detail": str(exc),
                "status_code": 503,
            },
        )
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "detail": str(exc),
                "status_code": 422,
            },
        )
    except Exception as exc:
        logger.error("Pipeline error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "pipeline_error",
                "detail": f"An internal error occurred: {type(exc).__name__}",
                "status_code": 500,
            },
        )


# ─── Prediction Endpoints ────────────────────────────────────────────────────

@router.post(
    "/predictions",
    response_model=PredictionResponse,
    tags=["Predictions"],
    summary="Predict water demand for a single farmer",
    responses={500: {"model": ErrorResponse}},
)
def predict_single(
    request: PredictionRequest,
    identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    """Run ML prediction for a single farmer. Permitted for Farmers and Experts."""
    try:
        service = _get_service()
        result = service.predict_single(
            farmer_data=request.farmer_data.model_dump(),
            model_name=request.model_name,
        )
        return prediction_to_dict(result, request.farmer_data.farmer_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail={"error": "model_missing", "detail": str(exc), "status_code": 503})
    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "prediction_error", "detail": str(exc), "status_code": 500})


@router.post(
    "/predictions/batch",
    response_model=PredictionBatchResponse,
    tags=["Predictions"],
    summary="Batch predict water demand",
)
def predict_batch(
    request: PredictionBatchRequest,
    identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    """Run ML predictions for multiple farmers. Permitted for Farmers and Experts."""
    try:
        service = _get_service()
        results = service.predict_batch(
            farmers_data=[fd.model_dump() for fd in request.farmers],
            model_name=request.model_name,
        )
        predictions = [
            prediction_to_dict(r, request.farmers[i].farmer_id)
            for i, r in enumerate(results)
        ]
        return {"predictions": predictions, "count": len(predictions)}
    except Exception as exc:
        logger.error("Batch prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "prediction_error", "detail": str(exc), "status_code": 500})


# ─── Conflict Endpoint ───────────────────────────────────────────────────────

@router.post(
    "/conflicts",
    response_model=ScenarioConflictReportResponse,
    tags=["Conflicts"],
    summary="Detect water-sharing conflicts",
)
def detect_conflicts(
    request: ConflictRequest,
    identity: Dict[str, Any] = Depends(require_expert),
) -> Dict[str, Any]:
    """Run conflict detection on a generated scenario. Restricted to verified Agricultural Experts."""
    try:
        service = _get_service()
        return service.detect_conflicts(
            scenario_type=request.scenario_type.value,
            n_farmers=request.n_farmers,
            seed=request.seed,
            model_name=request.model_name,
            available_water_override_m3=request.available_water_override_m3,
        )
    except Exception as exc:
        logger.error("Conflict detection error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "conflict_error", "detail": str(exc), "status_code": 500})


# ─── Allocation Endpoint ─────────────────────────────────────────────────────

@router.post(
    "/allocations",
    response_model=AllocationResponse,
    tags=["Allocation"],
    summary="Run LP water allocation",
)
def run_allocation(
    request: AllocationRequest,
    identity: Dict[str, Any] = Depends(require_expert),
) -> Dict[str, Any]:
    """Run LP-based water allocation on a generated scenario. Restricted to verified Agricultural Experts."""
    try:
        service = _get_service()
        return service.run_allocation(
            scenario_type=request.scenario_type.value,
            n_farmers=request.n_farmers,
            seed=request.seed,
            model_name=request.model_name,
            available_water_override_m3=request.available_water_override_m3,
        )
    except Exception as exc:
        logger.error("Allocation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "allocation_error", "detail": str(exc), "status_code": 500})


# ─── Negotiation Endpoint ────────────────────────────────────────────────────

@router.post(
    "/negotiations",
    response_model=NegotiationResponse,
    tags=["Negotiation"],
    summary="Run multi-agent negotiation",
)
def run_negotiation(
    request: NegotiationRequest,
    identity: Dict[str, Any] = Depends(require_expert),
) -> Dict[str, Any]:
    """Run the full negotiation pipeline on a generated scenario. Restricted to verified Agricultural Experts."""
    try:
        service = _get_service()
        return service.run_negotiation(
            scenario_type=request.scenario_type.value,
            n_farmers=request.n_farmers,
            seed=request.seed,
            model_name=request.model_name,
            available_water_override_m3=request.available_water_override_m3,
            max_rounds=request.max_rounds,
            acceptance_threshold=request.acceptance_threshold,
            rejection_threshold=request.rejection_threshold,
        )
    except Exception as exc:
        logger.error("Negotiation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "negotiation_error", "detail": str(exc), "status_code": 500})
