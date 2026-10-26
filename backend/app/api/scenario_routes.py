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
import traceback
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

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
from app.services.scenario_service import ScenarioService

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy-init service (avoids import-time DB connection)
_service: ScenarioService | None = None


def _get_service() -> ScenarioService:
    global _service
    if _service is None:
        _service = ScenarioService()
    return _service


# ─── Primary Endpoint ─────────────────────────────────────────────────────────

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
def run_scenario(request: ScenarioRunRequest) -> Dict[str, Any]:
    """
    Run the full AquaMediAI pipeline.

    This is the primary endpoint that orchestrates all phases.
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
def predict_single(request: PredictionRequest) -> Dict[str, Any]:
    """Run ML prediction for a single farmer."""
    try:
        service = _get_service()
        result = service.predict_single(
            farmer_data=request.farmer_data.model_dump(),
            model_name=request.model_name,
        )
        return {
            "farmer_id": request.farmer_data.farmer_id,
            "predicted_water_demand_m3": round(result.predicted_water_demand_m3, 2),
            "model_name": result.model_name,
            "model_version": result.model_version,
            "warning": result.warning,
            "input_summary": result.input_summary,
            "shadow_agronomic_estimate_m3": (
                round(result.shadow_agronomic_estimate_m3, 2)
                if result.shadow_agronomic_estimate_m3 is not None
                else None
            ),
            "shadow_comparison": result.shadow_comparison,
            "shadow_candidate_v3_estimate_m3": (
                round(result.shadow_candidate_v3_estimate_m3, 2)
                if result.shadow_candidate_v3_estimate_m3 is not None
                else None
            ),
            "shadow_candidate_v3_comparison": result.shadow_candidate_v3_comparison,
        }
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
def predict_batch(request: PredictionBatchRequest) -> Dict[str, Any]:
    """Run ML predictions for multiple farmers."""
    try:
        service = _get_service()
        results = service.predict_batch(
            farmers_data=[fd.model_dump() for fd in request.farmers],
            model_name=request.model_name,
        )
        predictions = [
            {
                "farmer_id": request.farmers[i].farmer_id,
                "predicted_water_demand_m3": round(r.predicted_water_demand_m3, 2),
                "model_name": r.model_name,
                "model_version": r.model_version,
                "warning": r.warning,
                "input_summary": r.input_summary,
                "shadow_agronomic_estimate_m3": (
                    round(r.shadow_agronomic_estimate_m3, 2)
                    if r.shadow_agronomic_estimate_m3 is not None
                    else None
                ),
                "shadow_comparison": r.shadow_comparison,
                "shadow_candidate_v3_estimate_m3": (
                    round(r.shadow_candidate_v3_estimate_m3, 2)
                    if r.shadow_candidate_v3_estimate_m3 is not None
                    else None
                ),
                "shadow_candidate_v3_comparison": r.shadow_candidate_v3_comparison,
            }
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
def detect_conflicts(request: ConflictRequest) -> Dict[str, Any]:
    """Run conflict detection on a generated scenario."""
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
def run_allocation(request: AllocationRequest) -> Dict[str, Any]:
    """Run LP-based water allocation on a generated scenario."""
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
def run_negotiation(request: NegotiationRequest) -> Dict[str, Any]:
    """Run the full negotiation pipeline on a generated scenario."""
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
