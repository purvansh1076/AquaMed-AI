"""
AquaMediAI — Conflict Detection Engine
========================================

Consumes a pool of Phase 3 FarmerAgent objects and identifies water-sharing
conflicts BEFORE any allocation or negotiation.

The detector output becomes the input to Phase 5 (OR-Tools LP Allocation).

Conflict Types Detected
-----------------------
1. RESOURCE_SHORTAGE          — Total demand > available water
2. IRRIGATION_WINDOW_OVERLAP  — Competing preferred irrigation windows
3. CANAL_CAPACITY_CONFLICT    — Simultaneous demand exceeds canal flow rate
4. MINIMUM_REQUIREMENT_CONFLICT — Available water < combined minimum requirements
5. HIGH_CROP_STRESS           — Farmers at high agronomic risk

Conflict Scoring Formula
------------------------

The overall conflict_score for a scenario is a weighted aggregate:

    conflict_score =
        w_shortage  * shortage_ratio
      + w_urgency   * urgency_disparity_score
      + w_overlap   * window_overlap_score
      + w_stress    * crop_stress_score

where:
    shortage_ratio = max(0, (total_demand - available) / total_demand)
    urgency_disparity_score = stddev of urgency scores (normalised to [0,1])
    window_overlap_score = fraction of farmer pairs with overlapping windows
    crop_stress_score = fraction of farmers with high crop stress

Default weights (configurable via ConflictScoringWeights):
    w_shortage = 0.40   (shortage is the primary conflict driver)
    w_urgency  = 0.20   (urgency disparity exacerbates conflict)
    w_overlap  = 0.25   (window overlap directly causes canal conflict)
    w_stress   = 0.15   (crop stress determines conflict urgency)

All individual component scores are clamped to [0, 1].
The final conflict_score is also clamped to [0, 1].

Design Principles
-----------------
- Deterministic: same input → same output, always.
- No LLM calls. No randomness.
- FarmerAgent is the single source of farmer data — no duplication.
- Available water must be provided externally (from scenario generator).

DISCLAIMER: All conflict analysis is performed on SYNTHETIC data.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.agents.farmer_agent import FarmerAgent
from app.conflict.conflict_types import (
    ConflictReport,
    ConflictType,
    ScenarioConflictReport,
    Severity,
    WindowInterval,
    severity_from_ratio,
)

logger = logging.getLogger(__name__)

# ─── Scoring weights ──────────────────────────────────────────────────────────

@dataclass
class ConflictScoringWeights:
    """
    Configurable weights for the overall conflict scoring formula.

    Attributes
    ----------
    shortage : float
        Weight for resource shortage ratio.
    urgency : float
        Weight for urgency disparity among farmers.
    overlap : float
        Weight for irrigation window overlap fraction.
    stress : float
        Weight for crop stress fraction.

    All weights must be >= 0. They do not need to sum to 1 —
    the result is normalised to [0, 1] by the theoretical maximum.
    """
    shortage: float = 0.40
    urgency: float = 0.20
    overlap: float = 0.25
    stress: float = 0.15

    def __post_init__(self) -> None:
        for attr in ("shortage", "urgency", "overlap", "stress"):
            v = getattr(self, attr)
            if v < 0.0:
                raise ValueError(f"ConflictScoringWeights.{attr} must be >= 0, got {v}")

    @property
    def total(self) -> float:
        return self.shortage + self.urgency + self.overlap + self.stress


# ─── Thresholds ────────────────────────────────────────────────────────────────

# Crop stress priority threshold — agents above this are considered high-stress
HIGH_STRESS_URGENCY_THRESHOLD: float = 0.70
HIGH_STRESS_SENSITIVITY_THRESHOLD: float = 0.70

# Canal capacity defaults (m³/hour) — used if not explicitly provided
DEFAULT_CANAL_CAPACITY_M3_PER_HOUR: float = 60.0


class ConflictDetector:
    """
    Deterministic Conflict Detection Engine.

    Consumes a list of FarmerAgent objects and available water,
    then detects all water-sharing conflicts.

    Parameters
    ----------
    agents : list of FarmerAgent
        The farmer digital agents for this scenario (Phase 3 output).
    available_water_m3 : float
        Total water available for the scenario (m³).
    canal_capacity_m3_per_hour : float
        Maximum canal flow rate (m³/hour). Default: 60.0.
    scoring_weights : ConflictScoringWeights, optional
        Configurable scoring weights.
    scenario_id : str
        Identifier for the scenario being analysed.

    Usage
    -----
        detector = ConflictDetector(agents, available_water_m3=4500.0)
        report = detector.detect_all()
    """

    def __init__(
        self,
        agents: List[FarmerAgent],
        available_water_m3: float,
        canal_capacity_m3_per_hour: float = DEFAULT_CANAL_CAPACITY_M3_PER_HOUR,
        scoring_weights: Optional[ConflictScoringWeights] = None,
        scenario_id: str = "unknown",
    ) -> None:
        if available_water_m3 < 0:
            raise ValueError(
                f"available_water_m3 must be >= 0, got {available_water_m3}"
            )
        if canal_capacity_m3_per_hour <= 0:
            raise ValueError(
                f"canal_capacity_m3_per_hour must be > 0, got {canal_capacity_m3_per_hour}"
            )

        self._agents = list(agents)
        self._available_water_m3 = available_water_m3
        self._canal_capacity_m3_per_hour = canal_capacity_m3_per_hour
        self._weights = scoring_weights or ConflictScoringWeights()
        self._scenario_id = scenario_id

        # Pre-compute aggregate scenario metrics (used by multiple detectors)
        self._total_demand_m3 = sum(a.predicted_water_demand for a in self._agents)
        self._total_min_req_m3 = sum(a.minimum_water_requirement for a in self._agents)

        logger.debug(
            "ConflictDetector initialised: %d agents, demand=%.1f m3, "
            "available=%.1f m3, canal=%.1f m3/h",
            len(self._agents),
            self._total_demand_m3,
            self._available_water_m3,
            self._canal_capacity_m3_per_hour,
        )

    # ─── Public API ───────────────────────────────────────────────────────────

    def detect_all(self) -> ScenarioConflictReport:
        """
        Run all conflict detectors and return a comprehensive scenario report.

        Returns
        -------
        ScenarioConflictReport
            Aggregate analysis with all detected conflicts.
        """
        if not self._agents:
            logger.info("ConflictDetector: no agents — returning empty report.")
            return ScenarioConflictReport(
                scenario_id=self._scenario_id,
                n_farmers=0,
                total_demand_m3=0.0,
                available_water_m3=self._available_water_m3,
                total_minimum_requirement_m3=0.0,
                conflicts=[],
            )

        conflicts: List[ConflictReport] = []

        # Run each detector
        shortage = self.detect_resource_shortage()
        if shortage:
            conflicts.append(shortage)

        min_req = self.detect_minimum_requirement_conflicts()
        if min_req:
            conflicts.append(min_req)

        conflicts.extend(self.detect_window_conflicts())
        conflicts.extend(self.detect_canal_conflicts())
        conflicts.extend(self.detect_crop_stress_conflicts())

        # Stamp scenario_id on all reports
        for c in conflicts:
            c.scenario_id = self._scenario_id

        report = ScenarioConflictReport(
            scenario_id=self._scenario_id,
            n_farmers=len(self._agents),
            total_demand_m3=self._total_demand_m3,
            available_water_m3=self._available_water_m3,
            total_minimum_requirement_m3=self._total_min_req_m3,
            conflicts=conflicts,
        )

        logger.info(
            "ConflictDetector[%s]: detected %d conflicts, "
            "shortage_ratio=%.3f, highest=%s",
            self._scenario_id,
            len(conflicts),
            report.overall_shortage_ratio,
            report.highest_severity.value if report.highest_severity else "none",
        )
        return report

    # ─── 1. Resource Shortage ─────────────────────────────────────────────────

    def detect_resource_shortage(self) -> Optional[ConflictReport]:
        """
        Detect RESOURCE_SHORTAGE conflict.

        Triggered when: total_predicted_demand > available_water

        Metrics
        -------
        resource_gap = total_demand - available_water
        shortage_ratio = resource_gap / total_demand  (in [0, 1])

        Severity thresholds (from conflict_types.severity_from_ratio):
            < 0.10 → LOW
            < 0.25 → MEDIUM
            < 0.50 → HIGH
            ≥ 0.50 → CRITICAL

        Returns None if no shortage exists.
        """
        if len(self._agents) == 0:
            return None

        resource_gap = self._total_demand_m3 - self._available_water_m3
        if resource_gap <= 0:
            logger.debug("detect_resource_shortage: no shortage (gap=%.1f)", resource_gap)
            return None

        shortage_ratio = resource_gap / self._total_demand_m3 if self._total_demand_m3 > 0 else 0.0
        shortage_ratio = max(0.0, min(1.0, shortage_ratio))
        severity = severity_from_ratio(shortage_ratio)

        explanation = (
            f"Total predicted water demand ({self._total_demand_m3:.1f} m³) "
            f"exceeds available supply ({self._available_water_m3:.1f} m³) "
            f"by {resource_gap:.1f} m³ ({shortage_ratio * 100:.1f}% shortage). "
            f"Severity: {severity.value.upper()}."
        )

        report = ConflictReport(
            conflict_type=ConflictType.RESOURCE_SHORTAGE,
            severity=severity,
            severity_score=round(shortage_ratio, 4),
            involved_farmer_ids=[a.farmer_id for a in self._agents],
            total_demand_m3=self._total_demand_m3,
            total_minimum_requirement_m3=self._total_min_req_m3,
            available_water_m3=self._available_water_m3,
            resource_gap_m3=resource_gap,
            minimum_requirement_gap_m3=max(0.0, self._total_min_req_m3 - self._available_water_m3),
            explanation=explanation,
            evidence={
                "shortage_ratio": round(shortage_ratio, 4),
                "resource_gap_m3": round(resource_gap, 2),
                "total_demand_m3": round(self._total_demand_m3, 2),
                "available_water_m3": round(self._available_water_m3, 2),
                "n_farmers": len(self._agents),
                "per_farmer_demands": {
                    a.farmer_id: round(a.predicted_water_demand, 2)
                    for a in self._agents
                },
            },
        )
        logger.info(
            "RESOURCE_SHORTAGE: gap=%.1f m3, ratio=%.3f, severity=%s",
            resource_gap, shortage_ratio, severity.value,
        )
        return report

    # ─── 2. Irrigation Window Overlap ─────────────────────────────────────────

    def detect_window_conflicts(self) -> List[ConflictReport]:
        """
        Detect IRRIGATION_WINDOW_OVERLAP conflicts.

        Two farmers conflict if their preferred irrigation windows overlap.
        All pairs of agents are checked.

        For each overlapping pair, a ConflictReport is generated with:
        - The overlapping time interval
        - Overlap duration in hours
        - Severity based on overlap fraction and combined urgency

        Overlap severity score:
            score = (overlap_hours / min_window_hours) * avg_urgency_weight

        Returns
        -------
        list of ConflictReport (one per conflicting pair)
        """
        reports: List[ConflictReport] = []
        n = len(self._agents)

        for i in range(n):
            for j in range(i + 1, n):
                agent_a = self._agents[i]
                agent_b = self._agents[j]

                win_a = WindowInterval(
                    start_hour=agent_a.preferred_start_time,
                    end_hour=agent_a.preferred_end_time,
                )
                win_b = WindowInterval(
                    start_hour=agent_b.preferred_start_time,
                    end_hour=agent_b.preferred_end_time,
                )

                overlap = win_a.overlaps(win_b)
                if overlap is None:
                    continue

                # Score: fraction of the shorter window that overlaps × urgency boost
                min_window = min(win_a.duration_hours, win_b.duration_hours)
                overlap_fraction = overlap.duration_hours / max(1, min_window)
                urgency_boost = (agent_a.urgency + agent_b.urgency) / 2.0
                severity_score = max(0.0, min(1.0, overlap_fraction * (0.5 + 0.5 * urgency_boost)))
                severity = severity_from_ratio(severity_score)

                explanation = (
                    f"Farmer {agent_a.farmer_id} (window {win_a.start_hour:02d}:00–{win_a.end_hour:02d}:00) "
                    f"and Farmer {agent_b.farmer_id} (window {win_b.start_hour:02d}:00–{win_b.end_hour:02d}:00) "
                    f"have overlapping preferred irrigation windows: "
                    f"{overlap.start_hour:02d}:00–{overlap.end_hour:02d}:00 "
                    f"({overlap.duration_hours}h overlap). "
                    f"Combined urgency: {urgency_boost:.2f}."
                )

                demand_pair = agent_a.predicted_water_demand + agent_b.predicted_water_demand
                min_pair = agent_a.minimum_water_requirement + agent_b.minimum_water_requirement

                report = ConflictReport(
                    conflict_type=ConflictType.IRRIGATION_WINDOW_OVERLAP,
                    severity=severity,
                    severity_score=round(severity_score, 4),
                    involved_farmer_ids=[agent_a.farmer_id, agent_b.farmer_id],
                    total_demand_m3=demand_pair,
                    total_minimum_requirement_m3=min_pair,
                    available_water_m3=self._available_water_m3,
                    resource_gap_m3=max(0.0, demand_pair - self._available_water_m3),
                    explanation=explanation,
                    evidence={
                        "farmer_a": {
                            "farmer_id": agent_a.farmer_id,
                            "window": win_a.as_dict(),
                            "urgency": round(agent_a.urgency, 4),
                            "demand_m3": round(agent_a.predicted_water_demand, 2),
                        },
                        "farmer_b": {
                            "farmer_id": agent_b.farmer_id,
                            "window": win_b.as_dict(),
                            "urgency": round(agent_b.urgency, 4),
                            "demand_m3": round(agent_b.predicted_water_demand, 2),
                        },
                        "overlap": overlap.as_dict(),
                        "overlap_fraction": round(overlap_fraction, 4),
                        "avg_urgency": round(urgency_boost, 4),
                    },
                )
                reports.append(report)
                logger.debug(
                    "WINDOW_OVERLAP: %s ∩ %s = %dh, score=%.3f, severity=%s",
                    agent_a.farmer_id, agent_b.farmer_id,
                    overlap.duration_hours, severity_score, severity.value,
                )

        return reports

    # ─── 3. Canal Capacity Conflict ───────────────────────────────────────────

    def detect_canal_conflicts(self) -> List[ConflictReport]:
        """
        Detect CANAL_CAPACITY_CONFLICT.

        For each pair of farmers with overlapping preferred windows,
        check if their simultaneous flow demand exceeds the canal capacity.

        Flow demand per farmer (m³/hour):
            flow_rate = predicted_demand / irrigation_window_hours

        If farmer_a.flow + farmer_b.flow > canal_capacity → conflict.

        Severity score:
            overload_ratio = (combined_flow - capacity) / capacity
            → mapped to Severity via severity_from_ratio

        Returns
        -------
        list of ConflictReport (one per overloading pair)
        """
        reports: List[ConflictReport] = []
        n = len(self._agents)

        for i in range(n):
            for j in range(i + 1, n):
                agent_a = self._agents[i]
                agent_b = self._agents[j]

                win_a = WindowInterval(
                    start_hour=agent_a.preferred_start_time,
                    end_hour=agent_a.preferred_end_time,
                )
                win_b = WindowInterval(
                    start_hour=agent_b.preferred_start_time,
                    end_hour=agent_b.preferred_end_time,
                )

                # Only check pairs with overlapping windows
                overlap = win_a.overlaps(win_b)
                if overlap is None:
                    continue

                # Flow demand (m³/h) = demand / window_hours
                window_a_h = max(1, win_a.duration_hours)
                window_b_h = max(1, win_b.duration_hours)
                flow_a = agent_a.predicted_water_demand / window_a_h
                flow_b = agent_b.predicted_water_demand / window_b_h
                combined_flow = flow_a + flow_b

                if combined_flow <= self._canal_capacity_m3_per_hour:
                    continue  # Within capacity

                overload = combined_flow - self._canal_capacity_m3_per_hour
                overload_ratio = overload / self._canal_capacity_m3_per_hour
                overload_ratio = max(0.0, min(1.0, overload_ratio))
                severity = severity_from_ratio(overload_ratio)

                explanation = (
                    f"Farmers {agent_a.farmer_id} and {agent_b.farmer_id} "
                    f"irrigate simultaneously during {overlap.start_hour:02d}:00–{overlap.end_hour:02d}:00. "
                    f"Combined flow demand ({combined_flow:.1f} m³/h) exceeds canal capacity "
                    f"({self._canal_capacity_m3_per_hour:.1f} m³/h) "
                    f"by {overload:.1f} m³/h ({overload_ratio*100:.1f}% overload)."
                )

                demand_pair = agent_a.predicted_water_demand + agent_b.predicted_water_demand
                min_pair = agent_a.minimum_water_requirement + agent_b.minimum_water_requirement

                report = ConflictReport(
                    conflict_type=ConflictType.CANAL_CAPACITY_CONFLICT,
                    severity=severity,
                    severity_score=round(overload_ratio, 4),
                    involved_farmer_ids=[agent_a.farmer_id, agent_b.farmer_id],
                    total_demand_m3=demand_pair,
                    total_minimum_requirement_m3=min_pair,
                    available_water_m3=self._available_water_m3,
                    resource_gap_m3=max(0.0, demand_pair - self._available_water_m3),
                    explanation=explanation,
                    evidence={
                        "farmer_a": {
                            "farmer_id": agent_a.farmer_id,
                            "flow_rate_m3_per_h": round(flow_a, 2),
                            "window": win_a.as_dict(),
                        },
                        "farmer_b": {
                            "farmer_id": agent_b.farmer_id,
                            "flow_rate_m3_per_h": round(flow_b, 2),
                            "window": win_b.as_dict(),
                        },
                        "combined_flow_m3_per_h": round(combined_flow, 2),
                        "canal_capacity_m3_per_h": round(self._canal_capacity_m3_per_hour, 2),
                        "overload_m3_per_h": round(overload, 2),
                        "overload_ratio": round(overload_ratio, 4),
                        "overlap_window": overlap.as_dict(),
                    },
                )
                reports.append(report)
                logger.debug(
                    "CANAL_CONFLICT: %s+%s flow=%.1f > capacity=%.1f, overload_ratio=%.3f",
                    agent_a.farmer_id, agent_b.farmer_id,
                    combined_flow, self._canal_capacity_m3_per_hour, overload_ratio,
                )

        return reports

    # ─── 4. Minimum Requirement Conflict ──────────────────────────────────────

    def detect_minimum_requirement_conflicts(self) -> Optional[ConflictReport]:
        """
        Detect MINIMUM_REQUIREMENT_CONFLICT.

        This is distinct from RESOURCE_SHORTAGE:
        - RESOURCE_SHORTAGE: total_demand > available (predicted demand gap)
        - MINIMUM_REQUIREMENT_CONFLICT: total_minimum_requirement > available
          (cannot meet even survival thresholds)

        minimum_requirement_gap = total_min_req - available_water
        If gap > 0 → critical conflict: crops will die even with minimum allocation.

        Severity:
            min_req_ratio = minimum_requirement_gap / total_min_req
            → mapped via severity_from_ratio

        Returns None if all minimum requirements can be met.
        """
        if len(self._agents) == 0:
            return None

        gap = self._total_min_req_m3 - self._available_water_m3
        if gap <= 0:
            logger.debug(
                "detect_minimum_requirement_conflicts: OK (min_req=%.1f <= available=%.1f)",
                self._total_min_req_m3, self._available_water_m3,
            )
            return None

        min_req_ratio = gap / self._total_min_req_m3 if self._total_min_req_m3 > 0 else 0.0
        min_req_ratio = max(0.0, min(1.0, min_req_ratio))
        # Min-req conflicts are always at least HIGH (existential threat to crops)
        severity = Severity.HIGH if min_req_ratio < 0.50 else Severity.CRITICAL

        # Identify the most vulnerable farmers (highest urgency × sensitivity)
        ranked = sorted(
            self._agents,
            key=lambda a: a.urgency * a.crop_sensitivity,
            reverse=True,
        )
        most_vulnerable_ids = [a.farmer_id for a in ranked[:3]]

        explanation = (
            f"Available water ({self._available_water_m3:.1f} m³) is insufficient "
            f"to meet the combined minimum crop-survival requirements "
            f"({self._total_min_req_m3:.1f} m³) of all {len(self._agents)} farmers. "
            f"Shortfall: {gap:.1f} m³ ({min_req_ratio*100:.1f}% of minimum needs). "
            f"Most vulnerable farmers: {most_vulnerable_ids}. "
            f"NOTE: This is distinct from RESOURCE_SHORTAGE — even survival-level "
            f"water allocation is impossible without prioritisation."
        )

        report = ConflictReport(
            conflict_type=ConflictType.MINIMUM_REQUIREMENT_CONFLICT,
            severity=severity,
            severity_score=round(min_req_ratio, 4),
            involved_farmer_ids=[a.farmer_id for a in self._agents],
            total_demand_m3=self._total_demand_m3,
            total_minimum_requirement_m3=self._total_min_req_m3,
            available_water_m3=self._available_water_m3,
            resource_gap_m3=max(0.0, self._total_demand_m3 - self._available_water_m3),
            minimum_requirement_gap_m3=gap,
            explanation=explanation,
            evidence={
                "minimum_requirement_gap_m3": round(gap, 2),
                "min_req_ratio": round(min_req_ratio, 4),
                "total_minimum_requirement_m3": round(self._total_min_req_m3, 2),
                "available_water_m3": round(self._available_water_m3, 2),
                "most_vulnerable_farmer_ids": most_vulnerable_ids,
                "per_farmer_min_req": {
                    a.farmer_id: round(a.minimum_water_requirement, 2)
                    for a in self._agents
                },
            },
        )
        logger.info(
            "MINIMUM_REQ_CONFLICT: gap=%.1f m3, ratio=%.3f, severity=%s",
            gap, min_req_ratio, severity.value,
        )
        return report

    # ─── 5. High Crop Stress Conflict ─────────────────────────────────────────

    def detect_crop_stress_conflicts(self) -> List[ConflictReport]:
        """
        Detect HIGH_CROP_STRESS conflicts.

        Identifies farmers at high agronomic risk based on:
            urgency, crop_sensitivity, growth_stage (criticality)

        Crop-Stress Priority Score (CSPS):
            CSPS = urgency × crop_sensitivity × stage_criticality

        This is a COMPUTATIONAL RISK INDICATOR, not a direct physiological
        measurement. It is derived from the synthetic simulation parameters
        and does NOT claim to represent real crop physiological stress.

        Farmers with CSPS > HIGH_STRESS_THRESHOLD generate a conflict report.

        Threshold: CSPS > 0.49 (urgency × sensitivity × criticality > 0.49)
        This represents agents where ALL three factors are simultaneously
        elevated — e.g., a flowering-stage sensitive crop with high urgency.

        Severity:
            CSPS 0.49–0.65 → MEDIUM
            CSPS 0.65–0.80 → HIGH
            CSPS > 0.80    → CRITICAL

        Returns
        -------
        list of ConflictReport (one per high-stress farmer)
        """
        reports: List[ConflictReport] = []

        for agent in self._agents:
            stage_criticality = agent.stage_criticality
            csps = agent.urgency * agent.crop_sensitivity * stage_criticality
            csps = max(0.0, min(1.0, csps))

            # Only report agents above the threshold
            if csps <= 0.49:
                continue

            severity = severity_from_ratio(csps)
            # Bump minimum to MEDIUM for crop stress (sub-threshold not reported)
            if severity == Severity.LOW:
                severity = Severity.MEDIUM

            explanation = (
                f"Farmer {agent.farmer_id} (crop: {agent.crop}, "
                f"stage: {agent.growth_stage}) has a high Crop-Stress Priority Score "
                f"(CSPS = {csps:.3f}). "
                f"Components: urgency={agent.urgency:.2f}, "
                f"crop_sensitivity={agent.crop_sensitivity:.2f}, "
                f"stage_criticality={stage_criticality:.2f}. "
                f"NOTE: CSPS is a synthetic simulation indicator, "
                f"not a direct physiological measurement. "
                f"This farmer should receive priority consideration in allocation."
            )

            report = ConflictReport(
                conflict_type=ConflictType.HIGH_CROP_STRESS,
                severity=severity,
                severity_score=round(csps, 4),
                involved_farmer_ids=[agent.farmer_id],
                total_demand_m3=agent.predicted_water_demand,
                total_minimum_requirement_m3=agent.minimum_water_requirement,
                available_water_m3=self._available_water_m3,
                resource_gap_m3=max(0.0, agent.predicted_water_demand - self._available_water_m3),
                explanation=explanation,
                evidence={
                    "farmer_id": agent.farmer_id,
                    "crop": agent.crop,
                    "growth_stage": agent.growth_stage,
                    "urgency": round(agent.urgency, 4),
                    "crop_sensitivity": round(agent.crop_sensitivity, 4),
                    "stage_criticality": round(stage_criticality, 4),
                    "csps": round(csps, 4),
                    "predicted_demand_m3": round(agent.predicted_water_demand, 2),
                    "minimum_requirement_m3": round(agent.minimum_water_requirement, 2),
                    "disclaimer": (
                        "CSPS is a synthetic simulation indicator derived from "
                        "urgency, crop_sensitivity, and stage_criticality parameters. "
                        "It does not represent real physiological crop stress measurements."
                    ),
                },
            )
            reports.append(report)
            logger.debug(
                "HIGH_CROP_STRESS: farmer=%s csps=%.3f severity=%s",
                agent.farmer_id, csps, severity.value,
            )

        return reports

    # ─── Overall Conflict Score ───────────────────────────────────────────────

    def compute_overall_conflict_score(self) -> Dict[str, Any]:
        """
        Compute the overall conflict score for the scenario.

        Formula
        -------
        conflict_score =
            w_shortage  * shortage_ratio
          + w_urgency   * urgency_disparity_score
          + w_overlap   * window_overlap_fraction
          + w_stress    * high_stress_fraction

        where:
            shortage_ratio = max(0, (demand - available) / demand)
            urgency_disparity_score = normalised std-dev of urgency scores [0,1]
            window_overlap_fraction = fraction of pairs with overlapping windows
            high_stress_fraction = fraction of farmers with CSPS > 0.49

        The result is normalised to [0, 1] by dividing by w_shortage + w_urgency
        + w_overlap + w_stress (theoretical maximum when all components = 1.0).

        Returns
        -------
        dict with component scores and the overall conflict_score.
        """
        w = self._weights
        n = len(self._agents)

        if n == 0:
            return {
                "shortage_ratio": 0.0,
                "urgency_disparity_score": 0.0,
                "window_overlap_fraction": 0.0,
                "high_stress_fraction": 0.0,
                "conflict_score": 0.0,
                "components": {},
            }

        # Shortage ratio
        shortage_ratio = (
            max(0.0, self._total_demand_m3 - self._available_water_m3) / self._total_demand_m3
            if self._total_demand_m3 > 0 else 0.0
        )
        shortage_ratio = max(0.0, min(1.0, shortage_ratio))

        # Urgency disparity — normalised std-dev of urgency scores
        urgencies = [a.urgency for a in self._agents]
        if len(urgencies) > 1:
            mean_u = sum(urgencies) / len(urgencies)
            var_u = sum((u - mean_u) ** 2 for u in urgencies) / len(urgencies)
            std_u = math.sqrt(var_u)
            # Max possible std-dev for [0,1] values is 0.5
            urgency_disparity = min(1.0, std_u / 0.5)
        else:
            urgency_disparity = 0.0

        # Window overlap fraction — proportion of pairs that overlap
        total_pairs = n * (n - 1) // 2
        if total_pairs > 0:
            overlap_count = 0
            for i in range(n):
                for j in range(i + 1, n):
                    win_i = WindowInterval(
                        self._agents[i].preferred_start_time,
                        self._agents[i].preferred_end_time,
                    )
                    win_j = WindowInterval(
                        self._agents[j].preferred_start_time,
                        self._agents[j].preferred_end_time,
                    )
                    if win_i.overlaps(win_j) is not None:
                        overlap_count += 1
            window_overlap_fraction = overlap_count / total_pairs
        else:
            window_overlap_fraction = 0.0

        # High stress fraction
        stress_count = 0
        for agent in self._agents:
            csps = agent.urgency * agent.crop_sensitivity * agent.stage_criticality
            if csps > 0.49:
                stress_count += 1
        high_stress_fraction = stress_count / n

        # Weighted sum
        raw_score = (
            w.shortage * shortage_ratio
            + w.urgency * urgency_disparity
            + w.overlap * window_overlap_fraction
            + w.stress * high_stress_fraction
        )

        # Normalise by theoretical maximum (all components = 1)
        max_score = w.total if w.total > 0 else 1.0
        conflict_score = max(0.0, min(1.0, raw_score / max_score))

        return {
            "shortage_ratio": round(shortage_ratio, 4),
            "urgency_disparity_score": round(urgency_disparity, 4),
            "window_overlap_fraction": round(window_overlap_fraction, 4),
            "high_stress_fraction": round(high_stress_fraction, 4),
            "conflict_score": round(conflict_score, 4),
            "components": {
                "shortage_contribution": round(w.shortage * shortage_ratio / max_score, 4),
                "urgency_contribution": round(w.urgency * urgency_disparity / max_score, 4),
                "overlap_contribution": round(w.overlap * window_overlap_fraction / max_score, 4),
                "stress_contribution": round(w.stress * high_stress_fraction / max_score, 4),
            },
            "weights": {
                "shortage": w.shortage,
                "urgency": w.urgency,
                "overlap": w.overlap,
                "stress": w.stress,
            },
        }

    # ─── Properties ──────────────────────────────────────────────────────────

    @property
    def agents(self) -> List[FarmerAgent]:
        return list(self._agents)

    @property
    def available_water_m3(self) -> float:
        return self._available_water_m3

    @property
    def total_demand_m3(self) -> float:
        return self._total_demand_m3

    @property
    def total_minimum_requirement_m3(self) -> float:
        return self._total_min_req_m3

    @property
    def canal_capacity_m3_per_hour(self) -> float:
        return self._canal_capacity_m3_per_hour
