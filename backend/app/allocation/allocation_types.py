"""
AquaMediAI — Allocation Types
===============================

Typed data models for Phase 5 LP-based water allocation results.

These are pure Python dataclasses — no database ORM, no FastAPI dependency.
They are serialisable to dict/JSON for use by Phase 7 (Explainability)
and Phase 8 (FastAPI).

Design Notes
------------
- AllocationResult is the single output type of the WaterAllocator.
- FarmerAllocation carries per-farmer allocation details and Phase 7 metadata.
- ConstraintVerificationResult carries a post-solve audit.
- SolverStatus mirrors the OR-Tools solver status codes.

DISCLAIMER: All allocations in this system are computed from SYNTHETIC data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SolverStatus(str, Enum):
    """
    Status codes for the OR-Tools GLOP solver.

    Values mirror ``pywraplp.Solver`` result status constants.
    """
    OPTIMAL = "optimal"            # Globally optimal solution found
    FEASIBLE = "feasible"          # Feasible but not proven optimal (shouldn't happen for LP)
    INFEASIBLE = "infeasible"      # Problem is infeasible (shouldn't occur with relaxed min)
    UNBOUNDED = "unbounded"        # Problem is unbounded (shouldn't occur)
    NOT_SOLVED = "not_solved"      # Solver not run yet
    ERROR = "error"                # Unexpected solver error
    RELAXED = "relaxed"            # Feasible via soft-constraint relaxation
    EMPTY = "empty"                # No farmers — trivially solved


@dataclass
class FarmerAllocation:
    """
    Per-farmer water allocation result.

    All water quantities are in cubic metres (m³).

    Attributes
    ----------
    farmer_id : str
        Farmer identifier (from FarmerAgent.farmer_id).
    allocated_water_m3 : float
        Water allocated to this farmer by the LP solver.
    predicted_demand_m3 : float
        ML-predicted water demand (from FarmerAgent.predicted_water_demand).
    minimum_requirement_m3 : float
        Minimum crop-survival water threshold.
    maximum_requirement_m3 : float
        Maximum useful water (diminishing returns above this).
    unmet_demand_m3 : float
        predicted_demand - allocated_water (>0 means unmet need).
    minimum_shortfall_m3 : float
        max(0, minimum_requirement - allocated_water).
        Positive only when minimum could not be met (severe shortage).
    satisfaction_ratio : float
        allocated / predicted_demand, clamped to [0, 1].
    urgency : float
        Agent urgency score [0, 1] (used in objective).
    crop_sensitivity : float
        Agent crop sensitivity [0, 1] (used in objective).
    growth_stage : str
        Agent growth stage (metadata for Phase 7).
    crop : str
        Crop type (metadata for Phase 7).
    constraint_status : str
        'satisfied' | 'minimum_relaxed' | 'at_maximum'.
    explanation_metadata : dict
        Structured data for Phase 7 explanation engine.
    """

    farmer_id: str
    allocated_water_m3: float
    predicted_demand_m3: float
    minimum_requirement_m3: float
    maximum_requirement_m3: float
    urgency: float
    crop_sensitivity: float
    growth_stage: str
    crop: str
    constraint_status: str = "satisfied"
    explanation_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.allocated_water_m3 < -1e-9:
            raise ValueError(
                f"allocated_water_m3 must be >= 0, got {self.allocated_water_m3:.6f}"
            )
        # Clamp tiny negatives from floating point
        self.allocated_water_m3 = max(0.0, self.allocated_water_m3)

    @property
    def unmet_demand_m3(self) -> float:
        return max(0.0, self.predicted_demand_m3 - self.allocated_water_m3)

    @property
    def minimum_shortfall_m3(self) -> float:
        return max(0.0, self.minimum_requirement_m3 - self.allocated_water_m3)

    @property
    def satisfaction_ratio(self) -> float:
        if self.predicted_demand_m3 <= 0:
            return 1.0
        return min(1.0, self.allocated_water_m3 / self.predicted_demand_m3)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "allocated_water_m3": round(self.allocated_water_m3, 2),
            "predicted_demand_m3": round(self.predicted_demand_m3, 2),
            "minimum_requirement_m3": round(self.minimum_requirement_m3, 2),
            "maximum_requirement_m3": round(self.maximum_requirement_m3, 2),
            "unmet_demand_m3": round(self.unmet_demand_m3, 2),
            "minimum_shortfall_m3": round(self.minimum_shortfall_m3, 2),
            "satisfaction_ratio": round(self.satisfaction_ratio, 4),
            "urgency": round(self.urgency, 4),
            "crop_sensitivity": round(self.crop_sensitivity, 4),
            "growth_stage": self.growth_stage,
            "crop": self.crop,
            "constraint_status": self.constraint_status,
            "explanation_metadata": self.explanation_metadata,
        }

    def __repr__(self) -> str:
        return (
            f"FarmerAllocation(id={self.farmer_id!r}, "
            f"alloc={self.allocated_water_m3:.1f}m3, "
            f"demand={self.predicted_demand_m3:.1f}m3, "
            f"sat={self.satisfaction_ratio:.3f})"
        )


@dataclass
class ConstraintVerificationResult:
    """
    Post-solve constraint verification report.

    Produced by verifying every hard constraint independently
    after the LP solver finishes. The system never trusts the
    solver blindly.

    Attributes
    ----------
    is_valid : bool
        True if ALL hard constraints are satisfied.
    total_water_ok : bool
        total_allocated <= available_water + tolerance.
    non_negative_ok : bool
        All allocations >= 0.
    maximum_ok : bool
        All allocations <= farmer.maximum_water_requirement.
    no_nan_ok : bool
        No NaN or Inf values in any allocation.
    all_farmers_present : bool
        All input farmer IDs appear in the result.
    violations : list of str
        Human-readable descriptions of each violation found.
    tolerance_m3 : float
        Numerical tolerance used for water balance check (default 1e-6).
    """

    is_valid: bool
    total_water_ok: bool
    non_negative_ok: bool
    maximum_ok: bool
    no_nan_ok: bool
    all_farmers_present: bool
    violations: List[str] = field(default_factory=list)
    tolerance_m3: float = 1e-6

    def as_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_water_ok": self.total_water_ok,
            "non_negative_ok": self.non_negative_ok,
            "maximum_ok": self.maximum_ok,
            "no_nan_ok": self.no_nan_ok,
            "all_farmers_present": self.all_farmers_present,
            "violations": self.violations,
            "tolerance_m3": self.tolerance_m3,
        }


@dataclass
class AllocationResult:
    """
    Complete result of a single LP water allocation run.

    Attributes
    ----------
    solver_status : SolverStatus
        Outcome of the LP solve.
    objective_value : float
        Value of the objective function at the optimal solution.
    available_water_m3 : float
        Total water available for the scenario.
    total_demand_m3 : float
        Sum of all predicted demands.
    total_minimum_requirement_m3 : float
        Sum of all minimum requirements.
    total_allocated_m3 : float
        Sum of all farmer allocations (from solver).
    remaining_water_m3 : float
        available_water - total_allocated (water not used).
    utilization : float
        total_allocated / available_water (in [0, 1]).
    fairness_score : float
        Jain's Fairness Index on satisfaction ratios (in [0, 1]).
    minimum_requirements_feasible : bool
        True if Σ min_req <= available_water.
    allocations : list of FarmerAllocation
        Per-farmer allocation objects.
    verification : ConstraintVerificationResult
        Independent post-solve constraint audit.
    scenario_id : str
        Reference to the originating scenario.
    solver_wall_time_ms : float
        Wall time for the LP solve in milliseconds.
    allocation_method : str
        'lp_optimal' | 'lp_relaxed' | 'proportional_fallback' | 'empty'.
    solved_at : str
        ISO-8601 UTC timestamp.
    """

    solver_status: SolverStatus
    objective_value: float
    available_water_m3: float
    total_demand_m3: float
    total_minimum_requirement_m3: float
    total_allocated_m3: float
    remaining_water_m3: float
    utilization: float
    fairness_score: float
    minimum_requirements_feasible: bool
    allocations: List[FarmerAllocation]
    verification: ConstraintVerificationResult
    scenario_id: str = "unknown"
    solver_wall_time_ms: float = 0.0
    allocation_method: str = "lp_optimal"
    solved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        # Clamp utilization and fairness to [0,1] after floating-point arithmetic
        self.utilization = max(0.0, min(1.0, self.utilization))
        self.fairness_score = max(0.0, min(1.0, self.fairness_score))

    @property
    def n_farmers(self) -> int:
        return len(self.allocations)

    @property
    def total_unmet_demand_m3(self) -> float:
        return sum(a.unmet_demand_m3 for a in self.allocations)

    @property
    def total_minimum_shortfall_m3(self) -> float:
        return sum(a.minimum_shortfall_m3 for a in self.allocations)

    @property
    def average_satisfaction(self) -> float:
        if not self.allocations:
            return 0.0
        return sum(a.satisfaction_ratio for a in self.allocations) / len(self.allocations)

    @property
    def is_valid(self) -> bool:
        return self.verification.is_valid

    def get_allocation(self, farmer_id: str) -> Optional[FarmerAllocation]:
        """Return the FarmerAllocation for a specific farmer_id."""
        for a in self.allocations:
            if a.farmer_id == farmer_id:
                return a
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "solver_status": self.solver_status.value,
            "objective_value": round(self.objective_value, 6),
            "allocation_method": self.allocation_method,
            "available_water_m3": round(self.available_water_m3, 2),
            "total_demand_m3": round(self.total_demand_m3, 2),
            "total_minimum_requirement_m3": round(self.total_minimum_requirement_m3, 2),
            "total_allocated_m3": round(self.total_allocated_m3, 2),
            "remaining_water_m3": round(self.remaining_water_m3, 2),
            "utilization": round(self.utilization, 4),
            "fairness_score": round(self.fairness_score, 4),
            "average_satisfaction": round(self.average_satisfaction, 4),
            "total_unmet_demand_m3": round(self.total_unmet_demand_m3, 2),
            "total_minimum_shortfall_m3": round(self.total_minimum_shortfall_m3, 2),
            "minimum_requirements_feasible": self.minimum_requirements_feasible,
            "n_farmers": self.n_farmers,
            "solver_wall_time_ms": round(self.solver_wall_time_ms, 3),
            "verification": self.verification.as_dict(),
            "allocations": [a.as_dict() for a in self.allocations],
            "solved_at": self.solved_at,
        }

    def __repr__(self) -> str:
        return (
            f"AllocationResult(status={self.solver_status.value}, "
            f"n={self.n_farmers}, "
            f"alloc={self.total_allocated_m3:.1f}/{self.available_water_m3:.1f}m3, "
            f"util={self.utilization:.3f}, fair={self.fairness_score:.3f})"
        )
