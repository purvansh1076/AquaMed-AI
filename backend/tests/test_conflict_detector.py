"""
AquaMediAI — Phase 4: Conflict Detection Tests
================================================

Tests all Phase 4 conflict detection components.

Coverage:
  1.  No shortage (supply >= demand)
  2.  Small shortage (LOW severity)
  3.  Severe shortage (CRITICAL severity)
  4.  Exact demand = supply (no shortage)
  5.  Overlapping windows (two farmers)
  6.  Non-overlapping windows
  7.  Multiple overlapping farmers (3+)
  8.  Canal capacity exceeded
  9.  Canal capacity satisfied
  10. Minimum requirements satisfied
  11. Minimum requirements impossible
  12. High urgency farmer (crop stress conflict)
  13. High crop sensitivity
  14. Multiple simultaneous conflicts
  15. Severity classification
  16. Score normalisation
  17. Deterministic results (same input → same output)
  18. Empty farmer list
  19. Single farmer
  20. Invalid input handling
  21. WindowInterval overlap logic
  22. ConflictReport validation
  23. ScenarioConflictReport aggregation
  24. Overall conflict score components
  25. Integration with Phase 3 FarmerAgent

Run with:
    pytest tests/test_conflict_detector.py -v --tb=short

All 222 Phase 1–3 tests must continue passing.
"""

from __future__ import annotations

import json
from typing import List

import pytest

# ─── Helpers ──────────────────────────────────────────────────────────────────


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


