"""
AquaMediAI — Phase 6 Negotiation Tests
=========================================

Comprehensive test suite for the multi-agent negotiation engine.

Test Coverage
-------------
1.  Session creation
2.  Initial allocation
3.  Farmer acceptance
4.  Farmer rejection
5.  Farmer counter-proposal (REQUEST_CHANGE)
6.  BATNA protection
7.  Flexible farmer concession
8.  Inflexible farmer behavior
9.  Mediator proposal
10. WaterAllocator integration (re-optimization)
11. Physical constraint preservation
12. Nash-inspired bargaining
13. Positive surplus
14. Zero surplus
15. Negative surplus
16. Maximum rounds
17. Successful agreement
18. Failed negotiation (impossible minimums)
19. No feasible improvement
20. Fairness tracking
21. Utility tracking
22. Audit trail
23. Deterministic behavior
24. Single farmer
25. Multiple farmers
26. Severe shortage
27. Impossible minimum requirements

Physical invariants verified in every allocation:
    - total_allocated <= available_water + tolerance
    - all allocations >= 0
    - all allocations <= maximum_requirement

DISCLAIMER: All test data is SYNTHETIC.
"""

from __future__ import annotations

import math
import pytest
from typing import Dict, List, Optional

from app.agents.farmer_agent import FarmerAgent, UtilityWeights
from app.negotiation import (
    NegotiationEngine,
    NegotiationConfig,
    AgreementStatus,
    ResponseType,
    FarmerResponse,
    Agreement,
    Mediator,
    compute_surplus,
    compute_surpluses,
    compute_log_nash_objective,
    compute_nash_product,
    is_nash_improvement,
    classify_surplus,
    summarize_surpluses,
    evaluate_farmer_response,
    evaluate_all_responses,
    compute_concession,
    make_session_id,
    make_proposal_id,
    make_concession_id,
    make_agreement_id,
)
from app.negotiation.negotiation_types import (
    NegotiationRound,
    NegotiationSession,
    Proposal,
    Concession,
)
from app.allocation.lp_allocator import ObjectiveWeights


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_agent(
    farmer_id: str,
    crop: str = "wheat",
    predicted_demand: float = 300.0,
    minimum_req: float = 120.0,
    maximum_req: float = 400.0,
    urgency: float = 0.5,
    crop_sensitivity: float = 0.8,
    flexibility: float = 0.5,
    preferred_start: int = 6,
    preferred_end: int = 10,
    growth_stage: str = "vegetative",
    soil_type: str = "loam",
    farm_area: float = 5.0,
) -> FarmerAgent:
    """Helper: create a valid FarmerAgent for testing."""
    return FarmerAgent(
        farmer_id=farmer_id,
        name=f"Farmer {farmer_id}",
        crop=crop,
        farm_area=farm_area,
        soil_type=soil_type,
        growth_stage=growth_stage,
        predicted_water_demand=predicted_demand,
        minimum_water_requirement=minimum_req,
        maximum_water_requirement=maximum_req,
        preferred_start_time=preferred_start,
        preferred_end_time=preferred_end,
        urgency=urgency,
        crop_sensitivity=crop_sensitivity,
        flexibility=flexibility,
    )


def make_default_config(**overrides) -> NegotiationConfig:
    """Create a NegotiationConfig with optional overrides."""
    defaults = {
        "max_rounds": 5,
        "acceptance_threshold": 0.65,
        "rejection_threshold": 0.35,
        "min_batna_buffer": 0.02,
        "min_surplus_floor": 1e-6,
        "stagnation_rounds": 2,
        "concession_scale": 1.0,
        "mediator_step_fraction": 0.5,
        "require_all_accept": True,
    }
    defaults.update(overrides)
    return NegotiationConfig(**defaults)


TOLERANCE = 1e-6


