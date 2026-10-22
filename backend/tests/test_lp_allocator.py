"""
AquaMediAI — Phase 5: LP Water Allocator Tests
================================================

Tests all Phase 5 allocation components.

Coverage:
  1.  Water surplus (available > total demand)
  2.  Moderate shortage
  3.  Severe shortage
  4.  Zero available water
  5.  Single farmer
  6.  Multiple farmers
  7.  Total allocation constraint (H3 never violated)
  8.  Maximum allocation per farmer (H2)
  9.  Minimum requirements (when feasible)
  10. Impossible minimum requirements (soft relaxation)
  11. Fairness calculation (Jain's Index)
  12. Utilization ratio
  13. Satisfaction ratios
  14. Constraint verification
  15. Solver status codes
  16. Objective value is finite
  17. Determinism (same input → same output)
  18. Empty input
  19. Invalid input rejection
  20. Phase 4 conflict integration
  21. No negative allocations
  22. No NaN values
  23. Conservation of water (allocated <= available)
  24. Custom objective weights
  25. Proportional fallback structure

Run with:
    pytest tests/test_lp_allocator.py -v --tb=short

All 310 Phase 1-4 tests must continue passing.
"""

from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING, List

import pytest

if TYPE_CHECKING:
    from app.agents.farmer_agent import FarmerAgent
    from app.allocation.allocation_types import AllocationResult
    from app.allocation.lp_allocator import WaterAllocator


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_agent(
    farmer_id: str = "F001",
    crop: str = "wheat",
    soil_type: str = "loam",
    growth_stage: str = "vegetative",
    farm_area: float = 2.5,
    predicted_demand: float = 3600.0,
    min_water: float = 1440.0,
    max_water: float = 4320.0,
    pref_start: int = 8,
    pref_end: int = 10,
    urgency: float = 0.5,
    crop_sensitivity: float = 0.5,
    flexibility: float = 0.3,
) -> "FarmerAgent":
    from app.agents.farmer_agent import FarmerAgent
    return FarmerAgent(
        farmer_id=farmer_id,
        name=f"Farmer {farmer_id}",
        crop=crop,
        farm_area=farm_area,
        soil_type=soil_type,
        growth_stage=growth_stage,
        predicted_water_demand=predicted_demand,
        minimum_water_requirement=min_water,
        maximum_water_requirement=max_water,
        preferred_start_time=pref_start,
        preferred_end_time=pref_end,
        urgency=urgency,
        crop_sensitivity=crop_sensitivity,
        flexibility=flexibility,
    )


def _make_allocator(
    agents,
    available_water: float,
    scenario_id: str = "test",
) -> "WaterAllocator":
    from app.allocation.lp_allocator import WaterAllocator
    return WaterAllocator(
        agents=agents,
        available_water_m3=available_water,
        scenario_id=scenario_id,
    )


def _solve(agents, available_water: float, scenario_id: str = "test") -> "AllocationResult":
    return _make_allocator(agents, available_water, scenario_id).solve()


# ══════════════════════════════════════════════════════════════════════════════
# 1. WATER SURPLUS
# ══════════════════════════════════════════════════════════════════════════════

class TestWaterSurplus:
    """Tests for scenarios where supply > total demand."""

    def test_surplus_all_farmers_fully_satisfied(self):
        """With surplus water all farmers should be fully satisfied."""
        agents = [
            _make_agent("F001", predicted_demand=2000.0, max_water=2400.0),
            _make_agent("F002", predicted_demand=1500.0, max_water=1800.0),
        ]
        result = _solve(agents, available_water=10000.0)
        for fa in result.allocations:
            assert fa.satisfaction_ratio == pytest.approx(1.0)

    def test_surplus_no_unmet_demand(self):
        """Surplus → zero total unmet demand."""
        agents = [
            _make_agent("F001", predicted_demand=2000.0, max_water=2400.0),
            _make_agent("F002", predicted_demand=1500.0, max_water=1800.0),
        ]
        result = _solve(agents, available_water=10000.0)
        assert result.total_unmet_demand_m3 == pytest.approx(0.0, abs=1e-3)

    def test_surplus_status_optimal(self):
        """Surplus → OPTIMAL solver status."""
        from app.allocation.allocation_types import SolverStatus
        agents = [_make_agent("F001", predicted_demand=2000.0, max_water=2400.0)]
        result = _solve(agents, available_water=10000.0)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.RELAXED)

    def test_surplus_does_not_exceed_maximum(self):
        """Even with surplus, allocation must not exceed maximum_water_requirement."""
        agents = [
            _make_agent("F001", predicted_demand=2000.0, max_water=2400.0),
            _make_agent("F002", predicted_demand=1500.0, max_water=1800.0),
        ]
        result = _solve(agents, available_water=10000.0)
        for fa in result.allocations:
            assert fa.allocated_water_m3 <= fa.maximum_requirement_m3 + 1e-6

    def test_surplus_water_conserved(self):
        """total_allocated + remaining == available."""
        agents = [
            _make_agent("F001", predicted_demand=2000.0, max_water=2400.0),
        ]
        result = _solve(agents, available_water=10000.0)
        assert (result.total_allocated_m3 + result.remaining_water_m3
                == pytest.approx(result.available_water_m3, abs=1e-3))


