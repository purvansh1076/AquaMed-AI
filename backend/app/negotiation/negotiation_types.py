"""
AquaMediAI — Negotiation Types
================================

Typed data models for the Phase 6 multi-agent negotiation engine.

Design
------
All models are pure Python dataclasses — no ORM, no FastAPI dependency.
They are serialisable to dict/JSON for audit trails and future UI consumption.

This is NOT an LLM system.  Every field is a numerical or categorical
computational result.  No language model controls any allocation decision.

Architecture
------------
NegotiationSession
  ├── session_id, scenario_id, status
  ├── participating farmers (farmer_ids)
  ├── initial_allocation (dict: farmer_id → m³)
  ├── current_allocation (dict: farmer_id → m³)
  ├── current_round (int)
  ├── max_rounds (int)
  ├── rounds: List[NegotiationRound]
  ├── proposals: List[Proposal]
  ├── concessions: List[Concession]
  ├── utility_history: List[Dict[str,float]] (per round)
  └── agreement (Agreement | None)

Agreement
  ├── agreement_id
  ├── session_id
  ├── final_allocation (dict: farmer_id → m³)
  ├── final_utilities (dict: farmer_id → float)
  ├── batna_utilities (dict: farmer_id → float)
  ├── final_surplus (dict: farmer_id → float)
  ├── fairness_score (float)
  ├── water_utilization (float)
  ├── negotiation_rounds (int)
  ├── agreement_status (AgreementStatus)
  ├── termination_reason (str)
  └── concessions (list of Concession)

DISCLAIMER: All data in this system is SYNTHETIC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


# ─── Response type ────────────────────────────────────────────────────────────

class ResponseType(str, Enum):
    """
    Computational response from a FarmerAgent to an allocation proposal.

    Determined entirely by numerical thresholds — no LLM involved.

    ACCEPT        : Farmer's utility meets or exceeds the acceptance threshold
                    AND is above BATNA utility + minimum buffer.
    REQUEST_CHANGE: Farmer's utility is above the rejection floor but below
                    acceptance threshold. Farmer is dissatisfied but willing
                    to negotiate further.
    REJECT        : Farmer's utility is below the rejection floor OR below
                    BATNA utility (BATNA protection rule).
    """
    ACCEPT        = "ACCEPT"
    REQUEST_CHANGE = "REQUEST_CHANGE"
    REJECT        = "REJECT"


# ─── Agreement status ─────────────────────────────────────────────────────────

class AgreementStatus(str, Enum):
    """
    Final status of a negotiation session.

    AGREED                : All required farmers accepted.
    MAX_ROUNDS_REACHED    : Negotiation ended without full agreement because
                            the maximum number of rounds was exhausted.
                            The best feasible allocation found is returned.
    NO_FEASIBLE_IMPROVEMENT: The mediator could not find an allocation that
                            improved the joint Nash objective for two
                            consecutive rounds.
    FAILED                : Unrecoverable error. Initial allocation returned.
    """
    AGREED                  = "AGREED"
    MAX_ROUNDS_REACHED      = "MAX_ROUNDS_REACHED"
    NO_FEASIBLE_IMPROVEMENT = "NO_FEASIBLE_IMPROVEMENT"
    FAILED                  = "FAILED"


# ─── Negotiation configuration ────────────────────────────────────────────────

@dataclass
class NegotiationConfig:
    """
    Configurable parameters for the negotiation engine.

    Attributes
    ----------
    max_rounds : int
        Maximum number of negotiation rounds (default 5).
    acceptance_threshold : float
        Minimum utility for ACCEPT response (default 0.65).
    rejection_threshold : float
        Utility below which REJECT is triggered (default 0.35).
    min_batna_buffer : float
        Minimum utility above BATNA required for ACCEPT (default 0.02).
        Prevents accepting an outcome only marginally better than BATNA.
    min_surplus_floor : float
        Minimum surplus used in Nash log computation (default 1e-6).
        Prevents log(0) or log(negative). See bargaining.py.
    stagnation_rounds : int
        Consecutive rounds with no Nash objective improvement before
        triggering NO_FEASIBLE_IMPROVEMENT (default 2).
    concession_scale : float
        Global scale factor for concession amounts (default 1.0).
        Set < 1.0 to make all farmers less willing to concede.
    mediator_step_fraction : float
        Fraction of the gap between current and target allocation that
        the mediator proposes per round (default 0.5). In [0, 1].
    require_all_accept : bool
        If True, AGREED requires ALL farmers to accept.
        If False, AGREED when majority accept and Nash objective improves.
        Default: True.
    """
    max_rounds: int = 5
    acceptance_threshold: float = 0.65
    rejection_threshold: float = 0.35
    min_batna_buffer: float = 0.02
    min_surplus_floor: float = 1e-6
    stagnation_rounds: int = 2
    min_nash_improvement: float = 1e-4
    concession_progress_threshold: float = 0.1
    concession_scale: float = 1.0
    mediator_step_fraction: float = 0.5
    require_all_accept: bool = True

    def __post_init__(self) -> None:
        if self.max_rounds < 1:
            raise ValueError(f"max_rounds must be >= 1, got {self.max_rounds}")
        if not (0.0 <= self.acceptance_threshold <= 1.0):
            raise ValueError(
                f"acceptance_threshold must be in [0,1], got {self.acceptance_threshold}"
            )
        if not (0.0 <= self.rejection_threshold <= self.acceptance_threshold):
            raise ValueError(
                f"rejection_threshold ({self.rejection_threshold}) must be in "
                f"[0, acceptance_threshold ({self.acceptance_threshold})]"
            )
        if not (0.0 <= self.min_batna_buffer <= 1.0):
            raise ValueError(
                f"min_batna_buffer must be in [0,1], got {self.min_batna_buffer}"
            )
        if self.min_surplus_floor <= 0.0:
            raise ValueError(
                f"min_surplus_floor must be > 0, got {self.min_surplus_floor}"
            )
        if self.stagnation_rounds < 1:
            raise ValueError(
                f"stagnation_rounds must be >= 1, got {self.stagnation_rounds}"
            )
        if not (0.0 < self.mediator_step_fraction <= 1.0):
            raise ValueError(
                f"mediator_step_fraction must be in (0, 1], got {self.mediator_step_fraction}"
            )
        if not (0.0 < self.concession_scale <= 2.0):
            raise ValueError(
                f"concession_scale must be in (0, 2], got {self.concession_scale}"
            )
        if self.min_nash_improvement <= 0.0:
            raise ValueError(
                f"min_nash_improvement must be > 0, got {self.min_nash_improvement}"
            )
        if not (0.0 <= self.concession_progress_threshold <= 1.0):
            raise ValueError(
                f"concession_progress_threshold must be in [0, 1], got "
                f"{self.concession_progress_threshold}"
            )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "max_rounds": self.max_rounds,
            "acceptance_threshold": self.acceptance_threshold,
            "rejection_threshold": self.rejection_threshold,
            "min_batna_buffer": self.min_batna_buffer,
            "min_surplus_floor": self.min_surplus_floor,
            "stagnation_rounds": self.stagnation_rounds,
            "min_nash_improvement": self.min_nash_improvement,
            "concession_progress_threshold": self.concession_progress_threshold,
            "concession_scale": self.concession_scale,
            "mediator_step_fraction": self.mediator_step_fraction,
            "require_all_accept": self.require_all_accept,
        }


# ─── Farmer response ──────────────────────────────────────────────────────────

@dataclass
class FarmerResponse:
    """
    Computational response from a single FarmerAgent to a proposed allocation.

    All fields are numerical — determined by the utility function and
    configurable thresholds. No LLM generates these values.

    Attributes
    ----------
    farmer_id : str
    allocation_m3 : float
        The proposed allocation for this farmer (m³).
    utility : float
        U_i computed at the proposed allocation. In [0, 1].
    batna_utility : float
        Farmer's BATNA utility (pre-computed). In [0, 1].
    surplus : float
        utility - batna_utility. May be negative.
    response_type : ResponseType
        ACCEPT / REQUEST_CHANGE / REJECT
    is_batna_protected : bool
        True if the response was driven by BATNA protection
        (utility < batna_utility).
    satisfaction_ratio : float
        allocation / predicted_demand, clamped to [0, 1].
    minimum_met : bool
        True if allocation >= minimum_water_requirement.
    reason : str
        Human-readable explanation of why this response was chosen.
        For audit trail only. Does NOT influence allocation decisions.
    round_number : int
        Which negotiation round this response belongs to.
    """
    farmer_id: str
    allocation_m3: float
    utility: float
    batna_utility: float
    surplus: float
    response_type: ResponseType
    is_batna_protected: bool
    satisfaction_ratio: float
    minimum_met: bool
    reason: str
    round_number: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "allocation_m3": round(self.allocation_m3, 2),
            "utility": round(self.utility, 4),
            "batna_utility": round(self.batna_utility, 4),
            "surplus": round(self.surplus, 4),
            "response_type": self.response_type.value,
            "is_batna_protected": self.is_batna_protected,
            "satisfaction_ratio": round(self.satisfaction_ratio, 4),
            "minimum_met": self.minimum_met,
            "reason": self.reason,
            "round_number": self.round_number,
        }


# ─── Proposal ─────────────────────────────────────────────────────────────────

@dataclass
class Proposal:
    """
    A candidate allocation proposal from the Mediator.

    Generated by the Mediator, then validated through WaterAllocator.
    The allocation dict is always the LP-verified result — never manually
    overridden post-solve.

    Attributes
    ----------
    proposal_id : str
    round_number : int
    proposed_allocation : dict
        farmer_id → m³ (LP-verified, always satisfies H1/H2/H3).
    target_preferences : dict
        farmer_id → target_m3 sent to WaterAllocator as preference.
    nash_objective : float
        Nash log-sum objective value for this proposal.
    fairness_score : float
        Jain's Fairness Index for this proposal.
    solver_status : str
        Status from WaterAllocator (e.g. 'optimal', 'relaxed').
    is_improvement : bool
        True if this proposal improves the Nash objective vs. previous round.
    proposed_by : str
        'mediator' | 'initial'
    """
    proposal_id: str
    round_number: int
    proposed_allocation: Dict[str, float]
    target_preferences: Dict[str, float]
    nash_objective: float
    fairness_score: float
    solver_status: str
    is_improvement: bool
    proposed_by: str = "mediator"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "round_number": self.round_number,
            "proposed_allocation": {
                k: round(v, 2) for k, v in self.proposed_allocation.items()
            },
            "target_preferences": {
                k: round(v, 2) for k, v in self.target_preferences.items()
            },
            "nash_objective": round(self.nash_objective, 6),
            "fairness_score": round(self.fairness_score, 4),
            "solver_status": self.solver_status,
            "is_improvement": self.is_improvement,
            "proposed_by": self.proposed_by,
        }


# ─── Concession ───────────────────────────────────────────────────────────────

@dataclass
class Concession:
    """
    Record of a computational concession made during negotiation.

    A concession reduces a farmer's effective demand presented to the
    WaterAllocator.  It is determined by flexibility, urgency, and
    current utility — never by LLM or manual override.

    Attributes
    ----------
    concession_id : str
    farmer_id : str
    round_number : int
    previous_ask_m3 : float
    new_ask_m3 : float
    concession_amount_m3 : float
    concession_ratio : float
        concession_amount / (previous_ask - minimum_requirement)
        (fraction of available concession space used)
    flexibility_factor : float
        The farmer's flexibility score [0,1] — influences concession size.
    urgency_factor : float
        1 - urgency.  Lower urgency → more willing to concede.
    reason : str
        Computational description of concession trigger.
    """
    concession_id: str
    farmer_id: str
    round_number: int
    previous_ask_m3: float
    new_ask_m3: float
    concession_amount_m3: float
    concession_ratio: float
    flexibility_factor: float
    urgency_factor: float
    reason: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "concession_id": self.concession_id,
            "farmer_id": self.farmer_id,
            "round_number": self.round_number,
            "previous_ask_m3": round(self.previous_ask_m3, 2),
            "new_ask_m3": round(self.new_ask_m3, 2),
            "concession_amount_m3": round(self.concession_amount_m3, 2),
            "concession_ratio": round(self.concession_ratio, 4),
            "flexibility_factor": round(self.flexibility_factor, 4),
            "urgency_factor": round(self.urgency_factor, 4),
            "reason": self.reason,
        }


# ─── Negotiation round ────────────────────────────────────────────────────────

@dataclass
class NegotiationRound:
    """
    Complete audit record for a single negotiation round.

    Stored in NegotiationSession.rounds for full traceability.

    Attributes
    ----------
    round_number : int
    current_allocation : dict (farmer_id → m³)
    farmer_responses : list of FarmerResponse
    utilities : dict (farmer_id → utility float)
    batna_utilities : dict (farmer_id → batna_utility float)
    surpluses : dict (farmer_id → surplus float)
    nash_objective : float
        Nash log-sum at this round.
    fairness_score : float
        Jain's Fairness Index at this round.
    n_accepting : int
    n_requesting_change : int
    n_rejecting : int
    proposed_changes : dict (farmer_id → proposed_m3) — from mediator
    accepted_concessions : list of Concession
    solver_status : str
    explanation : str
        Human-readable description of what happened this round.
    round_start_at : str (ISO-8601 UTC)
    """
    round_number: int
    current_allocation: Dict[str, float]
    farmer_responses: List[FarmerResponse]
    utilities: Dict[str, float]
    batna_utilities: Dict[str, float]
    surpluses: Dict[str, float]
    nash_objective: float
    fairness_score: float
    n_accepting: int
    n_requesting_change: int
    n_rejecting: int
    proposed_changes: Dict[str, float]
    accepted_concessions: List[Concession]
    solver_status: str
    explanation: str
    round_start_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def is_all_accepted(self) -> bool:
        return self.n_accepting == len(self.farmer_responses) and len(self.farmer_responses) > 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "current_allocation": {
                k: round(v, 2) for k, v in self.current_allocation.items()
            },
            "farmer_responses": [r.as_dict() for r in self.farmer_responses],
            "utilities": {k: round(v, 4) for k, v in self.utilities.items()},
            "batna_utilities": {k: round(v, 4) for k, v in self.batna_utilities.items()},
            "surpluses": {k: round(v, 4) for k, v in self.surpluses.items()},
            "nash_objective": round(self.nash_objective, 6),
            "fairness_score": round(self.fairness_score, 4),
            "n_accepting": self.n_accepting,
            "n_requesting_change": self.n_requesting_change,
            "n_rejecting": self.n_rejecting,
            "proposed_changes": {
                k: round(v, 2) for k, v in self.proposed_changes.items()
            },
            "accepted_concessions": [c.as_dict() for c in self.accepted_concessions],
            "solver_status": self.solver_status,
            "explanation": self.explanation,
            "is_all_accepted": self.is_all_accepted,
            "round_start_at": self.round_start_at,
        }


# ─── Negotiation session ──────────────────────────────────────────────────────

@dataclass
class NegotiationSession:
    """
    Complete record of a multi-agent negotiation session.

    Attributes
    ----------
    session_id : str
    scenario_id : str
    farmer_ids : list of str
    available_water_m3 : float
    initial_allocation : dict (farmer_id → m³)
    current_allocation : dict (farmer_id → m³)
    current_round : int
    max_rounds : int
    status : AgreementStatus or None (None = in progress)
    rounds : List[NegotiationRound]
    proposals : List[Proposal]
    concessions : List[Concession]
    utility_history : List[Dict[str,float]] (index = round, value = {farmer_id: utility})
    best_nash_objective : float
    best_allocation : dict (farmer_id → m³)
    agreement : Agreement or None
    config : NegotiationConfig
    created_at : str (ISO-8601 UTC)
    """
    session_id: str
    scenario_id: str
    farmer_ids: List[str]
    available_water_m3: float
    initial_allocation: Dict[str, float]
    current_allocation: Dict[str, float]
    current_round: int
    max_rounds: int
    status: Optional[AgreementStatus]
    rounds: List[NegotiationRound]
    proposals: List[Proposal]
    concessions: List[Concession]
    utility_history: List[Dict[str, float]]
    best_nash_objective: float
    best_allocation: Dict[str, float]
    config: NegotiationConfig
    agreement: Optional["Agreement"] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "farmer_ids": self.farmer_ids,
            "available_water_m3": round(self.available_water_m3, 2),
            "initial_allocation": {
                k: round(v, 2) for k, v in self.initial_allocation.items()
            },
            "current_allocation": {
                k: round(v, 2) for k, v in self.current_allocation.items()
            },
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "status": self.status.value if self.status else None,
            "n_rounds_completed": len(self.rounds),
            "n_proposals": len(self.proposals),
            "n_concessions": len(self.concessions),
            "best_nash_objective": round(self.best_nash_objective, 6),
            "best_allocation": {
                k: round(v, 2) for k, v in self.best_allocation.items()
            },
            "config": self.config.as_dict(),
            "agreement": self.agreement.as_dict() if self.agreement else None,
            "created_at": self.created_at,
        }


# ─── Agreement ────────────────────────────────────────────────────────────────

@dataclass
class Agreement:
    """
    Final outcome of a negotiation session.

    Produced by the NegotiationEngine regardless of whether full agreement
    was reached — always contains the best feasible allocation found.

    IMPORTANT: status == AGREED only when the defined acceptance conditions
    are actually met (all required farmers accepted). Never labelled AGREED
    otherwise.

    Attributes
    ----------
    agreement_id : str
    session_id : str
    final_allocation : dict (farmer_id → m³)
        Always physically valid: H1, H2, H3 verified by WaterAllocator.
    participating_farmers : list of str
    final_utilities : dict (farmer_id → float)
    batna_utilities : dict (farmer_id → float)
    final_surplus : dict (farmer_id → float)
    concessions : list of Concession
    fairness_score : float
        Jain's Fairness Index on the final allocation.
    water_utilization : float
        total_allocated / available_water.
    negotiation_rounds : int
        Number of rounds that ran.
    agreement_status : AgreementStatus
    termination_reason : str
    round_fairness_history : list of float
        Fairness score per round (for UI visualisation).
    round_nash_history : list of float
        Nash objective per round.
    is_physically_valid : bool
        Final constraint verification result.
    created_at : str (ISO-8601 UTC)
    """
    agreement_id: str
    session_id: str
    final_allocation: Dict[str, float]
    participating_farmers: List[str]
    final_utilities: Dict[str, float]
    batna_utilities: Dict[str, float]
    final_surplus: Dict[str, float]
    concessions: List[Concession]
    fairness_score: float
    water_utilization: float
    negotiation_rounds: int
    agreement_status: AgreementStatus
    termination_reason: str
    round_fairness_history: List[float]
    round_nash_history: List[float]
    is_physically_valid: bool
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "agreement_id": self.agreement_id,
            "session_id": self.session_id,
            "final_allocation": {
                k: round(v, 2) for k, v in self.final_allocation.items()
            },
            "participating_farmers": self.participating_farmers,
            "final_utilities": {k: round(v, 4) for k, v in self.final_utilities.items()},
            "batna_utilities": {k: round(v, 4) for k, v in self.batna_utilities.items()},
            "final_surplus": {k: round(v, 4) for k, v in self.final_surplus.items()},
            "concessions": [c.as_dict() for c in self.concessions],
            "fairness_score": round(self.fairness_score, 4),
            "water_utilization": round(self.water_utilization, 4),
            "negotiation_rounds": self.negotiation_rounds,
            "agreement_status": self.agreement_status.value,
            "termination_reason": self.termination_reason,
            "round_fairness_history": [round(f, 4) for f in self.round_fairness_history],
            "round_nash_history": [round(n, 6) for n in self.round_nash_history],
            "is_physically_valid": self.is_physically_valid,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return (
            f"Agreement(status={self.agreement_status.value}, "
            f"rounds={self.negotiation_rounds}, "
            f"fairness={self.fairness_score:.3f}, "
            f"utilization={self.water_utilization:.3f})"
        )


# ─── Helper factory ───────────────────────────────────────────────────────────

def make_session_id() -> str:
    """Generate a unique session ID."""
    return f"session_{uuid.uuid4().hex[:12]}"


def make_proposal_id(round_number: int) -> str:
    """Generate a unique proposal ID for a given round."""
    return f"proposal_r{round_number}_{uuid.uuid4().hex[:8]}"


def make_concession_id(farmer_id: str, round_number: int) -> str:
    """Generate a unique concession ID."""
    return f"concession_{farmer_id}_r{round_number}_{uuid.uuid4().hex[:6]}"


def make_agreement_id() -> str:
    """Generate a unique agreement ID."""
    return f"agreement_{uuid.uuid4().hex[:12]}"