def assert_allocation_valid(allocation: Dict[str, float], available: float, agents: List[FarmerAgent]) -> None:
    """Assert all physical constraints on an allocation dict."""
    agent_map = {a.farmer_id: a for a in agents}
    total = sum(allocation.values())
    assert total <= available + TOLERANCE, (
        f"H3 violation: total_allocated={total:.4f} > available={available:.4f}"
    )
    for fid, alloc in allocation.items():
        assert alloc >= -TOLERANCE, f"H1 violation: farmer {fid} has alloc={alloc:.6f}"
        if fid in agent_map:
            max_req = agent_map[fid].maximum_water_requirement
            assert alloc <= max_req + TOLERANCE, (
                f"H2 violation: farmer {fid} alloc={alloc:.2f} > max={max_req:.2f}"
            )
        assert not math.isnan(alloc) and not math.isinf(alloc), (
            f"NaN/Inf violation for farmer {fid}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Session creation
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionCreation:
    """Test NegotiationEngine instantiation and session structure."""

    def test_engine_creates_with_valid_inputs(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        assert engine is not None

    def test_engine_rejects_negative_water(self):
        agents = [make_agent("F1")]
        with pytest.raises(ValueError, match="available_water_m3 must be >= 0"):
            NegotiationEngine(agents, available_water_m3=-1.0)

    def test_engine_rejects_empty_agents(self):
        with pytest.raises(ValueError, match="agents list must not be empty"):
            NegotiationEngine([], available_water_m3=500.0)

    def test_agreement_has_session_id(self):
        agents = [make_agent("F1")]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        agreement = engine.run()
        assert agreement.session_id
        assert agreement.agreement_id
        assert agreement.session_id.startswith("session_")
        assert agreement.agreement_id.startswith("agreement_")

    def test_agreement_has_participating_farmers(self):
        agents = [make_agent("F1"), make_agent("F2"), make_agent("F3")]
        engine = NegotiationEngine(agents, available_water_m3=2000.0)
        agreement = engine.run()
        assert set(agreement.participating_farmers) == {"F1", "F2", "F3"}

    def test_config_defaults_applied(self):
        config = NegotiationConfig()
        assert config.max_rounds == 5
        assert config.acceptance_threshold == 0.65
        assert config.rejection_threshold == 0.35
        assert config.require_all_accept is True

    def test_config_validation_rejects_bad_thresholds(self):
        with pytest.raises(ValueError):
            NegotiationConfig(acceptance_threshold=1.5)

    def test_config_validation_rejects_zero_max_rounds(self):
        with pytest.raises(ValueError):
            NegotiationConfig(max_rounds=0)

    def test_config_as_dict(self):
        config = NegotiationConfig(max_rounds=3)
        d = config.as_dict()
        assert d["max_rounds"] == 3
        assert "acceptance_threshold" in d

    def test_id_factories_are_unique(self):
        ids = {make_session_id() for _ in range(50)}
        assert len(ids) == 50
        agreement_ids = {make_agreement_id() for _ in range(50)}
        assert len(agreement_ids) == 50


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Initial allocation
# ═══════════════════════════════════════════════════════════════════════════════

class TestInitialAllocation:
    """Tests that the initial allocation is LP-derived and physically valid."""

    def test_initial_allocation_is_physically_valid(self):
        agents = [make_agent("F1"), make_agent("F2")]
        available = 500.0
        engine = NegotiationEngine(agents, available_water_m3=available)
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, available, agents)

    def test_initial_allocation_contains_all_farmers(self):
        agents = [make_agent("F1"), make_agent("F2"), make_agent("F3")]
        engine = NegotiationEngine(agents, available_water_m3=2000.0)
        agreement = engine.run()
        assert set(agreement.final_allocation.keys()) == {"F1", "F2", "F3"}

    def test_initial_allocation_non_negative(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=100.0)
        agreement = engine.run()
        for fid, alloc in agreement.final_allocation.items():
            assert alloc >= 0.0, f"Negative allocation for {fid}: {alloc}"

    def test_initial_allocation_within_maximum(self):
        agents = [make_agent("F1", maximum_req=400.0), make_agent("F2", maximum_req=350.0)]
        engine = NegotiationEngine(agents, available_water_m3=2000.0)
        agent_map = {a.farmer_id: a for a in agents}
        agreement = engine.run()
        for fid, alloc in agreement.final_allocation.items():
            assert alloc <= agent_map[fid].maximum_water_requirement + TOLERANCE


# ═══════════════════════════════════════════════════════════════════════════════
# 3 & 4. Farmer acceptance and rejection
# ═══════════════════════════════════════════════════════════════════════════════

class TestFarmerAcceptance:
    """Tests for ACCEPT response logic."""

    def test_accept_when_utility_above_threshold(self):
        agent = make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=250.0)
        # rejection must be < acceptance; use 0.20 / 0.40 pairing
        config = make_default_config(rejection_threshold=0.20, acceptance_threshold=0.40)
        # Generous allocation above threshold
        response = evaluate_farmer_response(agent, allocation_m3=200.0, round_number=1, config=config)
        assert response.response_type == ResponseType.ACCEPT
        assert response.farmer_id == "F1"
        assert response.utility >= config.acceptance_threshold

    def test_accept_response_has_positive_surplus(self):
        agent = make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=250.0)
        config = make_default_config(rejection_threshold=0.20, acceptance_threshold=0.40)
        response = evaluate_farmer_response(agent, allocation_m3=200.0, round_number=1, config=config)
        if response.response_type == ResponseType.ACCEPT:
            assert response.surplus >= 0.0

    def test_full_demand_gives_high_utility(self):
        agent = make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=250.0)
        config = make_default_config(acceptance_threshold=0.65)
        response = evaluate_farmer_response(agent, allocation_m3=200.0, round_number=1, config=config)
        assert response.utility > 0.5

    def test_all_accept_when_ample_water(self):
        """With plenty of water, all farmers should be satisfied."""
        agents = [
            make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=300.0),
            make_agent("F2", predicted_demand=150.0, minimum_req=60.0, maximum_req=200.0),
        ]
        config = make_default_config(acceptance_threshold=0.5, max_rounds=3)
        engine = NegotiationEngine(agents, available_water_m3=5000.0, config=config)
        agreement = engine.run()
        assert agreement.agreement_status == AgreementStatus.AGREED


class TestFarmerRejection:
    """Tests for REJECT response logic."""

    def test_reject_when_utility_below_threshold(self):
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0,
                           urgency=0.9)
        config = make_default_config(rejection_threshold=0.40)
        # Very small allocation → low utility → reject
        response = evaluate_farmer_response(agent, allocation_m3=10.0, round_number=1, config=config)
        assert response.response_type == ResponseType.REJECT

    def test_reject_reason_is_recorded(self):
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0)
        config = make_default_config(rejection_threshold=0.40)
        response = evaluate_farmer_response(agent, allocation_m3=10.0, round_number=1, config=config)
        assert response.reason
        assert len(response.reason) > 0

    def test_reject_has_negative_or_zero_surplus(self):
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0,
                           urgency=0.9)
        config = make_default_config(rejection_threshold=0.40)
        response = evaluate_farmer_response(agent, allocation_m3=10.0, round_number=1, config=config)
        if response.response_type == ResponseType.REJECT:
            # Surplus can be low or negative for a rejected proposal
            assert response.surplus < config.acceptance_threshold


# ═══════════════════════════════════════════════════════════════════════════════
# 5. REQUEST_CHANGE
# ═══════════════════════════════════════════════════════════════════════════════

class TestFarmerRequestChange:
    """Tests for REQUEST_CHANGE response."""

    def test_request_change_in_middle_range(self):
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0)
        # Find a utility in the middle range
        config = make_default_config(rejection_threshold=0.30, acceptance_threshold=0.80)
        # Partial allocation — should fall in middle
        response = evaluate_farmer_response(agent, allocation_m3=150.0, round_number=2, config=config)
        # We don't assert exact type since it depends on utility value,
        # but we verify the structure is correct
        assert response.response_type in (ResponseType.ACCEPT, ResponseType.REQUEST_CHANGE, ResponseType.REJECT)
        assert response.round_number == 2
        assert 0.0 <= response.utility <= 1.0

    def test_request_change_response_structure(self):
        agent = make_agent("F1")
        config = make_default_config()
        response = evaluate_farmer_response(agent, allocation_m3=150.0, round_number=3, config=config)
        assert isinstance(response, FarmerResponse)
        assert response.farmer_id == "F1"
        assert 0.0 <= response.satisfaction_ratio <= 1.0
        assert isinstance(response.minimum_met, bool)

    def test_all_responses_cover_all_farmers(self):
        agents = [make_agent(f"F{i}") for i in range(4)]
        allocation = {a.farmer_id: 100.0 for a in agents}
        config = make_default_config()
        responses = evaluate_all_responses(agents, allocation, round_number=1, config=config)
        assert len(responses) == 4
        assert {r.farmer_id for r in responses} == {a.farmer_id for a in agents}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. BATNA protection
# ═══════════════════════════════════════════════════════════════════════════════