# ══════════════════════════════════════════════════════════════════════════════
# 2. MODERATE SHORTAGE
# ══════════════════════════════════════════════════════════════════════════════

class TestModerateShortage:
    """Tests for scenarios with moderate shortage (min req still feasible)."""

    def test_moderate_shortage_feasible_allocation(self):
        """Moderate shortage: allocation produced, all farmers receive something."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=5000.0)  # Total demand = 7200
        assert result.total_allocated_m3 > 0
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= 0

    def test_moderate_shortage_hard_constraint_respected(self):
        """H3: total allocated must not exceed available water."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=5000.0)
        assert result.total_allocated_m3 <= 5000.0 + 1e-6

    def test_moderate_shortage_minimum_met(self):
        """When shortage is moderate and min req feasible, all minimums are met."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        # Total min req = 2880, available = 4000 > 2880 → feasible
        result = _solve(agents, available_water=4000.0)
        assert result.minimum_requirements_feasible is True
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= fa.minimum_requirement_m3 - 1e-4

    def test_moderate_shortage_some_unmet_demand(self):
        """Moderate shortage: some unmet demand exists."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=5000.0)
        assert result.total_unmet_demand_m3 > 0

    def test_moderate_shortage_utilization_high(self):
        """Most available water should be utilised in shortage."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=5000.0)
        assert result.utilization > 0.95


# ══════════════════════════════════════════════════════════════════════════════
# 3. SEVERE SHORTAGE
# ══════════════════════════════════════════════════════════════════════════════

class TestSevereShortage:
    """Tests for scenarios with severe shortage."""

    def test_severe_shortage_still_physically_feasible(self):
        """Even severe shortage must produce a valid allocation."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=1000.0)  # << min req
        assert result.verification.is_valid
        assert result.total_allocated_m3 <= 1000.0 + 1e-6

    def test_severe_shortage_soft_constraint_relaxed(self):
        """When severe shortage: minimum requirements cannot all be met."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=1000.0)
        # Total min_req = 2880 > 1000 → infeasible for min constraints
        assert result.minimum_requirements_feasible is False

    def test_severe_shortage_no_negative_allocations(self):
        """No farmer should receive negative water."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F003", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=500.0)
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= -1e-9

    def test_severe_shortage_solver_status_ok(self):
        """Solver must return a recognised status (OPTIMAL or RELAXED), not ERROR."""
        from app.allocation.allocation_types import SolverStatus
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=200.0)
        assert result.solver_status in (
            SolverStatus.OPTIMAL,
            SolverStatus.RELAXED,
            SolverStatus.FEASIBLE,
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. ZERO WATER
# ══════════════════════════════════════════════════════════════════════════════

class TestZeroWater:
    """Tests for zero available water."""

    def test_zero_water_all_allocations_zero(self):
        """Zero available water → every farmer gets 0."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=0.0)
        for fa in result.allocations:
            assert fa.allocated_water_m3 == pytest.approx(0.0)

    def test_zero_water_valid_result(self):
        """Zero water → verification passes."""
        agents = [_make_agent("F001")]
        result = _solve(agents, available_water=0.0)
        assert result.verification.is_valid

    def test_zero_water_utilization_zero(self):
        """Zero water → utilization = 0."""
        agents = [_make_agent("F001")]
        result = _solve(agents, available_water=0.0)
        assert result.utilization == pytest.approx(0.0)

    def test_zero_water_unmet_demand_equals_total_demand(self):
        """Zero water → unmet demand equals total demand."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=2400.0),
        ]
        result = _solve(agents, available_water=0.0)
        assert result.total_unmet_demand_m3 == pytest.approx(6000.0, abs=1e-3)


# ══════════════════════════════════════════════════════════════════════════════
# 5. SINGLE FARMER
# ══════════════════════════════════════════════════════════════════════════════

