"""
AquaMediAI - Explainability Types
===================================

Structured data types for Phase 7 Explainability Layer.

These types carry explanation payloads derived from ACTUAL computational
results produced by Phases 2-6.  They are READ-ONLY consumers -- they
never modify predictions, allocations, or negotiation outcomes.

Design Notes
------------
- All types are pure Python dataclasses -- no ORM, no FastAPI dependency.
- All types are serialisable to dict/JSON via .as_dict().
- Types follow the same conventions used throughout Phases 2-6.
- The explanations describe computed results; they do NOT generate decisions.

DISCLAIMER: All explanations are derived from SYNTHETIC agronomic data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# --- Reason codes ---

class ReasonCode(str, Enum):
    """
    Structured reason codes for allocation and negotiation decisions.

    A reason code is ONLY emitted when the actual data supports it.
    The same inputs always produce the same set of codes (deterministic).

    Threshold notes (HIGH_URGENCY / HIGH_CROP_SENSITIVITY)
    -------------------------------------------------------
    These codes use thresholds that are EXPLAINABILITY LAYER CONVENTIONS,
    not LP optimizer cutoffs. The LP objective uses urgency and
    crop_sensitivity as continuous weights -- it does NOT apply a binary
    threshold. The threshold values (0.70 for both) are re-used from
    Phase 4 ConflictDetector constants (HIGH_STRESS_URGENCY_THRESHOLD,
    HIGH_STRESS_SENSITIVITY_THRESHOLD) for project-wide consistency.

    Causality note
    --------------
    FAIRNESS_ADJUSTMENT is retained as an enum member for future use only.
    It must NEVER be emitted to describe a current allocation because
    Jain's Fairness Index is a post-hoc measurement on the result --
    it is NOT a term in the Phase 5 LP objective and did NOT cause any
    individual farmer allocation.
    """
    RESOURCE_SHORTAGE           = "RESOURCE_SHORTAGE"
    WATER_SURPLUS               = "WATER_SURPLUS"
    HIGH_URGENCY                = "HIGH_URGENCY"
    HIGH_CROP_SENSITIVITY       = "HIGH_CROP_SENSITIVITY"
    MINIMUM_REQUIREMENT         = "MINIMUM_REQUIREMENT"
    MAXIMUM_REQUIREMENT         = "MAXIMUM_REQUIREMENT"
    CANAL_CAPACITY              = "CANAL_CAPACITY"
    WINDOW_CONFLICT             = "WINDOW_CONFLICT"
    FAIRNESS_ADJUSTMENT         = "FAIRNESS_ADJUSTMENT"
    NEGOTIATION_CONCESSION      = "NEGOTIATION_CONCESSION"
    BATNA_PROTECTION            = "BATNA_PROTECTION"
    UNMET_DEMAND                = "UNMET_DEMAND"
    FULL_DEMAND_SATISFACTION    = "FULL_DEMAND_SATISFACTION"


class ContributionDirection(str, Enum):
    """Direction of a SHAP feature contribution."""
    INCREASES  = "increases"
    DECREASES  = "decreases"
    NEGLIGIBLE = "negligible"


class ConstraintStatus(str, Enum):
    """Status of a constraint after the LP solve."""
    SATISFIED      = "satisfied"
    VIOLATED       = "violated"
    RELAXED        = "relaxed"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class FeatureContributionExplanation:
    """Human-readable explanation for a single SHAP feature contribution."""
    feature: str
    raw_value: float
    shap_value: float
    direction: ContributionDirection
    abs_shap: float
    rank: int
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "raw_value": round(self.raw_value, 6),
            "shap_value": round(self.shap_value, 6),
            "direction": self.direction.value,
            "abs_shap": round(self.abs_shap, 6),
            "rank": self.rank,
            "rationale": self.rationale,
        }


@dataclass
class PredictionExplanation:
    """
    Explanation for an ML water demand prediction.

    Attributes
    ----------
    farmer_id : str or None
    predicted_demand_m3 : float
    model_name : str
    model_version : str
    base_value : float
        SHAP base value (mean model output over background data).
    top_contributors : list of FeatureContributionExplanation
    positive_contributors : list of FeatureContributionExplanation
    negative_contributors : list of FeatureContributionExplanation
    all_features : list of FeatureContributionExplanation
    shap_available : bool
    summary : str
    data_disclaimer : str
    """
    farmer_id: Optional[str]
    predicted_demand_m3: float
    model_name: str
    model_version: str
    base_value: float
    top_contributors: List[FeatureContributionExplanation]
    positive_contributors: List[FeatureContributionExplanation]
    negative_contributors: List[FeatureContributionExplanation]
    all_features: List[FeatureContributionExplanation]
    shap_available: bool
    summary: str
    data_disclaimer: str = (
        "Prediction based on synthetic agronomic data (FAO-56 ETo x Kc x area). "
        "Not derived from real farmer records."
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "predicted_demand_m3": round(self.predicted_demand_m3, 4),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "base_value": round(self.base_value, 4),
            "shap_available": self.shap_available,
            "top_contributors": [c.as_dict() for c in self.top_contributors],
            "positive_contributors": [c.as_dict() for c in self.positive_contributors],
            "negative_contributors": [c.as_dict() for c in self.negative_contributors],
            "all_features": [c.as_dict() for c in self.all_features],
            "summary": self.summary,
            "data_disclaimer": self.data_disclaimer,
        }


@dataclass
class ConstraintExplanation:
    """Explanation of a single LP allocation constraint."""
    constraint_name: str
    actual_value: float
    limit: float
    status: ConstraintStatus
    is_hard: bool
    rationale: str
    farmer_id: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "constraint_name": self.constraint_name,
            "actual_value": round(self.actual_value, 4),
            "limit": round(self.limit, 4),
            "status": self.status.value,
            "is_hard": self.is_hard,
            "farmer_id": self.farmer_id,
            "rationale": self.rationale,
        }


@dataclass
class AllocationExplanation:
    """
    Explanation of the LP allocation for a single farmer.

    Attributes
    ----------
    farmer_id : str
    predicted_demand_m3 : float
    allocated_m3 : float
    unmet_demand_m3 : float
    minimum_requirement_m3 : float
    maximum_requirement_m3 : float
    satisfaction_ratio : float
    urgency : float
    crop_sensitivity : float
    growth_stage : str
    crop : str
    constraint_status : str
    reason_codes : list of ReasonCode
    constraint_explanations : list of ConstraintExplanation
    rationale : str
    """
    farmer_id: str
    predicted_demand_m3: float
    allocated_m3: float
    unmet_demand_m3: float
    minimum_requirement_m3: float
    maximum_requirement_m3: float
    satisfaction_ratio: float
    urgency: float
    crop_sensitivity: float
    growth_stage: str
    crop: str
    constraint_status: str
    reason_codes: List[ReasonCode]
    constraint_explanations: List[ConstraintExplanation]
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "predicted_demand_m3": round(self.predicted_demand_m3, 2),
            "allocated_m3": round(self.allocated_m3, 2),
            "unmet_demand_m3": round(self.unmet_demand_m3, 2),
            "minimum_requirement_m3": round(self.minimum_requirement_m3, 2),
            "maximum_requirement_m3": round(self.maximum_requirement_m3, 2),
            "satisfaction_ratio": round(self.satisfaction_ratio, 4),
            "urgency": round(self.urgency, 4),
            "crop_sensitivity": round(self.crop_sensitivity, 4),
            "growth_stage": self.growth_stage,
            "crop": self.crop,
            "constraint_status": self.constraint_status,
            "reason_codes": [r.value for r in self.reason_codes],
            "constraint_explanations": [c.as_dict() for c in self.constraint_explanations],
            "rationale": self.rationale,
        }


@dataclass
class FairnessExplanation:
    """
    Explanation of the Jain's Fairness Index result for the allocation.

    IMPORTANT: This explains the measured fairness value. It does NOT
    claim fairness directly caused any individual allocation (the LP
    objective does not include fairness as a direct optimisation term).
    """
    fairness_score: float
    n_farmers: int
    satisfaction_ratios: Dict[str, float]
    average_satisfaction: float
    is_minimum_requirements_feasible: bool
    rationale: str
    note: str = (
        "Jain's Fairness Index was measured on the allocation result. "
        "The LP optimisation objective did not include fairness as a direct term; "
        "fairness emerged from the weighted-demand objective."
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "fairness_score": round(self.fairness_score, 4),
            "n_farmers": self.n_farmers,
            "satisfaction_ratios": {
                k: round(v, 4) for k, v in self.satisfaction_ratios.items()
            },
            "average_satisfaction": round(self.average_satisfaction, 4),
            "is_minimum_requirements_feasible": self.is_minimum_requirements_feasible,
            "rationale": self.rationale,
            "note": self.note,
        }


@dataclass
class ConflictExplanationEntry:
    """Explanation of a single ConflictReport from Phase 4."""
    conflict_id: str
    conflict_type: str
    severity: str
    severity_score: float
    involved_farmer_ids: List[str]
    available_water_m3: float
    total_demand_m3: float
    total_minimum_requirement_m3: float
    resource_gap_m3: float
    minimum_requirement_gap_m3: float
    evidence: Dict[str, Any]
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "severity_score": round(self.severity_score, 4),
            "involved_farmer_ids": self.involved_farmer_ids,
            "available_water_m3": round(self.available_water_m3, 2),
            "total_demand_m3": round(self.total_demand_m3, 2),
            "total_minimum_requirement_m3": round(self.total_minimum_requirement_m3, 2),
            "resource_gap_m3": round(self.resource_gap_m3, 2),
            "minimum_requirement_gap_m3": round(self.minimum_requirement_gap_m3, 2),
            "evidence": self.evidence,
            "rationale": self.rationale,
        }


@dataclass
class BATNAExplanation:
    """Explanation of a farmer's BATNA utility from Phase 3/6."""
    farmer_id: str
    batna_utility: float
    batna_allocation_m3: float
    negotiated_utility: Optional[float]
    negotiated_allocation_m3: Optional[float]
    is_above_batna: Optional[bool]
    surplus: Optional[float]
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "batna_utility": round(self.batna_utility, 4),
            "batna_allocation_m3": round(self.batna_allocation_m3, 2),
            "negotiated_utility": (
                round(self.negotiated_utility, 4)
                if self.negotiated_utility is not None else None
            ),
            "negotiated_allocation_m3": (
                round(self.negotiated_allocation_m3, 2)
                if self.negotiated_allocation_m3 is not None else None
            ),
            "is_above_batna": self.is_above_batna,
            "surplus": (
                round(self.surplus, 4) if self.surplus is not None else None
            ),
            "rationale": self.rationale,
        }


