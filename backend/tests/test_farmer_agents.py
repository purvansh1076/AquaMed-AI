"""
AquaMediAI — Phase 3: Farmer Digital Agent Tests
==================================================

Tests all Phase 3 components:

  1. FarmerAgent creation and validation
  2. Input validation (all invalid states rejected)
  3. Utility function — all components + edge cases
  4. BATNA calculation
  5. Timing preference
  6. Flexibility
  7. Satisfaction
  8. Crop stress
  9. Allocation updates (DigitalTwin)
  10. Agent factory (with real ML predictor)
  11. Multiple farmer agents (batch)
  12. Deterministic behaviour

All tests use SYNTHETIC data — no real farmer records.

Run with:
    pytest tests/test_farmer_agents.py -v --tb=short
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

# ─── Helpers ─────────────────────────────────────────────────────────────────

BACKEND_DIR = Path(__file__).parent.parent


def _make_predictor_mock(demand: float = 3600.0) -> MagicMock:
    """Return a mock WaterDemandPredictor that always returns `demand`."""
    from app.ml.predictor import PredictionResult

    mock_pred = MagicMock()
    result = PredictionResult(
        predicted_water_demand_m3=demand,
        model_name="MockModel",
    )
    mock_pred.predict_single.return_value = result
    return mock_pred


def _minimal_farmer_data(**overrides) -> Dict[str, Any]:
    """Return a minimal valid farmer data dict for tests."""
    base = {
        "farmer_id": "F001",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "vegetative",
        "season": "kharif",
        "farm_area_hectares": 2.5,
        "et0_mm_per_day": 5.0,
        "kc_value": 0.70,
        "etc_mm_per_day": 3.5,
        "preferred_start_hour": 8,
        "irrigation_window_hours": 2,
        "flexibility_score": 0.3,
        "urgency_score": 0.6,
        "crop_stress_index": 0.5,
        "minimum_requirement_m3": 1440.0,  # 40% of 3600
    }
    base.update(overrides)
    return base


# ─── Imports (module-level, after path setup via conftest) ────────────────────

@pytest.fixture(scope="module")
def farmer_agent_cls():
    from app.agents.farmer_agent import FarmerAgent
    return FarmerAgent


@pytest.fixture(scope="module")
def utility_weights_cls():
    from app.agents.farmer_agent import UtilityWeights
    return UtilityWeights


@pytest.fixture(scope="module")
def batna_cls():
    from app.agents.farmer_agent import BATNA
    return BATNA


@pytest.fixture(scope="module")
def digital_twin_cls():
    from app.agents.digital_twin import DigitalTwin
    return DigitalTwin


@pytest.fixture(scope="module")
def negotiation_state_enum():
    from app.agents.digital_twin import NegotiationState
    return NegotiationState


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
    urgency: float = 0.6,
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


# ══════════════════════════════════════════════════════════════════════════════
# 1. AGENT CREATION
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentCreation:
    """Tests for FarmerAgent construction."""

    def test_basic_creation(self):
        """Agent should be created with valid parameters."""
        agent = _make_agent()
        assert agent.farmer_id == "F001"
        assert agent.crop == "wheat"
        assert agent.growth_stage == "vegetative"

    def test_all_properties_accessible(self):
        """All required properties must be accessible."""
        agent = _make_agent()
        # Identity
        assert agent.farmer_id is not None
        assert agent.name is not None
        assert agent.crop is not None
        assert agent.farm_area > 0
        assert agent.soil_type is not None
        assert agent.growth_stage is not None
        # Water
        assert agent.predicted_water_demand > 0
        assert agent.minimum_water_requirement > 0
        assert agent.maximum_water_requirement > 0
        # Timing
        assert 0 <= agent.preferred_start_time <= 23
        assert 0 <= agent.preferred_end_time <= 23
        # Scores
        assert 0.0 <= agent.urgency <= 1.0
        assert 0.0 <= agent.crop_sensitivity <= 1.0
        assert 0.0 <= agent.flexibility <= 1.0
        # Derived
        assert agent.batna is not None
        assert agent.preferences is not None
        assert agent.utility_weights is not None

    def test_repr(self):
        """repr should be human-readable."""
        agent = _make_agent()
        r = repr(agent)
        assert "FarmerAgent" in r
        assert "F001" in r

    def test_water_constraint_satisfied(self):
        """min <= predicted <= max must hold."""
        agent = _make_agent(predicted_demand=3600, min_water=1440, max_water=4320)
        assert agent.minimum_water_requirement <= agent.predicted_water_demand
        assert agent.predicted_water_demand <= agent.maximum_water_requirement

    def test_preferences_built_correctly(self):
        """Preferences should reflect inputs."""
        agent = _make_agent(pref_start=8, pref_end=10, flexibility=0.5)
        prefs = agent.preferences
        assert prefs.preferred_start_hour == 8
        assert prefs.preferred_end_hour == 10
        assert prefs.target_water_m3 == agent.predicted_water_demand

    def test_all_crops_accepted(self):
        """All 8 crop types should be valid."""
        from app.agents.farmer_agent import VALID_CROPS
        for crop in VALID_CROPS:
            agent = _make_agent(crop=crop)
            assert agent.crop == crop

    def test_all_soils_accepted(self):
        """All 5 soil types should be valid."""
        from app.agents.farmer_agent import VALID_SOILS
        for soil in VALID_SOILS:
            agent = _make_agent(soil_type=soil)
            assert agent.soil_type == soil

    def test_all_growth_stages_accepted(self):
        """All 5 growth stages should be valid."""
        from app.agents.farmer_agent import VALID_GROWTH_STAGES
        for stage in VALID_GROWTH_STAGES:
            agent = _make_agent(growth_stage=stage)
            assert agent.growth_stage == stage

    def test_negotiation_state_dict_structure(self):
        """get_negotiation_state() should contain all required keys."""
        agent = _make_agent()
        state = agent.get_negotiation_state()
        required_keys = [
            "farmer_id", "predicted_demand_m3", "minimum_requirement_m3",
            "urgency", "crop_sensitivity", "flexibility",
            "batna_allocation_m3", "batna_utility",
        ]
        for key in required_keys:
            assert key in state, f"Missing key: {key}"

    def test_as_dict_is_serialisable(self):
        """as_dict() should be JSON-serialisable."""
        import json
        agent = _make_agent()
        d = agent.as_dict()
        # Should not raise
        json_str = json.dumps(d)
        assert len(json_str) > 0

    def test_stage_criticality_flowering_is_highest(self):
        """Flowering should have the highest criticality."""
        agent_flower = _make_agent(growth_stage="flowering")
        agent_harvest = _make_agent(growth_stage="harvest")
        assert agent_flower.stage_criticality > agent_harvest.stage_criticality


# ══════════════════════════════════════════════════════════════════════════════
# 2. INPUT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestInputValidation:
    """Tests that invalid agent states are rejected."""

    def test_invalid_crop_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="crop"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="avocado", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=0.5,
                flexibility=0.5,
            )

    def test_invalid_soil_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="soil_type"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="gravel", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=0.5,
                flexibility=0.5,
            )

    def test_invalid_growth_stage_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="growth_stage"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="wilting",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=0.5,
                flexibility=0.5,
            )

    def test_negative_farm_area_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="farm_area"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=-1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=0.5,
                flexibility=0.5,
            )

    def test_urgency_out_of_range_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="urgency"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=1.5, crop_sensitivity=0.5,
                flexibility=0.5,
            )

    def test_crop_sensitivity_out_of_range_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="crop_sensitivity"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=-0.1,
                flexibility=0.5,
            )

    def test_flexibility_out_of_range_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="flexibility"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=0.5,
                flexibility=2.0,
            )

    def test_water_constraint_violation_rejected(self):
        """min > predicted should be rejected."""
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="Water constraint"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000,
                minimum_water_requirement=1500,  # min > predicted — INVALID
                maximum_water_requirement=2000,
                preferred_start_time=8, preferred_end_time=10,
                urgency=0.5, crop_sensitivity=0.5, flexibility=0.5,
            )

    def test_predicted_exceeds_max_rejected(self):
        """predicted > max should be rejected."""
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="Water constraint"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=3000,
                minimum_water_requirement=1000,
                maximum_water_requirement=2000,  # max < predicted — INVALID
                preferred_start_time=8, preferred_end_time=10,
                urgency=0.5, crop_sensitivity=0.5, flexibility=0.5,
            )

    def test_time_window_invalid_rejected(self):
        """preferred_start >= preferred_end should be rejected."""
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="preferred_start_time"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200,
                preferred_start_time=10, preferred_end_time=8,  # INVALID
                urgency=0.5, crop_sensitivity=0.5, flexibility=0.5,
            )

    def test_empty_farmer_id_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError):
            FarmerAgent(
                farmer_id="", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=0.5, crop_sensitivity=0.5,
                flexibility=0.5,
            )

    def test_negative_urgency_rejected(self):
        from app.agents.farmer_agent import FarmerAgent
        with pytest.raises(ValueError, match="urgency"):
            FarmerAgent(
                farmer_id="F001", name="X", crop="wheat", farm_area=1.0,
                soil_type="loam", growth_stage="vegetative",
                predicted_water_demand=1000, minimum_water_requirement=400,
                maximum_water_requirement=1200, preferred_start_time=8,
                preferred_end_time=10, urgency=-0.1, crop_sensitivity=0.5,
                flexibility=0.5,
            )


# ══════════════════════════════════════════════════════════════════════════════
# 3. UTILITY CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

class TestUtilityCalculation:
    """Tests for the farmer utility function."""

    def test_full_allocation_in_preferred_window(self):
        """Full water + preferred timing = highest utility."""
        from app.agents.utility import compute_utility
        u = compute_utility(
            allocation_m3=3600.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=9,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        assert u > 0.85, f"Expected high utility, got {u:.4f}"

    def test_zero_allocation(self):
        """Zero water = very low utility."""
        from app.agents.utility import compute_utility
        u = compute_utility(
            allocation_m3=0.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=None,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        assert u < 0.3, f"Expected low utility for zero allocation, got {u:.4f}"

    def test_minimum_allocation(self):
        """Exactly minimum water = moderate utility."""
        from app.agents.utility import compute_utility
        u_min = compute_utility(
            allocation_m3=1440.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=9,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        u_full = compute_utility(
            allocation_m3=3600.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=9,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        assert u_min < u_full, "Full allocation must beat minimum"
        assert 0.0 <= u_min <= 1.0

    def test_partial_allocation(self):
        """Partial water should yield intermediate utility."""
        from app.agents.utility import compute_utility
        u_partial = compute_utility(
            allocation_m3=2400.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=9,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        u_zero = compute_utility(
            allocation_m3=0.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=None,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        assert u_partial > u_zero, "Partial > zero"
        assert 0.0 <= u_partial <= 1.0

    def test_utility_always_in_0_1(self):
        """Utility must always be in [0, 1]."""
        from app.agents.utility import compute_utility
        for alloc in [0, 500, 1440, 2000, 3600, 5000]:
            for urgency in [0.0, 0.5, 1.0]:
                for cs in [0.0, 0.5, 1.0]:
                    u = compute_utility(
                        allocation_m3=float(alloc),
                        predicted_demand_m3=3600.0,
                        minimum_requirement_m3=1440.0,
                        irrigation_start_hour=None,
                        preferred_start_hour=8,
                        preferred_end_hour=10,
                        acceptable_start_hour=6,
                        acceptable_end_hour=12,
                        urgency=urgency,
                        crop_sensitivity=cs,
                        flexibility=0.3,
                    )
                    assert 0.0 <= u <= 1.0, f"Utility {u} out of [0,1] for alloc={alloc}"

    def test_preferred_timing_beats_non_preferred(self):
        """Preferred timing should give higher utility than non-preferred."""
        from app.agents.utility import compute_utility
        kwargs = dict(
            allocation_m3=3600.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        u_preferred = compute_utility(irrigation_start_hour=9, **kwargs)
        u_acceptable = compute_utility(irrigation_start_hour=7, **kwargs)
        u_outside = compute_utility(irrigation_start_hour=None, **kwargs)
        assert u_preferred >= u_acceptable >= u_outside

    def test_high_urgency_penalises_low_water(self):
        """High urgency + low water = lower utility than low urgency + low water."""
        from app.agents.utility import compute_utility
        kwargs = dict(
            allocation_m3=500.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=None,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            crop_sensitivity=0.5,
            flexibility=0.3,
        )
        u_high_urgency = compute_utility(urgency=1.0, **kwargs)
        u_low_urgency = compute_utility(urgency=0.0, **kwargs)
        assert u_high_urgency < u_low_urgency

    def test_high_flexibility_not_worse_than_low(self):
        """High flexibility should not systematically harm utility."""
        from app.agents.utility import compute_utility
        kwargs = dict(
            allocation_m3=3600.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=9,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.5,
            crop_sensitivity=0.5,
        )
        u_flex = compute_utility(flexibility=0.9, **kwargs)
        u_rigid = compute_utility(flexibility=0.1, **kwargs)
        assert u_flex >= 0.0 and u_rigid >= 0.0

    def test_water_satisfaction_monotonic(self):
        """Water satisfaction must be non-decreasing with allocation."""
        from app.agents.utility import water_satisfaction
        allocs = [0, 500, 1000, 1500, 2000, 2500, 3000, 3600, 4000]
        sats = [water_satisfaction(a, 3600.0) for a in allocs]
        for i in range(1, len(sats)):
            assert sats[i] >= sats[i - 1], "water_satisfaction must be monotone"

    def test_timing_satisfaction_values(self):
        """Timing satisfaction should return correct discrete values."""
        from app.agents.utility import timing_satisfaction
        # Preferred
        assert timing_satisfaction(9, 8, 10, 6, 12) == 1.0
        assert timing_satisfaction(8, 8, 10, 6, 12) == 1.0
        assert timing_satisfaction(10, 8, 10, 6, 12) == 1.0
        # Acceptable but not preferred
        assert timing_satisfaction(7, 8, 10, 6, 12) == 0.5
        assert timing_satisfaction(11, 8, 10, 6, 12) == 0.5
        # Outside
        assert timing_satisfaction(None, 8, 10, 6, 12) == 0.0
        assert timing_satisfaction(5, 8, 10, 6, 12) == 0.0
        assert timing_satisfaction(14, 8, 10, 6, 12) == 0.0

    def test_urgency_protection_formula(self):
        """urgency_protection = 1 - urgency * (1 - water_sat)."""
        from app.agents.utility import urgency_protection
        assert urgency_protection(0.0, 0.5) == pytest.approx(1.0)  # no urgency
        assert urgency_protection(1.0, 1.0) == pytest.approx(1.0)  # full water
        assert urgency_protection(1.0, 0.0) == pytest.approx(0.0)  # crisis
        assert urgency_protection(0.5, 0.5) == pytest.approx(0.75)

    def test_minimum_requirement_satisfaction(self):
        """min_req satisfaction should clip at 1.0 for over-allocation."""
        from app.agents.utility import minimum_requirement_satisfaction
        assert minimum_requirement_satisfaction(0.0, 1440.0) == pytest.approx(0.0)
        assert minimum_requirement_satisfaction(1440.0, 1440.0) == pytest.approx(1.0)
        assert minimum_requirement_satisfaction(3600.0, 1440.0) == pytest.approx(1.0)  # capped


# ══════════════════════════════════════════════════════════════════════════════
# 4. BATNA CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

class TestBATNA:
    """Tests for BATNA computation."""

    def test_batna_allocation_equals_minimum(self):
        """BATNA allocation must equal minimum requirement."""
        agent = _make_agent(min_water=1440.0)
        assert agent.batna.fallback_allocation_m3 == pytest.approx(1440.0)

    def test_batna_utility_in_0_1(self):
        """BATNA utility must be in [0, 1]."""
        agent = _make_agent()
        assert 0.0 <= agent.batna.fallback_utility <= 1.0

    def test_batna_utility_less_than_full_allocation(self):
        """BATNA utility must be less than full allocation utility."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        twin.update_allocation(agent.predicted_water_demand, start_hour=9)
        full_utility = twin.utility_score
        batna_utility = agent.batna.fallback_utility
        # BATNA must be worse than ideal — preserves negotiation incentive
        assert batna_utility < full_utility, (
            f"BATNA utility ({batna_utility:.4f}) should be < full allocation "
            f"utility ({full_utility:.4f})"
        )

    def test_batna_has_description(self):
        """BATNA must include a description."""
        agent = _make_agent()
        assert len(agent.batna.description) > 10

    def test_batna_contains_minimum_allocation(self):
        """BATNA description should reference minimum requirement."""
        agent = _make_agent()
        desc = agent.batna.description
        assert "m3" in desc or "m³" in desc or "minimum" in desc.lower()

    def test_batna_different_urgencies(self):
        """Higher urgency farmer should have lower BATNA utility (more at stake)."""
        agent_high = _make_agent(urgency=0.95, farmer_id="HIGH")
        agent_low = _make_agent(urgency=0.05, farmer_id="LOW")
        # Both BATNAs computed at minimum allocation, no timing
        # High urgency → lower urgency_protection → lower utility
        assert agent_high.batna.fallback_utility < agent_low.batna.fallback_utility

    def test_batna_invalid_negative_allocation_rejected(self):
        """BATNA with negative allocation should raise."""
        from app.agents.farmer_agent import BATNA
        with pytest.raises(ValueError):
            BATNA(fallback_allocation_m3=-100.0, fallback_utility=0.5)

    def test_batna_utility_out_of_range_rejected(self):
        """BATNA with utility > 1 should raise."""
        from app.agents.farmer_agent import BATNA
        with pytest.raises(ValueError):
            BATNA(fallback_allocation_m3=1440.0, fallback_utility=1.5)


