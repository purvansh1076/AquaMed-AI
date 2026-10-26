"""
AquaMediAI — Pydantic API Schemas
===================================

Request and response models for the Phase 8 FastAPI integration layer.

All schemas are JSON-serialisable.  No domain objects leak through the API.
The schemas validate input and structure output for the future React frontend.

DISCLAIMER: All data processed through these schemas is SYNTHETIC.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class ScenarioType(str, Enum):
    """Valid scenario types matching SyntheticDataGenerator.SCENARIO_TYPES."""
    NORMAL_WATER = "normal_water"
    MODERATE_SHORTAGE = "moderate_shortage"
    SEVERE_SHORTAGE = "severe_shortage"
    SUDDEN_RAINFALL = "sudden_rainfall"
    CANAL_REDUCTION = "canal_reduction"
    SIMULTANEOUS_DEMAND = "simultaneous_demand"
    HIGH_URGENCY_FARMER = "high_urgency_farmer"
    FLEXIBLE_FARMER = "flexible_farmer"


# ─── Request Models ──────────────────────────────────────────────────────────

class ScenarioRunRequest(BaseModel):
    """
    Request body for POST /api/v1/scenarios/run.

    Executes the full pipeline: data generation → ML prediction → agents →
    conflict detection → LP allocation → negotiation → explainability.
    """
    scenario_type: ScenarioType = Field(
        ...,
        description="Type of synthetic scenario to generate.",
    )
    n_farmers: int = Field(
        default=4,
        ge=2,
        le=20,
        description="Number of farmers in the scenario (2–20).",
    )
    seed: int = Field(
        default=42,
        ge=0,
        description="Random seed for reproducible scenario generation.",
    )
    model_name: str = Field(
        default="XGBoost",
        description="ML model to use: 'XGBoost' or 'RandomForest'.",
    )
    available_water_override_m3: Optional[float] = Field(
        default=None,
        ge=0.0,
        description=(
            "Override the scenario-generated available water (m³). "
            "If None, uses the scenario's generated supply."
        ),
    )


class FarmerInputData(BaseModel):
    """
    Raw farmer data for prediction endpoint.
    Same schema as WaterDemandPredictor.predict_single() input dict.
    """
    farmer_id: str = Field(..., min_length=1, description="Unique farmer ID.")
    crop_type: str = Field(..., description="Crop type (e.g., 'wheat', 'rice').")
    soil_type: str = Field(default="loam", description="Soil type.")
    growth_stage: str = Field(default="vegetative", description="Growth stage.")
    season: str = Field(default="kharif", description="Season.")
    farm_area_hectares: float = Field(..., gt=0, description="Farm area in hectares.")
    et0_mm_per_day: float = Field(..., gt=0, description="Reference evapotranspiration.")
    kc_value: float = Field(..., gt=0, description="Crop coefficient.")
    etc_mm_per_day: float = Field(..., gt=0, description="Crop evapotranspiration.")
    soil_whc_mm_per_m: float = Field(default=125.0, ge=0)
    preferred_start_hour: int = Field(default=6, ge=0, le=23)
    irrigation_window_hours: int = Field(default=4, ge=1, le=18)
    flexibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    urgency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    crop_stress_index: float = Field(default=0.5, ge=0.0, le=1.0)
    temperature_celsius: float = Field(default=28.0)
    humidity_percent: float = Field(default=60.0, ge=0.0, le=100.0)
    rainfall_mm: float = Field(default=0.0, ge=0.0)
    rainfall_forecast_mm: Optional[float] = Field(default=None, ge=0.0, description="Forecast rainfall for forward morning scheduling.")
    rainfall_observed_mm: Optional[float] = Field(default=None, ge=0.0, description="Observed rainfall for historical completed day accounting.")
    rainfall_input_mode: Optional[str] = Field(default=None, description="Input mode: 'observed_historical', 'forecast_forward', or 'fallback_antecedent'.")


class PredictionRequest(BaseModel):
    """Request for single prediction: POST /api/v1/predictions."""
    farmer_data: FarmerInputData
    model_name: str = Field(default="XGBoost", description="Model name.")


class PredictionBatchRequest(BaseModel):
    """Request for batch predictions: POST /api/v1/predictions/batch."""
    farmers: List[FarmerInputData] = Field(..., min_length=1, max_length=50)
    model_name: str = Field(default="XGBoost")


class ConflictRequest(BaseModel):
    """Request for conflict detection: POST /api/v1/conflicts."""
    scenario_type: ScenarioType
    n_farmers: int = Field(default=4, ge=2, le=20)
    seed: int = Field(default=42, ge=0)
    model_name: str = Field(default="XGBoost")
    available_water_override_m3: Optional[float] = Field(default=None, ge=0.0)


class AllocationRequest(BaseModel):
    """Request for LP allocation: POST /api/v1/allocations."""
    scenario_type: ScenarioType
    n_farmers: int = Field(default=4, ge=2, le=20)
    seed: int = Field(default=42, ge=0)
    model_name: str = Field(default="XGBoost")
    available_water_override_m3: Optional[float] = Field(default=None, ge=0.0)


class NegotiationRequest(BaseModel):
    """Request for negotiation: POST /api/v1/negotiations."""
    scenario_type: ScenarioType
    n_farmers: int = Field(default=4, ge=2, le=20)
    seed: int = Field(default=42, ge=0)
    model_name: str = Field(default="XGBoost")
    available_water_override_m3: Optional[float] = Field(default=None, ge=0.0)
    max_rounds: int = Field(default=5, ge=1, le=20)
    acceptance_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    rejection_threshold: float = Field(default=0.35, ge=0.0, le=1.0)


# ─── Response Models ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response for GET /api/v1/health."""
    status: str
    service: str
    version: str
    pipeline: str
    disclaimer: str


