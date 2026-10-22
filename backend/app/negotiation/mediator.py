"""
AquaMediAI — Negotiation Mediator
===================================

Phase 6: Computational mediator for multi-agent water negotiation.

Design Philosophy
-----------------
The Mediator is a purely computational entity.  It does NOT use an LLM.
Every decision is made by numerical comparison of utility values, surpluses,
and Nash objectives.

Critical Invariants
-------------------
1. The Mediator NEVER directly bypasses the WaterAllocator.
   Every candidate allocation it produces is passed through WaterAllocator.solve()
   before being accepted as a proposal.

2. Every allocation returned by the Mediator satisfies:
   - H1: x_i >= 0          (non-negative)
   - H2: x_i <= max_i       (physical limit)
   - H3: Σ x_i <= available  (supply limit)
   These are verified by the WaterAllocator's independent constraint checker.

3. The Mediator returns the BEST feasible allocation found, even if no
   farmer accepted.  An invalid allocation is never returned.

Mediator Algorithm (per round)
------------------------------
1. Receive current allocation (dict: farmer_id → m³).
2. Receive farmer responses (List[FarmerResponse]).
3. Identify dissatisfied farmers (REQUEST_CHANGE or REJECT).
4. For each dissatisfied farmer: compute their concession (reduced ask).
5. For requesting farmers: increase preference toward target demand.
6. Build candidate preference dict for WaterAllocator.
7. Call WaterAllocator.solve() with candidate preferences.
8. Evaluate resulting utilities.
9. Compute Nash log-sum objective.
10. Accept candidate if Nash objective improves; else keep current best.
11. Return (new_allocation, concessions_made, nash_objective, is_improvement).

Farmer Response Thresholds (from NegotiationConfig)
----------------------------------------------------
ACCEPT:
    utility >= acceptance_threshold (default 0.65)
    AND utility >= batna_utility + min_batna_buffer (default 0.02)
    BATNA protection: rejection overrides if utility < batna_utility

REQUEST_CHANGE:
    utility in [rejection_threshold, acceptance_threshold)
    AND not BATNA-protected

REJECT:
    utility < rejection_threshold
    OR utility < batna_utility (BATNA protection — any threshold)

Exception to BATNA rejection:
    In a severe shortage where the WaterAllocator cannot physically allocate
    even the minimum requirement, all farmers may receive below-BATNA utility.
    In this case, the mediator records the BATNA violation in the audit trail
    but continues negotiation to find the best feasible outcome.
    The agreement status will be MAX_ROUNDS_REACHED or NO_FEASIBLE_IMPROVEMENT
    rather than AGREED.

Concession Logic
----------------
A farmer's concession amount is computed as:

    available_space = current_ask - minimum_requirement
    flexibility_factor = flexibility                          [0, 1]
    urgency_factor = 1 - urgency                             [0, 1]
    concession_ratio = flexibility * urgency_factor * concession_scale
    concession_amount = available_space * concession_ratio

    new_ask = max(minimum_requirement, current_ask - concession_amount)

Interpretation:
  - High flexibility → larger concession
  - High urgency → smaller concession (urgency_factor = 1-urgency)
  - concession_scale is global (from NegotiationConfig)
  - The new ask NEVER goes below minimum_requirement (BATNA floor)
  - A fully inflexible farmer (flexibility=0) makes zero concession
  - A fully urgent farmer (urgency=1, urgency_factor=0) makes zero concession

DISCLAIMER: All values computed from SYNTHETIC data.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Tuple

from app.agents.farmer_agent import FarmerAgent
from app.agents.utility import compute_utility
from app.allocation.constraints import compute_jains_fairness_index
from app.allocation.lp_allocator import WaterAllocator, ObjectiveWeights
from app.negotiation.bargaining import (
    compute_log_nash_objective,
    compute_surplus,
    compute_surpluses,
    is_nash_improvement,
)
from app.negotiation.negotiation_types import (
    Concession,
    FarmerResponse,
    NegotiationConfig,
    Proposal,
    ResponseType,
    make_concession_id,
    make_proposal_id,
)

logger = logging.getLogger(__name__)


# ─── Farmer response evaluator ────────────────────────────────────────────────

def evaluate_farmer_response(
    agent: FarmerAgent,
    allocation_m3: float,
    round_number: int,
    config: NegotiationConfig,
) -> FarmerResponse:
    """
    Determine a FarmerAgent's computational response to a proposed allocation.

    Response Determination (deterministic, configurable thresholds)
    ---------------------------------------------------------------
    Step 1: Compute utility at the proposed allocation.
            (Uses FarmerAgent's utility function from Phase 3)
    Step 2: Compute surplus = utility - batna_utility.
    Step 3: Check BATNA protection:
            if utility < batna_utility → REJECT (BATNA protection)
    Step 4: Apply thresholds:
            if utility >= acceptance_threshold
               AND utility >= batna_utility + min_batna_buffer:
                → ACCEPT
            elif utility >= rejection_threshold:
                → REQUEST_CHANGE
            else:
                → REJECT

    This is a pure numerical computation — no LLM involved.

    Parameters
    ----------
    agent : FarmerAgent
    allocation_m3 : float
        Proposed water allocation (m³).
    round_number : int
        Current negotiation round number.
    config : NegotiationConfig
        Configurable thresholds.

    Returns
    -------
    FarmerResponse
    """
    prefs = agent.preferences
    batna = agent.batna

    # Compute utility at proposed allocation (using preferred window timing)
    utility = compute_utility(
        allocation_m3=allocation_m3,
        predicted_demand_m3=agent.predicted_water_demand,
        minimum_requirement_m3=agent.minimum_water_requirement,
        irrigation_start_hour=agent.preferred_start_time,
        preferred_start_hour=prefs.preferred_start_hour,
        preferred_end_hour=prefs.preferred_end_hour,
        acceptable_start_hour=prefs.acceptable_start_hour,
        acceptable_end_hour=prefs.acceptable_end_hour,
        urgency=agent.urgency,
        crop_sensitivity=agent.crop_sensitivity,
        flexibility=agent.flexibility,
        weights=agent.utility_weights,
    )

    batna_utility = batna.fallback_utility
    surplus = compute_surplus(utility, batna_utility)
    satisfaction_ratio = min(1.0, allocation_m3 / agent.predicted_water_demand) if agent.predicted_water_demand > 0 else 1.0
    minimum_met = allocation_m3 >= agent.minimum_water_requirement

    # ── BATNA protection check ────────────────────────────────────────────────
    is_batna_protected = utility < batna_utility
    if is_batna_protected:
        response_type = ResponseType.REJECT
        reason = (
            f"BATNA protection: utility ({utility:.4f}) < "
            f"batna_utility ({batna_utility:.4f}). "
            f"Allocation {allocation_m3:.2f}m³ below fallback level."
        )
        logger.debug(
            "Farmer %s: REJECT (BATNA protection) utility=%.4f batna=%.4f",
            agent.farmer_id, utility, batna_utility,
        )
        return FarmerResponse(
            farmer_id=agent.farmer_id,
            allocation_m3=allocation_m3,
            utility=utility,
            batna_utility=batna_utility,
            surplus=surplus,
            response_type=response_type,
            is_batna_protected=True,
            satisfaction_ratio=satisfaction_ratio,
            minimum_met=minimum_met,
            reason=reason,
            round_number=round_number,
        )

    # ── Threshold-based response ──────────────────────────────────────────────
    accept_condition = (
        utility >= config.acceptance_threshold
        and utility >= batna_utility + config.min_batna_buffer
    )

    if accept_condition:
        response_type = ResponseType.ACCEPT
        reason = (
            f"ACCEPT: utility ({utility:.4f}) >= threshold ({config.acceptance_threshold:.2f}) "
            f"and >= batna+buffer ({batna_utility + config.min_batna_buffer:.4f}). "
            f"Allocation {allocation_m3:.2f}m³ ({satisfaction_ratio*100:.1f}% of demand)."
        )
    elif utility >= config.rejection_threshold:
        response_type = ResponseType.REQUEST_CHANGE
        reason = (
            f"REQUEST_CHANGE: utility ({utility:.4f}) in "
            f"[{config.rejection_threshold:.2f}, {config.acceptance_threshold:.2f}). "
            f"Willing to negotiate. Allocation {allocation_m3:.2f}m³ "
            f"({satisfaction_ratio*100:.1f}% of demand)."
        )
    else:
        response_type = ResponseType.REJECT
        reason = (
            f"REJECT: utility ({utility:.4f}) < rejection_threshold "
            f"({config.rejection_threshold:.2f}). "
            f"Allocation {allocation_m3:.2f}m³ ({satisfaction_ratio*100:.1f}% of demand) "
            f"insufficient."
        )

    logger.debug(
        "Farmer %s: %s utility=%.4f batna=%.4f surplus=%.4f alloc=%.1f",
        agent.farmer_id, response_type.value, utility, batna_utility,
        surplus, allocation_m3,
    )

    return FarmerResponse(
        farmer_id=agent.farmer_id,
        allocation_m3=allocation_m3,
        utility=utility,
        batna_utility=batna_utility,
        surplus=surplus,
        response_type=response_type,
        is_batna_protected=False,
        satisfaction_ratio=satisfaction_ratio,
        minimum_met=minimum_met,
        reason=reason,
        round_number=round_number,
    )


def evaluate_all_responses(
    agents: List[FarmerAgent],
    allocation: Dict[str, float],
    round_number: int,
    config: NegotiationConfig,
) -> List[FarmerResponse]:
    """
    Evaluate all farmer responses for a given allocation dict.

    Parameters
    ----------
    agents : list of FarmerAgent
    allocation : dict (farmer_id → m³)
    round_number : int
    config : NegotiationConfig

    Returns
    -------
    list of FarmerResponse (one per agent)
    """
    responses = []
    for agent in agents:
        alloc_m3 = allocation.get(agent.farmer_id, 0.0)
        response = evaluate_farmer_response(agent, alloc_m3, round_number, config)
        responses.append(response)
    return responses


# ─── Concession computer ─────────────────────────────────────────────────────

def compute_concession(
    agent: FarmerAgent,
    current_ask_m3: float,
    round_number: int,
    config: NegotiationConfig,
) -> Concession:
    """
    Compute a computational concession for a farmer.

    Algorithm
    ---------
    available_space = current_ask - minimum_requirement
    flexibility_factor = agent.flexibility
    urgency_factor = 1 - agent.urgency     (low urgency → more concession)
    concession_ratio = flexibility_factor * urgency_factor * concession_scale
    concession_amount = available_space * concession_ratio
    new_ask = max(minimum_requirement, current_ask - concession_amount)

    This ensures:
    - Flexible farmers concede more than inflexible farmers.
    - High-urgency farmers concede less (urgency_factor approaches 0).
    - The new ask NEVER goes below minimum_requirement (BATNA floor).
    - A fully inflexible farmer (flexibility=0) makes zero concession.

    Parameters
    ----------
    agent : FarmerAgent
    current_ask_m3 : float
        The farmer's current ask (m³). Starts at predicted_demand.
    round_number : int
    config : NegotiationConfig

    Returns
    -------
    Concession
    """
    min_req = agent.minimum_water_requirement
    available_space = max(0.0, current_ask_m3 - min_req)

    flexibility_factor = agent.flexibility
    urgency_factor = 1.0 - agent.urgency  # low urgency → more willing
    concession_ratio = flexibility_factor * urgency_factor * config.concession_scale
    # Clamp to [0, 1] — concession_scale could push above 1
    concession_ratio = min(1.0, max(0.0, concession_ratio))

    concession_amount = available_space * concession_ratio
    new_ask = max(min_req, current_ask_m3 - concession_amount)

    reason = (
        f"Computational concession: flexibility={flexibility_factor:.2f}, "
        f"urgency_factor={urgency_factor:.2f} (urgency={agent.urgency:.2f}), "
        f"available_space={available_space:.2f}m³, "
        f"ratio={concession_ratio:.4f}, "
        f"amount={concession_amount:.2f}m³. "
        f"Ask: {current_ask_m3:.2f} → {new_ask:.2f}m³"
    )

    logger.debug(
        "Concession[%s]: r%d ask %.1f→%.1f (flex=%.2f, urg_f=%.2f, ratio=%.4f)",
        agent.farmer_id, round_number,
        current_ask_m3, new_ask,
        flexibility_factor, urgency_factor, concession_ratio,
    )

    return Concession(
        concession_id=make_concession_id(agent.farmer_id, round_number),
        farmer_id=agent.farmer_id,
        round_number=round_number,
        previous_ask_m3=current_ask_m3,
        new_ask_m3=new_ask,
        concession_amount_m3=current_ask_m3 - new_ask,
        concession_ratio=concession_ratio,
        flexibility_factor=flexibility_factor,
        urgency_factor=urgency_factor,
        reason=reason,
    )


# ─── Mediator ─────────────────────────────────────────────────────────────────

class Mediator:
    """
    Computational Mediator for multi-agent water negotiation.

    The Mediator receives the current allocation and farmer responses,
    identifies disputed resources, generates a feasible candidate adjustment
    via the WaterAllocator, evaluates farmer utilities, and accepts the
    candidate if it improves the Nash-bargaining-inspired objective.

    Critical invariant: Every final candidate allocation MUST pass through
    WaterAllocator.solve() before being returned.  The Mediator NEVER
    manually modifies allocations and presents them as valid.

    Parameters
    ----------
    agents : list of FarmerAgent
    available_water_m3 : float
    config : NegotiationConfig
    lp_weights : ObjectiveWeights, optional
        Weights for the WaterAllocator objective.
    scenario_id : str
    """

    def __init__(
        self,
        agents: List[FarmerAgent],
        available_water_m3: float,
        config: NegotiationConfig,
        lp_weights: Optional[ObjectiveWeights] = None,
        scenario_id: str = "unknown",
    ) -> None:
        self._agents = {a.farmer_id: a for a in agents}
        self._agent_list = list(agents)
        self._available = available_water_m3
        self._config = config
        self._lp_weights = lp_weights or ObjectiveWeights()
        self._scenario_id = scenario_id

        # Current asks: start at predicted demand
        self._current_asks: Dict[str, float] = {
            a.farmer_id: a.predicted_water_demand for a in agents
        }

        logger.info(
            "Mediator created: n_farmers=%d, available=%.1f m³, scenario=%s",
            len(agents), available_water_m3, scenario_id,
        )

    # ─── Public API ───────────────────────────────────────────────────────────

    def mediate(
        self,
        current_allocation: Dict[str, float],
        responses: List[FarmerResponse],
        round_number: int,
        best_nash_objective: float,
    ) -> Tuple[Proposal, List[Concession]]:
        """
        Run one round of mediation and produce a candidate proposal.

        Algorithm
        ---------
        1. Identify dissatisfied farmers (REQUEST_CHANGE or REJECT).
        2. For dissatisfied farmers: compute concessions (reduce ask).
        3. For accepting farmers: keep current ask (no change needed).
        4. Build preference dict for WaterAllocator.
        5. Run WaterAllocator with candidate preferences.
        6. Evaluate utilities + Nash objective on the LP result.
        7. Determine if this is an improvement.
        8. Return Proposal + Concessions.

        Parameters
        ----------
        current_allocation : dict (farmer_id → m³)
        responses : list of FarmerResponse
        round_number : int
        best_nash_objective : float
            Nash objective of the current best allocation (for comparison).

        Returns
        -------
        (Proposal, List[Concession])
        """
        dissatisfied = [
            r for r in responses
            if r.response_type in (ResponseType.REQUEST_CHANGE, ResponseType.REJECT)
        ]

        logger.info(
            "Mediator[r%d]: %d/%d farmers dissatisfied",
            round_number, len(dissatisfied), len(responses),
        )

        # ── Step 1: Compute concessions for dissatisfied farmers ──────────────
        concessions: List[Concession] = []
        for resp in dissatisfied:
            agent = self._agents.get(resp.farmer_id)
            if agent is None:
                continue
            current_ask = self._current_asks[resp.farmer_id]
            concession = compute_concession(agent, current_ask, round_number, self._config)
            self._current_asks[resp.farmer_id] = concession.new_ask_m3
            concessions.append(concession)

        # ── Step 2: For accepting farmers — try to increase their ask slightly
        # toward their target demand if water is available. This is the mediator
        # "step toward target" behaviour.
        for resp in responses:
            if resp.response_type == ResponseType.ACCEPT:
                agent = self._agents.get(resp.farmer_id)
                if agent is None:
                    continue
                current_ask = self._current_asks[resp.farmer_id]
                target = agent.predicted_water_demand
                if current_ask < target:
                    # Step toward target by mediator_step_fraction
                    gap = target - current_ask
                    new_ask = current_ask + gap * self._config.mediator_step_fraction
                    self._current_asks[resp.farmer_id] = min(
                        new_ask, agent.maximum_water_requirement
                    )

        # ── Step 3: Build candidate preferences ──────────────────────────────
        # Create modified agents with updated predicted_water_demand = current_ask
        # so WaterAllocator uses the negotiated asks as the demand targets.
        candidate_agents = self._build_candidate_agents()

        # ── Step 4: Run WaterAllocator (MANDATORY — never bypass) ─────────────
        allocator = WaterAllocator(
            agents=candidate_agents,
            available_water_m3=self._available,
            weights=self._lp_weights,
            scenario_id=f"{self._scenario_id}_mediator_r{round_number}",
        )
        lp_result = allocator.solve()

        # Extract the LP-verified allocation
        proposed_allocation: Dict[str, float] = {
            fa.farmer_id: fa.allocated_water_m3
            for fa in lp_result.allocations
        }

        # ── Step 5: Evaluate utilities at the proposed allocation ──────────────
        utilities = self._evaluate_utilities(proposed_allocation)
        batna_utilities = {
            fid: self._agents[fid].batna.fallback_utility
            for fid in self._agents
        }
        surpluses = {
            fid: compute_surplus(utilities[fid], batna_utilities[fid])
            for fid in utilities
        }

        # ── Step 6: Compute Nash objective ────────────────────────────────────
        nash_obj = compute_log_nash_objective(
            list(surpluses.values()),
            floor=self._config.min_surplus_floor,
        )
        improvement = is_nash_improvement(nash_obj, best_nash_objective)

        # ── Step 7: Fairness ──────────────────────────────────────────────────
        sat_ratios = [
            min(1.0, proposed_allocation.get(fid, 0.0) / self._agents[fid].predicted_water_demand)
            if self._agents[fid].predicted_water_demand > 0 else 1.0
            for fid in self._agents
        ]
        fairness = compute_jains_fairness_index(sat_ratios)

        # ── Build proposal ────────────────────────────────────────────────────
        proposal = Proposal(
            proposal_id=make_proposal_id(round_number),
            round_number=round_number,
            proposed_allocation=proposed_allocation,
            target_preferences=dict(self._current_asks),
            nash_objective=nash_obj,
            fairness_score=fairness,
            solver_status=lp_result.solver_status.value,
            is_improvement=improvement,
            proposed_by="mediator",
        )

        logger.info(
            "Mediator[r%d]: nash_obj=%.6f (prev=%.6f, improvement=%s), "
            "fairness=%.4f, solver=%s, concessions=%d",
            round_number, nash_obj, best_nash_objective, improvement,
            fairness, lp_result.solver_status.value, len(concessions),
        )

        return proposal, concessions

    def reset_asks(self) -> None:
        """Reset all farmer asks to their predicted demand (for restart)."""
        for agent in self._agent_list:
            self._current_asks[agent.farmer_id] = agent.predicted_water_demand

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _build_candidate_agents(self) -> List[FarmerAgent]:
        """
        Build a list of FarmerAgent objects with predicted_water_demand
        replaced by the current negotiated ask.

        This allows WaterAllocator to treat the asks as the demand targets
        without modifying the original immutable agents.
        """
        candidate_agents = []
        for agent in self._agent_list:
            ask = self._current_asks[agent.farmer_id]
            # Clamp ask to [minimum, maximum]
            ask = max(agent.minimum_water_requirement,
                      min(ask, agent.maximum_water_requirement))

            # Build a new FarmerAgent with the modified demand
            try:
                candidate_agent = FarmerAgent(
                    farmer_id=agent.farmer_id,
                    name=agent.name,
                    crop=agent.crop,
                    farm_area=agent.farm_area,
                    soil_type=agent.soil_type,
                    growth_stage=agent.growth_stage,
                    predicted_water_demand=ask,
                    minimum_water_requirement=agent.minimum_water_requirement,
                    maximum_water_requirement=agent.maximum_water_requirement,
                    preferred_start_time=agent.preferred_start_time,
                    preferred_end_time=agent.preferred_end_time,
                    urgency=agent.urgency,
                    crop_sensitivity=agent.crop_sensitivity,
                    flexibility=agent.flexibility,
                    utility_weights=agent.utility_weights,
                )
                candidate_agents.append(candidate_agent)
            except ValueError as exc:
                # If the ask causes a validation error (e.g. ask < min), use agent as-is
                logger.warning(
                    "Could not build candidate agent for %s with ask=%.2f: %s. "
                    "Using original agent.",
                    agent.farmer_id, ask, exc,
                )
                candidate_agents.append(agent)

        return candidate_agents

    def _evaluate_utilities(
        self,
        allocation: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Evaluate utility for each farmer at the given allocation.

        Uses the ORIGINAL agent's demand and preferences (not the negotiated asks)
        to correctly reflect how good this allocation is for each farmer.
        """
        utilities = {}
        for fid, agent in self._agents.items():
            alloc_m3 = allocation.get(fid, 0.0)
            prefs = agent.preferences
            u = compute_utility(
                allocation_m3=alloc_m3,
                predicted_demand_m3=agent.predicted_water_demand,
                minimum_requirement_m3=agent.minimum_water_requirement,
                irrigation_start_hour=agent.preferred_start_time,
                preferred_start_hour=prefs.preferred_start_hour,
                preferred_end_hour=prefs.preferred_end_hour,
                acceptable_start_hour=prefs.acceptable_start_hour,
                acceptable_end_hour=prefs.acceptable_end_hour,
                urgency=agent.urgency,
                crop_sensitivity=agent.crop_sensitivity,
                flexibility=agent.flexibility,
                weights=agent.utility_weights,
            )
            utilities[fid] = u
        return utilities

    @property
    def current_asks(self) -> Dict[str, float]:
        """Current negotiated asks (farmer_id → m³). Read-only copy."""
        return dict(self._current_asks)