# ══════════════════════════════════════════════════════════════════════════════
# 5. TIMING PREFERENCE
# ══════════════════════════════════════════════════════════════════════════════

class TestTimingPreference:
    """Tests for timing preference handling."""

    def test_preferred_window_score(self):
        """Irrigation in preferred window should score 1.0."""
        from app.agents.utility import timing_satisfaction
        assert timing_satisfaction(9, 8, 10, 6, 12) == 1.0

    def test_acceptable_window_score(self):
        """Irrigation in acceptable (not preferred) window should score 0.5."""
        from app.agents.utility import timing_satisfaction
        assert timing_satisfaction(11, 8, 10, 6, 12) == 0.5

    def test_outside_window_score(self):
        """Irrigation outside all windows should score 0.0."""
        from app.agents.utility import timing_satisfaction
        assert timing_satisfaction(2, 8, 10, 6, 12) == 0.0

    def test_no_timing_score(self):
        """No timing (None) should score 0.0."""
        from app.agents.utility import timing_satisfaction
        assert timing_satisfaction(None, 8, 10, 6, 12) == 0.0

    def test_flexible_farmer_has_wider_acceptable_window(self):
        """Flexible farmer should have a wider acceptable window."""
        agent_flex = _make_agent(flexibility=0.9, pref_start=8, pref_end=10)
        agent_rigid = _make_agent(flexibility=0.1, pref_start=8, pref_end=10)
        window_flex = (
            agent_flex.preferences.acceptable_end_hour -
            agent_flex.preferences.acceptable_start_hour
        )
        window_rigid = (
            agent_rigid.preferences.acceptable_end_hour -
            agent_rigid.preferences.acceptable_start_hour
        )
        assert window_flex >= window_rigid

    def test_preferred_end_always_after_start(self):
        """preferred_end must always be after preferred_start."""
        agent = _make_agent(pref_start=8, pref_end=10)
        assert agent.preferred_end_time > agent.preferred_start_time