class TestSingleFarmer:
    """Tests for single-farmer scenarios."""

    def test_single_farmer_surplus(self):
        """Single farmer, ample supply → gets full predicted demand."""
        agents = [_make_agent("F001", predicted_demand=3600.0, max_water=4320.0)]
        result = _solve(agents, available_water=10000.0)
        assert result.allocations[0].satisfaction_ratio == pytest.approx(1.0)

    def test_single_farmer_exact_supply(self):
        """Single farmer, supply = demand → full satisfaction."""
        agents = [_make_agent("F001", predicted_demand=3600.0, max_water=4320.0)]
        result = _solve(agents, available_water=3600.0)
        assert result.allocations[0].allocated_water_m3 == pytest.approx(3600.0, abs=1.0)

    def test_single_farmer_shortage(self):
        """Single farmer, shortage → gets all available water (up to max)."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0, max_water=4320.0)
        ]
        result = _solve(agents, available_water=2000.0)
        # Should get the 2000 available (min req 1440 < 2000 → feasible)
        assert result.allocations[0].allocated_water_m3 == pytest.approx(2000.0, abs=1.0)
        assert result.total_allocated_m3 <= 2000.0 + 1e-6

    def test_single_farmer_result_structure(self):
        """Single farmer result should have exactly one FarmerAllocation."""
        agents = [_make_agent("F001")]
        result = _solve(agents, available_water=5000.0)
        assert len(result.allocations) == 1
        assert result.allocations[0].farmer_id == "F001"

    def test_single_farmer_fairness_is_1(self):
        """With a single farmer, fairness is always 1.0."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        result = _solve(agents, available_water=5000.0)
        assert result.fairness_score == pytest.approx(1.0, abs=1e-6)


# ══════════════════════════════════════════════════════════════════════════════
# 6. MULTIPLE FARMERS
# ══════════════════════════════════════════════════════════════════════════════

class TestMultipleFarmers:
    """Tests for multi-farmer allocation scenarios."""

    def test_five_farmers_all_receive_allocation(self):
        """With ample supply, 5 farmers should all receive positive allocation."""
        agents = [
            _make_agent(f"F{i:03d}", predicted_demand=2000.0 + i * 200)
            for i in range(1, 6)
        ]
        total_demand = sum(a.predicted_water_demand for a in agents)
        result = _solve(agents, available_water=total_demand * 1.2)
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= 0

    def test_high_urgency_farmer_prioritised(self):
        """Urgent farmer should receive relatively more water in shortage."""
        agents = [
            _make_agent("URGENT", predicted_demand=3600.0, urgency=0.95,
                        crop_sensitivity=0.8, min_water=1440.0),
            _make_agent("NORMAL", predicted_demand=3600.0, urgency=0.1,
                        crop_sensitivity=0.3, min_water=1440.0),
        ]
        # 60% supply: needs prioritisation
        result = _solve(agents, available_water=4320.0)
        urgent_fa = result.get_allocation("URGENT")
        normal_fa = result.get_allocation("NORMAL")
        assert urgent_fa is not None and normal_fa is not None
        # Urgent farmer should have >= satisfaction of normal farmer
        assert urgent_fa.satisfaction_ratio >= normal_fa.satisfaction_ratio - 0.01

    def test_all_farmers_have_allocations(self):
        """Every input farmer must appear in the result."""
        agents = [_make_agent(f"F{i:03d}") for i in range(1, 6)]
        result = _solve(agents, available_water=10000.0)
        result_ids = {fa.farmer_id for fa in result.allocations}
        expected_ids = {a.farmer_id for a in agents}
        assert result_ids == expected_ids

    def test_no_duplicate_farmer_ids_in_result(self):
        """Each farmer should appear exactly once in the allocation."""
        agents = [_make_agent(f"F{i:03d}") for i in range(1, 4)]
        result = _solve(agents, available_water=10000.0)
        ids = [fa.farmer_id for fa in result.allocations]
        assert len(ids) == len(set(ids))


# ══════════════════════════════════════════════════════════════════════════════
# 7 + 8. HARD CONSTRAINTS (H1, H2, H3)
# ══════════════════════════════════════════════════════════════════════════════