class PredictionResponse(BaseModel):
    """Response for prediction endpoint."""
    farmer_id: Optional[str]
    predicted_water_demand_m3: float
    model_name: str
    model_version: str
    warning: Optional[str]
    input_summary: Dict[str, Any]
    shadow_agronomic_estimate_m3: Optional[float] = None
    shadow_comparison: Optional[Dict[str, Any]] = None
    shadow_candidate_v3_estimate_m3: Optional[float] = None
    shadow_candidate_v3_comparison: Optional[Dict[str, Any]] = None


class PredictionBatchResponse(BaseModel):
    """Response for batch prediction endpoint."""
    predictions: List[PredictionResponse]
    count: int


class FarmerAllocationResponse(BaseModel):
    """Per-farmer allocation in API response."""
    farmer_id: str
    allocated_water_m3: float
    predicted_demand_m3: float
    minimum_requirement_m3: float
    maximum_requirement_m3: float
    unmet_demand_m3: float
    minimum_shortfall_m3: float
    satisfaction_ratio: float
    urgency: float
    crop_sensitivity: float
    growth_stage: str
    crop: str
    constraint_status: str


class ConstraintVerificationResponse(BaseModel):
    """Post-solve constraint verification."""
    is_valid: bool
    total_water_ok: bool
    non_negative_ok: bool
    maximum_ok: bool
    no_nan_ok: bool
    all_farmers_present: bool
    violations: List[str]


class AllocationResponse(BaseModel):
    """LP allocation result."""
    scenario_id: str
    solver_status: str
    objective_value: float
    allocation_method: str
    available_water_m3: float
    total_demand_m3: float
    total_allocated_m3: float
    remaining_water_m3: float
    utilization: float
    fairness_score: float
    average_satisfaction: float
    total_unmet_demand_m3: float
    total_minimum_shortfall_m3: float
    minimum_requirements_feasible: bool
    n_farmers: int
    solver_wall_time_ms: float
    verification: ConstraintVerificationResponse
    allocations: List[FarmerAllocationResponse]