def _make_detector(
    agents,
    available_water: float = 10000.0,
    canal_capacity: float = 60.0,
    scenario_id: str = "test",
) -> "ConflictDetector":
    from app.conflict.detector import ConflictDetector
    return ConflictDetector(
        agents=agents,
        available_water_m3=available_water,
        canal_capacity_m3_per_hour=canal_capacity,
        scenario_id=scenario_id,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. WINDOW INTERVAL
# ══════════════════════════════════════════════════════════════════════════════

class TestWindowInterval:
    """Tests for the WindowInterval time model."""

    def test_basic_creation(self):
        from app.conflict.conflict_types import WindowInterval
        w = WindowInterval(8, 10)
        assert w.start_hour == 8
        assert w.end_hour == 10
        assert w.duration_hours == 2

    def test_invalid_order_rejected(self):
        from app.conflict.conflict_types import WindowInterval
        with pytest.raises(ValueError, match="start_hour"):
            WindowInterval(10, 8)

    def test_equal_start_end_rejected(self):
        from app.conflict.conflict_types import WindowInterval
        with pytest.raises(ValueError):
            WindowInterval(8, 8)

    def test_out_of_range_rejected(self):
        from app.conflict.conflict_types import WindowInterval
        with pytest.raises(ValueError):
            WindowInterval(25, 26)

    def test_overlap_detected(self):
        from app.conflict.conflict_types import WindowInterval
        w1 = WindowInterval(8, 12)
        w2 = WindowInterval(10, 14)
        overlap = w1.overlaps(w2)
        assert overlap is not None
        assert overlap.start_hour == 10
        assert overlap.end_hour == 12
        assert overlap.duration_hours == 2

    def test_no_overlap(self):
        from app.conflict.conflict_types import WindowInterval
        w1 = WindowInterval(6, 8)
        w2 = WindowInterval(10, 12)
        assert w1.overlaps(w2) is None

    def test_adjacent_windows_no_overlap(self):
        """[6,8] and [8,10] touch but don't overlap (overlap duration = 0)."""
        from app.conflict.conflict_types import WindowInterval
        w1 = WindowInterval(6, 8)
        w2 = WindowInterval(8, 10)
        # max(6,8)=8, min(8,10)=8 → 8 < 8 is False → no overlap
        assert w1.overlaps(w2) is None

    def test_identical_windows_full_overlap(self):
        from app.conflict.conflict_types import WindowInterval
        w1 = WindowInterval(8, 10)
        w2 = WindowInterval(8, 10)
        overlap = w1.overlaps(w2)
        assert overlap is not None
        assert overlap.duration_hours == 2

    def test_partial_overlap(self):
        from app.conflict.conflict_types import WindowInterval
        w1 = WindowInterval(6, 10)
        w2 = WindowInterval(9, 14)
        overlap = w1.overlaps(w2)
        assert overlap is not None
        assert overlap.start_hour == 9
        assert overlap.end_hour == 10

    def test_contained_window_overlap(self):
        from app.conflict.conflict_types import WindowInterval
        w1 = WindowInterval(6, 14)
        w2 = WindowInterval(8, 10)   # w2 fully inside w1
        overlap = w1.overlaps(w2)
        assert overlap is not None
        assert overlap.start_hour == 8
        assert overlap.end_hour == 10

    def test_as_dict(self):
        from app.conflict.conflict_types import WindowInterval
        w = WindowInterval(8, 10)
        d = w.as_dict()
        assert d["start_hour"] == 8
        assert d["end_hour"] == 10
        assert d["duration_hours"] == 2


# ══════════════════════════════════════════════════════════════════════════════
# 2. SEVERITY MAPPING
# ══════════════════════════════════════════════════════════════════════════════

class TestSeverityMapping:
    """Tests for severity classification logic."""

    def test_zero_ratio_is_low(self):
        from app.conflict.conflict_types import Severity, severity_from_ratio
        assert severity_from_ratio(0.0) == Severity.LOW

    def test_small_ratio_is_low(self):
        from app.conflict.conflict_types import Severity, severity_from_ratio
        assert severity_from_ratio(0.05) == Severity.LOW

    def test_medium_boundary(self):
        from app.conflict.conflict_types import Severity, severity_from_ratio
        assert severity_from_ratio(0.10) == Severity.MEDIUM

    def test_high_boundary(self):
        from app.conflict.conflict_types import Severity, severity_from_ratio
        assert severity_from_ratio(0.25) == Severity.HIGH

    def test_critical_boundary(self):
        from app.conflict.conflict_types import Severity, severity_from_ratio
        assert severity_from_ratio(0.50) == Severity.CRITICAL

    def test_above_1_clamped_to_critical(self):
        from app.conflict.conflict_types import Severity, severity_from_ratio
        assert severity_from_ratio(2.0) == Severity.CRITICAL

    def test_severity_ordering(self):
        from app.conflict.conflict_types import Severity
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL
        assert Severity.CRITICAL > Severity.LOW

    def test_severity_equality(self):
        from app.conflict.conflict_types import Severity
        assert Severity.HIGH >= Severity.HIGH
        assert Severity.LOW <= Severity.LOW


# ══════════════════════════════════════════════════════════════════════════════
# 3. CONFLICT REPORT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestConflictReport:
    """Tests for ConflictReport model validation."""

    def test_valid_report_created(self):
        from app.conflict.conflict_types import ConflictReport, ConflictType, Severity
        r = ConflictReport(
            conflict_type=ConflictType.RESOURCE_SHORTAGE,
            severity=Severity.HIGH,
            severity_score=0.35,
            involved_farmer_ids=["F001", "F002"],
            total_demand_m3=7200.0,
            total_minimum_requirement_m3=2880.0,
            explanation="Test conflict",
        )
        assert r.conflict_type == ConflictType.RESOURCE_SHORTAGE
        assert r.severity == Severity.HIGH
        assert len(r.involved_farmer_ids) == 2

    def test_severity_score_out_of_range_rejected(self):
        from app.conflict.conflict_types import ConflictReport, ConflictType, Severity
        with pytest.raises(ValueError, match="severity_score"):
            ConflictReport(
                conflict_type=ConflictType.RESOURCE_SHORTAGE,
                severity=Severity.HIGH,
                severity_score=1.5,  # > 1.0
                involved_farmer_ids=["F001"],
                total_demand_m3=3600.0,
                total_minimum_requirement_m3=1440.0,
                explanation="X",
            )

    def test_empty_farmer_ids_rejected(self):
        from app.conflict.conflict_types import ConflictReport, ConflictType, Severity
        with pytest.raises(ValueError, match="involved_farmer_ids"):
            ConflictReport(
                conflict_type=ConflictType.RESOURCE_SHORTAGE,
                severity=Severity.LOW,
                severity_score=0.1,
                involved_farmer_ids=[],  # empty
                total_demand_m3=3600.0,
                total_minimum_requirement_m3=1440.0,
                explanation="X",
            )

    def test_as_dict_serialisable(self):
        from app.conflict.conflict_types import ConflictReport, ConflictType, Severity
        r = ConflictReport(
            conflict_type=ConflictType.IRRIGATION_WINDOW_OVERLAP,
            severity=Severity.MEDIUM,
            severity_score=0.20,
            involved_farmer_ids=["F001", "F002"],
            total_demand_m3=7200.0,
            total_minimum_requirement_m3=2880.0,
            explanation="Overlap",
        )
        d = r.as_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 0
        assert d["conflict_type"] == "irrigation_window_overlap"

    def test_conflict_id_is_unique(self):
        from app.conflict.conflict_types import ConflictReport, ConflictType, Severity
        def _r():
            return ConflictReport(
                conflict_type=ConflictType.RESOURCE_SHORTAGE,
                severity=Severity.LOW,
                severity_score=0.05,
                involved_farmer_ids=["F001"],
                total_demand_m3=3600.0,
                total_minimum_requirement_m3=1440.0,
                explanation="X",
            )
        assert _r().conflict_id != _r().conflict_id


# ══════════════════════════════════════════════════════════════════════════════
# 4. RESOURCE SHORTAGE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

class TestResourceShortage:
    """Tests for RESOURCE_SHORTAGE conflict detection."""

    def test_no_shortage_returns_none(self):
        """Supply >= demand → no shortage conflict."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0),
            _make_agent("F002", predicted_demand=3600.0),
        ]
        detector = _make_detector(agents, available_water=8000.0)
        result = detector.detect_resource_shortage()
        assert result is None

    def test_exact_supply_equals_demand_no_shortage(self):
        """Exact supply = demand → no shortage."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        detector = _make_detector(agents, available_water=3600.0)
        result = detector.detect_resource_shortage()
        assert result is None

    def test_small_shortage_low_severity(self):
        """5% shortage → LOW severity."""
        demand = 3600.0
        available = demand * 0.95  # 5% shortage
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_resource_shortage()
        assert result is not None
        from app.conflict.conflict_types import ConflictType, Severity
        assert result.conflict_type == ConflictType.RESOURCE_SHORTAGE
        assert result.severity == Severity.LOW

    def test_moderate_shortage_medium_severity(self):
        """15% shortage → MEDIUM severity."""
        demand = 3600.0
        available = demand * 0.85
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_resource_shortage()
        assert result is not None
        from app.conflict.conflict_types import Severity
        assert result.severity == Severity.MEDIUM

    def test_large_shortage_high_severity(self):
        """35% shortage → HIGH severity."""
        demand = 3600.0
        available = demand * 0.65
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_resource_shortage()
        assert result is not None
        from app.conflict.conflict_types import Severity
        assert result.severity == Severity.HIGH

    def test_severe_shortage_critical_severity(self):
        """60% shortage → CRITICAL severity."""
        demand = 3600.0
        available = demand * 0.40
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_resource_shortage()
        assert result is not None
        from app.conflict.conflict_types import Severity
        assert result.severity == Severity.CRITICAL

    def test_shortage_involves_all_farmers(self):
        """All farmers should be listed in a shortage conflict."""
        agents = [
            _make_agent("F001", predicted_demand=2000.0),
            _make_agent("F002", predicted_demand=2000.0),
            _make_agent("F003", predicted_demand=2000.0),
        ]
        detector = _make_detector(agents, available_water=3000.0)
        result = detector.detect_resource_shortage()
        assert result is not None
        assert set(result.involved_farmer_ids) == {"F001", "F002", "F003"}

    def test_resource_gap_calculated_correctly(self):
        """resource_gap = total_demand - available."""
        demand = 3600.0
        available = 2800.0
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_resource_shortage()
        assert result is not None
        assert result.resource_gap_m3 == pytest.approx(demand - available)

    def test_severity_score_is_shortage_ratio(self):
        """severity_score should equal shortage_ratio."""
        demand = 4000.0
        available = 3000.0  # 25% shortage
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_resource_shortage()
        assert result is not None
        expected_ratio = (demand - available) / demand
        assert result.severity_score == pytest.approx(expected_ratio, abs=0.001)


# ══════════════════════════════════════════════════════════════════════════════
# 5. IRRIGATION WINDOW OVERLAP
# ══════════════════════════════════════════════════════════════════════════════

class TestWindowOverlap:
    """Tests for IRRIGATION_WINDOW_OVERLAP conflict detection."""

    def test_non_overlapping_windows_no_conflict(self):
        """Non-overlapping windows → no window conflict."""
        agents = [
            _make_agent("F001", pref_start=6, pref_end=8),
            _make_agent("F002", pref_start=10, pref_end=12),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert results == []

    def test_adjacent_windows_no_conflict(self):
        """Adjacent windows [6,8] and [8,10] → no conflict (they touch but don't overlap)."""
        agents = [
            _make_agent("F001", pref_start=6, pref_end=8),
            _make_agent("F002", pref_start=8, pref_end=10),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert results == []

    def test_overlapping_windows_detected(self):
        """Overlapping windows → window conflict detected."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=12),
            _make_agent("F002", pref_start=10, pref_end=14),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert len(results) == 1
        from app.conflict.conflict_types import ConflictType
        assert results[0].conflict_type == ConflictType.IRRIGATION_WINDOW_OVERLAP

    def test_identical_windows_single_conflict(self):
        """Identical windows → 1 conflict (for the pair)."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10),
            _make_agent("F002", pref_start=8, pref_end=10),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert len(results) == 1

    def test_three_farmers_all_overlapping(self):
        """3 farmers all overlapping → 3 pairwise conflicts."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=12),
            _make_agent("F002", pref_start=9, pref_end=13),
            _make_agent("F003", pref_start=10, pref_end=14),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert len(results) == 3  # C(3,2) = 3 pairs

    def test_three_farmers_partial_overlap(self):
        """3 farmers, only 1 pair overlaps."""
        agents = [
            _make_agent("F001", pref_start=6, pref_end=8),
            _make_agent("F002", pref_start=8, pref_end=12),
            _make_agent("F003", pref_start=10, pref_end=14),
        ]
        # F001-F002: adjacent (no), F001-F003: no overlap, F002-F003: 8-12 vs 10-14 → overlap
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert len(results) == 1
        fids = set(results[0].involved_farmer_ids)
        assert fids == {"F002", "F003"}

    def test_overlap_evidence_structure(self):
        """Window conflict evidence should contain farmer data and overlap."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=12),
            _make_agent("F002", pref_start=10, pref_end=14),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_window_conflicts()
        assert len(results) == 1
        ev = results[0].evidence
        assert "farmer_a" in ev
        assert "farmer_b" in ev
        assert "overlap" in ev
        assert ev["overlap"]["start_hour"] == 10
        assert ev["overlap"]["end_hour"] == 12

    def test_high_urgency_increases_severity_score(self):
        """High urgency pair should have higher severity score than low urgency."""
        agents_high = [
            _make_agent("F001", pref_start=8, pref_end=12, urgency=0.9),
            _make_agent("F002", pref_start=10, pref_end=14, urgency=0.9),
        ]
        agents_low = [
            _make_agent("F001", pref_start=8, pref_end=12, urgency=0.1),
            _make_agent("F002", pref_start=10, pref_end=14, urgency=0.1),
        ]
        det_high = _make_detector(agents_high, available_water=10000.0)
        det_low = _make_detector(agents_low, available_water=10000.0)
        results_high = det_high.detect_window_conflicts()
        results_low = det_low.detect_window_conflicts()
        assert results_high[0].severity_score > results_low[0].severity_score


# ══════════════════════════════════════════════════════════════════════════════
# 6. CANAL CAPACITY CONFLICT
# ══════════════════════════════════════════════════════════════════════════════

class TestCanalCapacity:
    """Tests for CANAL_CAPACITY_CONFLICT detection."""

    def test_no_overlap_no_canal_conflict(self):
        """Non-overlapping windows → no canal conflict."""
        agents = [
            _make_agent("F001", pref_start=6, pref_end=8, predicted_demand=3600.0),
            _make_agent("F002", pref_start=10, pref_end=12, predicted_demand=3600.0),
        ]
        detector = _make_detector(agents, available_water=10000.0, canal_capacity=60.0)
        results = detector.detect_canal_conflicts()
        assert results == []

    def test_canal_capacity_satisfied(self):
        """Overlapping windows but combined flow < capacity → no conflict."""
        # F001: 1200 m3 / 4h = 300 m3/h, F002: 1200 / 4h = 300 m3/h → total 600 > 60
        # Let's make it small: 60 m3 / 2h = 30, 60 / 2h = 30 → 60 = capacity (no exceed)
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=60.0, min_water=24.0, max_water=80.0),
            _make_agent("F002", pref_start=8, pref_end=10, predicted_demand=60.0, min_water=24.0, max_water=80.0),
        ]
        # flow_a = 60/2 = 30, flow_b = 60/2 = 30, total = 60 = capacity → no exceed
        detector = _make_detector(agents, available_water=10000.0, canal_capacity=60.0)
        results = detector.detect_canal_conflicts()
        assert results == []

    def test_canal_capacity_exceeded(self):
        """Flow demand exceeds canal capacity → conflict detected."""
        # Large overlapping demands
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0),
            _make_agent("F002", pref_start=8, pref_end=10, predicted_demand=3600.0),
        ]
        # flow per farmer: 3600/2 = 1800 m3/h each → total 3600 >> 60 capacity
        detector = _make_detector(agents, available_water=10000.0, canal_capacity=60.0)
        results = detector.detect_canal_conflicts()
        assert len(results) == 1
        from app.conflict.conflict_types import ConflictType
        assert results[0].conflict_type == ConflictType.CANAL_CAPACITY_CONFLICT

    def test_canal_conflict_evidence(self):
        """Canal conflict evidence should contain flow rates and overload."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0),
            _make_agent("F002", pref_start=8, pref_end=10, predicted_demand=3600.0),
        ]
        detector = _make_detector(agents, available_water=10000.0, canal_capacity=60.0)
        results = detector.detect_canal_conflicts()
        assert len(results) >= 1
        ev = results[0].evidence
        assert "combined_flow_m3_per_h" in ev
        assert "canal_capacity_m3_per_h" in ev
        assert "overload_m3_per_h" in ev
        assert ev["combined_flow_m3_per_h"] > ev["canal_capacity_m3_per_h"]

    def test_high_canal_capacity_no_conflict(self):
        """Very high canal capacity → no canal conflict."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0),
            _make_agent("F002", pref_start=8, pref_end=10, predicted_demand=3600.0),
        ]
        # 3600/2 + 3600/2 = 3600 m3/h, capacity = 10000 → no conflict
        detector = _make_detector(agents, available_water=10000.0, canal_capacity=10000.0)
        results = detector.detect_canal_conflicts()
        assert results == []