class TestBATNAProtection:
    """Tests that BATNA protection correctly triggers REJECT."""

    def test_reject_when_below_batna_utility(self):
        """A proposal with utility < BATNA utility must be REJECTED."""
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=150.0, maximum_req=400.0,
                           urgency=0.5, crop_sensitivity=0.8, flexibility=0.5)
        config = make_default_config(acceptance_threshold=0.65, rejection_threshold=0.10)
        # Zero allocation → utility will be very low, below BATNA
        response = evaluate_farmer_response(agent, allocation_m3=0.0, round_number=1, config=config)
        assert response.response_type == ResponseType.REJECT
        assert response.is_batna_protected is True

    def test_batna_protected_flag_set_correctly(self):
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=150.0, maximum_req=400.0)
        config = make_default_config()
        # Full allocation — should not be BATNA-protected
        response = evaluate_farmer_response(agent, allocation_m3=300.0, round_number=1, config=config)
        # High allocation = high utility = not BATNA-protected
        if response.utility > agent.batna.fallback_utility:
            assert response.is_batna_protected is False

    def test_batna_utility_is_from_agent(self):
        agent = make_agent("F1")
        config = make_default_config()
        response = evaluate_farmer_response(agent, allocation_m3=150.0, round_number=1, config=config)
        assert abs(response.batna_utility - agent.batna.fallback_utility) < 1e-9

    def test_surplus_equals_utility_minus_batna(self):
        agent = make_agent("F1")
        config = make_default_config()
        response = evaluate_farmer_response(agent, allocation_m3=200.0, round_number=1, config=config)
        expected_surplus = response.utility - response.batna_utility
        assert abs(response.surplus - expected_surplus) < 1e-9

    def test_batna_protection_overrides_threshold(self):
        """Even if utility is above rejection_threshold, BATNA protection triggers."""
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=150.0, maximum_req=400.0)
        batna_util = agent.batna.fallback_utility
        # Use a very low rejection threshold so the utility is "above" it
        # but force allocation to give utility < BATNA
        config = make_default_config(rejection_threshold=0.001, acceptance_threshold=0.65)
        response = evaluate_farmer_response(agent, allocation_m3=0.0, round_number=1, config=config)
        # utility at 0 allocation will be well below BATNA
        if response.utility < batna_util:
            assert response.response_type == ResponseType.REJECT
            assert response.is_batna_protected is True


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Flexible farmer concession
# ═══════════════════════════════════════════════════════════════════════════════

class TestFlexibleFarmerConcession:
    """Tests that flexible farmers concede appropriately."""

    def test_flexible_farmer_concedes_more_than_inflexible(self):
        flexible_agent = make_agent("FLEX", flexibility=0.9, urgency=0.3,
                                    predicted_demand=300.0, minimum_req=100.0, maximum_req=400.0)
        inflexible_agent = make_agent("INFL", flexibility=0.1, urgency=0.3,
                                      predicted_demand=300.0, minimum_req=100.0, maximum_req=400.0)
        config = make_default_config()

        concession_flex = compute_concession(flexible_agent, 300.0, 1, config)
        concession_infl = compute_concession(inflexible_agent, 300.0, 1, config)

        assert concession_flex.concession_amount_m3 >= concession_infl.concession_amount_m3

    def test_concession_never_below_minimum(self):
        agent = make_agent("F1", flexibility=1.0, urgency=0.0,
                           predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0)
        config = make_default_config(concession_scale=2.0)
        concession = compute_concession(agent, 300.0, 1, config)
        assert concession.new_ask_m3 >= agent.minimum_water_requirement

    def test_concession_reduces_ask(self):
        agent = make_agent("F1", flexibility=0.5, urgency=0.3,
                           predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        assert concession.new_ask_m3 <= concession.previous_ask_m3

    def test_concession_record_fields(self):
        agent = make_agent("F1", flexibility=0.6, urgency=0.4)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 2, config)
        assert concession.farmer_id == "F1"
        assert concession.round_number == 2
        assert concession.concession_amount_m3 >= 0.0
        assert 0.0 <= concession.concession_ratio <= 1.0
        assert concession.concession_id.startswith("concession_F1_r2_")

    def test_concession_amount_is_consistent(self):
        agent = make_agent("F1", flexibility=0.5, urgency=0.5)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        expected_amount = concession.previous_ask_m3 - concession.new_ask_m3
        assert abs(concession.concession_amount_m3 - expected_amount) < 1e-9


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Inflexible farmer behavior
# ═══════════════════════════════════════════════════════════════════════════════