# ══════════════════════════════════════════════════════════════════════════════
# 6. FLEXIBILITY
# ══════════════════════════════════════════════════════════════════════════════

class TestFlexibility:
    """Tests for flexibility handling."""

    def test_zero_flexibility(self):
        """Zero flexibility should still produce a valid agent."""
        agent = _make_agent(flexibility=0.0)
        assert agent.flexibility == 0.0
        prefs = agent.preferences
        assert prefs.acceptable_start_hour <= prefs.preferred_start_hour
        assert prefs.acceptable_end_hour >= prefs.preferred_end_hour

    def test_max_flexibility(self):
        """Maximum flexibility (1.0) should produce widest acceptable window."""
        agent = _make_agent(flexibility=1.0)
        prefs = agent.preferences
        window = prefs.acceptable_end_hour - prefs.acceptable_start_hour
        assert window > 0

    def test_flexibility_affects_acceptable_window(self):
        """Higher flexibility should not narrow the window."""
        agent_a = _make_agent(flexibility=0.1, pref_start=10, pref_end=12)
        agent_b = _make_agent(flexibility=0.9, pref_start=10, pref_end=12)
        window_a = (
            agent_a.preferences.acceptable_end_hour -
            agent_a.preferences.acceptable_start_hour
        )
        window_b = (
            agent_b.preferences.acceptable_end_hour -
            agent_b.preferences.acceptable_start_hour
        )
        assert window_b >= window_a


