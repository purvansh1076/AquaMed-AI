"""
AquaMediAI - Allocation Explainer
===================================

Explains Phase 5 AllocationResult objects.

Design
------
This module reads ACTUAL AllocationResult data and converts it to structured
explanation types. It is READ-ONLY with respect to the allocation -- it never
modifies AllocationResult, FarmerAllocation, or any Phase 5 outputs.

Allocation Method Vocabulary
-----------------------------
The AllocationResult.allocation_method field records which algorithm was used:

    'lp_optimal'          -- GLOP LP solved, all minimum requirements
                             could be enforced as hard constraints
    'lp_relaxed'          -- GLOP LP solved, minimum requirements could
                             NOT all be met simultaneously so S1 was
                             converted to a penalty term
    'proportional_fallback' -- LP solver failed unexpectedly (ERROR/INFEASIBLE);
                               water distributed as demand_i / total_demand
    'empty'               -- No farmers (trivial result)

Rationale text MUST distinguish these cases. Proportional distribution language
is ONLY used when allocation_method == 'proportional_fallback'.

Reason Code Thresholds (Explainability Layer Conventions)
----------------------------------------------------------
HIGH_URGENCY and HIGH_CROP_SENSITIVITY are Explainability Layer conventions.
These thresholds do NOT control the LP objective itself; the LP objective uses
the raw urgency/crop_sensitivity values continuously (not thresholded).

The thresholds used here match the Phase 4 ConflictDetector constants:
    HIGH_STRESS_URGENCY_THRESHOLD     = 0.70  (from app.conflict.detector)
    HIGH_STRESS_SENSITIVITY_THRESHOLD = 0.70  (from app.conflict.detector)

These are RE-USED from Phase 4 to keep the project consistent.
Using them in the explainability layer does NOT mean the LP optimizer applied
the same cutoff -- it did not. The LP uses continuous values.

Causality Rules
---------------
When writing rationale text, the following causal claims are permitted:

PERMITTED:
  "urgency was used as a weight in the LP objective"
  "crop_sensitivity was used as a weight in the LP objective"
  "minimum_requirement is a hard constraint in the LP"
  "maximum_requirement is a hard constraint in the LP"
  "total_allocated <= available_water is enforced by hard constraint H3"
  "Jain's Fairness Index of X.XX was measured on the result"

FORBIDDEN (no causal claim without LP evidence):
  "urgency caused this allocation"  -- urgency is a weight, not a sole cause
  "fairness caused the allocation"  -- fairness is post-hoc measurement
  "proportional distribution was applied" -- only when allocation_method confirms it

Fairness Note
-------------
Jain's Fairness Index is described as a POST-HOC MEASUREMENT on the result.
The LP objective does not include fairness as a direct term.

DISCLAIMER: All data is SYNTHETIC.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.allocation.allocation_types import AllocationResult, FarmerAllocation
from app.conflict.conflict_types import ConflictReport, ScenarioConflictReport
from app.explainability.explanation_types import (
    AllocationExplanation,
    ConstraintExplanation,
    ConstraintStatus,
    ConflictExplanationEntry,
    FairnessExplanation,
    ReasonCode,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reason code thresholds — Explainability Layer conventions
#
# These thresholds are RE-USED from Phase 4 ConflictDetector constants:
#     HIGH_STRESS_URGENCY_THRESHOLD     = 0.70
#     HIGH_STRESS_SENSITIVITY_THRESHOLD = 0.70
#
# They classify OBSERVED values for human-readable labelling.
# They do NOT represent cutoffs used by the Phase 5 LP optimizer,
# which treats urgency and crop_sensitivity as continuous weights.
# ---------------------------------------------------------------------------
_URGENCY_HIGH_THRESHOLD: float = 0.70        # from conflict.detector.HIGH_STRESS_URGENCY_THRESHOLD
_CROP_SENSITIVITY_HIGH_THRESHOLD: float = 0.70   # from conflict.detector.HIGH_STRESS_SENSITIVITY_THRESHOLD
_UNMET_DEMAND_TOLERANCE: float = 1e-6
_SATISFACTION_FULL_THRESHOLD: float = 0.9999


def _lp_method_description(allocation_method: str) -> str:
    """
    Return a short human-readable description of the allocation method.

    This is the ONLY place where the allocation method string is converted to
    natural language. All rationale text delegates here.
    """
    method_map = {
        "lp_optimal": (
            "OR-Tools GLOP LP optimisation (all minimum requirements "
            "enforced as hard constraints)"
        ),
        "lp_relaxed": (
            "OR-Tools GLOP LP optimisation with relaxed minimum constraints "
            "(S1 converted to penalty term because total minimum requirements "
            "exceed available water)"
        ),
        "proportional_fallback": (
            "proportional fallback allocation "
            "(LP solver failed; water distributed as demand_i / total_demand)"
        ),
        "empty": "trivial allocation (no farmers)",
    }
    return method_map.get(allocation_method, f"allocation method '{allocation_method}'")


def _is_proportional_fallback(allocation_result: AllocationResult) -> bool:
    """Return True only when the actual allocation used proportional fallback."""
    return allocation_result.allocation_method == "proportional_fallback"


def _is_lp_result(allocation_result: AllocationResult) -> bool:
    """Return True when a GLOP LP solve produced the allocation."""
    return allocation_result.allocation_method in ("lp_optimal", "lp_relaxed")


# ---------------------------------------------------------------------------
# Reason code generation
# ---------------------------------------------------------------------------

def _generate_reason_codes(
    fa: FarmerAllocation,
    allocation_result: AllocationResult,
    has_concession: bool = False,
    batna_protected: bool = False,
) -> List[ReasonCode]:
    """
    Generate reason codes for a single farmer's allocation.

    A reason code is emitted ONLY when the actual data supports it.
    The same input always produces the same codes (deterministic).

    Threshold notes
    ---------------
    HIGH_URGENCY / HIGH_CROP_SENSITIVITY thresholds (both 0.70) are
    explainability-layer conventions that re-use Phase 4 ConflictDetector
    constants.  They DO NOT represent optimizer cutoffs.
    """
    codes: List[ReasonCode] = []

    # Resource shortage (scenario-level observation)
    if allocation_result.total_demand_m3 > allocation_result.available_water_m3 + _UNMET_DEMAND_TOLERANCE:
        codes.append(ReasonCode.RESOURCE_SHORTAGE)

    # Water surplus (remaining water > 0 AND this farmer fully satisfied)
    if (allocation_result.remaining_water_m3 > _UNMET_DEMAND_TOLERANCE
            and fa.satisfaction_ratio >= _SATISFACTION_FULL_THRESHOLD):
        codes.append(ReasonCode.WATER_SURPLUS)

    # High urgency observation (threshold = 0.70, matches Phase 4 constant)
    if fa.urgency > _URGENCY_HIGH_THRESHOLD:
        codes.append(ReasonCode.HIGH_URGENCY)

    # High crop sensitivity observation (threshold = 0.70, matches Phase 4 constant)
    if fa.crop_sensitivity > _CROP_SENSITIVITY_HIGH_THRESHOLD:
        codes.append(ReasonCode.HIGH_CROP_SENSITIVITY)

    # Minimum requirement: constraint_status from actual AllocationResult
    if fa.constraint_status == "minimum_relaxed":
        codes.append(ReasonCode.MINIMUM_REQUIREMENT)

    # At maximum requirement: constraint_status from actual AllocationResult
    if fa.constraint_status == "at_maximum":
        codes.append(ReasonCode.MAXIMUM_REQUIREMENT)

    # Unmet demand (observed in actual result)
    if fa.unmet_demand_m3 > _UNMET_DEMAND_TOLERANCE:
        codes.append(ReasonCode.UNMET_DEMAND)

    # Full demand satisfaction (observed in actual result)
    if fa.satisfaction_ratio >= _SATISFACTION_FULL_THRESHOLD:
        codes.append(ReasonCode.FULL_DEMAND_SATISFACTION)

    # Negotiation concession (from Phase 6, if applicable)
    if has_concession:
        codes.append(ReasonCode.NEGOTIATION_CONCESSION)

    # BATNA protection triggered (from Phase 6, if applicable)
    if batna_protected:
        codes.append(ReasonCode.BATNA_PROTECTION)

    return codes


# ---------------------------------------------------------------------------
# Per-farmer constraint explanations
# ---------------------------------------------------------------------------

def _build_farmer_constraint_explanations(
    fa: FarmerAllocation,
    allocation_result: AllocationResult,
) -> List[ConstraintExplanation]:
    """
    Build per-farmer constraint explanations from actual AllocationResult.

    Covers:
    - H1: non-negativity (hard)
    - H2: maximum requirement (hard)
    - S1: minimum requirement (soft -- hard when feasible, penalty when not)

    All actual/limit values come directly from fa and allocation_result fields.
    """
    explanations: List[ConstraintExplanation] = []
    method_desc = _lp_method_description(allocation_result.allocation_method)

    # H1: Non-negativity
    h1_ok = fa.allocated_water_m3 >= 0
    explanations.append(ConstraintExplanation(
        constraint_name="NON_NEGATIVITY (H1)",
        actual_value=fa.allocated_water_m3,
        limit=0.0,
        status=ConstraintStatus.SATISFIED if h1_ok else ConstraintStatus.VIOLATED,
        is_hard=True,
        farmer_id=fa.farmer_id,
        rationale=(
            f"Farmer {fa.farmer_id}: allocated {fa.allocated_water_m3:.2f} m3 "
            f"({'satisfies' if h1_ok else 'VIOLATES'} hard constraint H1: x_i >= 0). "
            f"Allocation produced by {method_desc}."
        ),
    ))

    # H2: Maximum requirement
    h2_ok = fa.allocated_water_m3 <= fa.maximum_requirement_m3 + 1e-6
    explanations.append(ConstraintExplanation(
        constraint_name="MAXIMUM_REQUIREMENT (H2)",
        actual_value=fa.allocated_water_m3,
        limit=fa.maximum_requirement_m3,
        status=ConstraintStatus.SATISFIED if h2_ok else ConstraintStatus.VIOLATED,
        is_hard=True,
        farmer_id=fa.farmer_id,
        rationale=(
            f"Farmer {fa.farmer_id}: allocated {fa.allocated_water_m3:.2f} m3 "
            f"against maximum {fa.maximum_requirement_m3:.2f} m3. "
            f"Hard constraint H2 (x_i <= max_i) is "
            f"{'satisfied' if h2_ok else 'VIOLATED'}."
        ),
    ))

    # S1: Minimum requirement (soft)
    min_met = fa.allocated_water_m3 >= fa.minimum_requirement_m3 - 1e-6
    if fa.constraint_status == "minimum_relaxed":
        s1_status = ConstraintStatus.RELAXED
        s1_rationale = (
            f"Farmer {fa.farmer_id}: minimum requirement {fa.minimum_requirement_m3:.2f} m3 "
            f"could not be fully met (allocated {fa.allocated_water_m3:.2f} m3, "
            f"shortfall {fa.minimum_shortfall_m3:.2f} m3). "
            f"Soft constraint S1 was converted to a penalty term in the LP objective "
            f"because total minimum requirements "
            f"({allocation_result.total_minimum_requirement_m3:.2f} m3) exceed "
            f"available water ({allocation_result.available_water_m3:.2f} m3). "
            f"The LP still produced a physically valid solution."
        )
    elif min_met:
        if allocation_result.minimum_requirements_feasible:
            s1_detail = (
                "S1 was enforced as a hard LP constraint because minimum requirements "
                "are simultaneously feasible."
            )
        else:
            s1_detail = (
                "S1 was treated as a penalty term, but this farmer's minimum "
                "was covered by the LP solution."
            )
        s1_status = ConstraintStatus.SATISFIED
        s1_rationale = (
            f"Farmer {fa.farmer_id}: minimum requirement {fa.minimum_requirement_m3:.2f} m3 "
            f"met (allocated {fa.allocated_water_m3:.2f} m3). {s1_detail}"
        )
    else:
        s1_status = ConstraintStatus.VIOLATED
        s1_rationale = (
            f"Farmer {fa.farmer_id}: minimum requirement {fa.minimum_requirement_m3:.2f} m3 "
            f"not met (allocated {fa.allocated_water_m3:.2f} m3). "
            f"Shortfall: {fa.minimum_shortfall_m3:.2f} m3. "
            f"Constraint verification flagged this allocation."
        )

    explanations.append(ConstraintExplanation(
        constraint_name="MINIMUM_REQUIREMENT (S1)",
        actual_value=fa.allocated_water_m3,
        limit=fa.minimum_requirement_m3,
        status=s1_status,
        is_hard=False,
        farmer_id=fa.farmer_id,
        rationale=s1_rationale,
    ))

    return explanations


# ---------------------------------------------------------------------------
# Per-farmer rationale
# ---------------------------------------------------------------------------

def _build_farmer_rationale(
    fa: FarmerAllocation,
    allocation_result: AllocationResult,
    reason_codes: List[ReasonCode],
) -> str:
    """
    Build a deterministic rationale for a farmer's allocation.

    Causal claims are restricted to what the Phase 5 LP actually does.
    Fairness is never cited as a cause.
    Proportional language is only used when allocation_method confirms fallback.
    """
    method_desc = _lp_method_description(allocation_result.allocation_method)
    is_proportional = _is_proportional_fallback(allocation_result)
    is_lp = _is_lp_result(allocation_result)

    parts: List[str] = []

    # Core allocation statement
    parts.append(
        f"Farmer {fa.farmer_id} received {fa.allocated_water_m3:.2f} m3 "
        f"against a predicted demand of {fa.predicted_demand_m3:.2f} m3 "
        f"(satisfaction ratio: {fa.satisfaction_ratio:.2%}). "
        f"Allocation method: {method_desc}."
    )

    # Resource shortage context (observation, not cause)
    if ReasonCode.RESOURCE_SHORTAGE in reason_codes:
        parts.append(
            f"Observed: total demand ({allocation_result.total_demand_m3:.2f} m3) "
            f"exceeds available water ({allocation_result.available_water_m3:.2f} m3). "
        )
        if is_lp:
            parts.append(
                "The LP objective weighted allocation by urgency and crop_sensitivity; "
                "no single-farmer allocation was pre-determined."
            )
        elif is_proportional:
            parts.append(
                "Because the LP solver failed, water was distributed proportionally "
                "to predicted demand (x_i = available x demand_i / total_demand)."
            )

    # Urgency and crop_sensitivity: LP objective factors, not sole causes
    if ReasonCode.HIGH_URGENCY in reason_codes and is_lp:
        parts.append(
            f"Urgency score {fa.urgency:.2f} (> {_URGENCY_HIGH_THRESHOLD:.2f} threshold): "
            f"urgency is used as a continuous weight in the LP objective "
            f"(coefficient w_urg x urgency_i x satisfaction_i). "
            f"It increases the objective contribution of this farmer's satisfaction, "
            f"but does not guarantee a specific allocation by itself."
        )
    elif ReasonCode.HIGH_URGENCY in reason_codes:
        parts.append(
            f"Urgency score {fa.urgency:.2f} (> {_URGENCY_HIGH_THRESHOLD:.2f} threshold, observed)."
        )

    if ReasonCode.HIGH_CROP_SENSITIVITY in reason_codes and is_lp:
        parts.append(
            f"Crop sensitivity {fa.crop_sensitivity:.2f} (> {_CROP_SENSITIVITY_HIGH_THRESHOLD:.2f} threshold): "
            f"crop_sensitivity is used as a continuous weight in the LP objective "
            f"(coefficient w_cs x cs_i x satisfaction_i). "
            f"It increases the objective contribution of this farmer's satisfaction."
        )
    elif ReasonCode.HIGH_CROP_SENSITIVITY in reason_codes:
        parts.append(
            f"Crop sensitivity {fa.crop_sensitivity:.2f} (> {_CROP_SENSITIVITY_HIGH_THRESHOLD:.2f} threshold, observed)."
        )

    # Unmet demand (observation)
    if ReasonCode.UNMET_DEMAND in reason_codes:
        parts.append(
            f"Unmet demand: {fa.unmet_demand_m3:.2f} m3 was not allocated."
        )

    # Minimum requirement
    if ReasonCode.MINIMUM_REQUIREMENT in reason_codes:
        parts.append(
            f"Minimum requirement ({fa.minimum_requirement_m3:.2f} m3) soft constraint "
            f"was relaxed to a penalty term: total minimum requirements exceed available water."
        )

    # At maximum
    if ReasonCode.MAXIMUM_REQUIREMENT in reason_codes:
        parts.append(
            f"Allocation reached the hard maximum requirement "
            f"({fa.maximum_requirement_m3:.2f} m3) constraint (H2)."
        )

    # Full demand satisfaction (observation)
    if ReasonCode.FULL_DEMAND_SATISFACTION in reason_codes:
        parts.append("Full predicted demand was satisfied.")

    # Negotiation concession (from Phase 6)
    if ReasonCode.NEGOTIATION_CONCESSION in reason_codes:
        parts.append(
            "A Phase 6 negotiation concession adjusted the effective demand used "
            "in a re-optimisation round."
        )

    # BATNA protection (from Phase 6)
    if ReasonCode.BATNA_PROTECTION in reason_codes:
        parts.append(
            "Phase 6 BATNA protection was triggered: "
            "the proposed allocation did not exceed this farmer's BATNA utility."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Global constraint explanations
# ---------------------------------------------------------------------------

def build_global_constraint_explanations(
    allocation_result: AllocationResult,
) -> List[ConstraintExplanation]:
    """
    Build global (scenario-level) constraint explanations.

    Covers:
    - H3: total water limit (hard)
    - S1 feasibility: whether all minimum requirements could be simultaneously satisfied

    All values come from AllocationResult fields.
    """
    explanations: List[ConstraintExplanation] = []
    method_desc = _lp_method_description(allocation_result.allocation_method)

    # H3: Total water limit
    h3_ok = allocation_result.total_allocated_m3 <= allocation_result.available_water_m3 + 1e-6
    explanations.append(ConstraintExplanation(
        constraint_name="TOTAL_WATER_LIMIT (H3)",
        actual_value=allocation_result.total_allocated_m3,
        limit=allocation_result.available_water_m3,
        status=ConstraintStatus.SATISFIED if h3_ok else ConstraintStatus.VIOLATED,
        is_hard=True,
        farmer_id=None,
        rationale=(
            f"Total allocated {allocation_result.total_allocated_m3:.2f} m3 "
            f"against available {allocation_result.available_water_m3:.2f} m3. "
            f"Remaining: {allocation_result.remaining_water_m3:.2f} m3. "
            f"Hard constraint H3 (sum x_i <= available_water) is "
            f"{'satisfied' if h3_ok else 'VIOLATED'}. "
            f"Allocation produced by {method_desc}."
        ),
    ))

    # S1 feasibility (scenario-level)
    if allocation_result.minimum_requirements_feasible:
        s1_global_status = ConstraintStatus.SATISFIED
        s1_rationale = (
            f"Total minimum requirements ({allocation_result.total_minimum_requirement_m3:.2f} m3) "
            f"are within available water ({allocation_result.available_water_m3:.2f} m3). "
            f"Soft constraint S1 could be enforced as a hard LP constraint; "
            f"all minimum requirements were included as lower bounds in the LP."
        )
    else:
        s1_global_status = ConstraintStatus.RELAXED
        s1_rationale = (
            f"Total minimum requirements ({allocation_result.total_minimum_requirement_m3:.2f} m3) "
            f"exceed available water ({allocation_result.available_water_m3:.2f} m3). "
            f"Soft constraint S1 was converted to a penalty term in the LP objective "
            f"(penalty = w_min x shortfall_i / demand_i) to maintain LP feasibility. "
            f"The LP still produced a physically valid solution satisfying H1/H2/H3."
        )

    explanations.append(ConstraintExplanation(
        constraint_name="MINIMUM_REQUIREMENTS_FEASIBILITY (S1 global)",
        actual_value=allocation_result.total_minimum_requirement_m3,
        limit=allocation_result.available_water_m3,
        status=s1_global_status,
        is_hard=False,
        farmer_id=None,
        rationale=s1_rationale,
    ))

    return explanations


# ---------------------------------------------------------------------------
# explain_allocation
# ---------------------------------------------------------------------------

def explain_allocation(
    allocation_result: AllocationResult,
    concession_farmer_ids: Optional[List[str]] = None,
    batna_protected_farmer_ids: Optional[List[str]] = None,
) -> List[AllocationExplanation]:
    """
    Build AllocationExplanation objects from an AllocationResult.

    Parameters
    ----------
    allocation_result : AllocationResult
        Phase 5 LP allocation result.
    concession_farmer_ids : list of str or None
        Farmer IDs that made a negotiation concession (from Phase 6).
    batna_protected_farmer_ids : list of str or None
        Farmer IDs where BATNA protection was triggered.

    Returns
    -------
    list of AllocationExplanation, one per farmer.
    """
    if not allocation_result.allocations:
        return []

    concession_ids = set(concession_farmer_ids or [])
    batna_ids = set(batna_protected_farmer_ids or [])

    explanations: List[AllocationExplanation] = []
    for fa in allocation_result.allocations:
        has_concession = fa.farmer_id in concession_ids
        batna_protected = fa.farmer_id in batna_ids

        reason_codes = _generate_reason_codes(
            fa, allocation_result,
            has_concession=has_concession,
            batna_protected=batna_protected,
        )
        constraint_exps = _build_farmer_constraint_explanations(fa, allocation_result)
        rationale = _build_farmer_rationale(fa, allocation_result, reason_codes)

        explanations.append(AllocationExplanation(
            farmer_id=fa.farmer_id,
            predicted_demand_m3=fa.predicted_demand_m3,
            allocated_m3=fa.allocated_water_m3,
            unmet_demand_m3=fa.unmet_demand_m3,
            minimum_requirement_m3=fa.minimum_requirement_m3,
            maximum_requirement_m3=fa.maximum_requirement_m3,
            satisfaction_ratio=fa.satisfaction_ratio,
            urgency=fa.urgency,
            crop_sensitivity=fa.crop_sensitivity,
            growth_stage=fa.growth_stage,
            crop=fa.crop,
            constraint_status=fa.constraint_status,
            reason_codes=reason_codes,
            constraint_explanations=constraint_exps,
            rationale=rationale,
        ))

    return explanations


# ---------------------------------------------------------------------------
# explain_fairness
# ---------------------------------------------------------------------------

def explain_fairness(allocation_result: AllocationResult) -> FairnessExplanation:
    """
    Build a FairnessExplanation from an AllocationResult.

    The Jain's Fairness Index is a POST-HOC MEASUREMENT on the allocation.
    It is NOT a term in the LP objective and did NOT cause the allocation.
    This distinction is always stated in the rationale and note fields.

    Parameters
    ----------
    allocation_result : AllocationResult

    Returns
    -------
    FairnessExplanation
    """
    sat_ratios = {
        fa.farmer_id: fa.satisfaction_ratio
        for fa in allocation_result.allocations
    }

    avg_sat = allocation_result.average_satisfaction
    js = allocation_result.fairness_score
    feasible = allocation_result.minimum_requirements_feasible
    method_desc = _lp_method_description(allocation_result.allocation_method)

    if js >= 0.95:
        fairness_level = "high"
    elif js >= 0.75:
        fairness_level = "moderate"
    else:
        fairness_level = "low"

    rationale = (
        f"Jain's Fairness Index (J) measured on the allocation result: {js:.4f} ({fairness_level}). "
        f"Formula: J = (sum s_i)^2 / (n x sum s_i^2), where s_i = allocated_i / demand_i. "
        f"Average satisfaction ratio: {avg_sat:.2%} across {len(sat_ratios)} farmer(s). "
        f"Minimum requirements were {'feasible' if feasible else 'infeasible (S1 relaxed)'}. "
        f"Allocation method: {method_desc}. "
        f"A score of 1.0 indicates equal satisfaction ratios across all farmers; "
        f"lower scores indicate inequality."
    )

    return FairnessExplanation(
        fairness_score=js,
        n_farmers=len(sat_ratios),
        satisfaction_ratios=sat_ratios,
        average_satisfaction=avg_sat,
        is_minimum_requirements_feasible=feasible,
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# explain_conflict / explain_all_conflicts
# ---------------------------------------------------------------------------

def explain_conflict(conflict_report: ConflictReport) -> ConflictExplanationEntry:
    """
    Build a ConflictExplanationEntry from a Phase 4 ConflictReport.

    All values come directly from the ConflictReport fields.

    Parameters
    ----------
    conflict_report : ConflictReport

    Returns
    -------
    ConflictExplanationEntry
    """
    ct = conflict_report.conflict_type.value
    sev = conflict_report.severity.value

    if ct == "resource_shortage":
        rationale = (
            f"RESOURCE_SHORTAGE detected by Phase 4 ConflictDetector: "
            f"available water {conflict_report.available_water_m3:.2f} m3, "
            f"combined demand {conflict_report.total_demand_m3:.2f} m3, "
            f"resource gap {conflict_report.resource_gap_m3:.2f} m3 "
            f"({conflict_report.severity_score * 100:.1f}% shortage ratio). "
            f"Severity: {sev}. "
            f"Farmers involved: {', '.join(conflict_report.involved_farmer_ids)}."
        )
    elif ct == "irrigation_window_overlap":
        rationale = (
            f"IRRIGATION_WINDOW_OVERLAP detected by Phase 4 ConflictDetector: "
            f"farmers {', '.join(conflict_report.involved_farmer_ids)} "
            f"have overlapping preferred irrigation windows. "
            f"Severity: {sev} (score: {conflict_report.severity_score:.3f})."
        )
    elif ct == "canal_capacity_conflict":
        rationale = (
            f"CANAL_CAPACITY_CONFLICT detected by Phase 4 ConflictDetector: "
            f"simultaneous demand from farmers "
            f"{', '.join(conflict_report.involved_farmer_ids)} "
            f"may exceed canal flow capacity. "
            f"Severity: {sev} (score: {conflict_report.severity_score:.3f})."
        )
    elif ct == "minimum_requirement_conflict":
        rationale = (
            f"MINIMUM_REQUIREMENT_CONFLICT detected by Phase 4 ConflictDetector: "
            f"total minimum requirements "
            f"({conflict_report.total_minimum_requirement_m3:.2f} m3) "
            f"exceed available water ({conflict_report.available_water_m3:.2f} m3). "
            f"Gap: {conflict_report.minimum_requirement_gap_m3:.2f} m3. "
            f"Severity: {sev}."
        )
    elif ct == "high_crop_stress":
        rationale = (
            f"HIGH_CROP_STRESS detected by Phase 4 ConflictDetector: "
            f"farmers {', '.join(conflict_report.involved_farmer_ids)} "
            f"are at high agronomic risk (urgency >= {0.70:.2f} and/or "
            f"crop_sensitivity >= {0.70:.2f}, per Phase 4 thresholds). "
            f"Severity: {sev} (score: {conflict_report.severity_score:.3f})."
        )
    else:
        rationale = (
            f"Conflict type '{ct}' detected by Phase 4 ConflictDetector for farmers "
            f"{', '.join(conflict_report.involved_farmer_ids)}. "
            f"Severity: {sev} (score: {conflict_report.severity_score:.3f}). "
            f"Details: {conflict_report.explanation}"
        )

    return ConflictExplanationEntry(
        conflict_id=conflict_report.conflict_id,
        conflict_type=ct,
        severity=sev,
        severity_score=conflict_report.severity_score,
        involved_farmer_ids=conflict_report.involved_farmer_ids,
        available_water_m3=conflict_report.available_water_m3,
        total_demand_m3=conflict_report.total_demand_m3,
        total_minimum_requirement_m3=conflict_report.total_minimum_requirement_m3,
        resource_gap_m3=conflict_report.resource_gap_m3,
        minimum_requirement_gap_m3=conflict_report.minimum_requirement_gap_m3,
        evidence=conflict_report.evidence,
        rationale=rationale,
    )


def explain_all_conflicts(
    scenario_conflict_report: Optional[ScenarioConflictReport],
) -> List[ConflictExplanationEntry]:
    """
    Build ConflictExplanationEntry objects from a ScenarioConflictReport.

    Parameters
    ----------
    scenario_conflict_report : ScenarioConflictReport or None

    Returns
    -------
    list of ConflictExplanationEntry (empty if no conflicts or None input)
    """
    if scenario_conflict_report is None:
        return []
    return [explain_conflict(cr) for cr in scenario_conflict_report.conflicts]