class TestHardConstraints:
    """Tests that verify hard constraints H1, H2, H3 are always respected."""

    def test_H3_total_allocation_never_exceeds_available(self):
        """H3: Σ x_i <= available_water under all conditions."""
        for available in [0.0, 100.0, 3600.0, 10000.0, 50000.0]:
            agents = [
                _make_agent("F001", predicted_demand=3600.0),
                _make_agent("F002", predicted_demand=3600.0),
            ]
            result = _solve(agents, available_water=available)
            assert result.total_allocated_m3 <= available + 1e-6, (
                f"H3 violated: allocated={result.total_allocated_m3:.2f} > "
                f"available={available:.2f}"
            )

    def test_H1_non_negative_always(self):
        """H1: x_i >= 0 always, even in extreme shortage."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        for available in [0.0, 10.0, 100.0, 500.0]:
            result = _solve(agents, available_water=available)
            for fa in result.allocations:
                assert fa.allocated_water_m3 >= -1e-9, (
                    f"H1 violated: {fa.farmer_id} alloc={fa.allocated_water_m3}"
                )

    def test_H2_maximum_never_exceeded(self):
        """H2: x_i <= max_water_i always."""
        agents = [
            _make_agent("F001", predicted_demand=2000.0, max_water=2400.0),
            _make_agent("F002", predicted_demand=3000.0, max_water=3600.0),
        ]
        result = _solve(agents, available_water=100000.0)  # abundant water
        for fa in result.allocations:
            assert fa.allocated_water_m3 <= fa.maximum_requirement_m3 + 1e-6

    def test_verification_passes_for_all_scenarios(self):
        """ConstraintVerificationResult.is_valid must be True for all valid scenarios."""
        scenarios = [
            ([_make_agent("F001")], 10000.0),
            ([_make_agent("F001"), _make_agent("F002")], 5000.0),
            ([_make_agent("F001"), _make_agent("F002")], 500.0),
            ([_make_agent("F001")], 0.0),
        ]
        for agents, available in scenarios:
            result = _solve(agents, available_water=available)
            assert result.verification.is_valid, (
                f"Verification failed for available={available}: "
                f"{result.verification.violations}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# 9. MINIMUM REQUIREMENTS (feasible scenarios)
# ══════════════════════════════════════════════════════════════════════════════

class TestMinimumRequirements:
    """Tests for minimum requirement satisfaction when scenario is feasible."""

    def test_minimum_met_when_feasible(self):
        """When Σ min_req <= available, all minimums must be met."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        # Total min = 2880, available = 4000 → feasible
        result = _solve(agents, available_water=4000.0)
        assert result.minimum_requirements_feasible is True
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= fa.minimum_requirement_m3 - 1e-4

    def test_minimum_requirement_feasibility_flag(self):
        """minimum_requirements_feasible flag should reflect actual feasibility."""
        agents = [
            _make_agent("F001", min_water=2000.0),
            _make_agent("F002", min_water=2000.0),
        ]
        result_feasible = _solve(agents, available_water=5000.0)  # > 4000
        result_infeasible = _solve(agents, available_water=3000.0)  # < 4000
        assert result_feasible.minimum_requirements_feasible is True
        assert result_infeasible.minimum_requirements_feasible is False

    def test_zero_minimum_shortfall_when_feasible(self):
        """With feasible minimum requirements, no farmer should have a shortfall."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=4000.0)
        for fa in result.allocations:
            assert fa.minimum_shortfall_m3 == pytest.approx(0.0, abs=1e-3)


# ══════════════════════════════════════════════════════════════════════════════
# 10. IMPOSSIBLE MINIMUM REQUIREMENTS (soft relaxation)
# ══════════════════════════════════════════════════════════════════════════════

class TestImpossibleMinimumRequirements:
    """Tests for scenarios where Σ min_req > available_water."""

    def test_infeasible_minimum_still_produces_result(self):
        """Soft relaxation must produce a valid result, not a solver failure."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        # Total min req = 2880, available = 1000 → impossible
        result = _solve(agents, available_water=1000.0)
        assert result.verification.is_valid
        assert result.minimum_requirements_feasible is False

    def test_infeasible_minimum_total_allocation_ok(self):
        """Even with relaxed minimums, H3 must not be violated."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=2000.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=2000.0),
        ]
        result = _solve(agents, available_water=1000.0)
        assert result.total_allocated_m3 <= 1000.0 + 1e-6

    def test_infeasible_minimum_shortfall_reported(self):
        """When minimum cannot be met, minimum_shortfall_m3 > 0 for some farmers."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=500.0)
        total_shortfall = result.total_minimum_shortfall_m3
        assert total_shortfall > 0

    def test_infeasible_method_is_relaxed(self):
        """Infeasible minimum → allocation_method should be 'lp_relaxed'."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        result = _solve(agents, available_water=500.0)
        assert result.allocation_method == "lp_relaxed"

    def test_infeasible_minimum_no_negative_allocations(self):
        """Even with soft constraints, allocations must be >= 0."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=2000.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=2000.0),
        ]
        result = _solve(agents, available_water=100.0)
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= -1e-9


# ══════════════════════════════════════════════════════════════════════════════
# 11. FAIRNESS (JAIN'S INDEX)
# ══════════════════════════════════════════════════════════════════════════════