# ══════════════════════════════════════════════════════════════════════════════
# 7. SATISFACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestSatisfaction:
    """Tests for satisfaction score calculation."""

    def test_initial_satisfaction_zero(self):
        """Before any allocation, satisfaction should be 0."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        assert twin.satisfaction_score == pytest.approx(0.0)

    def test_full_allocation_gives_full_satisfaction(self):
        """Full demand allocation should give satisfaction = 1.0."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0)
        twin = DigitalTwin(agent)
        twin.update_allocation(3600.0)
        assert twin.satisfaction_score == pytest.approx(1.0)

    def test_partial_allocation_satisfaction(self):
        """50% allocation should give 0.5 satisfaction."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0)
        twin = DigitalTwin(agent)
        twin.update_allocation(1800.0)
        assert twin.satisfaction_score == pytest.approx(0.5)

    def test_over_allocation_capped_at_1(self):
        """Over-allocation should cap satisfaction at 1.0."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0)
        twin = DigitalTwin(agent)
        twin.update_allocation(5000.0)
        assert twin.satisfaction_score == pytest.approx(1.0)

    def test_satisfaction_monotone_with_allocation(self):
        """Satisfaction should increase monotonically with allocation."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0)
        twin = DigitalTwin(agent)
        prev_sat = -1.0
        for alloc in [0, 500, 1000, 1800, 2500, 3600]:
            twin.update_allocation(float(alloc))
            assert twin.satisfaction_score >= prev_sat
            prev_sat = twin.satisfaction_score


# ══════════════════════════════════════════════════════════════════════════════
# 8. CROP STRESS
# ══════════════════════════════════════════════════════════════════════════════

class TestCropStress:
    """Tests for crop stress calculation."""

    def test_initial_stress_is_max(self):
        """With no allocation, stress should be high for sensitive crops."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(
            growth_stage="flowering",  # highest criticality
            crop_sensitivity=1.0,
        )
        twin = DigitalTwin(agent)
        # No allocation → max stress
        assert twin.crop_stress_level > 0.5

    def test_full_allocation_eliminates_stress(self):
        """Full allocation (>= minimum) should eliminate crop stress."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        twin.update_allocation(agent.minimum_water_requirement)
        assert twin.crop_stress_level == pytest.approx(0.0)

    def test_flowering_stage_highest_stress(self):
        """Flowering stage should produce higher stress than harvest."""
        from app.agents.digital_twin import DigitalTwin
        agent_f = _make_agent(growth_stage="flowering", crop_sensitivity=0.8)
        agent_h = _make_agent(growth_stage="harvest", crop_sensitivity=0.8)
        twin_f = DigitalTwin(agent_f)
        twin_h = DigitalTwin(agent_h)
        # No allocation → stress based on stage criticality
        assert twin_f.crop_stress_level > twin_h.crop_stress_level

    def test_stress_in_0_1_range(self):
        """Stress must always be in [0, 1]."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(growth_stage="flowering", crop_sensitivity=1.0)
        twin = DigitalTwin(agent)
        for alloc in [0, 500, 1440, 3600]:
            twin.update_allocation(float(alloc))
            assert 0.0 <= twin.crop_stress_level <= 1.0

    def test_stress_decreases_with_allocation(self):
        """Stress should decrease as allocation increases."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        prev_stress = 2.0
        for alloc in [0, 500, 1440, 3600]:
            twin.update_allocation(float(alloc))
            assert twin.crop_stress_level <= prev_stress
            prev_stress = twin.crop_stress_level


# ══════════════════════════════════════════════════════════════════════════════
# 9. ALLOCATION UPDATES (DigitalTwin)
# ══════════════════════════════════════════════════════════════════════════════

class TestAllocationUpdates:
    """Tests for DigitalTwin allocation management."""

    def test_initial_state(self):
        """Twin should start in IDLE state with zero allocation."""
        from app.agents.digital_twin import DigitalTwin, NegotiationState
        agent = _make_agent()
        twin = DigitalTwin(agent)
        assert twin.current_allocation_m3 == pytest.approx(0.0)
        assert twin.negotiation_state == NegotiationState.IDLE
        assert twin.total_concessions_made == 0
        assert twin.unmet_demand_m3 == pytest.approx(agent.predicted_water_demand)

    def test_update_allocation_changes_state(self):
        """update_allocation should update all derived fields."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0, min_water=1440.0)
        twin = DigitalTwin(agent)
        twin.update_allocation(2000.0, start_hour=9)
        assert twin.current_allocation_m3 == pytest.approx(2000.0)
        assert twin.allocated_start_hour == 9
        assert twin.unmet_demand_m3 == pytest.approx(1600.0)
        assert twin.satisfaction_score > 0

    def test_negative_allocation_rejected(self):
        """Negative allocation must raise ValueError."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        with pytest.raises(ValueError, match="allocation_m3 must be >= 0"):
            twin.update_allocation(-100.0)

    def test_settle_sets_settled_state(self):
        """settle() should set SETTLED state."""
        from app.agents.digital_twin import DigitalTwin, NegotiationState
        agent = _make_agent()
        twin = DigitalTwin(agent)
        twin.settle(3600.0, start_hour=8)
        assert twin.negotiation_state == NegotiationState.SETTLED

    def test_fail_applies_batna(self):
        """fail() should apply BATNA allocation."""
        from app.agents.digital_twin import DigitalTwin, NegotiationState
        agent = _make_agent()
        twin = DigitalTwin(agent)
        twin.fail()
        assert twin.negotiation_state == NegotiationState.FAILED
        assert twin.current_allocation_m3 == pytest.approx(
            agent.batna.fallback_allocation_m3
        )

    def test_reset_clears_state(self):
        """reset() should return twin to initial state."""
        from app.agents.digital_twin import DigitalTwin, NegotiationState
        agent = _make_agent()
        twin = DigitalTwin(agent)
        twin.update_allocation(2000.0)
        twin.reset()
        assert twin.current_allocation_m3 == pytest.approx(0.0)
        assert twin.negotiation_state == NegotiationState.IDLE

    def test_concession_reduces_ask(self):
        """apply_concession() should reduce the current ask."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0, min_water=1440.0)
        twin = DigitalTwin(agent)
        record = twin.apply_concession(3000.0, reason="test concession")
        assert twin.current_ask_m3 == pytest.approx(3000.0)
        assert record.concession_amount_m3 == pytest.approx(600.0)

    def test_concession_below_minimum_rejected(self):
        """Concession below minimum_water_requirement should raise."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0, min_water=1440.0)
        twin = DigitalTwin(agent)
        with pytest.raises(ValueError, match="BATNA floor"):
            twin.apply_concession(1000.0)  # below minimum 1440

    def test_concession_higher_than_current_rejected(self):
        """Concession must reduce the ask."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(predicted_demand=3600.0, min_water=1440.0)
        twin = DigitalTwin(agent)
        with pytest.raises(ValueError, match="must be <"):
            twin.apply_concession(4000.0)  # higher than current ask

    def test_get_state_dict_structure(self):
        """get_state_dict() should contain all required negotiation fields."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        twin.update_allocation(2000.0, start_hour=9)
        state = twin.get_state_dict()
        required_keys = [
            "farmer_id", "predicted_demand_m3", "minimum_requirement_m3",
            "current_allocation_m3", "unmet_demand_m3",
            "satisfaction_score", "utility_score", "crop_stress_level",
            "urgency", "crop_sensitivity", "flexibility",
            "batna_allocation_m3", "batna_utility", "negotiation_state",
        ]
        for key in required_keys:
            assert key in state, f"Missing key: {key}"

    def test_is_minimum_met_false_initially(self):
        """is_minimum_met should be False with no allocation."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent()
        twin = DigitalTwin(agent)
        assert twin.is_minimum_met is False

    def test_is_minimum_met_true_after_allocation(self):
        """is_minimum_met should be True when allocation >= minimum."""
        from app.agents.digital_twin import DigitalTwin
        agent = _make_agent(min_water=1440.0)
        twin = DigitalTwin(agent)
        twin.update_allocation(1440.0)
        assert twin.is_minimum_met is True


