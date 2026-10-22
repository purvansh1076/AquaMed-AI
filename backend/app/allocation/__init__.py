"""
AquaMediAI — Allocation Package
==================================

Phase 5: Constraint-Based Water Allocation (OR-Tools GLOP LP)

Exports
-------
WaterAllocator          — main LP allocation engine
ObjectiveWeights        — configurable objective function weights
AllocationResult        — complete allocation output
FarmerAllocation        — per-farmer allocation details
ConstraintVerificationResult — post-solve audit
SolverStatus            — solver status enum
AllocationConstraints   — constraint bounds model
build_constraints       — build constraints from agents
compute_jains_fairness_index — Jain's Fairness Index
verify_constraints      — independent post-solve verifier

Pipeline
--------
FarmerAgent[] + available_water_m3
        ↓
WaterAllocator(agents, available_water_m3)
        ↓
AllocationResult
  ├── per-farmer FarmerAllocation
  ├── ConstraintVerificationResult
  ├── fairness_score (Jain's Index)
  └── utilization / remaining_water

DISCLAIMER: All allocations are computed from SYNTHETIC data.
"""

from app.allocation.allocation_types import (
    AllocationResult,
    ConstraintVerificationResult,
    FarmerAllocation,
    SolverStatus,
)
from app.allocation.constraints import (
    AllocationConstraints,
    build_constraints,
    compute_jains_fairness_index,
)
from app.allocation.lp_allocator import (
    ObjectiveWeights,
    WaterAllocator,
    verify_constraints,
)

__all__ = [
    # allocation_types
    "AllocationResult",
    "FarmerAllocation",
    "ConstraintVerificationResult",
    "SolverStatus",
    # constraints
    "AllocationConstraints",
    "build_constraints",
    "compute_jains_fairness_index",
    # lp_allocator
    "WaterAllocator",
    "ObjectiveWeights",
    "verify_constraints",
]