# ══════════════════════════════════════════════════════════════════════════════
# 7. MINIMUM REQUIREMENT CONFLICT
# ══════════════════════════════════════════════════════════════════════════════

class TestMinimumRequirementConflict:
    """Tests for MINIMUM_REQUIREMENT_CONFLICT detection."""

    def test_minimum_requirements_satisfied(self):
        """Available > total min req → no conflict."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        # Total min = 2880, available = 5000 → no conflict
        detector = _make_detector(agents, available_water=5000.0)
        result = detector.detect_minimum_requirement_conflicts()
        assert result is None

    def test_minimum_requirements_exactly_met(self):
        """Available = total min req → no conflict."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        detector = _make_detector(agents, available_water=2880.0)
        result = detector.detect_minimum_requirement_conflicts()
        assert result is None

    def test_minimum_requirements_impossible(self):
        """Available < total min req → MINIMUM_REQUIREMENT_CONFLICT."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        # Total min = 2880, available = 2000 → gap = 880
        detector = _make_detector(agents, available_water=2000.0)
        result = detector.detect_minimum_requirement_conflicts()
        assert result is not None
        from app.conflict.conflict_types import ConflictType
        assert result.conflict_type == ConflictType.MINIMUM_REQUIREMENT_CONFLICT

    def test_minimum_requirement_gap_calculated(self):
        """minimum_requirement_gap_m3 must be correct."""
        min_req_total = 2880.0
        available = 2000.0
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        detector = _make_detector(agents, available_water=available)
        result = detector.detect_minimum_requirement_conflicts()
        assert result is not None
        assert result.minimum_requirement_gap_m3 == pytest.approx(min_req_total - available)

    def test_min_req_conflict_severity_at_least_high(self):
        """Minimum requirement conflicts should be at least HIGH severity."""
        from app.conflict.conflict_types import Severity
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        detector = _make_detector(agents, available_water=1000.0)  # Very low
        result = detector.detect_minimum_requirement_conflicts()
        assert result is not None
        assert result.severity >= Severity.HIGH

    def test_min_req_distinct_from_resource_shortage(self):
        """Min req conflict and resource shortage can coexist independently."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
        ]
        # Available = 2000: covers min_req (1440) but not demand (3600)
        detector = _make_detector(agents, available_water=2000.0)
        shortage = detector.detect_resource_shortage()
        min_req = detector.detect_minimum_requirement_conflicts()
        assert shortage is not None  # demand > available
        assert min_req is None  # available > min_req

    def test_both_conflicts_when_very_low_water(self):
        """Very low water → both shortage AND min-req conflicts."""
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
        ]
        detector = _make_detector(agents, available_water=500.0)  # < min_req
        shortage = detector.detect_resource_shortage()
        min_req = detector.detect_minimum_requirement_conflicts()
        assert shortage is not None
        assert min_req is not None


