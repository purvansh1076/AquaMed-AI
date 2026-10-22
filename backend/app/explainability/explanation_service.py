"""
AquaMediAI - Explanation Service
===================================

High-level orchestration service for the Phase 7 Explainability Layer.

Combines prediction, conflict, allocation, and negotiation explainers
into a unified ExplanationService that produces FinalDecisionExplanation.

Design
------
ExplanationService is READ-ONLY. It consumes actual computational results
from Phases 2-6 and produces structured explanations. It never modifies
any Phase inputs or outputs.

Usage
-----
    from app.explainability.explanation_service import ExplanationService

    service = ExplanationService()

    # With full pipeline results:
    final_explanation = service.explain_final_decision(
        allocation_result=my_allocation,
        negotiation_session=my_session,
        conflict_report=my_conflict_report,
        scenario_id="scenario_001",
    )

    # Serialize:
    explanation_dict = final_explanation.as_dict()

Counterfactual readiness
------------------------
FinalDecisionExplanation.counterfactual_baseline is reserved for future
what-if analysis. It accepts a dict containing baseline result data
alongside which a counterfactual can be compared in a future phase.
The service does NOT implement counterfactual simulation in Phase 7.

DISCLAIMER: All explanations are derived from SYNTHETIC agronomic data.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.allocation.allocation_types import AllocationResult
from app.conflict.conflict_types import ScenarioConflictReport
from app.negotiation.negotiation_types import NegotiationSession
from app.explainability.explanation_types import (
    AllocationExplanation,
    ConstraintExplanation,
    ConflictExplanationEntry,
    FairnessExplanation,
    FinalDecisionExplanation,
    NegotiationExplanation,
    PredictionExplanation,
    ReasonCode,
)
from app.explainability.allocation_explainer import (
    build_global_constraint_explanations,
    explain_all_conflicts,
    explain_allocation,
    explain_fairness,
)
from app.explainability.negotiation_explainer import (
    explain_negotiation_session,
)

logger = logging.getLogger(__name__)


def _collect_concession_farmer_ids(
    session: Optional[NegotiationSession],
) -> List[str]:
    """Return list of farmer IDs that made concessions in the session."""
    if session is None:
        return []
    return [c.farmer_id for c in session.concessions]


def _collect_batna_protected_farmer_ids(
    session: Optional[NegotiationSession],
) -> List[str]:
    """Return farmer IDs where BATNA protection was triggered in any round."""
    if session is None:
        return []
    result = []
    for rnd in session.rounds:
        for fr in rnd.farmer_responses:
            if fr.is_batna_protected and fr.farmer_id not in result:
                result.append(fr.farmer_id)
    return result


def _collect_all_reason_codes(
    allocation_explanations: List[AllocationExplanation],
) -> List[ReasonCode]:
    """Collect the unique set of reason codes across all allocation explanations."""
    seen = set()
    codes = []
    for ae in allocation_explanations:
        for rc in ae.reason_codes:
            if rc not in seen:
                seen.add(rc)
                codes.append(rc)
    return codes


def _collect_unresolved_issues(
    allocation_result: Optional[AllocationResult],
    allocation_explanations: List[AllocationExplanation],
    constraint_explanations: List[ConstraintExplanation],
) -> List[str]:
    """Collect list of unresolved issues from actual result data."""
    issues: List[str] = []

    if allocation_result is not None:
        # Total unmet demand
        total_unmet = allocation_result.total_unmet_demand_m3
        if total_unmet > 1e-6:
            issues.append(
                f"Total unmet demand: {total_unmet:.2f} m3 across all farmers."
            )

        # Minimum requirement shortfall
        total_shortfall = allocation_result.total_minimum_shortfall_m3
        if total_shortfall > 1e-6:
            issues.append(
                f"Total minimum requirement shortfall: {total_shortfall:.2f} m3."
            )

        # Per-farmer unmet demand
        for fa in allocation_result.allocations:
            if fa.unmet_demand_m3 > 1e-6:
                issues.append(
                    f"Farmer {fa.farmer_id}: unmet demand {fa.unmet_demand_m3:.2f} m3 "
                    f"(satisfaction: {fa.satisfaction_ratio:.2%})."
                )

        # Constraint violations from verification
        if not allocation_result.verification.is_valid:
            for v in allocation_result.verification.violations:
                issues.append(f"Constraint violation: {v}")

    return issues


def _build_final_summary(
    allocation_result: Optional[AllocationResult],
    conflict_explanations: List[ConflictExplanationEntry],
    negotiation_explanation: Optional[NegotiationExplanation],
    scenario_id: str,
) -> str:
    """Build a deterministic high-level summary of the final decision."""
    parts: List[str] = [f"Scenario {scenario_id}:"]

    if allocation_result is not None:
        n = allocation_result.n_farmers
        avail = allocation_result.available_water_m3
        alloc = allocation_result.total_allocated_m3
        fairness = allocation_result.fairness_score
        parts.append(
            f"{n} farmer(s) participated. "
            f"Available water: {avail:.2f} m3. "
            f"Total allocated: {alloc:.2f} m3. "
            f"Fairness (Jain): {fairness:.4f}. "
            f"Solver status: {allocation_result.solver_status.value}."
        )

    if conflict_explanations:
        n_conflicts = len(conflict_explanations)
        types = list(set(ce.conflict_type for ce in conflict_explanations))
        parts.append(
            f"{n_conflicts} conflict(s) detected: {', '.join(types)}."
        )
    else:
        parts.append("No conflicts detected.")

    if negotiation_explanation is not None:
        parts.append(
            f"Negotiation: {negotiation_explanation.n_rounds} round(s), "
            f"status: {negotiation_explanation.agreement_status}."
        )

    return " ".join(parts)


class ExplanationService:
    """
    Orchestrates the Phase 7 Explainability Layer.

    This service is stateless -- call explain_* methods directly.
    It is READ-ONLY with respect to all Phase 2-6 outputs.

    All explanations are deterministic: the same input produces the same output.

    DISCLAIMER: All explanations are derived from SYNTHETIC data.
    """

    def explain_allocation_result(
        self,
        allocation_result: AllocationResult,
        session: Optional[NegotiationSession] = None,
    ) -> tuple:
        """
        Build allocation and constraint explanations from an AllocationResult.

        Parameters
        ----------
        allocation_result : AllocationResult
        session : NegotiationSession or None
            If provided, concession/BATNA data enriches the explanations.

        Returns
        -------
        tuple of (
            list[AllocationExplanation],
            list[ConstraintExplanation],
            FairnessExplanation
        )
        """
        concession_ids = _collect_concession_farmer_ids(session)
        batna_ids = _collect_batna_protected_farmer_ids(session)

        allocation_explanations = explain_allocation(
            allocation_result,
            concession_farmer_ids=concession_ids,
            batna_protected_farmer_ids=batna_ids,
        )
        constraint_explanations = build_global_constraint_explanations(allocation_result)
        fairness_explanation = explain_fairness(allocation_result)

        return allocation_explanations, constraint_explanations, fairness_explanation

    def explain_negotiation(
        self,
        session: NegotiationSession,
        floor_value: float = 1e-6,
    ) -> NegotiationExplanation:
        """
        Build a NegotiationExplanation from a NegotiationSession.

        Parameters
        ----------
        session : NegotiationSession
        floor_value : float
            Surplus floor for Nash objective (from NegotiationConfig.min_surplus_floor).

        Returns
        -------
        NegotiationExplanation
        """
        return explain_negotiation_session(session, floor_value=floor_value)

    def explain_final_decision(
        self,
        allocation_result: AllocationResult,
        scenario_id: str,
        prediction_explanations: Optional[List[PredictionExplanation]] = None,
        conflict_report: Optional[ScenarioConflictReport] = None,
        negotiation_session: Optional[NegotiationSession] = None,
        floor_value: float = 1e-6,
        counterfactual_baseline: Optional[Dict[str, Any]] = None,
    ) -> FinalDecisionExplanation:
        """
        Build the unified FinalDecisionExplanation spanning the full pipeline.

        Parameters
        ----------
        allocation_result : AllocationResult
            Phase 5 LP allocation result (required).
        scenario_id : str
            Scenario identifier.
        prediction_explanations : list of PredictionExplanation or None
            Phase 2/7 prediction explanations, one per farmer.
        conflict_report : ScenarioConflictReport or None
            Phase 4 conflict analysis.
        negotiation_session : NegotiationSession or None
            Phase 6 negotiation session.
        floor_value : float
            Nash surplus floor.
        counterfactual_baseline : dict or None
            Reserved for future what-if analysis. Accepts baseline result data
            to be compared against a counterfactual in a future phase.
            Pass None for Phase 7 (not yet implemented).

        Returns
        -------
        FinalDecisionExplanation
        """
        if allocation_result is None:
            raise ValueError("allocation_result must not be None")

        # Conflict explanations from Phase 4
        conflict_explanations = explain_all_conflicts(conflict_report)

        # Allocation explanations from Phase 5
        concession_ids = _collect_concession_farmer_ids(negotiation_session)
        batna_ids = _collect_batna_protected_farmer_ids(negotiation_session)

        allocation_explanations = explain_allocation(
            allocation_result,
            concession_farmer_ids=concession_ids,
            batna_protected_farmer_ids=batna_ids,
        )
        constraint_explanations = build_global_constraint_explanations(allocation_result)
        fairness_explanation = explain_fairness(allocation_result)

        # Negotiation explanation from Phase 6
        negotiation_explanation: Optional[NegotiationExplanation] = None
        final_allocation: Dict[str, float] = {}
        final_utilities: Dict[str, float] = {}
        agreement_status: Optional[str] = None

        if negotiation_session is not None:
            negotiation_explanation = explain_negotiation_session(
                negotiation_session, floor_value=floor_value
            )
            final_allocation = dict(negotiation_explanation.final_allocation)
            final_utilities = dict(negotiation_explanation.final_utilities)
            agreement_status = negotiation_explanation.agreement_status
        else:
            # No negotiation: use allocation as final result
            final_allocation = {
                fa.farmer_id: fa.allocated_water_m3
                for fa in allocation_result.allocations
            }

        # Aggregate reason codes
        all_reason_codes = _collect_all_reason_codes(allocation_explanations)

        # Unresolved issues
        unresolved_issues = _collect_unresolved_issues(
            allocation_result, allocation_explanations, constraint_explanations
        )

        # Summary
        summary = _build_final_summary(
            allocation_result, conflict_explanations,
            negotiation_explanation, scenario_id,
        )

        return FinalDecisionExplanation(
            scenario_id=scenario_id,
            summary=summary,
            prediction_explanations=prediction_explanations or [],
            conflict_explanations=conflict_explanations,
            allocation_explanations=allocation_explanations,
            fairness_explanation=fairness_explanation,
            constraint_explanations=constraint_explanations,
            negotiation_explanation=negotiation_explanation,
            final_allocation=final_allocation,
            final_utilities=final_utilities,
            agreement_status=agreement_status,
            all_reason_codes=all_reason_codes,
            unresolved_issues=unresolved_issues,
            counterfactual_baseline=counterfactual_baseline,
        )