@dataclass
class ConcessionExplanation:
    """Explanation of a single computational concession from Phase 6."""
    farmer_id: str
    round_number: int
    previous_ask_m3: float
    new_ask_m3: float
    concession_amount_m3: float
    concession_ratio: float
    flexibility_factor: float
    urgency_factor: float
    reason: str
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "round_number": self.round_number,
            "previous_ask_m3": round(self.previous_ask_m3, 2),
            "new_ask_m3": round(self.new_ask_m3, 2),
            "concession_amount_m3": round(self.concession_amount_m3, 2),
            "concession_ratio": round(self.concession_ratio, 4),
            "flexibility_factor": round(self.flexibility_factor, 4),
            "urgency_factor": round(self.urgency_factor, 4),
            "reason": self.reason,
            "rationale": self.rationale,
        }


@dataclass
class NegotiationRoundExplanation:
    """Explanation of a single NegotiationRound from Phase 6."""
    round_number: int
    current_allocation: Dict[str, float]
    farmer_responses: List[Dict[str, Any]]
    utilities: Dict[str, float]
    batna_utilities: Dict[str, float]
    surpluses: Dict[str, float]
    n_accepting: int
    n_requesting_change: int
    n_rejecting: int
    nash_objective: float
    fairness_score: float
    proposed_changes: Dict[str, float]
    concession_explanations: List[ConcessionExplanation]
    solver_status: str
    outcome_rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "current_allocation": {k: round(v, 2) for k, v in self.current_allocation.items()},
            "farmer_responses": self.farmer_responses,
            "utilities": {k: round(v, 4) for k, v in self.utilities.items()},
            "batna_utilities": {k: round(v, 4) for k, v in self.batna_utilities.items()},
            "surpluses": {k: round(v, 4) for k, v in self.surpluses.items()},
            "n_accepting": self.n_accepting,
            "n_requesting_change": self.n_requesting_change,
            "n_rejecting": self.n_rejecting,
            "nash_objective": round(self.nash_objective, 6),
            "fairness_score": round(self.fairness_score, 4),
            "proposed_changes": {k: round(v, 2) for k, v in self.proposed_changes.items()},
            "concession_explanations": [c.as_dict() for c in self.concession_explanations],
            "solver_status": self.solver_status,
            "outcome_rationale": self.outcome_rationale,
        }