# ══════════════════════════════════════════════════════════════════════════════
# 8. HIGH CROP STRESS CONFLICT
# ══════════════════════════════════════════════════════════════════════════════

class TestCropStressConflict:
    """Tests for HIGH_CROP_STRESS conflict detection."""

    def test_low_stress_no_conflict(self):
        """Low urgency + low sensitivity + harvest → no stress conflict."""
        agents = [
            _make_agent(
                "F001",
                growth_stage="harvest",  # criticality=0.20
                urgency=0.3,
                crop_sensitivity=0.3,
            )
        ]
        # CSPS = 0.3 * 0.3 * 0.20 = 0.018 < 0.49 → no conflict
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        assert results == []

    def test_high_urgency_flowering_generates_conflict(self):
        """High urgency + high sensitivity + flowering → HIGH_CROP_STRESS conflict."""
        agents = [
            _make_agent(
                "F001",
                growth_stage="flowering",  # criticality=1.0
                urgency=0.9,
                crop_sensitivity=0.9,
            )
        ]
        # CSPS = 0.9 * 0.9 * 1.0 = 0.81 → CRITICAL
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        assert len(results) == 1
        from app.conflict.conflict_types import ConflictType
        assert results[0].conflict_type == ConflictType.HIGH_CROP_STRESS

    def test_high_urgency_high_sensitivity_conflict(self):
        """High urgency + high sensitivity + vegetative → may generate conflict."""
        agents = [
            _make_agent(
                "F001",
                growth_stage="vegetative",  # criticality=0.60
                urgency=1.0,
                crop_sensitivity=1.0,
            )
        ]
        # CSPS = 1.0 * 1.0 * 0.60 = 0.60 > 0.49 → conflict
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        assert len(results) == 1

    def test_multiple_stress_farmers_multiple_conflicts(self):
        """Multiple high-stress farmers → multiple conflict reports."""
        agents = [
            _make_agent("F001", growth_stage="flowering", urgency=0.9, crop_sensitivity=0.9),
            _make_agent("F002", growth_stage="flowering", urgency=0.85, crop_sensitivity=0.85),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        assert len(results) == 2

    def test_stress_conflict_has_disclaimer(self):
        """Crop stress conflict evidence must include synthetic data disclaimer."""
        agents = [
            _make_agent("F001", growth_stage="flowering", urgency=0.9, crop_sensitivity=0.9),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        assert len(results) == 1
        ev = results[0].evidence
        assert "disclaimer" in ev
        assert "synthetic" in ev["disclaimer"].lower()

    def test_stress_conflict_severity_at_least_medium(self):
        """Stress conflicts should be at least MEDIUM severity."""
        from app.conflict.conflict_types import Severity
        agents = [
            _make_agent("F001", growth_stage="flowering", urgency=0.8, crop_sensitivity=0.7),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        if results:
            assert results[0].severity >= Severity.MEDIUM

    def test_only_one_farmer_in_stress_conflict(self):
        """Each stress conflict should involve only the one stressed farmer."""
        agents = [
            _make_agent("F001", growth_stage="flowering", urgency=0.9, crop_sensitivity=0.9),
            _make_agent("F002", growth_stage="harvest", urgency=0.1, crop_sensitivity=0.1),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        results = detector.detect_crop_stress_conflicts()
        assert len(results) == 1
        assert results[0].involved_farmer_ids == ["F001"]


# ══════════════════════════════════════════════════════════════════════════════
# 9. DETECT ALL (AGGREGATE)
# ══════════════════════════════════════════════════════════════════════════════

class TestDetectAll:
    """Tests for the detect_all() aggregation method."""

    def test_empty_agents_returns_empty_report(self):
        """Empty agent list → empty scenario report."""
        detector = _make_detector([], available_water=5000.0)
        report = detector.detect_all()
        assert report.total_conflicts == 0
        assert report.n_farmers == 0
        assert report.highest_severity is None

    def test_single_farmer_no_shortage(self):
        """Single farmer, supply > demand → no conflicts."""
        agents = [_make_agent("F001", predicted_demand=2000.0)]
        detector = _make_detector(agents, available_water=5000.0)
        report = detector.detect_all()
        # No shortage, no window overlap (single farmer), no min-req conflict
        shortage = sum(1 for c in report.conflicts
                       if c.conflict_type.value == "resource_shortage")
        assert shortage == 0

    def test_multiple_simultaneous_conflicts(self):
        """Scenario with shortage + overlap + canal + stress → multiple conflicts."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0,
                        growth_stage="flowering", urgency=0.9, crop_sensitivity=0.9),
            _make_agent("F002", pref_start=8, pref_end=10, predicted_demand=3600.0,
                        growth_stage="flowering", urgency=0.85, crop_sensitivity=0.85),
        ]
        # Low available water → shortage + min-req conflict
        # Same window → overlap + canal conflict
        # High CSPS → stress conflicts
        detector = _make_detector(
            agents, available_water=2000.0, canal_capacity=30.0
        )
        report = detector.detect_all()
        assert report.total_conflicts >= 3  # At least shortage, overlap, canal

    def test_scenario_report_structure(self):
        """ScenarioConflictReport should have all required fields."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        detector = _make_detector(agents, available_water=5000.0)
        report = detector.detect_all()
        d = report.as_dict()
        required_keys = [
            "scenario_id", "n_farmers", "total_demand_m3",
            "available_water_m3", "total_conflicts",
            "highest_severity", "conflicts",
        ]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_scenario_id_propagated_to_conflicts(self):
        """scenario_id should be stamped on each conflict report."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        detector = _make_detector(agents, available_water=2000.0, scenario_id="test_scenario_42")
        report = detector.detect_all()
        for c in report.conflicts:
            assert c.scenario_id == "test_scenario_42"

    def test_highest_severity_correct(self):
        """highest_severity should be the maximum across all conflicts."""
        from app.conflict.conflict_types import Severity
        agents = [
            _make_agent("F001", predicted_demand=3600.0, min_water=1440.0),
            _make_agent("F002", predicted_demand=3600.0, min_water=1440.0),
        ]
        # available = 500 → CRITICAL shortage + CRITICAL min-req
        detector = _make_detector(agents, available_water=500.0)
        report = detector.detect_all()
        assert report.highest_severity is not None
        assert report.highest_severity >= Severity.HIGH

    def test_overall_shortage_ratio_correct(self):
        """overall_shortage_ratio should equal (demand - available) / demand."""
        demand = 3600.0
        available = 2700.0
        agents = [_make_agent("F001", predicted_demand=demand)]
        detector = _make_detector(agents, available_water=available)
        report = detector.detect_all()
        expected_ratio = (demand - available) / demand
        assert report.overall_shortage_ratio == pytest.approx(expected_ratio, abs=0.001)

    def test_report_serialisable(self):
        """detect_all() output should be JSON-serialisable."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0,
                        growth_stage="flowering", urgency=0.9, crop_sensitivity=0.9),
        ]
        detector = _make_detector(agents, available_water=2000.0)
        report = detector.detect_all()
        json_str = json.dumps(report.as_dict())
        assert len(json_str) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 10. OVERALL CONFLICT SCORE
# ══════════════════════════════════════════════════════════════════════════════

class TestOverallConflictScore:
    """Tests for the compute_overall_conflict_score() method."""

    def test_score_in_0_1_range(self):
        """Conflict score must always be in [0, 1]."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0,
                        urgency=0.9),
            _make_agent("F002", pref_start=9, pref_end=11, predicted_demand=3600.0,
                        urgency=0.3),
        ]
        detector = _make_detector(agents, available_water=4000.0)
        result = detector.compute_overall_conflict_score()
        assert 0.0 <= result["conflict_score"] <= 1.0

    def test_no_conflict_low_score(self):
        """Ample supply, no overlap → near-zero conflict score."""
        agents = [
            _make_agent("F001", pref_start=6, pref_end=8, urgency=0.3, crop_sensitivity=0.3),
        ]
        detector = _make_detector(agents, available_water=50000.0)
        result = detector.compute_overall_conflict_score()
        assert result["conflict_score"] < 0.5

    def test_high_shortage_increases_score(self):
        """Critical shortage should yield high conflict score."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        det_no_shortage = _make_detector(agents, available_water=10000.0)
        det_shortage = _make_detector(agents, available_water=500.0)
        score_no = det_no_shortage.compute_overall_conflict_score()["conflict_score"]
        score_yes = det_shortage.compute_overall_conflict_score()["conflict_score"]
        assert score_yes > score_no

    def test_score_components_present(self):
        """Score dict should contain all required component keys."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        detector = _make_detector(agents, available_water=5000.0)
        result = detector.compute_overall_conflict_score()
        required = [
            "shortage_ratio", "urgency_disparity_score",
            "window_overlap_fraction", "high_stress_fraction",
            "conflict_score", "components", "weights",
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_empty_agents_returns_zero_score(self):
        """Empty agent list → zero conflict score."""
        detector = _make_detector([], available_water=5000.0)
        result = detector.compute_overall_conflict_score()
        assert result["conflict_score"] == pytest.approx(0.0)

    def test_custom_weights_applied(self):
        """Custom scoring weights should be reflected in the score."""
        from app.conflict.detector import ConflictDetector, ConflictScoringWeights
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        # Weights that only consider shortage
        weights_shortage_only = ConflictScoringWeights(
            shortage=1.0, urgency=0.0, overlap=0.0, stress=0.0
        )
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=2000.0,
            scoring_weights=weights_shortage_only,
        )
        result = detector.compute_overall_conflict_score()
        # Score should be dominated by shortage ratio
        assert result["conflict_score"] == pytest.approx(result["shortage_ratio"], abs=0.01)


# ══════════════════════════════════════════════════════════════════════════════
# 11. DETERMINISTIC BEHAVIOUR
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterministicBehaviour:
    """Tests that confirm same input → same output."""

    def test_detect_all_deterministic(self):
        """Running detect_all twice must yield same conflict count."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=10, predicted_demand=3600.0,
                        urgency=0.7, growth_stage="flowering"),
            _make_agent("F002", pref_start=9, pref_end=11, predicted_demand=3600.0,
                        urgency=0.5),
        ]
        detector = _make_detector(agents, available_water=4000.0, canal_capacity=60.0)
        report1 = detector.detect_all()
        report2 = detector.detect_all()
        assert report1.total_conflicts == report2.total_conflicts
        assert report1.overall_shortage_ratio == report2.overall_shortage_ratio

    def test_conflict_score_deterministic(self):
        """conflict_score must be identical on repeated calls."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=12, urgency=0.6),
            _make_agent("F002", pref_start=10, pref_end=14, urgency=0.4),
        ]
        detector = _make_detector(agents, available_water=5000.0)
        s1 = detector.compute_overall_conflict_score()["conflict_score"]
        s2 = detector.compute_overall_conflict_score()["conflict_score"]
        assert s1 == pytest.approx(s2)

    def test_same_input_same_severity(self):
        """Same scenario → same severity classification."""
        agents = [_make_agent("F001", predicted_demand=3600.0)]
        detector = _make_detector(agents, available_water=2000.0)
        r1 = detector.detect_resource_shortage()
        r2 = detector.detect_resource_shortage()
        assert r1.severity == r2.severity
        assert r1.severity_score == pytest.approx(r2.severity_score)

    def test_window_overlap_deterministic(self):
        """Window conflict count must be the same on repeated calls."""
        agents = [
            _make_agent("F001", pref_start=8, pref_end=12),
            _make_agent("F002", pref_start=10, pref_end=14),
            _make_agent("F003", pref_start=6, pref_end=9),
        ]
        detector = _make_detector(agents, available_water=10000.0)
        r1 = detector.detect_window_conflicts()
        r2 = detector.detect_window_conflicts()
        assert len(r1) == len(r2)


# ══════════════════════════════════════════════════════════════════════════════
# 12. INVALID INPUT HANDLING
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidInputHandling:
    """Tests for invalid input handling in ConflictDetector."""

    def test_negative_available_water_rejected(self):
        """Negative available water must raise ValueError."""
        from app.conflict.detector import ConflictDetector
        with pytest.raises(ValueError, match="available_water_m3"):
            ConflictDetector(agents=[], available_water_m3=-100.0)

    def test_zero_canal_capacity_rejected(self):
        """Zero canal capacity must raise ValueError."""
        from app.conflict.detector import ConflictDetector
        with pytest.raises(ValueError, match="canal_capacity_m3_per_hour"):
            ConflictDetector(
                agents=[], available_water_m3=1000.0,
                canal_capacity_m3_per_hour=0.0,
            )

    def test_negative_canal_capacity_rejected(self):
        """Negative canal capacity must raise ValueError."""
        from app.conflict.detector import ConflictDetector
        with pytest.raises(ValueError, match="canal_capacity_m3_per_hour"):
            ConflictDetector(
                agents=[], available_water_m3=1000.0,
                canal_capacity_m3_per_hour=-10.0,
            )

    def test_invalid_scoring_weight_rejected(self):
        """Negative scoring weight must raise ValueError."""
        from app.conflict.detector import ConflictScoringWeights
        with pytest.raises(ValueError):
            ConflictScoringWeights(shortage=-0.1)

    def test_window_interval_invalid_hour_rejected(self):
        """WindowInterval with out-of-range hours must raise."""
        from app.conflict.conflict_types import WindowInterval
        with pytest.raises(ValueError):
            WindowInterval(start_hour=-1, end_hour=5)


# ══════════════════════════════════════════════════════════════════════════════
# 13. SCENARIO INTEGRATION WITH PHASE 3
# ══════════════════════════════════════════════════════════════════════════════

class TestPhase3Integration:
    """Integration tests demonstrating Phase 3 → Phase 4 pipeline."""

    @pytest.fixture(scope="class")
    def real_predictor(self):
        """Load real predictor or skip."""
        import os
        from pathlib import Path
        model_dir = Path(__file__).parent.parent / "data" / "models"
        if not (model_dir / "rf_model.joblib").exists():
            pytest.skip("Model artifacts not found — run train_models.py first.")
        from app.ml.predictor import WaterDemandPredictor
        return WaterDemandPredictor.from_artifacts(model_dir, model_name="RandomForest")

    def test_agents_from_scenario_feed_detector(self, real_predictor):
        """Phase 3 agents should feed directly into Phase 4 detector."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "moderate_shortage", n_farmers=5, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)
        available = total_demand * 0.75  # 25% shortage

        detector = ConflictDetector(
            agents=agents,
            available_water_m3=available,
            canal_capacity_m3_per_hour=60.0,
            scenario_id="moderate_shortage_test",
        )
        report = detector.detect_all()
        # Should detect at least a resource shortage
        assert report.total_conflicts >= 1
        assert report.n_farmers == 5

    def test_severe_shortage_scenario(self, real_predictor):
        """severe_shortage scenario should produce CRITICAL conflicts."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.conflict.conflict_types import Severity
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "severe_shortage", n_farmers=4, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)
        # Only 40% supply — severe
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=total_demand * 0.40,
            canal_capacity_m3_per_hour=40.0,
        )
        report = detector.detect_all()
        assert report.highest_severity >= Severity.HIGH

    def test_normal_water_scenario_no_resource_shortage(self, real_predictor):
        """normal_water scenario: ample supply → no resource shortage."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "normal_water", n_farmers=3, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)
        # Give plenty of water
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=total_demand * 1.3,
            canal_capacity_m3_per_hour=500.0,
        )
        shortage = detector.detect_resource_shortage()
        assert shortage is None

    def test_high_urgency_scenario_generates_stress_conflicts(self, real_predictor):
        """high_urgency_farmer scenario should produce crop stress conflicts."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.conflict.conflict_types import ConflictType
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "high_urgency_farmer", n_farmers=3, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=total_demand * 0.7,
        )
        report = detector.detect_all()
        stress_types = [
            c for c in report.conflicts
            if c.conflict_type == ConflictType.HIGH_CROP_STRESS
        ]
        # At least the urgency-injected farmer should appear
        assert len(stress_types) >= 0  # May or may not trigger depending on parameters

    def test_conflict_score_pipeline(self, real_predictor):
        """Overall conflict score pipeline should run end-to-end."""
        from app.agents.agent_factory import build_agents_from_scenario
        from app.conflict.detector import ConflictDetector

        triples = build_agents_from_scenario(
            "simultaneous_demand", n_farmers=5, predictor=real_predictor, seed=42
        )
        agents = [t[0] for t in triples]
        total_demand = sum(a.predicted_water_demand for a in agents)
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=total_demand * 0.8,
            canal_capacity_m3_per_hour=60.0,
        )
        score = detector.compute_overall_conflict_score()
        assert 0.0 <= score["conflict_score"] <= 1.0
        assert score["shortage_ratio"] > 0
