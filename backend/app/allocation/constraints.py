"""
AquaMediAI — Allocation Constraints
======================================

Documents and implements the constraint system for Phase 5 LP allocation.

Constraint Classification
--------------------------

HARD CONSTRAINTS (never relaxed, always enforced by the LP model):
  H1. x_i >= 0                             (non-negative allocation)
  H2. x_i <= maximum_water_requirement_i   (physical saturation limit)
  H3. Σ x_i <= available_water             (total supply cannot be exceeded)

SOFT CONSTRAINTS (relaxed via penalty when scenario is infeasible):
  S1. x_i >= minimum_water_requirement_i   (crop survival minimum)

S1 is soft because:
  When Σ minimum_requirement_i > available_water, it is mathematically
  impossible to satisfy all minimum requirements simultaneously while
  also respecting H3.  Imposing S1 as a hard constraint would make the
  LP infeasible with NO solution at all, which is worse than a solution
  with unmet minimums.

  Therefore, when the scenario is infeasible (Σ min_req > available),
  S1 is converted to a penalty term in the objective function rather
  than a hard constraint.  The LP still produces a valid, physically
  feasible solution, but with documented minimum shortfalls.

Infeasibility Detection
-----------------------
  A scenario is minimum-infeasible when:
      Σ minimum_water_requirement_i > available_water

  This is checked BEFORE calling the solver.
  The check result determines whether S1 is imposed as a hard constraint
  or relaxed to a soft penalty.

References
----------
  - Dantzig & Thapa (1997): Linear Programming
  - FAO-56 (Allen et al. 1998): crop water requirements (minimum thresholds)
  - Jain et al. (1984): Jain's Fairness Index

DISCLAIMER: Constraint parameters are derived from SYNTHETIC data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.agents.farmer_agent import FarmerAgent


@dataclass
class AllocationConstraints:
    """
    Computed constraint bounds for a single allocation scenario.

    All values are in cubic metres (m³).

    Attributes
    ----------
    available_water_m3 : float
        Total available water (H3 upper bound).
    n_farmers : int
        Number of farmers.
    total_demand_m3 : float
        Sum of predicted demands.
    total_minimum_requirement_m3 : float
        Sum of minimum requirements.
    total_maximum_requirement_m3 : float
        Sum of maximum requirements.
    is_minimum_feasible : bool
        True if Σ min_req <= available_water.
    per_farmer_lower_bounds : list of float
        Hard lower bounds (always 0 since min is soft when infeasible).
    per_farmer_soft_lower_bounds : list of float
        Soft lower bounds (minimum_requirement per farmer).
    per_farmer_upper_bounds : list of float
        Hard upper bounds (maximum_requirement per farmer).
    """

    available_water_m3: float
    n_farmers: int
    total_demand_m3: float
    total_minimum_requirement_m3: float
    total_maximum_requirement_m3: float
    is_minimum_feasible: bool
    per_farmer_lower_bounds: List[float]
    per_farmer_soft_lower_bounds: List[float]
    per_farmer_upper_bounds: List[float]

    @property
    def supply_gap_m3(self) -> float:
        """Shortage vs total demand (positive = shortage)."""
        return max(0.0, self.total_demand_m3 - self.available_water_m3)

    @property
    def minimum_infeasibility_gap_m3(self) -> float:
        """Shortfall vs minimum requirements (positive = cannot meet all minimums)."""
        return max(0.0, self.total_minimum_requirement_m3 - self.available_water_m3)

    def as_dict(self) -> dict:
        return {
            "available_water_m3": round(self.available_water_m3, 2),
            "n_farmers": self.n_farmers,
            "total_demand_m3": round(self.total_demand_m3, 2),
            "total_minimum_requirement_m3": round(self.total_minimum_requirement_m3, 2),
            "total_maximum_requirement_m3": round(self.total_maximum_requirement_m3, 2),
            "is_minimum_feasible": self.is_minimum_feasible,
            "supply_gap_m3": round(self.supply_gap_m3, 2),
            "minimum_infeasibility_gap_m3": round(self.minimum_infeasibility_gap_m3, 2),
        }


def build_constraints(
    agents: List[FarmerAgent],
    available_water_m3: float,
) -> AllocationConstraints:
    """
    Build the AllocationConstraints model from a list of FarmerAgents.

    Parameters
    ----------
    agents : list of FarmerAgent
    available_water_m3 : float
        Total available water for the scenario.

    Returns
    -------
    AllocationConstraints
    """
    total_min = sum(a.minimum_water_requirement for a in agents)
    total_max = sum(a.maximum_water_requirement for a in agents)
    total_demand = sum(a.predicted_water_demand for a in agents)
    is_feasible = total_min <= available_water_m3

    return AllocationConstraints(
        available_water_m3=available_water_m3,
        n_farmers=len(agents),
        total_demand_m3=total_demand,
        total_minimum_requirement_m3=total_min,
        total_maximum_requirement_m3=total_max,
        is_minimum_feasible=is_feasible,
        # Hard lower bounds: always 0 (x_i >= 0)
        per_farmer_lower_bounds=[0.0] * len(agents),
        # Soft lower bounds: min requirements (may not be enforceable)
        per_farmer_soft_lower_bounds=[a.minimum_water_requirement for a in agents],
        # Hard upper bounds: max requirements
        per_farmer_upper_bounds=[a.maximum_water_requirement for a in agents],
    )


def compute_jains_fairness_index(satisfaction_ratios: List[float]) -> float:
    """
    Compute Jain's Fairness Index for a list of satisfaction ratios.

    Formula
    -------
    J = (Σ s_i)² / (n × Σ s_i²)

    where s_i = satisfaction ratio of farmer i = x_i / demand_i
    clamped to [0, 1].

    Properties
    ----------
    - J = 1.0 when all s_i are equal (maximum fairness).
    - J = 1/n when only one farmer receives all resources.
    - J is always in (0, 1] for positive s_i, or 0 for all-zero case.

    References
    ----------
    Jain, R., Chiu, D., & Hawe, W. (1984). A Quantitative Measure of
    Fairness and Discrimination for Resource Allocation in Shared Computer Systems.
    DEC Research Report TR-301.

    Parameters
    ----------
    satisfaction_ratios : list of float
        Each s_i should be in [0, 1].

    Returns
    -------
    float in [0, 1]
    """
    n = len(satisfaction_ratios)
    if n == 0:
        return 0.0

    # Clamp to [0, 1]
    s = [max(0.0, min(1.0, si)) for si in satisfaction_ratios]

    sum_s = sum(s)
    sum_s2 = sum(si ** 2 for si in s)

    if sum_s2 < 1e-12:
        # All zero: technically undefined; return 0 (no resources distributed)
        return 0.0

    return (sum_s ** 2) / (n * sum_s2)