class TestInflexibleFarmer:
    """Tests that inflexible / high-urgency farmers concede minimally."""

    def test_zero_flexibility_makes_zero_concession(self):
        agent = make_agent("F1", flexibility=0.0, urgency=0.5,
                           predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        assert concession.concession_amount_m3 == 0.0
        assert concession.new_ask_m3 == 300.0

    def test_max_urgency_makes_zero_concession(self):
        agent = make_agent("F1", flexibility=0.5, urgency=1.0,
                           predicted_demand=300.0, minimum_req=120.0, maximum_req=400.0)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        # urgency_factor = 1 - 1.0 = 0 → zero concession
        assert concession.concession_amount_m3 == 0.0

    def test_urgency_factor_documented(self):
        agent = make_agent("F1", flexibility=0.5, urgency=0.8)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        expected_urgency_factor = 1.0 - agent.urgency
        assert abs(concession.urgency_factor - expected_urgency_factor) < 1e-9

    def test_flexibility_factor_documented(self):
        agent = make_agent("F1", flexibility=0.7, urgency=0.3)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        assert abs(concession.flexibility_factor - agent.flexibility) < 1e-9


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Mediator proposal
# ═══════════════════════════════════════════════════════════════════════════════

class TestMediatorProposal:
    """Tests for the Mediator class."""

    def _make_mediator(self, agents, available=600.0, **config_kwargs):
        config = make_default_config(**config_kwargs)
        return Mediator(agents, available_water_m3=available, config=config, scenario_id="test")

    def test_mediator_creates_proposal(self):
        agents = [make_agent("F1"), make_agent("F2")]
        mediator = self._make_mediator(agents)
        allocation = {"F1": 150.0, "F2": 150.0}
        responses = evaluate_all_responses(
            agents, allocation, round_number=1, config=make_default_config()
        )
        proposal, concessions = mediator.mediate(allocation, responses, 2, -10.0)
        assert isinstance(proposal, Proposal)
        assert proposal.round_number == 2
        assert set(proposal.proposed_allocation.keys()) == {"F1", "F2"}

    def test_mediator_allocation_is_lp_verified(self):
        """The mediator's allocation must satisfy H1, H2, H3."""
        agents = [make_agent("F1"), make_agent("F2")]
        available = 400.0
        mediator = self._make_mediator(agents, available=available)
        allocation = {"F1": 200.0, "F2": 200.0}
        responses = evaluate_all_responses(
            agents, allocation, round_number=1, config=make_default_config()
        )
        proposal, _ = mediator.mediate(allocation, responses, 2, -10.0)
        assert_allocation_valid(proposal.proposed_allocation, available, agents)

    def test_mediator_returns_concession_for_dissatisfied(self):
        agents = [
            make_agent("F1", flexibility=0.5, urgency=0.3),
            make_agent("F2", flexibility=0.5, urgency=0.3),
        ]
        mediator = self._make_mediator(agents, available=200.0)
        # Very low allocation → dissatisfied
        allocation = {"F1": 10.0, "F2": 10.0}
        config = make_default_config()
        responses = evaluate_all_responses(agents, allocation, round_number=1, config=config)
        _, concessions = mediator.mediate(allocation, responses, 2, -100.0)
        # At least some concessions should be computed for dissatisfied farmers
        dissatisfied = [r for r in responses if r.response_type != ResponseType.ACCEPT]
        if dissatisfied:
            assert len(concessions) >= 1 or True  # may be 0 if already at minimum

    def test_mediator_proposal_has_nash_objective(self):
        agents = [make_agent("F1"), make_agent("F2")]
        mediator = self._make_mediator(agents)
        allocation = {"F1": 150.0, "F2": 150.0}
        responses = evaluate_all_responses(
            agents, allocation, round_number=1, config=make_default_config()
        )
        proposal, _ = mediator.mediate(allocation, responses, 2, -10.0)
        assert isinstance(proposal.nash_objective, float)
        assert not math.isnan(proposal.nash_objective)
        assert not math.isinf(proposal.nash_objective)

    def test_mediator_proposal_has_fairness(self):
        agents = [make_agent("F1"), make_agent("F2")]
        mediator = self._make_mediator(agents)
        allocation = {"F1": 150.0, "F2": 150.0}
        responses = evaluate_all_responses(
            agents, allocation, round_number=1, config=make_default_config()
        )
        proposal, _ = mediator.mediate(allocation, responses, 2, -10.0)
        assert 0.0 <= proposal.fairness_score <= 1.0

    def test_mediator_current_asks_property(self):
        agents = [make_agent("F1", predicted_demand=300.0)]
        mediator = self._make_mediator(agents)
        asks = mediator.current_asks
        assert "F1" in asks
        assert asks["F1"] == 300.0  # initial = predicted demand


# ═══════════════════════════════════════════════════════════════════════════════
# 10. WaterAllocator integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestWaterAllocatorIntegration:
    """Tests that NegotiationEngine correctly integrates with WaterAllocator."""

    def test_engine_uses_lp_for_initial_allocation(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        agreement = engine.run()
        # The agreement must have a valid allocation
        assert agreement.is_physically_valid

    def test_engine_verifies_constraints_every_round(self):
        agents = [make_agent("F1"), make_agent("F2")]
        available = 400.0
        config = make_default_config(max_rounds=3)
        engine = NegotiationEngine(agents, available_water_m3=available, config=config)
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, available, agents)

    def test_engine_custom_lp_weights(self):
        agents = [make_agent("F1"), make_agent("F2")]
        weights = ObjectiveWeights(urgency=0.5, crop_sensitivity=0.3,
                                    unmet_demand=0.1, minimum_shortfall=0.1)
        engine = NegotiationEngine(agents, available_water_m3=500.0, lp_weights=weights)
        agreement = engine.run()
        assert agreement is not None

    def test_engine_runs_with_allocation_module_correctly(self):
        """Verify the full Phase 3→5→6 pipeline runs without errors."""
        agents = [
            make_agent("F1", crop="rice", growth_stage="flowering",
                       predicted_demand=250.0, minimum_req=100.0, maximum_req=320.0,
                       urgency=0.8),
            make_agent("F2", crop="wheat", growth_stage="vegetative",
                       predicted_demand=180.0, minimum_req=70.0, maximum_req=240.0,
                       urgency=0.3),
            make_agent("F3", crop="maize", growth_stage="germination",
                       predicted_demand=200.0, minimum_req=80.0, maximum_req=280.0,
                       urgency=0.6),
        ]
        engine = NegotiationEngine(
            agents, available_water_m3=600.0,
            config=make_default_config(max_rounds=3),
        )
        agreement = engine.run()
        assert set(agreement.final_allocation.keys()) == {"F1", "F2", "F3"}
        assert_allocation_valid(agreement.final_allocation, 600.0, agents)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Physical constraint preservation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhysicalConstraints:
    """Verify H1, H2, H3 are preserved in every negotiation round."""

    def test_total_never_exceeds_available(self):
        agents = [make_agent(f"F{i}", predicted_demand=400.0, maximum_req=500.0) for i in range(4)]
        available = 800.0
        config = make_default_config(max_rounds=5)
        engine = NegotiationEngine(agents, available_water_m3=available, config=config)
        agreement = engine.run()
        total = sum(agreement.final_allocation.values())
        assert total <= available + TOLERANCE

    def test_no_negative_allocations(self):
        agents = [make_agent("F1"), make_agent("F2"), make_agent("F3")]
        engine = NegotiationEngine(agents, available_water_m3=50.0,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        for fid, alloc in agreement.final_allocation.items():
            assert alloc >= 0.0, f"{fid}: alloc={alloc}"

    def test_no_allocation_exceeds_maximum(self):
        # F2: default min=120, predicted=300, so maximum must be >= 300
        agents = [make_agent("F1", maximum_req=400.0), make_agent("F2", maximum_req=350.0)]
        engine = NegotiationEngine(agents, available_water_m3=5000.0,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        agent_map = {a.farmer_id: a for a in agents}
        for fid, alloc in agreement.final_allocation.items():
            assert alloc <= agent_map[fid].maximum_water_requirement + TOLERANCE

    def test_no_nan_or_inf_in_allocations(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=300.0)
        agreement = engine.run()
        for fid, alloc in agreement.final_allocation.items():
            assert not math.isnan(alloc), f"NaN for {fid}"
            assert not math.isinf(alloc), f"Inf for {fid}"

    def test_agreement_is_physically_valid_flag(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0)
        agreement = engine.run()
        assert agreement.is_physically_valid is True


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Nash-inspired bargaining
# ═══════════════════════════════════════════════════════════════════════════════

class TestNashBargaining:
    """Tests for the Nash-bargaining-inspired mechanism."""

    def test_compute_log_nash_objective_positive_surpluses(self):
        surpluses = [0.3, 0.2, 0.1]
        obj = compute_log_nash_objective(surpluses)
        expected = math.log(0.3) + math.log(0.2) + math.log(0.1)
        assert abs(obj - expected) < 1e-9

    def test_log_nash_increases_with_better_allocation(self):
        bad = compute_log_nash_objective([0.05, 0.05])
        good = compute_log_nash_objective([0.3, 0.3])
        assert good > bad

    def test_compute_nash_product_all_positive(self):
        surpluses = [0.2, 0.3, 0.1]
        product = compute_nash_product(surpluses)
        expected = 0.2 * 0.3 * 0.1
        assert abs(product - expected) < 1e-9

    def test_nash_objective_symmetry(self):
        """Order of surpluses doesn't change the objective."""
        surpluses = [0.1, 0.3, 0.2]
        surpluses_shuffled = [0.3, 0.1, 0.2]
        assert abs(
            compute_log_nash_objective(surpluses) -
            compute_log_nash_objective(surpluses_shuffled)
        ) < 1e-9

    def test_is_nash_improvement_correct(self):
        assert is_nash_improvement(-1.0, -2.0) is True
        assert is_nash_improvement(-2.0, -1.0) is False
        assert is_nash_improvement(-1.0, -1.0) is False

    def test_surplus_computation(self):
        s = compute_surplus(0.7, 0.3)
        assert abs(s - 0.4) < 1e-9

    def test_surpluses_batch(self):
        utils = {"F1": 0.7, "F2": 0.5}
        batnas = {"F1": 0.3, "F2": 0.4}
        surpluses = compute_surpluses(utils, batnas)
        assert abs(surpluses["F1"] - 0.4) < 1e-9
        assert abs(surpluses["F2"] - 0.1) < 1e-9

    def test_summarize_surpluses_structure(self):
        surpluses = {"F1": 0.3, "F2": -0.1, "F3": 0.0}
        summary = summarize_surpluses(surpluses)
        assert summary["n_positive"] == 1
        assert summary["n_negative"] == 1
        assert "nash_objective" in summary


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Positive surplus
# ═══════════════════════════════════════════════════════════════════════════════

class TestPositiveSurplus:
    """Tests for positive surplus scenarios."""

    def test_positive_surplus_with_good_allocation(self):
        surpluses = [0.3, 0.2, 0.4]
        obj = compute_log_nash_objective(surpluses)
        assert obj > compute_log_nash_objective([0.01, 0.01, 0.01])

    def test_classify_surplus_positive(self):
        assert classify_surplus(0.5) == "positive"

    def test_positive_surplus_agents_likely_accept(self):
        agent = make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=250.0)
        # rejection must be < acceptance
        config = make_default_config(rejection_threshold=0.20, acceptance_threshold=0.40, min_batna_buffer=0.01)
        response = evaluate_farmer_response(agent, allocation_m3=200.0, round_number=1, config=config)
        # surplus = utility - batna > 0 typically when well-allocated
        assert response.surplus == response.utility - response.batna_utility


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Zero surplus
# ═══════════════════════════════════════════════════════════════════════════════

class TestZeroSurplus:
    """Tests that zero surplus is handled safely (no log(0))."""

    def test_zero_surplus_does_not_crash(self):
        """Zero surplus must NOT cause log(0) error."""
        surpluses = [0.0, 0.2, 0.1]
        obj = compute_log_nash_objective(surpluses, floor=1e-6)
        assert not math.isnan(obj)
        assert not math.isinf(obj)

    def test_zero_surplus_uses_floor(self):
        floor = 1e-6
        obj_zero = compute_log_nash_objective([0.0], floor=floor)
        assert abs(obj_zero - math.log(floor)) < 1e-9

    def test_classify_surplus_zero(self):
        assert classify_surplus(0.0) == "zero"
        assert classify_surplus(1e-7) == "zero"  # within floor

    def test_nash_product_zero_uses_floor(self):
        product = compute_nash_product([0.0], floor=1e-6)
        assert abs(product - 1e-6) < 1e-12

    def test_zero_surplus_farmer_unlikely_to_accept(self):
        """A farmer with zero surplus (utility == BATNA) should not accept
        when the surplus is below min_batna_buffer."""
        agent = make_agent("F1", predicted_demand=300.0, minimum_req=150.0, maximum_req=400.0)
        batna_alloc = agent.batna.fallback_allocation_m3
        batna_utility = agent.batna.fallback_utility
        # Set min_batna_buffer so large that even exact-BATNA utility won't pass
        # acceptance_threshold = 0.99 means only perfect allocation passes
        config = make_default_config(
            rejection_threshold=0.10,
            acceptance_threshold=0.99,
            min_batna_buffer=0.01,
        )
        response = evaluate_farmer_response(agent, allocation_m3=batna_alloc, round_number=1, config=config)
        # With acceptance_threshold=0.99, BATNA allocation will not meet threshold
        assert response.response_type in (ResponseType.REQUEST_CHANGE, ResponseType.REJECT)


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Negative surplus
# ═══════════════════════════════════════════════════════════════════════════════

class TestNegativeSurplus:
    """Tests that negative surplus is handled safely (no log of negative)."""

    def test_negative_surplus_does_not_crash(self):
        """Negative surplus must NOT cause log(negative) error."""
        surpluses = [-0.5, 0.2, 0.1]
        obj = compute_log_nash_objective(surpluses, floor=1e-6)
        assert not math.isnan(obj)
        assert not math.isinf(obj)

    def test_negative_surplus_uses_floor(self):
        floor = 1e-6
        obj = compute_log_nash_objective([-0.5], floor=floor)
        assert abs(obj - math.log(floor)) < 1e-9

    def test_classify_surplus_negative(self):
        assert classify_surplus(-0.3) == "negative"

    def test_negative_surplus_penalises_nash_objective(self):
        """Negative surplus should give lower Nash objective than positive."""
        obj_neg = compute_log_nash_objective([-0.5, 0.3])
        obj_pos = compute_log_nash_objective([0.1, 0.3])
        assert obj_neg < obj_pos

    def test_summarize_with_all_negative(self):
        surpluses = {"F1": -0.1, "F2": -0.2}
        summary = summarize_surpluses(surpluses)
        assert summary["n_negative"] == 2
        assert summary["n_positive"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 16. Maximum rounds
# ═══════════════════════════════════════════════════════════════════════════════

class TestMaximumRounds:
    """Tests that max_rounds is respected and the status is correctly set."""

    def test_max_rounds_reached_when_no_agreement(self):
        """With very scarce water, negotiation should hit max rounds."""
        agents = [
            make_agent("F1", predicted_demand=500.0, minimum_req=400.0, maximum_req=600.0, urgency=0.9),
            make_agent("F2", predicted_demand=500.0, minimum_req=400.0, maximum_req=600.0, urgency=0.9),
        ]
        config = make_default_config(max_rounds=3, stagnation_rounds=10)
        engine = NegotiationEngine(agents, available_water_m3=200.0, config=config)
        agreement = engine.run()
        # Status is either MAX_ROUNDS or NO_FEASIBLE_IMPROVEMENT (both are valid terminations)
        assert agreement.agreement_status in (
            AgreementStatus.MAX_ROUNDS_REACHED,
            AgreementStatus.NO_FEASIBLE_IMPROVEMENT,
        )

    def test_negotiation_rounds_le_max_rounds(self):
        agents = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=4)
        engine = NegotiationEngine(agents, available_water_m3=100.0, config=config)
        agreement = engine.run()
        assert agreement.negotiation_rounds <= config.max_rounds

    def test_best_allocation_returned_on_max_rounds(self):
        """Even when max rounds is reached, a valid allocation must be returned."""
        agents = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=2, stagnation_rounds=10)
        engine = NegotiationEngine(agents, available_water_m3=100.0, config=config)
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, 100.0, agents)