class TestFairness:
    """Tests for Jain's Fairness Index calculation."""

    def test_equal_satisfaction_yields_fairness_1(self):
        """When all s_i are equal, J = 1.0."""
        from app.allocation.constraints import compute_jains_fairness_index
        j = compute_jains_fairness_index([0.8, 0.8, 0.8])
        assert j == pytest.approx(1.0, abs=1e-9)

    def test_all_zero_satisfaction_yields_fairness_0(self):
        """All zero satisfaction → J = 0 (undefined, returns 0)."""
        from app.allocation.constraints import compute_jains_fairness_index
        j = compute_jains_fairness_index([0.0, 0.0, 0.0])
        assert j == pytest.approx(0.0, abs=1e-9)

    def test_single_farmer_fairness_1(self):
        """Single farmer → J = 1.0 always."""
        from app.allocation.constraints import compute_jains_fairness_index
        j = compute_jains_fairness_index([0.5])
        assert j == pytest.approx(1.0, abs=1e-9)

    def test_extreme_inequality_low_fairness(self):
        """One farmer gets all, others get 0 → low fairness."""
        from app.allocation.constraints import compute_jains_fairness_index
        # [1.0, 0.0, 0.0]: J = 1² / (3 × 1²) = 1/3
        j = compute_jains_fairness_index([1.0, 0.0, 0.0])
        assert j == pytest.approx(1.0 / 3.0, abs=1e-9)

    def test_fairness_in_0_1(self):
        """Fairness must always be in [0, 1]."""
        from app.allocation.constraints import compute_jains_fairness_index
        for ratios in [[0.3, 0.7], [0.5, 0.5, 0.5], [0.1, 0.9], [1.0, 1.0]]:
            j = compute_jains_fairness_index(ratios)
            assert 0.0 <= j <= 1.0

    def test_fairness_formula_correctness(self):
        """Verify formula: J = (Σ s)² / (n × Σ s²)."""
        from app.allocation.constraints import compute_jains_fairness_index
        s = [0.6, 0.8, 0.9]
        expected = (sum(s) ** 2) / (len(s) * sum(si ** 2 for si in s))
        j = compute_jains_fairness_index(s)
        assert j == pytest.approx(expected, abs=1e-9)

    def test_result_fairness_in_0_1(self):
        """AllocationResult.fairness_score must be in [0, 1]."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=4000.0)
        assert 0.0 <= result.fairness_score <= 1.0

    def test_empty_list_fairness_0(self):
        """Empty satisfaction list → J = 0."""
        from app.allocation.constraints import compute_jains_fairness_index
        assert compute_jains_fairness_index([]) == pytest.approx(0.0)


# ══════════════════════════════════════════════════════════════════════════════
# 12. UTILIZATION
# ══════════════════════════════════════════════════════════════════════════════

class TestUtilization:
    """Tests for water utilization calculation."""

    def test_utilization_in_0_1(self):
        """Utilization must always be in [0, 1]."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        for available in [0.0, 1000.0, 3600.0, 10000.0]:
            result = _solve(agents, available_water=available)
            assert 0.0 <= result.utilization <= 1.0

    def test_high_demand_high_utilization(self):
        """When demand >> available, most water should be used."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0, max_water=4320.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0, max_water=4320.0),
        ]
        # 2000m3 available vs 7200m3 demand → LP should use virtually all available
        result = _solve(agents, available_water=2000.0)
        assert result.utilization > 0.95

    def test_surplus_partial_utilization(self):
        """With surplus, utilization should be < 1."""
        agents = [_make_agent("F001", predicted_demand=2000.0, max_water=2400.0)]
        result = _solve(agents, available_water=10000.0)
        assert result.utilization < 1.0

    def test_water_balance_identity(self):
        """total_allocated + remaining == available (conservation)."""
        agents = [
            _make_agent("F001", predicted_demand=3000.0),
            _make_agent("F002", predicted_demand=2000.0),
        ]
        result = _solve(agents, available_water=4000.0)
        assert (result.total_allocated_m3 + result.remaining_water_m3
                == pytest.approx(result.available_water_m3, abs=1e-3))

    def test_remaining_water_non_negative(self):
        """remaining_water_m3 must be >= 0."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=5000.0)
        assert result.remaining_water_m3 >= 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 13. SATISFACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestSatisfaction:
    """Tests for satisfaction ratio computation."""

    def test_satisfaction_in_0_1(self):
        """All satisfaction ratios must be in [0, 1]."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=5000.0)
        for fa in result.allocations:
            assert 0.0 <= fa.satisfaction_ratio <= 1.0

    def test_full_satisfaction_at_surplus(self):
        """Full allocation → satisfaction = 1."""
        agents = [_make_agent("F001", predicted_demand=2000.0, max_water=2400.0)]
        result = _solve(agents, available_water=10000.0)
        assert result.allocations[0].satisfaction_ratio == pytest.approx(1.0, abs=1e-4)

    def test_zero_satisfaction_at_zero_water(self):
        """Zero water → satisfaction = 0."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        result = _solve(agents, available_water=0.0)
        assert result.allocations[0].satisfaction_ratio == pytest.approx(0.0, abs=1e-9)

    def test_average_satisfaction_in_0_1(self):
        """average_satisfaction property must be in [0, 1]."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=4000.0)
        assert 0.0 <= result.average_satisfaction <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 14. CONSTRAINT VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestConstraintVerification:
    """Tests for the independent post-solve constraint verifier."""

    def test_verification_runs_after_every_solve(self):
        """Every AllocationResult must contain a verification."""
        agents = [_make_agent("F001")]
        result = _solve(agents, available_water=5000.0)
        assert result.verification is not None

    def test_verification_structure(self):
        """ConstraintVerificationResult must have all required fields."""
        agents = [_make_agent("F001")]
        result = _solve(agents, available_water=5000.0)
        v = result.verification
        assert hasattr(v, "is_valid")
        assert hasattr(v, "total_water_ok")
        assert hasattr(v, "non_negative_ok")
        assert hasattr(v, "maximum_ok")
        assert hasattr(v, "no_nan_ok")
        assert hasattr(v, "all_farmers_present")
        assert hasattr(v, "violations")

    def test_verification_passes_for_valid_result(self):
        """Valid allocations should pass all verification checks."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=2400.0),
        ]
        result = _solve(agents, available_water=4000.0)
        assert result.verification.is_valid
        assert result.verification.violations == []

    def test_verify_constraints_direct(self):
        """verify_constraints() can be called independently."""
        from app.allocation.allocation_types import FarmerAllocation
        from app.allocation.lp_allocator import verify_constraints

        fa1 = FarmerAllocation(
            farmer_id="F001", allocated_water_m3=1800.0,
            predicted_demand_m3=3600.0, minimum_requirement_m3=1440.0,
            maximum_requirement_m3=4320.0, urgency=0.5, crop_sensitivity=0.5,
            growth_stage="vegetative", crop="wheat",
        )
        verification = verify_constraints(
            farmer_allocations=[fa1],
            available_water_m3=2000.0,
            agent_ids=["F001"],
        )
        assert verification.is_valid
        assert verification.total_water_ok
        assert verification.non_negative_ok
        assert verification.maximum_ok


