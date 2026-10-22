"""
AquaMediAI — Conflict Types
============================

Strongly-typed enumerations and models for the Phase 4 Conflict Detection Engine.

Conflict Types
--------------
1. RESOURCE_SHORTAGE          — Total demand > available water
2. IRRIGATION_WINDOW_OVERLAP  — Farmers competing for same time window
3. CANAL_CAPACITY_CONFLICT    — Simultaneous demand exceeds canal flow rate
4. MINIMUM_REQUIREMENT_CONFLICT — Available water < combined minimum requirements
5. HIGH_CROP_STRESS           — Farmers at high agronomic risk (urgency+stage+sensitivity)

Severity Levels
---------------
LOW      — Minor imbalance, likely resolvable without allocation change
MEDIUM   — Moderate conflict, may require reordering or partial reallocation
HIGH     — Significant shortage or overlap; allocation change required
CRITICAL — Severe shortage; minimum requirements cannot all be met

Severity Scoring Thresholds
----------------------------
shortage_ratio = resource_gap / total_demand

  < 0.10  →  LOW      (< 10% shortage)
  < 0.25  →  MEDIUM   (10–25% shortage)
  < 0.50  →  HIGH     (25–50% shortage)
  >= 0.50 →  CRITICAL (>50% shortage)

For non-shortage conflicts, severity is derived from a normalised
conflict_score (see ConflictDetector for formula).

DISCLAIMER: All conflict analysis in this system is computed from SYNTHETIC data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ConflictType(str, Enum):
    """
    Enumeration of conflict types detectable by the conflict engine.

    Values are lowercase strings for JSON-serialisation compatibility.
    """
    RESOURCE_SHORTAGE = "resource_shortage"
    IRRIGATION_WINDOW_OVERLAP = "irrigation_window_overlap"
    CANAL_CAPACITY_CONFLICT = "canal_capacity_conflict"
    MINIMUM_REQUIREMENT_CONFLICT = "minimum_requirement_conflict"
    HIGH_CROP_STRESS = "high_crop_stress"


class Severity(str, Enum):
    """
    Conflict severity levels — ordered from least to most severe.

    Comparison operators follow severity order (LOW < MEDIUM < HIGH < CRITICAL).
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def order(self) -> int:
        """Numeric ordering for severity comparison."""
        return {"low": 0, "medium": 1, "high": 2, "critical": 3}[self.value]

    def __lt__(self, other: "Severity") -> bool:
        return self.order < other.order

    def __le__(self, other: "Severity") -> bool:
        return self.order <= other.order

    def __gt__(self, other: "Severity") -> bool:
        return self.order > other.order

    def __ge__(self, other: "Severity") -> bool:
        return self.order >= other.order


def severity_from_ratio(ratio: float) -> Severity:
    """
    Map a normalised shortage/conflict ratio [0, 1] to a Severity level.

    Thresholds
    ----------
    ratio < 0.10  →  LOW      (minor imbalance)
    ratio < 0.25  →  MEDIUM   (moderate)
    ratio < 0.50  →  HIGH     (significant)
    ratio >= 0.50 →  CRITICAL (severe)

    Parameters
    ----------
    ratio : float in [0, 1]
        Normalised shortage or conflict intensity.

    Returns
    -------
    Severity
    """
    ratio = max(0.0, min(1.0, ratio))
    if ratio < 0.10:
        return Severity.LOW
    elif ratio < 0.25:
        return Severity.MEDIUM
    elif ratio < 0.50:
        return Severity.HIGH
    else:
        return Severity.CRITICAL


@dataclass
class WindowInterval:
    """
    Represents a time interval for irrigation window calculations.

    Hours are 24-hour clock integers (0–23).
    An interval [start, end] is inclusive on both ends.
    """
    start_hour: int
    end_hour: int

    def __post_init__(self) -> None:
        if not (0 <= self.start_hour <= 23):
            raise ValueError(f"start_hour must be in [0,23], got {self.start_hour}")
        if not (0 <= self.end_hour <= 23):
            raise ValueError(f"end_hour must be in [0,23], got {self.end_hour}")
        if self.start_hour >= self.end_hour:
            raise ValueError(
                f"start_hour ({self.start_hour}) must be < end_hour ({self.end_hour})"
            )

    @property
    def duration_hours(self) -> int:
        return self.end_hour - self.start_hour

    def overlaps(self, other: "WindowInterval") -> Optional["WindowInterval"]:
        """
        Return the overlapping interval with `other`, or None if no overlap.

        Two windows [a, b] and [c, d] overlap if max(a,c) < min(b,d).
        """
        overlap_start = max(self.start_hour, other.start_hour)
        overlap_end = min(self.end_hour, other.end_hour)
        if overlap_start < overlap_end:
            return WindowInterval(start_hour=overlap_start, end_hour=overlap_end)
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
            "duration_hours": self.duration_hours,
        }