class FarmerResponseModel(BaseModel):
    """Per-farmer negotiation response."""
    farmer_id: str
    allocation_m3: float
    utility: float
    batna_utility: float
    surplus: float
    response_type: str
    is_batna_protected: bool
    satisfaction_ratio: float
    minimum_met: bool
    reason: str
    round_number: int


class ConcessionResponse(BaseModel):
    """Negotiation concession record."""
    farmer_id: str
    round_number: int
    previous_ask_m3: float
    new_ask_m3: float
    concession_amount_m3: float
    concession_ratio: float
    flexibility_factor: float
    urgency_factor: float
    reason: str


class AgreementResponse(BaseModel):
    """Final negotiation agreement."""
    agreement_id: str
    session_id: str
    final_allocation: Dict[str, float]
    participating_farmers: List[str]
    final_utilities: Dict[str, float]
    batna_utilities: Dict[str, float]
    final_surplus: Dict[str, float]
    concessions: List[ConcessionResponse]
    fairness_score: float
    water_utilization: float
    negotiation_rounds: int
    agreement_status: str
    termination_reason: str
    round_fairness_history: List[float]
    round_nash_history: List[float]
    is_physically_valid: bool


class NegotiationRoundResponse(BaseModel):
    """Single negotiation round summary."""
    round_number: int
    n_accepting: int
    n_requesting_change: int
    n_rejecting: int
    nash_objective: float
    fairness_score: float
    solver_status: str


class NegotiationResponse(BaseModel):
    """Negotiation session result."""
    session_id: str
    scenario_id: str
    n_rounds: int
    agreement_status: str
    termination_reason: str
    initial_allocation: Dict[str, float]
    best_allocation: Dict[str, float]
    rounds: List[NegotiationRoundResponse]
    agreement: Optional[AgreementResponse]


class ConflictReportResponse(BaseModel):
    """Single conflict report."""
    conflict_id: str
    conflict_type: str
    severity: str
    severity_score: float
    involved_farmer_ids: List[str]
    available_water_m3: float
    total_demand_m3: float
    resource_gap_m3: float
    explanation: str


class ScenarioConflictReportResponse(BaseModel):
    """Full conflict report for a scenario."""
    scenario_id: str
    n_farmers: int
    total_demand_m3: float
    available_water_m3: float
    resource_gap_m3: float
    overall_shortage_ratio: float
    total_conflicts: int
    highest_severity: str
    conflicts: List[ConflictReportResponse]


class ExplanationResponse(BaseModel):
    """Final decision explanation (Phase 7)."""
    scenario_id: str
    summary: str
    prediction_explanations: List[Dict[str, Any]]
    conflict_explanations: List[Dict[str, Any]]
    allocation_explanations: List[Dict[str, Any]]
    fairness_explanation: Optional[Dict[str, Any]]
    constraint_explanations: List[Dict[str, Any]]
    negotiation_explanation: Optional[Dict[str, Any]]
    final_allocation: Dict[str, float]
    final_utilities: Dict[str, float]
    agreement_status: Optional[str]
    all_reason_codes: List[str]
    unresolved_issues: List[str]
    data_disclaimer: str


class ScenarioRunResponse(BaseModel):
    """
    Response for POST /api/v1/scenarios/run.

    Contains the full pipeline output with all phase results.
    """
    scenario_id: str
    status: str
    scenario_type: str
    n_farmers: int
    available_water_m3: float
    total_demand_m3: float
    predictions: List[PredictionResponse]
    farmers: List[Dict[str, Any]]
    conflicts: ScenarioConflictReportResponse
    initial_allocation: AllocationResponse
    negotiation: Optional[NegotiationResponse]
    final_allocation: AllocationResponse
    explanations: ExplanationResponse
    final_decision: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Structured error response."""
    error: str
    detail: str
    status_code: int