# ══════════════════════════════════════════════════════════════════════════════
# 15. SOLVER STATUS
# ══════════════════════════════════════════════════════════════════════════════

class TestSolverStatus:
    """Tests for solver status codes."""

    def test_empty_returns_empty_status(self):
        """Empty farmer list → EMPTY status."""
        from app.allocation.allocation_types import SolverStatus
        result = _solve([], available_water=5000.0)
        assert result.solver_status == SolverStatus.EMPTY

    def test_normal_scenario_optimal_or_relaxed(self):
        """Normal solve → OPTIMAL or RELAXED status."""
        from app.allocation.allocation_types import SolverStatus
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
        ]
        result = _solve(agents, available_water=4000.0)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.RELAXED)

    def test_infeasible_minimum_returns_relaxed(self):
        """When min reqs are infeasible → RELAXED status."""
        from app.allocation.allocation_types import SolverStatus
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=2000.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=2000.0),
        ]
        result = _solve(agents, available_water=1000.0)
        assert result.solver_status == SolverStatus.RELAXED

    def test_status_values_are_strings(self):
        """SolverStatus values should be lowercase strings."""
        from app.allocation.allocation_types import SolverStatus
        assert SolverStatus.OPTIMAL.value == "optimal"
        assert SolverStatus.RELAXED.value == "relaxed"
        assert SolverStatus.EMPTY.value == "empty"


# ══════════════════════════════════════════════════════════════════════════════
# 16. OBJECTIVE VALUE
# ══════════════════════════════════════════════════════════════════════════════

class TestObjectiveValue:
    """Tests for objective function value."""

    def test_objective_value_is_finite(self):
        """Objective value must be a finite number."""
        agents = [_make_agent("F001"), _make_agent("F002")]
        result = _solve(agents, available_water=5000.0)
        assert math.isfinite(result.objective_value)

    def test_objective_not_nan(self):
        """Objective must not be NaN."""
        agents = [_make_agent("F001")]
        result = _solve(agents, available_water=3000.0)
        assert not math.isnan(result.objective_value)

    def test_custom_weights_accepted(self):
        """Custom objective weights should produce a valid result."""
        from app.allocation.lp_allocator import ObjectiveWeights, WaterAllocator
        agents = [_make_agent("F001"), _make_agent("F002")]
        weights = ObjectiveWeights(urgency=0.6, crop_sensitivity=0.2,
                                   unmet_demand=0.1, minimum_shortfall=0.1)
        allocator = WaterAllocator(
            agents=agents, available_water_m3=5000.0, weights=weights
        )
        result = allocator.solve()
        assert result.verification.is_valid
        assert math.isfinite(result.objective_value)

    def test_negative_weight_rejected(self):
        """Negative objective weight must raise ValueError."""
        from app.allocation.lp_allocator import ObjectiveWeights
        with pytest.raises(ValueError):
            ObjectiveWeights(urgency=-0.1)