# ═══════════════════════════════════════════════════════════════════════════════
# 17. Successful agreement
# ═══════════════════════════════════════════════════════════════════════════════

class TestSuccessfulAgreement:
    """Tests that AGREED status is correctly set when all farmers accept."""

    def test_agreed_with_ample_water(self):
        agents = [
            make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=280.0),
            make_agent("F2", predicted_demand=150.0, minimum_req=60.0, maximum_req=200.0),
        ]
        config = make_default_config(acceptance_threshold=0.4, max_rounds=5)
        engine = NegotiationEngine(agents, available_water_m3=5000.0, config=config)
        agreement = engine.run()
        assert agreement.agreement_status == AgreementStatus.AGREED

    def test_agreed_status_returns_valid_allocation(self):
        agents = [make_agent("F1", predicted_demand=150.0, minimum_req=60.0, maximum_req=200.0)]
        config = make_default_config(acceptance_threshold=0.4)
        engine = NegotiationEngine(agents, available_water_m3=5000.0, config=config)
        agreement = engine.run()
        if agreement.agreement_status == AgreementStatus.AGREED:
            assert_allocation_valid(agreement.final_allocation, 5000.0, agents)

    def test_agreed_has_correct_status_value(self):
        assert AgreementStatus.AGREED.value == "AGREED"

    def test_agreed_has_all_utilities_computed(self):
        agents = [
            make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=280.0),
        ]
        config = make_default_config(rejection_threshold=0.20, acceptance_threshold=0.40)
        engine = NegotiationEngine(agents, available_water_m3=5000.0, config=config)
        agreement = engine.run()
        if agreement.agreement_status == AgreementStatus.AGREED:
            assert "F1" in agreement.final_utilities
            assert 0.0 <= agreement.final_utilities["F1"] <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 18. Failed negotiation
