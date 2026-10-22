"""
AquaMediAI - Negotiation Explainer
=====================================

Explains Phase 6 NegotiationSession and Agreement objects.

Design
------
This module reads ACTUAL NegotiationSession, NegotiationRound, Concession,
Agreement, and FarmerResponse objects from Phase 6 and converts them to
structured explanation types.

It is READ-ONLY with respect to negotiation state -- it never modifies any
Phase 6 outputs.

Key functions:
  explain_negotiation_round()   -- single NegotiationRound
  explain_concession()          -- single Concession
  explain_batna()               -- single farmer BATNA
  explain_nash_objective()      -- Nash-inspired objective
  explain_negotiation_session() -- full NegotiationSession

All rationale text is:
  - Derived from actual structured values (not invented)
  - Deterministic (same input -> same output)
  - Neutral and computational in language (no emotions/intentions)

DISCLAIMER: All data is SYNTHETIC.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.negotiation.negotiation_types import (
    Agreement,
    AgreementStatus,
    Concession,
    FarmerResponse,
    NegotiationRound,
    NegotiationSession,
    ResponseType,
)
from app.explainability.explanation_types import (
    BATNAExplanation,
    ConcessionExplanation,
    NashObjectiveExplanation,
    NegotiationExplanation,
    NegotiationRoundExplanation,
)

logger = logging.getLogger(__name__)


def explain_concession(concession: Concession) -> ConcessionExplanation:
    """
    Build a ConcessionExplanation from an actual Phase 6 Concession.

    Exposes all fields of the Concession object with deterministic rationale.

    Parameters
    ----------
    concession : Concession

    Returns
    -------
    ConcessionExplanation
    """
    amount = concession.concession_amount_m3
    ratio = concession.concession_ratio
    flexibility = concession.flexibility_factor
    urgency_factor = concession.urgency_factor

    rationale = (
        f"Farmer {concession.farmer_id} made a concession in round {concession.round_number}. "
        f"Previous ask: {concession.previous_ask_m3:.2f} m3 -> "
        f"New ask: {concession.new_ask_m3:.2f} m3 "
        f"(reduction: {amount:.2f} m3, ratio: {ratio:.4f}). "
        f"Flexibility factor: {flexibility:.4f} (higher = more willing to concede). "
        f"Urgency factor: {urgency_factor:.4f} (1 - urgency; lower urgency = larger concession). "
        f"Concession formula: available_space x flexibility x urgency_factor x concession_scale."
    )

    return ConcessionExplanation(
        farmer_id=concession.farmer_id,
        round_number=concession.round_number,
        previous_ask_m3=concession.previous_ask_m3,
        new_ask_m3=concession.new_ask_m3,
        concession_amount_m3=concession.concession_amount_m3,
        concession_ratio=concession.concession_ratio,
        flexibility_factor=concession.flexibility_factor,
        urgency_factor=concession.urgency_factor,
        reason=concession.reason,
        rationale=rationale,
    )


def explain_batna(
    farmer_id: str,
    batna_utility: float,
    batna_allocation_m3: float,
    negotiated_utility: Optional[float] = None,
    negotiated_allocation_m3: Optional[float] = None,
) -> BATNAExplanation:
    """
    Build a BATNAExplanation from actual Phase 3/6 BATNA values.

    All values come from the existing BATNA and Agreement objects.
    No utility or allocation values are computed here.

    Parameters
    ----------
    farmer_id : str
    batna_utility : float
        From BATNA.fallback_utility.
    batna_allocation_m3 : float
        From BATNA.fallback_allocation_m3 (= minimum_water_requirement).
    negotiated_utility : float or None
        From Agreement.final_utilities[farmer_id], if available.
    negotiated_allocation_m3 : float or None
        From Agreement.final_allocation[farmer_id], if available.

    Returns
    -------
    BATNAExplanation
    """
    surplus: Optional[float] = None
    is_above_batna: Optional[bool] = None

    if negotiated_utility is not None:
        surplus = negotiated_utility - batna_utility
        is_above_batna = negotiated_utility > batna_utility

    # Build rationale
    batna_part = (
        f"Farmer {farmer_id}'s BATNA utility is {batna_utility:.4f} "
        f"(fallback allocation: {batna_allocation_m3:.2f} m3, "
        f"equal to the FAO-56 minimum water requirement). "
    )
    if negotiated_utility is not None and negotiated_allocation_m3 is not None:
        comparison = "above" if is_above_batna else "at or below"
        batna_part += (
            f"The negotiated allocation is {negotiated_allocation_m3:.2f} m3 "
            f"with utility {negotiated_utility:.4f}, which is {comparison} the BATNA utility. "
            f"Surplus above BATNA: {surplus:.4f}."
        )
    else:
        batna_part += (
            "No negotiated allocation data available for comparison."
        )

    return BATNAExplanation(
        farmer_id=farmer_id,
        batna_utility=batna_utility,
        batna_allocation_m3=batna_allocation_m3,
        negotiated_utility=negotiated_utility,
        negotiated_allocation_m3=negotiated_allocation_m3,
        is_above_batna=is_above_batna,
        surplus=surplus,
        rationale=batna_part,
    )


def explain_negotiation_round(
    round_obj: NegotiationRound,
) -> NegotiationRoundExplanation:
    """
    Build a NegotiationRoundExplanation from an actual NegotiationRound.

    All values come from the NegotiationRound object.
    No values are computed or invented here.

    Parameters
    ----------
    round_obj : NegotiationRound

    Returns
    -------
    NegotiationRoundExplanation
    """
    concession_explanations = [
        explain_concession(c) for c in round_obj.accepted_concessions
    ]

    # Build response summaries from actual FarmerResponse objects
    farmer_responses_dicts = [r.as_dict() for r in round_obj.farmer_responses]

    # Build outcome rationale from actual round state
    rationale_parts: List[str] = [
        f"Round {round_obj.round_number}: "
        f"{round_obj.n_accepting} farmer(s) ACCEPT, "
        f"{round_obj.n_requesting_change} REQUEST_CHANGE, "
        f"{round_obj.n_rejecting} REJECT."
    ]

    # Per-farmer response interpretation
    for fr in round_obj.farmer_responses:
        response_name = fr.response_type.value
        if fr.response_type == ResponseType.ACCEPT:
            interp = f"utility {fr.utility:.4f} >= acceptance threshold"
        elif fr.response_type == ResponseType.REQUEST_CHANGE:
            interp = f"utility {fr.utility:.4f} in [rejection, acceptance) range"
        else:  # REJECT
            if fr.is_batna_protected:
                interp = f"utility {fr.utility:.4f} < BATNA utility {fr.batna_utility:.4f} (BATNA protection)"
            else:
                interp = f"utility {fr.utility:.4f} < rejection threshold"

        rationale_parts.append(
            f"  Farmer {fr.farmer_id}: {response_name} ({interp}). "
            f"Allocation: {fr.allocation_m3:.2f} m3. "
            f"Surplus: {fr.surplus:.4f}."
        )

    rationale_parts.append(
        f"Nash-inspired objective this round: {round_obj.nash_objective:.6f}. "
        f"Fairness (Jain's Index): {round_obj.fairness_score:.4f}. "
        f"Solver status: {round_obj.solver_status}."
    )

    if concession_explanations:
        concession_farmer_ids = [c.farmer_id for c in concession_explanations]
        rationale_parts.append(
            f"Concessions made by: {', '.join(concession_farmer_ids)}."
        )

    if round_obj.proposed_changes:
        rationale_parts.append(
            f"Mediator proposed changes: "
            + ", ".join(
                f"{fid}={m3:.2f} m3" for fid, m3 in round_obj.proposed_changes.items()
            ) + "."
        )

    outcome_rationale = " ".join(rationale_parts)

    return NegotiationRoundExplanation(
        round_number=round_obj.round_number,
        current_allocation=dict(round_obj.current_allocation),
        farmer_responses=farmer_responses_dicts,
        utilities=dict(round_obj.utilities),
        batna_utilities=dict(round_obj.batna_utilities),
        surpluses=dict(round_obj.surpluses),
        n_accepting=round_obj.n_accepting,
        n_requesting_change=round_obj.n_requesting_change,
        n_rejecting=round_obj.n_rejecting,
        nash_objective=round_obj.nash_objective,
        fairness_score=round_obj.fairness_score,
        proposed_changes=dict(round_obj.proposed_changes),
        concession_explanations=concession_explanations,
        solver_status=round_obj.solver_status,
        outcome_rationale=outcome_rationale,
    )


def explain_nash_objective(
    agreement: Agreement,
    floor_value: float = 1e-6,
) -> NashObjectiveExplanation:
    """
    Build a NashObjectiveExplanation from an actual Agreement.

    Uses the actual round_nash_history and final surplus values.
    Always calls this a "Nash-bargaining-inspired" heuristic.

    Parameters
    ----------
    agreement : Agreement
    floor_value : float
        The surplus floor used in log computation (from NegotiationConfig.min_surplus_floor).

    Returns
    -------
    NashObjectiveExplanation
    """
    trajectory = list(agreement.round_nash_history)
    final_value = trajectory[-1] if trajectory else float("-inf")
    initial_value = trajectory[0] if trajectory else None

    # Interpretation
    n_rounds = len(trajectory)
    if n_rounds > 1:
        delta = final_value - initial_value if initial_value is not None else 0.0
        direction = "improved" if delta > 0 else "did not improve" if delta < 0 else "did not change"
        interp = (
            f"The log-Nash objective started at {initial_value:.6f} and ended at {final_value:.6f} "
            f"over {n_rounds} rounds ({direction} by {abs(delta):.6f}). "
            f"Higher values indicate better joint outcomes above BATNA. "
            f"Negative surplus contributions are floor-clamped to log({floor_value:.0e})."
        )
    else:
        interp = (
            f"The log-Nash objective is {final_value:.6f}. "
            f"Negative surplus contributions are floor-clamped to log({floor_value:.0e}). "
            f"Higher values indicate better joint outcomes above BATNA."
        )

    return NashObjectiveExplanation(
        formula="Sum_i log(max(utility_i - BATNA_utility_i, floor))",
        floor_value=floor_value,
        final_value=final_value,
        initial_value=initial_value,
        trajectory=trajectory,
        interpretation=interp,
    )


def explain_negotiation_session(
    session: NegotiationSession,
    floor_value: float = 1e-6,
) -> NegotiationExplanation:
    """
    Build a complete NegotiationExplanation from an actual NegotiationSession.

    All data is read from the NegotiationSession object.
    No values are invented or computed independently.

    Parameters
    ----------
    session : NegotiationSession
    floor_value : float
        Surplus floor from NegotiationConfig.min_surplus_floor.

    Returns
    -------
    NegotiationExplanation
    """
    if session is None:
        raise ValueError("session must not be None")

    # Round explanations
    round_explanations = [
        explain_negotiation_round(r) for r in session.rounds
    ]

    # Concession explanations (all concessions in the session)
    all_concession_explanations = [
        explain_concession(c) for c in session.concessions
    ]

    # BATNA explanations -- use Agreement data if available
    batna_explanations: List[BATNAExplanation] = []
    agreement = session.agreement

    for farmer_id in session.farmer_ids:
        # Get BATNA utility from the last round's batna_utilities if available
        batna_utility: Optional[float] = None
        batna_alloc: float = 0.0
        final_utility: Optional[float] = None
        final_alloc: Optional[float] = None

        if session.rounds:
            last_round = session.rounds[-1]
            batna_utility = last_round.batna_utilities.get(farmer_id)

        if agreement is not None:
            batna_utility = agreement.batna_utilities.get(farmer_id, batna_utility)
            final_utility = agreement.final_utilities.get(farmer_id)
            final_alloc = agreement.final_allocation.get(farmer_id)

        if batna_utility is None:
            batna_utility = 0.0

        batna_explanations.append(explain_batna(
            farmer_id=farmer_id,
            batna_utility=batna_utility,
            batna_allocation_m3=batna_alloc,
            negotiated_utility=final_utility,
            negotiated_allocation_m3=final_alloc,
        ))

    # Nash objective explanation
    if agreement is not None:
        nash_expl = explain_nash_objective(agreement, floor_value=floor_value)
        final_fairness = agreement.fairness_score
        final_utilization = agreement.water_utilization
        final_allocation = dict(agreement.final_allocation)
        final_utilities = dict(agreement.final_utilities)
        agreement_status = agreement.agreement_status.value
        termination_reason = agreement.termination_reason
    else:
        # Session in progress or no agreement yet
        nash_expl = NashObjectiveExplanation(
            formula="Sum_i log(max(utility_i - BATNA_utility_i, floor))",
            floor_value=floor_value,
            final_value=session.best_nash_objective,
            initial_value=None,
            trajectory=[],
            interpretation=(
                f"Best Nash-inspired objective found: {session.best_nash_objective:.6f}. "
                f"Session status: {session.status}."
            ),
        )
        final_fairness = 0.0
        final_utilization = 0.0
        final_allocation = dict(session.best_allocation)
        final_utilities = {}
        agreement_status = session.status.value if session.status else "in_progress"
        termination_reason = "Session in progress or not terminated."

    # Summary
    n_rounds = len(session.rounds)
    n_concessions = len(session.concessions)

    summary_parts = [
        f"Negotiation session {session.session_id}: "
        f"{n_rounds} round(s) completed, "
        f"status: {agreement_status}."
    ]
    if agreement is not None:
        summary_parts.append(
            f"Final fairness (Jain's Index): {final_fairness:.4f}. "
            f"Water utilization: {final_utilization:.2%}. "
            f"Termination reason: {termination_reason}."
        )
    if n_concessions > 0:
        summary_parts.append(f"{n_concessions} concession(s) made.")

    summary = " ".join(summary_parts)

    return NegotiationExplanation(
        session_id=session.session_id,
        scenario_id=session.scenario_id,
        farmer_ids=list(session.farmer_ids),
        available_water_m3=session.available_water_m3,
        n_rounds=n_rounds,
        agreement_status=agreement_status,
        termination_reason=termination_reason,
        round_explanations=round_explanations,
        batna_explanations=batna_explanations,
        concession_explanations=all_concession_explanations,
        nash_objective_explanation=nash_expl,
        final_fairness_score=final_fairness,
        final_water_utilization=final_utilization,
        final_allocation=final_allocation,
        final_utilities=final_utilities,
        summary=summary,
    )