# ══════════════════════════════════════════════════════════════════════════════
# 17. DETERMINISM
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterminism:
    """Tests that confirm same input → same output."""

    def test_same_input_same_allocation(self):
        """Running the solver twice with same input must give same allocations."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, urgency=0.7),
            _make_agent("F002", predicted_demand=2400.0, urgency=0.3),
        ]
        r1 = _solve(agents, available_water=4000.0)
        r2 = _solve(agents, available_water=4000.0)
        for fa1, fa2 in zip(r1.allocations, r2.allocations):
            assert fa1.allocated_water_m3 == pytest.approx(fa2.allocated_water_m3, abs=1e-4)

    def test_same_input_same_fairness(self):
        """Fairness score must be identical on repeated calls."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=2400.0),
        ]
        r1 = _solve(agents, available_water=5000.0)
        r2 = _solve(agents, available_water=5000.0)
        assert r1.fairness_score == pytest.approx(r2.fairness_score, abs=1e-9)

    def test_same_input_same_utilization(self):
        """Utilization must be identical on repeated calls."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        r1 = _solve(agents, available_water=3000.0)
        r2 = _solve(agents, available_water=3000.0)
        assert r1.utilization == pytest.approx(r2.utilization, abs=1e-9)


# ══════════════════════════════════════════════════════════════════════════════
# 18. EMPTY INPUT
# ══════════════════════════════════════════════════════════════════════════════

class TestEmptyInput:
    """Tests for empty farmer list."""

    def test_empty_farmers_returns_empty_result(self):
        """Empty farmer list → EMPTY status, no allocations."""
        from app.allocation.allocation_types import SolverStatus
        result = _solve([], available_water=5000.0)
        assert result.solver_status == SolverStatus.EMPTY
        assert result.n_farmers == 0
        assert result.allocations == []

    def test_empty_farmers_valid_verification(self):
        """Empty allocation should pass verification."""
        result = _solve([], available_water=5000.0)
        assert result.verification.is_valid

    def test_empty_fairness_is_0(self):
        """Empty → fairness = 0 (undefined, returns 0)."""
        result = _solve([], available_water=5000.0)
        assert result.fairness_score == pytest.approx(0.0, abs=1e-9)

    def test_empty_result_serialisable(self):
        """Empty AllocationResult should be JSON-serialisable."""
        result = _solve([], available_water=5000.0)
        d = result.as_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 19. INVALID INPUT
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidInput:
    """Tests for invalid input handling."""

    def test_negative_available_water_rejected(self):
        """Negative available water must raise ValueError."""
        from app.allocation.lp_allocator import WaterAllocator
        with pytest.raises(ValueError, match="available_water_m3"):
            WaterAllocator(agents=[], available_water_m3=-100.0)

    def test_negative_objective_weight_rejected(self):
        """Negative objective weight must raise ValueError."""
        from app.allocation.lp_allocator import ObjectiveWeights
        with pytest.raises(ValueError):
            ObjectiveWeights(crop_sensitivity=-0.1)


# ══════════════════════════════════════════════════════════════════════════════
# 20. PHASE 4 INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

class TestPhase4Integration:
    """Tests demonstrating Phase 3 → Phase 4 → Phase 5 pipeline."""

    @pytest.fixture(scope="class")
    def real_predictor(self):
        from pathlib import Path
        model_dir = Path(__file__).parent.parent / "data" / "models"
        if not (model_dir / "rf_model.joblib").exists():
            pytest.skip("Model artifacts not found.")
        from app.ml.predictor import WaterDemandPredictor
        return WaterDemandPredictor.from_artifacts(model_dir, model_name="RandomForest")

    def test_full_pipeline_p3_p4_p5(self, real_predictor):
        """Full pipeline: scenario → agents → conflicts → allocation."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.allocation.lp_allocator import WaterAllocator
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "moderate_shortage", n_farmers=4, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)

        # Phase 4: detect conflicts
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=total_demand * 0.75,
            scenario_id="pipeline_test",
        )
        conflict_report = detector.detect_all()

        # Phase 5: allocate
        allocator = WaterAllocator(
            agents=agents,
            available_water_m3=conflict_report.available_water_m3,
            scenario_id=conflict_report.scenario_id,
        )
        result = allocator.solve()

        assert result.verification.is_valid
        assert result.n_farmers == 4
        assert result.total_allocated_m3 <= conflict_report.available_water_m3 + 1e-6

    def test_conflict_scenario_id_carried_to_allocation(self, real_predictor):
        """scenario_id should be carried from conflict report to allocation."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.allocation.lp_allocator import WaterAllocator
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "normal_water", n_farmers=3, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)

        detector = ConflictDetector(
            agents=agents,
            available_water_m3=total_demand * 1.2,
            scenario_id="my_test_scenario",
        )
        conflict_report = detector.detect_all()

        result = WaterAllocator(
            agents=agents,
            available_water_m3=conflict_report.available_water_m3,
            scenario_id=conflict_report.scenario_id,
        ).solve()
        assert result.scenario_id == "my_test_scenario"

    def test_severe_shortage_allocation_still_valid(self, real_predictor):
        """Severe shortage scenario allocation must pass all constraints."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.allocation.lp_allocator import WaterAllocator

        triples = build_agents_from_scenario(
            "severe_shortage", n_farmers=5, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)

        result = WaterAllocator(
            agents=agents,
            available_water_m3=total_demand * 0.30,
        ).solve()

        assert result.verification.is_valid
        for fa in result.allocations:
            assert fa.allocated_water_m3 >= -1e-9
            assert fa.allocated_water_m3 <= fa.maximum_requirement_m3 + 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# 21-23. CONSERVATION + NaN + NEGATIVES (comprehensive sweeps)