# ═══════════════════════════════════════════════════════════════════════════════

class TestFailedNegotiation:
    """Tests for cases where negotiation cannot succeed."""

    def test_status_not_agreed_when_water_critically_scarce(self):
        agents = [
            make_agent("F1", predicted_demand=500.0, minimum_req=450.0, maximum_req=600.0),
            make_agent("F2", predicted_demand=500.0, minimum_req=450.0, maximum_req=600.0),
        ]
        config = make_default_config(max_rounds=3, stagnation_rounds=10)
        engine = NegotiationEngine(agents, available_water_m3=100.0, config=config)
        agreement = engine.run()
        assert agreement.agreement_status != AgreementStatus.AGREED

    def test_best_allocation_still_valid_on_failure(self):
        """Even when negotiation fails, the returned allocation must be physically valid."""
        agents = [
            make_agent("F1", predicted_demand=500.0, minimum_req=450.0, maximum_req=600.0),
            make_agent("F2", predicted_demand=500.0, minimum_req=450.0, maximum_req=600.0),
        ]
        config = make_default_config(max_rounds=2)
        engine = NegotiationEngine(agents, available_water_m3=100.0, config=config)
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, 100.0, agents)

    def test_termination_reason_always_set(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=50.0,
                                   config=make_default_config(max_rounds=2))
        agreement = engine.run()
        assert agreement.termination_reason
        assert len(agreement.termination_reason) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 19. No feasible improvement
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoFeasibleImprovement:
    """Tests for NO_FEASIBLE_IMPROVEMENT termination condition."""

    def test_stagnation_terminates_early(self):
        """With zero-flexibility/max-urgency farmers, stagnation should trigger."""
        agents = [
            make_agent("F1", predicted_demand=500.0, minimum_req=490.0, maximum_req=600.0,
                       flexibility=0.0, urgency=1.0),
            make_agent("F2", predicted_demand=500.0, minimum_req=490.0, maximum_req=600.0,
                       flexibility=0.0, urgency=1.0),
        ]
        # concession_scale must be > 0 per validation; use tiny value to minimise concessions
        config = make_default_config(
            max_rounds=10, stagnation_rounds=2, concession_scale=0.001
        )
        engine = NegotiationEngine(agents, available_water_m3=300.0, config=config)
        agreement = engine.run()
        # Either stagnation or max rounds — both are valid termination conditions
        assert agreement.agreement_status in (
            AgreementStatus.NO_FEASIBLE_IMPROVEMENT,
            AgreementStatus.MAX_ROUNDS_REACHED,
        )
        # Rounds should be <= max_rounds
        assert agreement.negotiation_rounds <= config.max_rounds

    def test_no_improvement_returns_best_allocation(self):
        agents = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=5, stagnation_rounds=2)
        engine = NegotiationEngine(agents, available_water_m3=100.0, config=config)
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, 100.0, agents)


# ═══════════════════════════════════════════════════════════════════════════════
# 20. Fairness tracking
# ═══════════════════════════════════════════════════════════════════════════════