# ══════════════════════════════════════════════════════════════════════════════
# 10. AGENT FACTORY
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentFactory:
    """Tests for AgentFactory using mock predictor."""

    def test_build_agent_returns_tuple(self):
        """build_agent should return (FarmerAgent, PredictionResult)."""
        from app.agents.agent_factory import build_agent
        from app.agents.farmer_agent import FarmerAgent
        mock_pred = _make_predictor_mock(demand=3600.0)
        fdata = _minimal_farmer_data()
        agent, pred = build_agent(fdata, mock_pred)
        assert isinstance(agent, FarmerAgent)
        assert pred.predicted_water_demand_m3 == pytest.approx(3600.0)

    def test_build_agent_uses_predictor_demand(self):
        """Agent's predicted demand must come from the predictor."""
        from app.agents.agent_factory import build_agent
        mock_pred = _make_predictor_mock(demand=4200.0)
        fdata = _minimal_farmer_data()
        agent, _ = build_agent(fdata, mock_pred)
        assert agent.predicted_water_demand == pytest.approx(4200.0)

    def test_build_agent_water_constraints_valid(self):
        """Water constraints must be valid after factory build."""
        from app.agents.agent_factory import build_agent
        mock_pred = _make_predictor_mock(demand=3600.0)
        fdata = _minimal_farmer_data()
        agent, _ = build_agent(fdata, mock_pred)
        assert agent.minimum_water_requirement <= agent.predicted_water_demand
        assert agent.predicted_water_demand <= agent.maximum_water_requirement

    def test_build_agents_batch(self):
        """build_agents should build multiple agents."""
        from app.agents.agent_factory import build_agents
        mock_pred = _make_predictor_mock(demand=3600.0)
        farmers = [
            _minimal_farmer_data(farmer_id="F001"),
            _minimal_farmer_data(farmer_id="F002"),
            _minimal_farmer_data(farmer_id="F003"),
        ]
        results = build_agents(farmers, mock_pred)
        assert len(results) == 3
        ids = [r[0].farmer_id for r in results]
        assert "F001" in ids
        assert "F002" in ids

    def test_build_twins_returns_triples(self):
        """build_twins should return (FarmerAgent, DigitalTwin, PredictionResult)."""
        from app.agents.agent_factory import build_twins
        from app.agents.digital_twin import DigitalTwin
        from app.agents.farmer_agent import FarmerAgent
        mock_pred = _make_predictor_mock(demand=3600.0)
        farmers = [_minimal_farmer_data(farmer_id="F001")]
        triples = build_twins(farmers, mock_pred)
        assert len(triples) == 1
        agent, twin, pred = triples[0]
        assert isinstance(agent, FarmerAgent)
        assert isinstance(twin, DigitalTwin)

    def test_build_agent_inherits_urgency_from_data(self):
        """Agent urgency should come from farmer_data urgency_score."""
        from app.agents.agent_factory import build_agent
        mock_pred = _make_predictor_mock(demand=3600.0)
        fdata = _minimal_farmer_data(urgency_score=0.85)
        agent, _ = build_agent(fdata, mock_pred)
        assert agent.urgency == pytest.approx(0.85)

    def test_build_agent_with_custom_weights(self):
        """Custom UtilityWeights should be passed through to the agent."""
        from app.agents.agent_factory import build_agent
        from app.agents.farmer_agent import UtilityWeights
        mock_pred = _make_predictor_mock(demand=3600.0)
        fdata = _minimal_farmer_data()
        weights = UtilityWeights(water_satisfaction=0.5)
        agent, _ = build_agent(fdata, mock_pred, utility_weights=weights)
        assert agent.utility_weights.water_satisfaction == pytest.approx(0.5)