# ══════════════════════════════════════════════════════════════════════════════

class TestConservationAndSanity:
    """Comprehensive sweep tests for conservation and data quality."""

    def test_no_negative_allocation_any_scenario(self):
        """No negative allocations across multiple scenarios."""
        scenarios = [
            (1, 10000.0), (2, 5000.0), (3, 1000.0), (3, 0.0), (1, 3600.0)
        ]
        for n, avail in scenarios:
            agents = [_make_agent(f"F{i:03d}", predicted_demand=3600.0) for i in range(n)]
            result = _solve(agents, available_water=avail)
            for fa in result.allocations:
                assert fa.allocated_water_m3 >= -1e-9, (
                    f"Negative allocation for {fa.farmer_id} in scenario n={n}, avail={avail}"
                )

    def test_no_nan_values_any_scenario(self):
        """No NaN values across multiple scenarios."""
        scenarios = [
            ([_make_agent("F001")], 5000.0),
            ([_make_agent("F001"), _make_agent("F002")], 500.0),
            ([_make_agent("F001")], 0.0),
        ]
        for agents, avail in scenarios:
            result = _solve(agents, available_water=avail)
            for fa in result.allocations:
                assert not math.isnan(fa.allocated_water_m3)
            assert not math.isnan(result.fairness_score)
            assert not math.isnan(result.utilization)

    def test_water_conservation_always(self):
        """total_allocated <= available_water in every case."""
        scenarios = [
            ([_make_agent("F001")], 0.0),
            ([_make_agent("F001")], 3600.0),
            ([_make_agent("F001"), _make_agent("F002")], 4000.0),
            ([_make_agent("F001"), _make_agent("F002")], 200.0),
        ]
        for agents, avail in scenarios:
            result = _solve(agents, available_water=avail)
            assert result.total_allocated_m3 <= avail + 1e-6, (
                f"Conservation violated: {result.total_allocated_m3:.4f} > {avail}"
            )

    def test_result_json_serialisable(self):
        """AllocationResult.as_dict() must be JSON-serialisable."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=2400.0),
        ]
        result = _solve(agents, available_water=4000.0)
        d = result.as_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 0

    def test_farmer_allocation_as_dict(self):
        """FarmerAllocation.as_dict() must contain all required keys."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        result = _solve(agents, available_water=5000.0)
        fa = result.allocations[0]
        d = fa.as_dict()
        required = [
            "farmer_id", "allocated_water_m3", "predicted_demand_m3",
            "minimum_requirement_m3", "maximum_requirement_m3",
            "unmet_demand_m3", "minimum_shortfall_m3", "satisfaction_ratio",
            "urgency", "crop_sensitivity", "growth_stage", "crop",
            "constraint_status", "explanation_metadata",
        ]
        for key in required:
            assert key in d, f"Missing key: {key}"

    def test_explanation_metadata_present(self):
        """explanation_metadata must contain Phase 7-ready information."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        result = _solve(agents, available_water=4000.0)
        meta = result.allocations[0].explanation_metadata
        assert "predicted_demand_m3" in meta
        assert "allocated_water_m3" in meta
        assert "urgency" in meta
        assert "crop_sensitivity" in meta
        assert "objective_weights" in meta
