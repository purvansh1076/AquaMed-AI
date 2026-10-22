"""
AquaMediAI — Farmer Digital Agent
===================================

A deterministic, computational Farmer Digital Agent (FDA).

Design Philosophy
-----------------
Each farmer is represented as a validated, typed computational model that
exposes a structured state suitable for negotiation, conflict detection,
and LP-based water allocation.  This is NOT an LLM chatbot — it is a
fully deterministic agent whose behaviour is governed by mathematical
models grounded in agronomic literature.

Architecture
------------
FarmerAgent
  ├── Identity & farm characteristics
  ├── ML-predicted water demand (from WaterDemandPredictor)
  ├── FarmerPreferences (timing, water bounds)
  ├── UtilityWeights (configurable, not hard-coded)
  └── BATNA (calculated from minimum requirement)

References
----------
- FAO-56 (Allen et al. 1998): minimum crop water requirements.
- Doorenbos & Pruitt (1977): soil depletion thresholds.

DISCLAIMER: All data used to build agents in this project is SYNTHETIC.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─── Valid categorical constants ──────────────────────────────────────────────
VALID_CROPS = frozenset([
    "wheat", "rice", "cotton", "sugarcane", "maize",
    "soybean", "groundnut", "sunflower",
])
VALID_SOILS = frozenset(["clay", "loam", "sandy", "silt", "clay_loam"])
VALID_GROWTH_STAGES = frozenset([
    "germination", "vegetative", "flowering", "maturity", "harvest"
])

# Growth stage criticality — from data_generator.STAGE_CRITICALITY
STAGE_CRITICALITY: Dict[str, float] = {
    "germination": 0.90,
    "vegetative":  0.60,
    "flowering":   1.00,
    "maturity":    0.50,
    "harvest":     0.20,
}

# Crop sensitivity — derived from FAO-56 yield-response factors (Ky)
# Higher Ky = more sensitive to water stress
CROP_SENSITIVITY_TABLE: Dict[str, float] = {
    "wheat":     0.80,
    "rice":      1.00,
    "cotton":    0.85,
    "sugarcane": 1.20,  # Ky > 1 means disproportionate sensitivity (clipped at 1.0)
    "maize":     1.25,
    "soybean":   0.85,
    "groundnut": 0.70,
    "sunflower": 0.95,
}


# ─── Preference model ─────────────────────────────────────────────────────────

@dataclass
class FarmerPreferences:
    """
    Structured irrigation preference representation.

    All time values are 24-hour clock hours (integers 0–23).
    Water values are in cubic metres (m³).

    Parameters
    ----------
    preferred_start_hour : int
        Preferred irrigation start time (e.g., 8 for 08:00).
    preferred_end_hour : int
        Preferred irrigation end time (e.g., 10 for 10:00).
    acceptable_start_hour : int
        Earliest acceptable start (may be before preferred window).
    acceptable_end_hour : int
        Latest acceptable end (may be after preferred window).
    minimum_water_m3 : float
        Absolute minimum water requirement (m³). Below this, crop dies.
    target_water_m3 : float
        Target (predicted demand) water amount (m³).
    maximum_water_m3 : float
        Maximum useful water — beyond this, excess runoff occurs.
    flexibility : float
        [0, 1] — 1.0 = fully flexible about timing, 0.0 = strictly preferred window.
    """

    preferred_start_hour: int
    preferred_end_hour: int
    acceptable_start_hour: int
    acceptable_end_hour: int
    minimum_water_m3: float
    target_water_m3: float
    maximum_water_m3: float
    flexibility: float

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        errors: List[str] = []

        # Hour bounds
        for attr in ("preferred_start_hour", "preferred_end_hour",
                     "acceptable_start_hour", "acceptable_end_hour"):
            v = getattr(self, attr)
            if not isinstance(v, int) or not (0 <= v <= 23):
                errors.append(f"{attr} must be integer in [0, 23], got {v!r}")

        # Preferred window ordering
        if self.preferred_start_hour >= self.preferred_end_hour:
            errors.append(
                f"preferred_start_hour ({self.preferred_start_hour}) "
                f"must be < preferred_end_hour ({self.preferred_end_hour})"
            )

        # Acceptable window must contain or equal preferred window
        if self.acceptable_start_hour > self.preferred_start_hour:
            errors.append(
                f"acceptable_start_hour ({self.acceptable_start_hour}) "
                f"must be <= preferred_start_hour ({self.preferred_start_hour})"
            )
        if self.acceptable_end_hour < self.preferred_end_hour:
            errors.append(
                f"acceptable_end_hour ({self.acceptable_end_hour}) "
                f"must be >= preferred_end_hour ({self.preferred_end_hour})"
            )

        # Water constraints: minimum <= target <= maximum
        if not (0 < self.minimum_water_m3 <= self.target_water_m3 <= self.maximum_water_m3):
            errors.append(
                f"Water constraints violated: minimum ({self.minimum_water_m3:.2f}) "
                f"<= target ({self.target_water_m3:.2f}) "
                f"<= maximum ({self.maximum_water_m3:.2f}) required."
            )

        # Flexibility bounds
        if not (0.0 <= self.flexibility <= 1.0):
            errors.append(f"flexibility must be in [0, 1], got {self.flexibility}")

        if errors:
            raise ValueError("FarmerPreferences validation failed:\n  " + "\n  ".join(errors))

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Utility weights ──────────────────────────────────────────────────────────

@dataclass
class UtilityWeights:
    """
    Configurable weights for the farmer utility function.

    Weights do not need to sum to 1 — they are relative importances.
    The utility function normalises the final output to [0, 1].

    Attributes
    ----------
    water_satisfaction : float
        Weight on received water relative to predicted demand.
    timing_satisfaction : float
        Weight on whether irrigation falls in preferred window.
    urgency_protection : float
        Weight on protecting high-urgency farmers from unmet demand.
    crop_protection : float
        Weight on meeting the minimum crop-survival water requirement.
    stress_penalty : float
        Weight on penalty for unmet minimum requirement (crop stress).
    """

    water_satisfaction: float = 0.35
    timing_satisfaction: float = 0.20
    urgency_protection: float = 0.20
    crop_protection: float = 0.15
    stress_penalty: float = 0.10

    def __post_init__(self) -> None:
        for attr_name in (
            "water_satisfaction", "timing_satisfaction",
            "urgency_protection", "crop_protection", "stress_penalty"
        ):
            v = getattr(self, attr_name)
            if v < 0.0:
                raise ValueError(f"UtilityWeights.{attr_name} must be >= 0, got {v}")

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── BATNA ────────────────────────────────────────────────────────────────────

@dataclass
class BATNA:
    """
    Best Alternative To a Negotiated Agreement.

    Methodology: Proportional Minimum Fallback
    ------------------------------------------
    If negotiation fails, the farmer's fallback outcome is:
      - Allocation = minimum_requirement_m3 (FAO-56 crop survival threshold)
      - Timing = no preference respected (worst-case timing)
      - Utility computed at these fallback values

    This is defensible because:
    1. The minimum requirement is grounded in FAO-56 depletion thresholds.
    2. It represents the minimum a farmer can guarantee through a basic
       "priority safety-net" outside the negotiation system.
    3. It is always worse than a successful negotiated outcome, preserving
       the incentive to negotiate.

    Attributes
    ----------
    fallback_allocation_m3 : float
        Water the farmer receives if negotiation fails (= minimum_requirement).
    fallback_utility : float
        Utility at the fallback allocation with no timing preference (in [0,1]).
    description : str
        Human-readable description of the BATNA calculation.
    """

    fallback_allocation_m3: float
    fallback_utility: float
    description: str = "Proportional minimum fallback (FAO-56 survival threshold)"

    def __post_init__(self) -> None:
        if self.fallback_allocation_m3 < 0:
            raise ValueError("BATNA.fallback_allocation_m3 must be >= 0")
        if not (0.0 <= self.fallback_utility <= 1.0):
            raise ValueError(f"BATNA.fallback_utility must be in [0,1], got {self.fallback_utility}")

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── FarmerAgent ─────────────────────────────────────────────────────────────

class FarmerAgent:
    """
    Deterministic Farmer Digital Agent.

    Represents a farmer as a computational entity capable of participating
    in the water mediation negotiation system.

    This is NOT an LLM chatbot.  All behaviour is deterministic and
    mathematically defined.

    Parameters
    ----------
    farmer_id : str
        Unique identifier for the farmer.
    name : str
        Human-readable name.
    crop : str
        Crop type (must be in VALID_CROPS).
    farm_area : float
        Farm area in hectares (> 0).
    soil_type : str
        Soil type (must be in VALID_SOILS).
    growth_stage : str
        Current crop growth stage (must be in VALID_GROWTH_STAGES).
    predicted_water_demand : float
        ML-predicted daily water demand (m³). Must be > 0.
    minimum_water_requirement : float
        Minimum water for crop survival (m³). Must satisfy:
        0 < minimum <= predicted_demand <= maximum.
    maximum_water_requirement : float
        Maximum useful water (m³). Beyond this, excess runoff occurs.
    preferred_start_time : int
        Preferred irrigation start hour (0–23).
    preferred_end_time : int
        Preferred irrigation end hour (0–23), must be > preferred_start_time.
    urgency : float
        Urgency score [0, 1]. 1.0 = crop will die without immediate water.
    crop_sensitivity : float
        Crop water stress sensitivity [0, 1]. From FAO-56 yield-response Ky.
    flexibility : float
        Timing flexibility [0, 1]. 1.0 = any time is acceptable.
    utility_weights : UtilityWeights, optional
        Configurable utility function weights.
    batna : BATNA, optional
        Pre-computed BATNA. If None, auto-calculated from minimum requirement.
    """

    def __init__(
        self,
        farmer_id: str,
        name: str,
        crop: str,
        farm_area: float,
        soil_type: str,
        growth_stage: str,
        predicted_water_demand: float,
        minimum_water_requirement: float,
        maximum_water_requirement: float,
        preferred_start_time: int,
        preferred_end_time: int,
        urgency: float,
        crop_sensitivity: float,
        flexibility: float,
        utility_weights: Optional[UtilityWeights] = None,
        batna: Optional[BATNA] = None,
    ) -> None:
        # Store raw values before validation so errors are informative
        self._farmer_id = farmer_id
        self._name = name
        self._crop = crop
        self._farm_area = farm_area
        self._soil_type = soil_type
        self._growth_stage = growth_stage
        self._predicted_water_demand = predicted_water_demand
        self._minimum_water_requirement = minimum_water_requirement
        self._maximum_water_requirement = maximum_water_requirement
        self._preferred_start_time = preferred_start_time
        self._preferred_end_time = preferred_end_time
        self._urgency = urgency
        self._crop_sensitivity = crop_sensitivity
        self._flexibility = flexibility
        self._utility_weights = utility_weights or UtilityWeights()

        self._validate()

        # Build preferences (acceptable window = preferred ± flexibility buffer)
        buf_hours = max(1, int(flexibility * 6))  # up to 6h buffer at max flexibility
        self._preferences = FarmerPreferences(
            preferred_start_hour=preferred_start_time,
            preferred_end_hour=preferred_end_time,
            acceptable_start_hour=max(0, preferred_start_time - buf_hours),
            acceptable_end_hour=min(23, preferred_end_time + buf_hours),
            minimum_water_m3=minimum_water_requirement,
            target_water_m3=predicted_water_demand,
            maximum_water_m3=maximum_water_requirement,
            flexibility=flexibility,
        )

        # Auto-compute BATNA if not provided
        if batna is None:
            self._batna = self._compute_batna()
        else:
            self._batna = batna

        logger.debug(
            "FarmerAgent created: id=%s crop=%s stage=%s demand=%.1fm3 urgency=%.2f",
            farmer_id, crop, growth_stage, predicted_water_demand, urgency,
        )

    # ─── Validation ───────────────────────────────────────────────────────────

    def _validate(self) -> None:
        errors: List[str] = []

        if not self._farmer_id or not isinstance(self._farmer_id, str):
            errors.append("farmer_id must be a non-empty string")

        if not self._name or not isinstance(self._name, str):
            errors.append("name must be a non-empty string")

        if self._crop not in VALID_CROPS:
            errors.append(f"crop {self._crop!r} not in {sorted(VALID_CROPS)}")

        if not isinstance(self._farm_area, (int, float)) or self._farm_area <= 0:
            errors.append(f"farm_area must be > 0, got {self._farm_area}")

        if self._soil_type not in VALID_SOILS:
            errors.append(f"soil_type {self._soil_type!r} not in {sorted(VALID_SOILS)}")

        if self._growth_stage not in VALID_GROWTH_STAGES:
            errors.append(
                f"growth_stage {self._growth_stage!r} not in {sorted(VALID_GROWTH_STAGES)}"
            )

        if not isinstance(self._predicted_water_demand, (int, float)) or self._predicted_water_demand <= 0:
            errors.append(f"predicted_water_demand must be > 0, got {self._predicted_water_demand}")

        if not (0 < self._minimum_water_requirement
                <= self._predicted_water_demand
                <= self._maximum_water_requirement):
            errors.append(
                f"Water constraint violated: minimum ({self._minimum_water_requirement:.2f}) "
                f"<= predicted ({self._predicted_water_demand:.2f}) "
                f"<= maximum ({self._maximum_water_requirement:.2f}) required."
            )

        for time_attr, val in [
            ("preferred_start_time", self._preferred_start_time),
            ("preferred_end_time", self._preferred_end_time),
        ]:
            if not isinstance(val, int) or not (0 <= val <= 23):
                errors.append(f"{time_attr} must be int in [0,23], got {val!r}")

        if self._preferred_start_time >= self._preferred_end_time:
            errors.append(
                f"preferred_start_time ({self._preferred_start_time}) must be "
                f"< preferred_end_time ({self._preferred_end_time})"
            )

        for score_name, score_val in [
            ("urgency", self._urgency),
            ("crop_sensitivity", self._crop_sensitivity),
            ("flexibility", self._flexibility),
        ]:
            if not isinstance(score_val, (int, float)) or not (0.0 <= score_val <= 1.0):
                errors.append(f"{score_name} must be float in [0,1], got {score_val!r}")

        if errors:
            raise ValueError(
                f"FarmerAgent validation failed for farmer_id={self._farmer_id!r}:\n  "
                + "\n  ".join(errors)
            )

    # ─── BATNA computation ────────────────────────────────────────────────────

    def _compute_batna(self) -> BATNA:
        """
        Compute BATNA as the proportional minimum fallback.

        Methodology
        -----------
        fallback_allocation = minimum_requirement_m3
            (FAO-56 crop survival threshold — ~40% of predicted demand)

        fallback_utility = U_i evaluated at:
            - allocation = fallback_allocation
            - timing = no preference (timing_satisfaction = 0)
            - urgency = self.urgency (unchanged — urgency is an intrinsic property)

        The utility at BATNA is always <= utility at any successful negotiated
        outcome where allocation > minimum, preserving the incentive to negotiate.
        """
        from app.agents.utility import compute_utility

        fallback_utility = compute_utility(
            allocation_m3=self._minimum_water_requirement,
            predicted_demand_m3=self._predicted_water_demand,
            minimum_requirement_m3=self._minimum_water_requirement,
            irrigation_start_hour=None,  # No timing — worst case
            preferred_start_hour=self._preferred_start_time,
            preferred_end_hour=self._preferred_end_time,
            acceptable_start_hour=max(0, self._preferred_start_time - 1),
            acceptable_end_hour=min(23, self._preferred_end_time + 1),
            urgency=self._urgency,
            crop_sensitivity=self._crop_sensitivity,
            flexibility=self._flexibility,
            weights=self._utility_weights,
        )

        return BATNA(
            fallback_allocation_m3=self._minimum_water_requirement,
            fallback_utility=fallback_utility,
            description=(
                f"Proportional minimum fallback: {self._minimum_water_requirement:.2f} m3 "
                f"({self._minimum_water_requirement / self._predicted_water_demand * 100:.1f}% "
                f"of predicted demand). FAO-56 crop survival threshold. "
                f"Utility at BATNA: {fallback_utility:.4f}."
            ),
        )

    # ─── Read-only properties ─────────────────────────────────────────────────

    @property
    def farmer_id(self) -> str:
        return self._farmer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def crop(self) -> str:
        return self._crop

    @property
    def farm_area(self) -> float:
        return self._farm_area

    @property
    def soil_type(self) -> str:
        return self._soil_type

    @property
    def growth_stage(self) -> str:
        return self._growth_stage

    @property
    def predicted_water_demand(self) -> float:
        return self._predicted_water_demand

    @property
    def minimum_water_requirement(self) -> float:
        return self._minimum_water_requirement

    @property
    def maximum_water_requirement(self) -> float:
        return self._maximum_water_requirement

    @property
    def preferred_start_time(self) -> int:
        return self._preferred_start_time

    @property
    def preferred_end_time(self) -> int:
        return self._preferred_end_time

    @property
    def urgency(self) -> float:
        return self._urgency

    @property
    def crop_sensitivity(self) -> float:
        return self._crop_sensitivity

    @property
    def flexibility(self) -> float:
        return self._flexibility

    @property
    def utility_weights(self) -> UtilityWeights:
        return self._utility_weights

    @property
    def batna(self) -> BATNA:
        return self._batna

    @property
    def preferences(self) -> FarmerPreferences:
        return self._preferences

    # ─── Derived agronomic properties ────────────────────────────────────────

    @property
    def stage_criticality(self) -> float:
        """Return the growth stage criticality [0,1] from FAO-56 data."""
        return STAGE_CRITICALITY.get(self._growth_stage, 0.5)

    @property
    def crop_sensitivity_from_table(self) -> float:
        """Return the tabulated crop sensitivity (Ky-based), clamped to [0,1]."""
        return min(1.0, CROP_SENSITIVITY_TABLE.get(self._crop, 0.8))

    # ─── State export ─────────────────────────────────────────────────────────

    def get_negotiation_state(self) -> Dict[str, Any]:
        """
        Return a structured state dict suitable for negotiation engine consumption.

        Values are computed by the system — not hard-coded.
        """
        return {
            "farmer_id": self._farmer_id,
            "name": self._name,
            "crop": self._crop,
            "growth_stage": self._growth_stage,
            "farm_area_ha": round(self._farm_area, 3),
            "predicted_demand_m3": round(self._predicted_water_demand, 2),
            "minimum_requirement_m3": round(self._minimum_water_requirement, 2),
            "maximum_water_m3": round(self._maximum_water_requirement, 2),
            "preferred_start_hour": self._preferred_start_time,
            "preferred_end_hour": self._preferred_end_time,
            "urgency": round(self._urgency, 4),
            "crop_sensitivity": round(self._crop_sensitivity, 4),
            "flexibility": round(self._flexibility, 4),
            "stage_criticality": round(self.stage_criticality, 4),
            "batna_allocation_m3": round(self._batna.fallback_allocation_m3, 2),
            "batna_utility": round(self._batna.fallback_utility, 4),
            "utility_weights": self._utility_weights.as_dict(),
        }

    def as_dict(self) -> Dict[str, Any]:
        """Full serialisable representation of the agent."""
        d = self.get_negotiation_state()
        d["preferences"] = self._preferences.as_dict()
        d["batna"] = self._batna.as_dict()
        return d

    def __repr__(self) -> str:
        return (
            f"FarmerAgent(id={self._farmer_id!r}, crop={self._crop!r}, "
            f"stage={self._growth_stage!r}, demand={self._predicted_water_demand:.1f}m3, "
            f"urgency={self._urgency:.2f}, flex={self._flexibility:.2f})"
        )