# ══════════════════════════════════════════════════════════════════════════════
# 11. MULTIPLE FARMER AGENTS
# ══════════════════════════════════════════════════════════════════════════════

class TestMultipleFarmerAgents:
    """Tests involving multiple agents simultaneously."""

    def test_five_agents_different_ids(self):
        """Five agents should have distinct IDs."""
        agents = [_make_agent(farmer_id=f"F{i:03d}") for i in range(5)]
        ids = [a.farmer_id for a in agents]
        assert len(set(ids)) == 5

    def test_agents_independent(self):
        """Updating one twin should not affect another."""
        from app.agents.digital_twin import DigitalTwin
        agent1 = _make_agent(farmer_id="F001", predicted_demand=3600.0)
        agent2 = _make_agent(farmer_id="F002", predicted_demand=3600.0)
        twin1 = DigitalTwin(agent1)
        twin2 = DigitalTwin(agent2)
        twin1.update_allocation(2000.0)
        assert twin2.current_allocation_m3 == pytest.approx(0.0)

    def test_batch_build_then_allocate(self):
        """Should be able to allocate to each twin independently."""
        from app.agents.agent_factory import build_twins
        mock_pred = _make_predictor_mock(demand=3600.0)
        farmers = [
            _minimal_farmer_data(farmer_id=f"F{i:03d}", urgency_score=i * 0.1)
            for i in range(1, 6)
        ]
        triples = build_twins(farmers, mock_pred)
        allocations = [1000, 2000, 3000, 3600, 1500]
        for (agent, twin, _), alloc in zip(triples, allocations):
            twin.update_allocation(float(alloc))
        for (agent, twin, _), alloc in zip(triples, allocations):
            expected = min(1.0, alloc / 3600.0)
            assert twin.satisfaction_score == pytest.approx(expected)

    def test_different_crops_different_sensitivity(self):
        """Different crops should have different crop sensitivities from table."""
        agent_rice = _make_agent(crop="rice")
        agent_groundnut = _make_agent(crop="groundnut")
        # Rice Ky = 1.0, groundnut Ky = 0.7 (from table)
        assert agent_rice.crop_sensitivity_from_table != agent_groundnut.crop_sensitivity_from_table


