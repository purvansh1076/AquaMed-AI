"""
AquaMediAI — Negotiation Package
===================================

Phase 6: Multi-agent negotiation and mediation engine.

This is NOT an LLM system.  All negotiation decisions are deterministic
and computational.  LLM-generated text, if added in Phase 7 for
explanation, must NOT control any numerical allocation decisions.

Public Exports
--------------

Types:
    ResponseType           — ACCEPT / REQUEST_CHANGE / REJECT
    AgreementStatus        — AGREED / MAX_ROUNDS_REACHED / NO_FEASIBLE_IMPROVEMENT / FAILED
    NegotiationConfig      — configurable engine parameters
    FarmerResponse         — per-farmer evaluation result
    Proposal               — mediator candidate allocation (LP-verified)
    Concession             — farmer concession record
    NegotiationRound       — per-round audit record
    NegotiationSession     — full session record
    Agreement              — final negotiation outcome

Engine:
    NegotiationEngine      — top-level orchestrator

Mediator:
    Mediator               — candidate allocation generator
    evaluate_farmer_response   — single-farmer response evaluator
    evaluate_all_responses     — batch response evaluator
    compute_concession         — concession computation

Bargaining:
    compute_surplus            — u_i - batna_i
    compute_surpluses          — batch surplus computation
    compute_nash_product       — Π max(surplus_i, floor)
    compute_log_nash_objective — Σ log(max(surplus_i, floor))
    is_nash_improvement        — improvement check
    classify_surplus           — positive / zero / negative classification
    summarize_surpluses        — summary statistics

DISCLAIMER: All values computed from SYNTHETIC data.
"""

from app.negotiation.negotiation_types import (
    ResponseType,
    AgreementStatus,
    NegotiationConfig,
    FarmerResponse,
    Proposal,
    Concession,
    NegotiationRound,
    NegotiationSession,
    Agreement,
    make_session_id,
    make_proposal_id,
    make_concession_id,
    make_agreement_id,
)
from app.negotiation.bargaining import (
    compute_surplus,
    compute_surpluses,
    compute_nash_product,
    compute_log_nash_objective,
    is_nash_improvement,
    classify_surplus,
    summarize_surpluses,
)
from app.negotiation.mediator import (
    Mediator,
    evaluate_farmer_response,
    evaluate_all_responses,
    compute_concession,
)
from app.negotiation.negotiation_engine import NegotiationEngine

__all__ = [
    # Types
    "ResponseType",
    "AgreementStatus",
    "NegotiationConfig",
    "FarmerResponse",
    "Proposal",
    "Concession",
    "NegotiationRound",
    "NegotiationSession",
    "Agreement",
    # ID factories
    "make_session_id",
    "make_proposal_id",
    "make_concession_id",
    "make_agreement_id",
    # Bargaining
    "compute_surplus",
    "compute_surpluses",
    "compute_nash_product",
    "compute_log_nash_objective",
    "is_nash_improvement",
    "classify_surplus",
    "summarize_surpluses",
    # Mediator
    "Mediator",
    "evaluate_farmer_response",
    "evaluate_all_responses",
    "compute_concession",
    # Engine
    "NegotiationEngine",
]
