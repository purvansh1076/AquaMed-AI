"""
AquaMediAI — Negotiation Engine
================================

Phase 6: Multi-agent negotiation engine for water allocation mediation.

This is the top-level orchestrator that runs the full negotiation pipeline:

    FarmerAgent[]
          ↓
    ConflictDetector (optional — can be used upstream)
          ↓
    WaterAllocator (initial allocation)
          ↓
    Initial Allocation
          ↓
    Farmer Agents evaluate utility
          ↓
    Objections / Dissatisfaction
          ↓
    Mediator
          ↓
    Candidate concession + preference adjustment
          ↓
    WaterAllocator (re-optimization — MANDATORY)
          ↓
    Constraint verification
          ↓
    Agents evaluate new allocation
          ↓
    Agreement OR next round
          ↓
    Final feasible allocation
          ↓
    Agreement record

Design
------
- Fully deterministic: same scenario + same config = same Agreement.
- No LLM involved in any allocation decision.
- Every allocation passes through WaterAllocator (LP/constraint-verified).
- Full audit trail stored in NegotiationSession and Agreement.
- Reuses Phase 3 FarmerAgent/DigitalTwin, Phase 5 WaterAllocator, and
  Phase 5 Jain's fairness calculation — no duplication.

Termination Conditions
---------------------
1. All required farmers ACCEPT → AGREED
2. max_rounds reached → MAX_ROUNDS_REACHED (returns best allocation)
3. Nash objective did not improve for stagnation_rounds consecutive rounds
   AND no meaningful concession progress → NO_FEASIBLE_IMPROVEMENT
   (returns best allocation)
4. Unrecoverable exception → FAILED (returns initial allocation if available)

DISCLAIMER: All values are computed from SYNTHETIC data.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

from app.agents.farmer_agent import FarmerAgent
from app.agents.digital_twin import DigitalTwin, NegotiationState
from app.allocation.constraints import compute_jains_fairness_index
from app.allocation.lp_allocator import WaterAllocator, ObjectiveWeights
from app.negotiation.bargaining import (
    compute_log_nash_objective,
    compute_surplus,
    compute_surpluses,
    is_nash_improvement,
)
from app.negotiation.mediator import (
    Mediator,
    evaluate_all_responses,
)
from app.negotiation.negotiation_types import (
    Agreement,
    AgreementStatus,
    Concession,
    FarmerResponse,
    NegotiationConfig,
    NegotiationRound,
    NegotiationSession,
    Proposal,
    ResponseType,
    make_agreement_id,
    make_proposal_id,
    make_session_id,
)

logger = logging.getLogger(__name__)


class NegotiationEngine:
    """
    Multi-agent negotiation engine for water allocation.

    Orchestrates the full negotiation pipeline between FarmerAgent objects
    and the WaterAllocator.

    Parameters
    ----------
    agents : list of FarmerAgent
        Phase 3 farmer digital agents.
    available_water_m3 : float
        Total available water (m³).
    config : NegotiationConfig, optional
        Configurable parameters (max_rounds, thresholds, etc.).
    lp_weights : ObjectiveWeights, optional
        Weights for the WaterAllocator LP objective.
    scenario_id : str
        Identifier for the originating scenario.

    Usage
    -----
        engine = NegotiationEngine(agents, available_water_m3=3000.0)
        agreement = engine.run()
    """

    def __init__(
        self,
        agents: List[FarmerAgent],
        available_water_m3: float,
        config: Optional[NegotiationConfig] = None,
        lp_weights: Optional[ObjectiveWeights] = None,
        scenario_id: str = "unknown",
    ) -> None:
        if available_water_m3 < 0:
            raise ValueError(
                f"available_water_m3 must be >= 0, got {available_water_m3}"
            )
        if not agents:
            raise ValueError("agents list must not be empty")

        self._agents = list(agents)
        self._agent_map: Dict[str, FarmerAgent] = {a.farmer_id: a for a in agents}
        self._available = available_water_m3
        self._config = config or NegotiationConfig()
        self._lp_weights = lp_weights or ObjectiveWeights()
        self._scenario_id = scenario_id
        self._session: Optional[NegotiationSession] = None

        logger.info(
            "NegotiationEngine created: n=%d farmers, available=%.1f m³, "
            "max_rounds=%d, scenario=%s",
            len(agents), available_water_m3,
            self._config.max_rounds, scenario_id,
        )

    # ─── Public API ───────────────────────────────────────────────────────────

    @property
    def session(self) -> Optional[NegotiationSession]:
        """Return the active or completed negotiation session, including rounds and history."""
        return self._session

    def run(self) -> Agreement:
        """
        Run the full negotiation process and return an Agreement.

        The Agreement always contains the best feasible allocation found,
        even if no full consensus was reached.

        Algorithm
        ---------
        1. Get initial allocation via WaterAllocator.
        2. Evaluate farmer utilities + responses.
        3. If all accept → return AGREED.
        4. Otherwise, loop:
           a. Mediator computes concessions + candidate allocation (via LP).
           b. Evaluate farmer utilities + responses on new allocation.
           c. Check acceptance / stagnation / max rounds.
        5. Build and return Agreement.

        Returns
        -------
        Agreement
        """
        session_id = make_session_id()

        # ── Step 1: Initial allocation ─────────────────────────────────────────
        try:
            initial_result = self._run_allocator(self._agents, f"{self._scenario_id}_initial")
        except Exception as exc:  # noqa: BLE001
            logger.error("Initial allocation failed: %s", exc, exc_info=True)
            return self._build_failed_agreement(
                session_id=session_id,
                reason=f"Initial WaterAllocator failed: {exc}",
            )

        initial_allocation: Dict[str, float] = {
            fa.farmer_id: fa.allocated_water_m3
            for fa in initial_result.allocations
        }
        initial_fairness = initial_result.fairness_score

        # ── Step 2: Evaluate initial responses ────────────────────────────────
        initial_responses = evaluate_all_responses(
            self._agents, initial_allocation, round_number=1,
            config=self._config,
        )
        initial_utilities = {
            r.farmer_id: r.utility for r in initial_responses
        }
        initial_batna_utils = {
            a.farmer_id: a.batna.fallback_utility for a in self._agents
        }
        initial_surpluses = compute_surpluses(initial_utilities, initial_batna_utils)
        initial_nash = compute_log_nash_objective(
            list(initial_surpluses.values()),
            floor=self._config.min_surplus_floor,
        )

        # Construct initial round record
        initial_round = self._build_round_record(
            round_number=1,
            allocation=initial_allocation,
            responses=initial_responses,
            utilities=initial_utilities,
            batna_utilities=initial_batna_utils,
            surpluses=initial_surpluses,
            nash_objective=initial_nash,
            fairness_score=initial_fairness,
            proposed_changes={},
            concessions=[],
            solver_status=initial_result.solver_status.value,
            explanation=(
                f"Initial LP allocation. "
                f"Fairness={initial_fairness:.4f}, "
                f"Utilization={initial_result.utilization:.4f}, "
                f"Nash={initial_nash:.6f}."
            ),
        )

        # Build the session object
        session = NegotiationSession(
            session_id=session_id,
            scenario_id=self._scenario_id,
            farmer_ids=[a.farmer_id for a in self._agents],
            available_water_m3=self._available,
            initial_allocation=dict(initial_allocation),
            current_allocation=dict(initial_allocation),
            current_round=1,
            max_rounds=self._config.max_rounds,
            status=None,
            rounds=[initial_round],
            proposals=[
                Proposal(
                    proposal_id=make_proposal_id(1),
                    round_number=1,
                    proposed_allocation=dict(initial_allocation),
                    target_preferences={
                        a.farmer_id: a.predicted_water_demand for a in self._agents
                    },
                    nash_objective=initial_nash,
                    fairness_score=initial_fairness,
                    solver_status=initial_result.solver_status.value,
                    is_improvement=True,
                    proposed_by="initial",
                )
            ],
            concessions=[],
            utility_history=[dict(initial_utilities)],
            best_nash_objective=initial_nash,
            best_allocation=dict(initial_allocation),
            config=self._config,
        )
        self._session = session

        # ── Step 3: Check if initial allocation is already accepted ───────────
        if self._is_agreement_reached(initial_responses):
            logger.info("NegotiationEngine: AGREED after initial allocation (round 1).")
            session.status = AgreementStatus.AGREED
            agreement = self._build_agreement(
                session=session,
                final_allocation=initial_allocation,
                final_responses=initial_responses,
                final_utilities=initial_utilities,
                status=AgreementStatus.AGREED,
                termination_reason="All farmers accepted the initial LP allocation.",
                round_fairness_history=[initial_fairness],
                round_nash_history=[initial_nash],
                is_valid=initial_result.verification.is_valid,
            )
            session.agreement = agreement
            return agreement

        # ── Step 4: Negotiation loop ──────────────────────────────────────────
        mediator = Mediator(
            agents=self._agents,
            available_water_m3=self._available,
            config=self._config,
            lp_weights=self._lp_weights,
            scenario_id=self._scenario_id,
        )

        current_allocation = dict(initial_allocation)
        best_allocation = dict(initial_allocation)
        best_nash = initial_nash
        best_utilities = dict(initial_utilities)
        best_responses = list(initial_responses)
        best_fairness = initial_fairness

        round_fairness_history = [initial_fairness]
        round_nash_history = [initial_nash]
        stagnation_count = 0
        all_concessions: List[Concession] = []
        termination_reason = ""
        final_status = AgreementStatus.MAX_ROUNDS_REACHED

        for round_num in range(2, self._config.max_rounds + 1):
            session.current_round = round_num

            logger.info(
                "NegotiationEngine: starting round %d/%d",
                round_num, self._config.max_rounds,
            )

            # Mediator proposes a new allocation (runs WaterAllocator internally)
            try:
                proposal, round_concessions = mediator.mediate(
                    current_allocation=current_allocation,
                    responses=initial_responses if round_num == 2 else current_responses,
                    round_number=round_num,
                    best_nash_objective=best_nash,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Mediator failed at round %d: %s", round_num, exc, exc_info=True
                )
                final_status = AgreementStatus.FAILED
                termination_reason = f"Mediator exception at round {round_num}: {exc}"
                break

            session.proposals.append(proposal)
            session.concessions.extend(round_concessions)
            all_concessions.extend(round_concessions)

            new_allocation = proposal.proposed_allocation

            # Evaluate responses to the new proposal
            current_responses = evaluate_all_responses(
                self._agents, new_allocation, round_number=round_num,
                config=self._config,
            )
            current_utilities = {r.farmer_id: r.utility for r in current_responses}
            current_surpluses = compute_surpluses(current_utilities, initial_batna_utils)
            current_nash = proposal.nash_objective
            current_fairness = proposal.fairness_score

            # Build round record
            round_record = self._build_round_record(
                round_number=round_num,
                allocation=new_allocation,
                responses=current_responses,
                utilities=current_utilities,
                batna_utilities=initial_batna_utils,
                surpluses=current_surpluses,
                nash_objective=current_nash,
                fairness_score=current_fairness,
                proposed_changes=proposal.target_preferences,
                concessions=round_concessions,
                solver_status=proposal.solver_status,
                explanation=self._build_round_explanation(
                    round_num, current_responses, current_nash, best_nash,
                    proposal.is_improvement, stagnation_count,
                ),
            )
            session.rounds.append(round_record)
            session.utility_history.append(dict(current_utilities))
            round_fairness_history.append(current_fairness)
            round_nash_history.append(current_nash)

            # Update current allocation
            current_allocation = dict(new_allocation)
            initial_responses = current_responses  # used as "previous" in next round

            # Update best if improved (using configured minimum delta and concession progress)
            improvement = is_nash_improvement(
                current_nash, best_nash, min_delta=self._config.min_nash_improvement,
            )
            concession_progress = self._check_concession_progress(
                current_allocation, current_responses,
                best_allocation, best_nash,
            )
            
            if improvement or concession_progress:
                best_allocation = dict(new_allocation)
                best_nash = current_nash
                best_utilities = dict(current_utilities)
                best_responses = list(current_responses)
                best_fairness = current_fairness
                stagnation_count = 0
                session.best_allocation = dict(best_allocation)
                session.best_nash_objective = best_nash
            else:
                stagnation_count += 1
                logger.info(
                    "NegotiationEngine[r%d]: no improvement (stagnation=%d/%d)",
                    round_num, stagnation_count, self._config.stagnation_rounds,
                )

            # Check termination conditions

            # Condition 1: all accepted
            if self._is_agreement_reached(current_responses):
                logger.info("NegotiationEngine: AGREED at round %d.", round_num)
                final_status = AgreementStatus.AGREED
                termination_reason = (
                    f"All required farmers accepted the allocation at round {round_num}."
                )
                best_allocation = dict(new_allocation)
                best_utilities = dict(current_utilities)
                best_responses = list(current_responses)
                best_fairness = current_fairness
                break

            # Condition 2: stagnation
            if stagnation_count >= self._config.stagnation_rounds:
                # But check if there's meaningful concession progress first
                if not self._check_concession_progress(
                    current_allocation, current_responses,
                    best_allocation, best_nash,
                ):
                    logger.info(
                        "NegotiationEngine: NO_FEASIBLE_IMPROVEMENT after %d "
                        "stagnation rounds at round %d.",
                        stagnation_count, round_num,
                    )
                    final_status = AgreementStatus.NO_FEASIBLE_IMPROVEMENT
                    termination_reason = (
                        f"Nash objective did not improve for {stagnation_count} "
                        f"consecutive rounds (stagnation limit: {self._config.stagnation_rounds}). "
                        f"Returning best feasible allocation from round {round_num - stagnation_count}."
                    )
                    break
                else:
                    logger.info(
                        "NegotiationEngine: stagnation but concession progress "
                        "detected at round %d, continuing negotiation.",
                        round_num,
                    )
        else:
            # Loop completed without break → max rounds reached
            final_status = AgreementStatus.MAX_ROUNDS_REACHED
            termination_reason = (
                f"Maximum negotiation rounds ({self._config.max_rounds}) reached "
                f"without full agreement. Returning best feasible allocation found "
                f"(Nash objective: {best_nash:.6f})."
            )

        session.status = final_status

        # Verify the final best allocation
        is_valid = self._verify_allocation_physics(best_allocation)

        # Build final agreement
        final_utilities_to_use = best_utilities
        agreement = self._build_agreement(
            session=session,
            final_allocation=best_allocation,
            final_responses=best_responses,
            final_utilities=final_utilities_to_use,
            status=final_status,
            termination_reason=termination_reason,
            round_fairness_history=round_fairness_history,
            round_nash_history=round_nash_history,
            is_valid=is_valid,
        )
        agreement.concessions.extend(all_concessions)
        session.agreement = agreement

        logger.info(
            "NegotiationEngine: done. status=%s, rounds=%d, "
            "fairness=%.4f, utilization=%.4f, nash=%.6f",
            final_status.value,
            session.current_round,
            agreement.fairness_score,
            agreement.water_utilization,
            best_nash,
        )

        return agreement

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _run_allocator(
        self,
        agents: List[FarmerAgent],
        scenario_id: str,
    ):
        """Run WaterAllocator and return AllocationResult."""
        allocator = WaterAllocator(
            agents=agents,
            available_water_m3=self._available,
            weights=self._lp_weights,
            scenario_id=scenario_id,
        )
        return allocator.solve()

    def _is_agreement_reached(self, responses: List[FarmerResponse]) -> bool:
        """
        Determine if the acceptance condition for AGREED is met.

        If config.require_all_accept = True (default):
            All farmers must return ACCEPT.
        Else:
            More than half must ACCEPT AND Nash objective has improved.
        """
        if not responses:
            return False
        if self._config.require_all_accept:
            return all(r.response_type == ResponseType.ACCEPT for r in responses)
        else:
            n_accept = sum(1 for r in responses if r.response_type == ResponseType.ACCEPT)
            return n_accept > len(responses) / 2

    def _verify_allocation_physics(self, allocation: Dict[str, float]) -> bool:
        """
        Independently verify physical constraints on an allocation dict.

        Returns True if:
        - total <= available + tolerance
        - all >= 0
        - all <= maximum
        - no NaN/Inf
        """
        tolerance = 1e-6
        total = sum(allocation.values())
        if total > self._available + tolerance:
            logger.warning(
                "Physics check FAILED: total=%.4f > available=%.4f",
                total, self._available,
            )
            return False
        for fid, alloc in allocation.items():
            if math.isnan(alloc) or math.isinf(alloc):
                logger.warning("Physics check FAILED: NaN/Inf for farmer %s", fid)
                return False
            if alloc < -tolerance:
                logger.warning(
                    "Physics check FAILED: negative alloc %.6f for farmer %s",
                    alloc, fid,
                )
                return False
            agent = self._agent_map.get(fid)
            if agent and alloc > agent.maximum_water_requirement + tolerance:
                logger.warning(
                    "Physics check FAILED: alloc %.2f > max %.2f for farmer %s",
                    alloc, agent.maximum_water_requirement, fid,
                )
                return False
        return True

    def _build_round_record(
        self,
        round_number: int,
        allocation: Dict[str, float],
        responses: List[FarmerResponse],
        utilities: Dict[str, float],
        batna_utilities: Dict[str, float],
        surpluses: Dict[str, float],
        nash_objective: float,
        fairness_score: float,
        proposed_changes: Dict[str, float],
        concessions: List[Concession],
        solver_status: str,
        explanation: str,
    ) -> NegotiationRound:
        n_accept = sum(1 for r in responses if r.response_type == ResponseType.ACCEPT)
        n_req = sum(1 for r in responses if r.response_type == ResponseType.REQUEST_CHANGE)
        n_rej = sum(1 for r in responses if r.response_type == ResponseType.REJECT)

        return NegotiationRound(
            round_number=round_number,
            current_allocation=dict(allocation),
            farmer_responses=responses,
            utilities=dict(utilities),
            batna_utilities=dict(batna_utilities),
            surpluses=dict(surpluses),
            nash_objective=nash_objective,
            fairness_score=fairness_score,
            n_accepting=n_accept,
            n_requesting_change=n_req,
            n_rejecting=n_rej,
            proposed_changes=dict(proposed_changes),
            accepted_concessions=list(concessions),
            solver_status=solver_status,
            explanation=explanation,
        )

    def _build_round_explanation(
        self,
        round_num: int,
        responses: List[FarmerResponse],
        nash_obj: float,
        prev_nash: float,
        is_improvement: bool,
        stagnation_count: int,
    ) -> str:
        n_accept = sum(1 for r in responses if r.response_type == ResponseType.ACCEPT)
        n_req = sum(1 for r in responses if r.response_type == ResponseType.REQUEST_CHANGE)
        n_rej = sum(1 for r in responses if r.response_type == ResponseType.REJECT)
        delta = nash_obj - prev_nash
        return (
            f"Round {round_num}: {n_accept} accepted, {n_req} requesting change, "
            f"{n_rej} rejected. Nash obj={nash_obj:.6f} (Δ={delta:+.6f}). "
            f"Improvement: {is_improvement}. Stagnation: {stagnation_count}/{self._config.stagnation_rounds}."
        )

    def _check_concession_progress(
        self,
        current_allocation: Dict[str, float],
        current_responses: List[FarmerResponse],
        best_allocation: Dict[str, float],
        best_nash: float,
    ) -> bool:
        """
        Check if farmers are making meaningful concession progress.

        Even if the Nash objective hasn't improved, if farmers are willingly
        reducing their water requests (conceding), this should prevent
        premature stagnation termination.

        Returns True if the total concession amount exceeds the threshold.
        """
        tolerance = 1e-6
        # Calculate total water conceded relative to the best allocation
        current_total = sum(current_allocation.get(a.farmer_id, 0.0) for a in self._agents)
        best_total = sum(best_allocation.get(a.farmer_id, 0.0) for a in self._agents)
        if best_total <= tolerance:
            return False
        conceded = best_total - current_total
        progress_fraction = conceded / best_total
        return progress_fraction >= self._config.concession_progress_threshold

    def _build_failed_agreement(
        self,
        session_id: str,
        reason: str,
    ) -> Agreement:
        """Build a FAILED agreement when initial allocation itself fails."""
        empty_alloc = {a.farmer_id: 0.0 for a in self._agents}
        empty_utils = {a.farmer_id: 0.0 for a in self._agents}
        batna_utils = {a.farmer_id: a.batna.fallback_utility for a in self._agents}
        surpluses = {fid: 0.0 - batna_utils[fid] for fid in empty_utils}

        return Agreement(
            agreement_id=make_agreement_id(),
            session_id=session_id,
            final_allocation=empty_alloc,
            participating_farmers=[a.farmer_id for a in self._agents],
            final_utilities=empty_utils,
            batna_utilities=batna_utils,
            final_surplus=surpluses,
            concessions=[],
            fairness_score=0.0,
            water_utilization=0.0,
            negotiation_rounds=0,
            agreement_status=AgreementStatus.FAILED,
            termination_reason=reason,
            round_fairness_history=[],
            round_nash_history=[],
            is_physically_valid=False,
        )

    def _build_agreement(
        self,
        session: NegotiationSession,
        final_allocation: Dict[str, float],
        final_responses: List[FarmerResponse],
        final_utilities: Dict[str, float],
        status: AgreementStatus,
        termination_reason: str,
        round_fairness_history: List[float],
        round_nash_history: List[float],
        is_valid: bool,
    ) -> Agreement:
        """Build the final Agreement object from session data."""
        batna_utils = {a.farmer_id: a.batna.fallback_utility for a in self._agents}
        surpluses = compute_surpluses(final_utilities, batna_utils)

        # Fairness on final allocation
        sat_ratios = [
            min(1.0, final_allocation.get(a.farmer_id, 0.0) / a.predicted_water_demand)
            if a.predicted_water_demand > 0 else 1.0
            for a in self._agents
        ]
        fairness = compute_jains_fairness_index(sat_ratios)

        total_allocated = sum(final_allocation.values())
        utilization = total_allocated / self._available if self._available > 0 else 0.0
        utilization = min(1.0, max(0.0, utilization))

        return Agreement(
            agreement_id=make_agreement_id(),
            session_id=session.session_id,
            final_allocation=dict(final_allocation),
            participating_farmers=[a.farmer_id for a in self._agents],
            final_utilities=dict(final_utilities),
            batna_utilities=batna_utils,
            final_surplus=surpluses,
            concessions=list(session.concessions),
            fairness_score=fairness,
            water_utilization=utilization,
            negotiation_rounds=session.current_round,
            agreement_status=status,
            termination_reason=termination_reason,
            round_fairness_history=list(round_fairness_history),
            round_nash_history=list(round_nash_history),
            is_physically_valid=is_valid,
        )