@dataclass
class ConflictReport:
    """
    Structured report for a single detected conflict.

    All numerical values are derived from actual scenario data —
    never hard-coded.

    Attributes
    ----------
    conflict_id : str
        Unique identifier for this conflict report (UUID).
    conflict_type : ConflictType
        Type of conflict detected.
    severity : Severity
        Assessed severity level.
    severity_score : float
        Normalised conflict intensity [0, 1] used to determine severity.
    involved_farmer_ids : list of str
        IDs of farmers involved in this conflict.
    available_water_m3 : float
        Total water available for the scenario (m³). May be None for
        non-resource conflicts.
    total_demand_m3 : float
        Sum of predicted demands of involved farmers (m³).
    total_minimum_requirement_m3 : float
        Sum of minimum requirements of involved farmers (m³).
    resource_gap_m3 : float
        total_demand_m3 - available_water_m3. Positive = shortage.
    minimum_requirement_gap_m3 : float
        total_minimum_requirement_m3 - available_water_m3.
        Positive = cannot meet even minimum requirements.
    explanation : str
        Human-readable explanation of the conflict.
    evidence : dict
        Supporting numerical evidence for the conflict.
    scenario_id : str
        Reference to the scenario that generated this conflict.
    detected_at : str
        ISO-8601 timestamp of detection.
    """

    conflict_type: ConflictType
    severity: Severity
    severity_score: float
    involved_farmer_ids: List[str]
    total_demand_m3: float
    total_minimum_requirement_m3: float
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    available_water_m3: float = 0.0
    resource_gap_m3: float = 0.0
    minimum_requirement_gap_m3: float = 0.0
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str = "unknown"
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not (0.0 <= self.severity_score <= 1.0):
            raise ValueError(
                f"severity_score must be in [0, 1], got {self.severity_score}"
            )
        if not self.involved_farmer_ids:
            raise ValueError("involved_farmer_ids must not be empty")

    def as_dict(self) -> Dict[str, Any]:
        """Return serialisable dict representation."""
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "severity_score": round(self.severity_score, 4),
            "involved_farmer_ids": self.involved_farmer_ids,
            "available_water_m3": round(self.available_water_m3, 2),
            "total_demand_m3": round(self.total_demand_m3, 2),
            "total_minimum_requirement_m3": round(self.total_minimum_requirement_m3, 2),
            "resource_gap_m3": round(self.resource_gap_m3, 2),
            "minimum_requirement_gap_m3": round(self.minimum_requirement_gap_m3, 2),
            "explanation": self.explanation,
            "evidence": self.evidence,
            "scenario_id": self.scenario_id,
            "detected_at": self.detected_at,
        }

    def __repr__(self) -> str:
        return (
            f"ConflictReport({self.conflict_type.value}, "
            f"severity={self.severity.value}, "
            f"score={self.severity_score:.3f}, "
            f"farmers={self.involved_farmer_ids})"
        )


@dataclass
class ScenarioConflictReport:
    """
    Aggregate conflict analysis for an entire scenario.

    Summarises all conflicts detected across a pool of FarmerAgents.

    Attributes
    ----------
    scenario_id : str
        Scenario identifier.
    n_farmers : int
        Number of farmers in the scenario.
    total_demand_m3 : float
        Sum of all predicted demands.
    available_water_m3 : float
        Total water available.
    total_minimum_requirement_m3 : float
        Sum of all minimum requirements.
    total_conflicts : int
        Number of conflicts detected.
    highest_severity : Severity
        Most severe conflict in the scenario.
    overall_shortage_ratio : float
        (total_demand - available) / total_demand, clipped to [0,1].
    conflicts : list of ConflictReport
        All individual conflict reports.
    detected_at : str
        ISO-8601 timestamp.
    """

    scenario_id: str
    n_farmers: int
    total_demand_m3: float
    available_water_m3: float
    total_minimum_requirement_m3: float
    conflicts: List[ConflictReport] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_conflicts(self) -> int:
        return len(self.conflicts)

    @property
    def resource_gap_m3(self) -> float:
        return max(0.0, self.total_demand_m3 - self.available_water_m3)

    @property
    def minimum_requirement_gap_m3(self) -> float:
        return max(0.0, self.total_minimum_requirement_m3 - self.available_water_m3)

    @property
    def overall_shortage_ratio(self) -> float:
        if self.total_demand_m3 <= 0:
            return 0.0
        return max(0.0, min(1.0, self.resource_gap_m3 / self.total_demand_m3))

    @property
    def highest_severity(self) -> Optional[Severity]:
        if not self.conflicts:
            return None
        return max(c.severity for c in self.conflicts)

    @property
    def conflicts_by_type(self) -> Dict[str, List[ConflictReport]]:
        result: Dict[str, List[ConflictReport]] = {}
        for c in self.conflicts:
            result.setdefault(c.conflict_type.value, []).append(c)
        return result

    def as_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "n_farmers": self.n_farmers,
            "total_demand_m3": round(self.total_demand_m3, 2),
            "available_water_m3": round(self.available_water_m3, 2),
            "total_minimum_requirement_m3": round(self.total_minimum_requirement_m3, 2),
            "resource_gap_m3": round(self.resource_gap_m3, 2),
            "minimum_requirement_gap_m3": round(self.minimum_requirement_gap_m3, 2),
            "overall_shortage_ratio": round(self.overall_shortage_ratio, 4),
            "total_conflicts": self.total_conflicts,
            "highest_severity": self.highest_severity.value if self.highest_severity else None,
            "conflicts": [c.as_dict() for c in self.conflicts],
            "detected_at": self.detected_at,
        }