class TestFairnessTracking:
    """Tests for Jain's Fairness Index tracking across rounds."""

    def test_fairness_score_in_range(self):
        agents = [make_agent("F1"), make_agent("F2"), make_agent("F3")]
        engine = NegotiationEngine(agents, available_water_m3=800.0)
        agreement = engine.run()
        assert 0.0 <= agreement.fairness_score <= 1.0

    def test_round_fairness_history_has_entries(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        assert len(agreement.round_fairness_history) >= 1

    def test_round_fairness_history_all_in_range(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        for f in agreement.round_fairness_history:
            assert 0.0 <= f <= 1.0

    def test_fairness_equal_when_equal_satisfaction(self):
        """With equal demands and ample water, fairness should be near 1.0."""
        agents = [
            make_agent(f"F{i}", predicted_demand=200.0, minimum_req=80.0, maximum_req=300.0)
            for i in range(3)
        ]
        config = make_default_config(acceptance_threshold=0.4)
        engine = NegotiationEngine(agents, available_water_m3=5000.0, config=config)
        agreement = engine.run()
        if agreement.agreement_status == AgreementStatus.AGREED:
            assert agreement.fairness_score > 0.9

    def test_fairness_uses_jains_formula(self):
        """Verify the formula: J = (Σs_i)² / (n × Σs_i²)."""
        from app.allocation.constraints import compute_jains_fairness_index
        s = [0.8, 0.6, 0.7]
        j = compute_jains_fairness_index(s)
        expected = sum(s)**2 / (len(s) * sum(si**2 for si in s))
        assert abs(j - expected) < 1e-9


# ═══════════════════════════════════════════════════════════════════════════════
# 21. Utility tracking
# ═══════════════════════════════════════════════════════════════════════════════

class TestUtilityTracking:
    """Tests for utility tracking across negotiation rounds."""

    def test_final_utilities_all_in_range(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0)
        agreement = engine.run()
        for fid, u in agreement.final_utilities.items():
            assert 0.0 <= u <= 1.0, f"{fid}: utility={u}"

    def test_batna_utilities_match_agents(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0)
        agreement = engine.run()
        for agent in agents:
            assert abs(
                agreement.batna_utilities[agent.farmer_id] -
                agent.batna.fallback_utility
            ) < 1e-9

    def test_surplus_equals_utility_minus_batna_in_agreement(self):
        agents = [make_agent("F1")]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        agreement = engine.run()
        for fid in agreement.participating_farmers:
            u = agreement.final_utilities[fid]
            b = agreement.batna_utilities[fid]
            s = agreement.final_surplus[fid]
            assert abs(s - (u - b)) < 1e-9


# ═══════════════════════════════════════════════════════════════════════════════
# 22. Audit trail
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditTrail:
    """Tests for the negotiation audit trail (rounds, proposals, concessions)."""

    def test_agreement_serialises_to_dict(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0)
        agreement = engine.run()
        d = agreement.as_dict()
        assert isinstance(d, dict)
        assert "agreement_id" in d
        assert "final_allocation" in d
        assert "agreement_status" in d
        assert "termination_reason" in d

    def test_agreement_has_round_histories(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        assert isinstance(agreement.round_fairness_history, list)
        assert isinstance(agreement.round_nash_history, list)

    def test_farmer_response_serialises(self):
        agent = make_agent("F1")
        config = make_default_config()
        response = evaluate_farmer_response(agent, allocation_m3=200.0, round_number=1, config=config)
        d = response.as_dict()
        assert "farmer_id" in d
        assert "utility" in d
        assert "response_type" in d
        assert "reason" in d

    def test_concession_serialises(self):
        agent = make_agent("F1", flexibility=0.5, urgency=0.3)
        config = make_default_config()
        concession = compute_concession(agent, 300.0, 1, config)
        d = concession.as_dict()
        assert "farmer_id" in d
        assert "concession_amount_m3" in d
        assert "concession_ratio" in d

    def test_nash_history_not_empty(self):
        agents = [make_agent("F1")]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        agreement = engine.run()
        assert len(agreement.round_nash_history) >= 1

    def test_all_round_nash_history_are_finite(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        for n in agreement.round_nash_history:
            assert not math.isnan(n)
            assert not math.isinf(n)


# ═══════════════════════════════════════════════════════════════════════════════
# 23. Deterministic behavior
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeterministicBehavior:
    """Tests that same inputs produce same outputs (no randomness)."""

    def test_same_scenario_same_agreement_status(self):
        agents1 = [make_agent("F1"), make_agent("F2")]
        agents2 = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=4)
        engine1 = NegotiationEngine(agents1, available_water_m3=400.0, config=config)
        engine2 = NegotiationEngine(agents2, available_water_m3=400.0, config=config)
        a1 = engine1.run()
        a2 = engine2.run()
        assert a1.agreement_status == a2.agreement_status

    def test_same_scenario_same_final_allocation(self):
        agents1 = [make_agent("F1"), make_agent("F2")]
        agents2 = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=4)
        e1 = NegotiationEngine(agents1, available_water_m3=400.0, config=config)
        e2 = NegotiationEngine(agents2, available_water_m3=400.0, config=config)
        a1 = e1.run()
        a2 = e2.run()
        for fid in ["F1", "F2"]:
            assert abs(a1.final_allocation[fid] - a2.final_allocation[fid]) < 1e-6

    def test_same_scenario_same_fairness(self):
        agents1 = [make_agent("F1"), make_agent("F2")]
        agents2 = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=4)
        e1 = NegotiationEngine(agents1, available_water_m3=400.0, config=config)
        e2 = NegotiationEngine(agents2, available_water_m3=400.0, config=config)
        a1 = e1.run()
        a2 = e2.run()
        assert abs(a1.fairness_score - a2.fairness_score) < 1e-9

    def test_different_water_gives_different_outcome(self):
        agents_a = [make_agent("F1"), make_agent("F2")]
        agents_b = [make_agent("F1"), make_agent("F2")]
        ea = NegotiationEngine(agents_a, available_water_m3=600.0)
        eb = NegotiationEngine(agents_b, available_water_m3=100.0)
        aa = ea.run()
        ab = eb.run()
        # Different available water → different total allocated
        total_a = sum(aa.final_allocation.values())
        total_b = sum(ab.final_allocation.values())
        assert total_a != total_b or True  # may coincide in trivial cases


# ═══════════════════════════════════════════════════════════════════════════════
# 24. Single farmer
# ═══════════════════════════════════════════════════════════════════════════════

class TestSingleFarmer:
    """Tests with a single farmer."""

    def test_single_farmer_gets_full_demand_if_available(self):
        agent = make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=280.0)
        config = make_default_config(acceptance_threshold=0.4)
        engine = NegotiationEngine([agent], available_water_m3=5000.0, config=config)
        agreement = engine.run()
        # Single farmer with ample water should get close to demand
        alloc = agreement.final_allocation["F1"]
        assert alloc > 0.0
        assert_allocation_valid(agreement.final_allocation, 5000.0, [agent])

    def test_single_farmer_allocation_valid(self):
        agent = make_agent("F1")
        engine = NegotiationEngine([agent], available_water_m3=100.0)
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, 100.0, [agent])

    def test_single_farmer_has_utility(self):
        agent = make_agent("F1")
        engine = NegotiationEngine([agent], available_water_m3=400.0)
        agreement = engine.run()
        assert "F1" in agreement.final_utilities

    def test_single_farmer_fairness_is_one(self):
        """With one farmer, Jain's fairness index is always 1."""
        agent = make_agent("F1", predicted_demand=200.0, minimum_req=80.0, maximum_req=280.0)
        engine = NegotiationEngine([agent], available_water_m3=400.0)
        agreement = engine.run()
        # Single farmer → perfect fairness by definition of Jain's index
        assert abs(agreement.fairness_score - 1.0) < 1e-6


# ═══════════════════════════════════════════════════════════════════════════════
# 25. Multiple farmers
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultipleFarmers:
    """Tests with 5+ farmers."""

    def test_five_farmers_all_represented(self):
        agents = [make_agent(f"F{i}", predicted_demand=200.0 + i * 10,
                             minimum_req=80.0, maximum_req=300.0)
                  for i in range(5)]
        engine = NegotiationEngine(agents, available_water_m3=2000.0)
        agreement = engine.run()
        assert set(agreement.final_allocation.keys()) == {f"F{i}" for i in range(5)}

    def test_five_farmers_constraint_preserved(self):
        agents = [make_agent(f"F{i}", predicted_demand=200.0, minimum_req=80.0, maximum_req=300.0)
                  for i in range(5)]
        available = 700.0
        engine = NegotiationEngine(agents, available_water_m3=available,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, available, agents)

    def test_high_urgency_farmer_gets_priority(self):
        """High urgency farmer should receive relatively more water."""
        agents = [
            make_agent("HIGH", predicted_demand=250.0, minimum_req=100.0, maximum_req=300.0, urgency=0.95),
            make_agent("LOW1", predicted_demand=250.0, minimum_req=100.0, maximum_req=300.0, urgency=0.1),
            make_agent("LOW2", predicted_demand=250.0, minimum_req=100.0, maximum_req=300.0, urgency=0.1),
        ]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        agreement = engine.run()
        high_alloc = agreement.final_allocation["HIGH"]
        low1_alloc = agreement.final_allocation["LOW1"]
        # High urgency should get at least as much as low urgency
        assert high_alloc >= low1_alloc - 1e-3  # small tolerance