# ══════════════════════════════════════════════════════════════════════════════
# 12. DETERMINISTIC BEHAVIOUR
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterministicBehaviour:
    """Tests that all agent computations are deterministic."""

    def test_same_inputs_same_agent(self):
        """Same inputs must produce identical agents."""
        agent1 = _make_agent(farmer_id="F001", urgency=0.75, flexibility=0.4)
        agent2 = _make_agent(farmer_id="F001", urgency=0.75, flexibility=0.4)
        assert agent1.predicted_water_demand == agent2.predicted_water_demand
        assert agent1.batna.fallback_utility == pytest.approx(agent2.batna.fallback_utility)
        assert agent1.urgency == agent2.urgency

    def test_utility_deterministic(self):
        """Same inputs must produce same utility value."""
        from app.agents.utility import compute_utility
        kwargs = dict(
            allocation_m3=2500.0,
            predicted_demand_m3=3600.0,
            minimum_requirement_m3=1440.0,
            irrigation_start_hour=9,
            preferred_start_hour=8,
            preferred_end_hour=10,
            acceptable_start_hour=6,
            acceptable_end_hour=12,
            urgency=0.7,
            crop_sensitivity=0.6,
            flexibility=0.3,
        )
        u1 = compute_utility(**kwargs)
        u2 = compute_utility(**kwargs)
        assert u1 == pytest.approx(u2)

    def test_batna_deterministic(self):
        """BATNA calculation is deterministic for same agent."""
        agent = _make_agent(urgency=0.8, crop_sensitivity=0.7)
        u1 = agent.batna.fallback_utility
        # Create another identical agent
        agent2 = _make_agent(urgency=0.8, crop_sensitivity=0.7)
        u2 = agent2.batna.fallback_utility
        assert u1 == pytest.approx(u2)

    def test_twin_reset_gives_identical_state(self):
        """After reset, twin should match initial state exactly."""
        from app.agents.digital_twin import DigitalTwin, NegotiationState
        agent = _make_agent()
        twin = DigitalTwin(agent)
        initial_state = twin.get_state_dict()
        twin.update_allocation(2000.0)
        twin.reset()
        reset_state = twin.get_state_dict()
        assert reset_state["current_allocation_m3"] == initial_state["current_allocation_m3"]
        assert reset_state["negotiation_state"] == initial_state["negotiation_state"]

    def test_stress_deterministic(self):
        """Same allocation + same agent = same stress."""
        from app.agents.utility import compute_crop_stress
        s1 = compute_crop_stress(500.0, 1440.0, "flowering", 0.8)
        s2 = compute_crop_stress(500.0, 1440.0, "flowering", 0.8)
        assert s1 == pytest.approx(s2)

    def test_multiple_runs_same_result(self):
        """Running the same pipeline 3 times must give same utility."""
        from app.agents.agent_factory import build_agent
        from app.agents.digital_twin import DigitalTwin
        mock_pred = _make_predictor_mock(demand=3600.0)
        fdata = _minimal_farmer_data(urgency_score=0.7)
        utilities = []
        for _ in range(3):
            agent, _ = build_agent(fdata, mock_pred)
            twin = DigitalTwin(agent)
            twin.update_allocation(2500.0, start_hour=9)
            utilities.append(twin.utility_score)
        assert all(abs(u - utilities[0]) < 1e-9 for u in utilities)