@dataclass
class NashObjectiveExplanation:
    """
    Explanation of the Nash-inspired objective used during negotiation.

    IMPORTANT: This is a Nash-bargaining-inspired heuristic, NOT a
    mathematically complete Nash Bargaining Solution.
    """
    formula: str
    floor_value: float
    final_value: float
    initial_value: Optional[float]
    trajectory: List[float]
    interpretation: str
    disclaimer: str = (
        "This is a Nash-bargaining-inspired utility optimization. "
        "It is NOT a mathematically complete Nash Bargaining Solution. "
        "It serves as a tractable heuristic for the mediator to evaluate "
        "whether a candidate allocation improves the joint outcome."
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "formula": self.formula,
            "floor_value": self.floor_value,
            "final_value": round(self.final_value, 6),
            "initial_value": (
                round(self.initial_value, 6) if self.initial_value is not None else None
            ),
            "trajectory": [round(v, 6) for v in self.trajectory],
            "interpretation": self.interpretation,
            "disclaimer": self.disclaimer,
        }


@dataclass
class NegotiationExplanation:
    """Complete explanation of a NegotiationSession from Phase 6."""
    session_id: str
    scenario_id: str
    farmer_ids: List[str]
    available_water_m3: float
    n_rounds: int
    agreement_status: str
    termination_reason: str
    round_explanations: List[NegotiationRoundExplanation]
    batna_explanations: List[BATNAExplanation]
    concession_explanations: List[ConcessionExplanation]
    nash_objective_explanation: NashObjectiveExplanation
    final_fairness_score: float
    final_water_utilization: float
    final_allocation: Dict[str, float]
    final_utilities: Dict[str, float]
    summary: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "farmer_ids": self.farmer_ids,
            "available_water_m3": round(self.available_water_m3, 2),
            "n_rounds": self.n_rounds,
            "agreement_status": self.agreement_status,
            "termination_reason": self.termination_reason,
            "round_explanations": [r.as_dict() for r in self.round_explanations],
            "batna_explanations": [b.as_dict() for b in self.batna_explanations],
            "concession_explanations": [c.as_dict() for c in self.concession_explanations],
            "nash_objective_explanation": self.nash_objective_explanation.as_dict(),
            "final_fairness_score": round(self.final_fairness_score, 4),
            "final_water_utilization": round(self.final_water_utilization, 4),
            "final_allocation": {k: round(v, 2) for k, v in self.final_allocation.items()},
            "final_utilities": {k: round(v, 4) for k, v in self.final_utilities.items()},
            "summary": self.summary,
        }