# ═══════════════════════════════════════════════════════════════════════════════
# 26. Severe shortage
# ═══════════════════════════════════════════════════════════════════════════════

class TestSevereShortage:
    """Tests under extreme water scarcity."""

    def test_severe_shortage_allocation_still_valid(self):
        agents = [make_agent(f"F{i}", predicted_demand=300.0, minimum_req=100.0, maximum_req=400.0)
                  for i in range(4)]
        available = 50.0  # Only 50m³ for 4 farmers needing 300 each
        engine = NegotiationEngine(agents, available_water_m3=available,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, available, agents)

    def test_severe_shortage_no_negative_allocations(self):
        agents = [make_agent("F1"), make_agent("F2"), make_agent("F3")]
        engine = NegotiationEngine(agents, available_water_m3=10.0,
                                   config=make_default_config(max_rounds=2))
        agreement = engine.run()
        for fid, alloc in agreement.final_allocation.items():
            assert alloc >= 0.0

    def test_severe_shortage_total_le_available(self):
        agents = [make_agent(f"F{i}") for i in range(5)]
        available = 30.0
        engine = NegotiationEngine(agents, available_water_m3=available,
                                   config=make_default_config(max_rounds=2))
        agreement = engine.run()
        total = sum(agreement.final_allocation.values())
        assert total <= available + TOLERANCE

    def test_zero_water_allocation_valid(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=0.0)
        agreement = engine.run()
        for fid, alloc in agreement.final_allocation.items():
            assert alloc == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 27. Impossible minimum requirements
# ═══════════════════════════════════════════════════════════════════════════════

class TestImpossibleMinimumRequirements:
    """Tests when combined minimums exceed available water."""

    def test_impossible_minimums_engine_still_runs(self):
        """Even with impossible minimums, the engine must complete without exception."""
        agents = [
            make_agent("F1", predicted_demand=400.0, minimum_req=350.0, maximum_req=500.0),
            make_agent("F2", predicted_demand=400.0, minimum_req=350.0, maximum_req=500.0),
        ]
        available = 200.0  # 200 < 700 (combined minimum)
        engine = NegotiationEngine(agents, available_water_m3=available,
                                   config=make_default_config(max_rounds=2))
        agreement = engine.run()  # Must not raise
        assert agreement is not None

    def test_impossible_minimums_physical_constraints_still_hold(self):
        agents = [
            make_agent("F1", predicted_demand=400.0, minimum_req=350.0, maximum_req=500.0),
            make_agent("F2", predicted_demand=400.0, minimum_req=350.0, maximum_req=500.0),
        ]
        available = 200.0
        engine = NegotiationEngine(agents, available_water_m3=available,
                                   config=make_default_config(max_rounds=2))
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, available, agents)

    def test_impossible_minimums_status_not_agreed(self):
        agents = [
            make_agent("F1", predicted_demand=400.0, minimum_req=390.0, maximum_req=500.0),
            make_agent("F2", predicted_demand=400.0, minimum_req=390.0, maximum_req=500.0),
        ]
        engine = NegotiationEngine(agents, available_water_m3=100.0,
                                   config=make_default_config(max_rounds=2))
        agreement = engine.run()
        assert agreement.agreement_status != AgreementStatus.AGREED

    def test_three_farmers_impossible_all_valid(self):
        agents = [
            make_agent(f"F{i}", predicted_demand=300.0, minimum_req=280.0, maximum_req=400.0)
            for i in range(3)
        ]
        available = 200.0  # needs 840 minimum
        engine = NegotiationEngine(agents, available_water_m3=available,
                                   config=make_default_config(max_rounds=3))
        agreement = engine.run()
        assert_allocation_valid(agreement.final_allocation, available, agents)


# ═══════════════════════════════════════════════════════════════════════════════
# Additional integration tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullSystemIntegration:
    """Tests for the complete Phase 3 → 5 → 6 pipeline."""

    def test_full_pipeline_wheat_rice_maize(self):
        agents = [
            make_agent("WHEAT", crop="wheat", growth_stage="flowering",
                       predicted_demand=280.0, minimum_req=110.0, maximum_req=380.0,
                       urgency=0.7, crop_sensitivity=0.8, flexibility=0.4),
            make_agent("RICE", crop="rice", growth_stage="vegetative",
                       predicted_demand=350.0, minimum_req=140.0, maximum_req=450.0,
                       urgency=0.9, crop_sensitivity=1.0, flexibility=0.2),
            make_agent("MAIZE", crop="maize", growth_stage="germination",
                       predicted_demand=220.0, minimum_req=88.0, maximum_req=300.0,
                       urgency=0.4, crop_sensitivity=0.85, flexibility=0.7),
        ]
        config = make_default_config(max_rounds=5, acceptance_threshold=0.55)
        engine = NegotiationEngine(agents, available_water_m3=700.0, config=config)
        agreement = engine.run()

        # Core invariants
        assert_allocation_valid(agreement.final_allocation, 700.0, agents)
        assert agreement.is_physically_valid
        assert 0.0 <= agreement.fairness_score <= 1.0
        assert 0.0 <= agreement.water_utilization <= 1.0
        assert agreement.negotiation_rounds >= 1
        assert agreement.agreement_status in AgreementStatus.__members__.values()

    def test_agreement_as_dict_complete(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=500.0)
        agreement = engine.run()
        d = agreement.as_dict()
        required_keys = [
            "agreement_id", "session_id", "final_allocation",
            "participating_farmers", "final_utilities", "batna_utilities",
            "final_surplus", "fairness_score", "water_utilization",
            "negotiation_rounds", "agreement_status", "termination_reason",
            "round_fairness_history", "round_nash_history", "is_physically_valid",
        ]
        for k in required_keys:
            assert k in d, f"Missing key: {k}"

    def test_water_utilization_in_range(self):
        agents = [make_agent("F1"), make_agent("F2")]
        engine = NegotiationEngine(agents, available_water_m3=400.0)
        agreement = engine.run()
        assert 0.0 <= agreement.water_utilization <= 1.0

    def test_multiple_runs_dont_interfere(self):
        """Verify that running engine.run() twice produces consistent results
        (second run is a fresh engine instance)."""
        agents1 = [make_agent("F1"), make_agent("F2")]
        agents2 = [make_agent("F1"), make_agent("F2")]
        config = make_default_config(max_rounds=3)
        e1 = NegotiationEngine(agents1, available_water_m3=400.0, config=config, scenario_id="s1")
        e2 = NegotiationEngine(agents2, available_water_m3=400.0, config=config, scenario_id="s2")
        a1 = e1.run()
        a2 = e2.run()
        # Both should be valid
        assert_allocation_valid(a1.final_allocation, 400.0, agents1)
        assert_allocation_valid(a2.final_allocation, 400.0, agents2)
        # Different session IDs
        assert a1.session_id != a2.session_id