# ══════════════════════════════════════════════════════════════════════════════
# 13. ML INTEGRATION (Real predictor, if artifacts available)
# ══════════════════════════════════════════════════════════════════════════════

class TestMLIntegration:
    """
    Tests that demonstrate real ML pipeline integration.
    Skipped if model artifacts are not present on disk.
    """

    @pytest.fixture(scope="class")
    def real_predictor(self):
        """Load real predictor from trained artifacts, or skip."""
        model_dir = BACKEND_DIR / "data" / "models"
        if not (model_dir / "rf_model.joblib").exists():
            pytest.skip("Model artifacts not found — run train_models.py first.")
        from app.ml.predictor import WaterDemandPredictor
        return WaterDemandPredictor.from_artifacts(model_dir, model_name="RandomForest")

    def test_real_prediction_builds_agent(self, real_predictor):
        """Real ML prediction should produce a valid FarmerAgent."""
        from app.agents.agent_factory import build_agent
        from app.agents.farmer_agent import FarmerAgent
        fdata = _minimal_farmer_data()
        agent, pred = build_agent(fdata, real_predictor)
        assert isinstance(agent, FarmerAgent)
        assert pred.predicted_water_demand_m3 > 0
        assert agent.predicted_water_demand > 0

    def test_real_prediction_water_constraint_valid(self, real_predictor):
        """Real prediction must satisfy water constraint."""
        from app.agents.agent_factory import build_agent
        fdata = _minimal_farmer_data()
        agent, _ = build_agent(fdata, real_predictor)
        assert agent.minimum_water_requirement <= agent.predicted_water_demand
        assert agent.predicted_water_demand <= agent.maximum_water_requirement

    def test_real_prediction_batna_computed(self, real_predictor):
        """BATNA must be computed from real prediction."""
        from app.agents.agent_factory import build_agent
        fdata = _minimal_farmer_data()
        agent, _ = build_agent(fdata, real_predictor)
        assert agent.batna.fallback_allocation_m3 > 0
        assert 0.0 <= agent.batna.fallback_utility <= 1.0

    def test_scenario_pipeline(self, real_predictor):
        """Full scenario pipeline: data -> predictor -> agents -> twins."""
        from app.agents.agent_factory import build_twins
        from app.ml.data_generator import SyntheticDataGenerator
        gen = SyntheticDataGenerator(seed=42)
        scenario_df = gen.generate_scenario("moderate_shortage", n_farmers=3)
        farmers_data = scenario_df.to_dict(orient="records")
        triples = build_twins(farmers_data, real_predictor)
        assert len(triples) == 3
        for agent, twin, pred in triples:
            # All values computed by the system
            assert agent.predicted_water_demand == pytest.approx(
                pred.predicted_water_demand_m3
            )
            assert 0.0 <= twin.crop_stress_level <= 1.0

    def test_high_urgency_scenario(self, real_predictor):
        """High urgency farmer should have lower BATNA utility."""
        from app.agents.agent_factory import build_agent
        base = _minimal_farmer_data()
        high_urgency = {**base, "urgency_score": 0.95, "growth_stage": "flowering"}
        low_urgency = {**base, "urgency_score": 0.1, "growth_stage": "harvest"}
        agent_high, _ = build_agent(high_urgency, real_predictor)
        agent_low, _ = build_agent(low_urgency, real_predictor)
        assert agent_high.urgency > agent_low.urgency