@dataclass
class FinalDecisionExplanation:
    """
    Unified explanation spanning the entire AquaMediAI pipeline.

    Combines prediction, conflict, allocation, constraint, fairness, and
    negotiation explanations into a single traceable document.

    All numerical values are derived from actual computational results.
    No values are invented or approximated.

    The counterfactual_baseline field is reserved for future Phase 8+
    what-if analysis; it accepts a dict of baseline result data alongside
    which a counterfactual can later be compared.
    """
    scenario_id: str
    summary: str
    prediction_explanations: List[PredictionExplanation]
    conflict_explanations: List[ConflictExplanationEntry]
    allocation_explanations: List[AllocationExplanation]
    fairness_explanation: Optional[FairnessExplanation]
    constraint_explanations: List[ConstraintExplanation]
    negotiation_explanation: Optional[NegotiationExplanation]
    final_allocation: Dict[str, float]
    final_utilities: Dict[str, float]
    agreement_status: Optional[str]
    all_reason_codes: List[ReasonCode]
    unresolved_issues: List[str]
    data_disclaimer: str = (
        "All results are derived from SYNTHETIC agronomic data. "
        "Not derived from real farmer records or real water bodies."
    )
    counterfactual_baseline: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "summary": self.summary,
            "prediction_explanations": [p.as_dict() for p in self.prediction_explanations],
            "conflict_explanations": [c.as_dict() for c in self.conflict_explanations],
            "allocation_explanations": [a.as_dict() for a in self.allocation_explanations],
            "fairness_explanation": (
                self.fairness_explanation.as_dict() if self.fairness_explanation else None
            ),
            "constraint_explanations": [c.as_dict() for c in self.constraint_explanations],
            "negotiation_explanation": (
                self.negotiation_explanation.as_dict()
                if self.negotiation_explanation else None
            ),
            "final_allocation": {k: round(v, 2) for k, v in self.final_allocation.items()},
            "final_utilities": {k: round(v, 4) for k, v in self.final_utilities.items()},
            "agreement_status": self.agreement_status,
            "all_reason_codes": [r.value for r in self.all_reason_codes],
            "unresolved_issues": self.unresolved_issues,
            "data_disclaimer": self.data_disclaimer,
            "counterfactual_baseline": self.counterfactual_baseline,
        }
