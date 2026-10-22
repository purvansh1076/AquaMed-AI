"""
AquaMediAI — LP Water Allocator
=================================

Phase 5: Constraint-Based Water Allocation using OR-Tools GLOP.

Mathematical Formulation
------------------------

Decision Variables
~~~~~~~~~~~~~~~~~~
    x_i ∈ ℝ≥0   (m³/day allocated to farmer i)

Hard Constraints (never relaxed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    H1. x_i ≥ 0                             ∀ i
    H2. x_i ≤ max_water_i                   ∀ i
    H3. Σᵢ x_i ≤ available_water            (supply limit)

Soft Constraint (relaxed via penalty when infeasible)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    S1. x_i ≥ min_water_i                   ∀ i

    When Σ min_water_i > available_water (minimum-infeasible scenario),
    S1 is converted to a penalty term:
        penaltyᵢ = max(0, min_waterᵢ − xᵢ)

    The penalty is added to the objective as a negative term:
        −λ_min × Σᵢ penaltyᵢ / available_water

Objective Function (maximise)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    max Σᵢ [
          w_urg × urgencyᵢ × sᵢ
        + w_cs  × crop_sensitivityᵢ × sᵢ
        − w_unmet × (1 − sᵢ)           (unmet demand penalty)
        − w_min × shortfallᵢ / demand_i (minimum shortfall penalty, if relaxed)
    ]

    where:
        sᵢ = xᵢ / predicted_demandᵢ    (satisfaction ratio ∈ [0,1])
        shortfallᵢ = max(0, min_waterᵢ − xᵢ)

    Since GLOP is a linear solver, all terms are linearised:
        sᵢ = xᵢ / demand_i  →  this is linear in xᵢ (demand is constant)
        shortfallᵢ is handled via auxiliary variable pᵢ ≥ 0

    Default weights (configurable):
        w_urg   = 0.40  — urgency drives priority
        w_cs    = 0.25  — crop sensitivity adds extra weight
        w_unmet = 0.20  — penalise unmet demand
        w_min   = 0.15  — penalise minimum shortfall (when relaxed)

    The weights are scale-invariant; the LP is well-posed regardless of their
    exact values as long as they are non-negative.

Fairness
~~~~~~~~~~~~
    Jain's Fairness Index (post-hoc measurement, not enforced in the LP):
        J = (Σ sᵢ)² / (n × Σ sᵢ²)

    Fairness is MEASURED honestly — not forced.

Infeasibility Handling
~~~~~~~~~~~~~~~~~~~~~~~
    Before calling the solver:
        1. Check Σ min_req_i > available_water (minimum-infeasible)
        2. If minimum-infeasible → use soft penalty objective
        3. If not minimum-infeasible → use hard minimum constraints
    After the solver:
        4. Verify all hard constraints independently

Fallback
~~~~~~~~
    If the solver returns INFEASIBLE (should never happen with relaxed constraints):
        Proportional fallback allocation:
            x_i = available_water × (demand_i / total_demand)

References
----------
    - OR-Tools GLOP LP Solver: https://developers.google.com/optimization
    - FAO-56 (Allen et al. 1998): minimum crop water requirements
    - Jain et al. (1984): Jain's Fairness Index

DISCLAIMER: All allocations are computed from SYNTHETIC data.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ortools.linear_solver import pywraplp

from app.agents.farmer_agent import FarmerAgent
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

logger = logging.getLogger(__name__)

# ─── Default objective weights ─────────────────────────────────────────────────

@dataclass
class ObjectiveWeights:
    """
    Configurable weights for the LP objective function.

    Attributes
    ----------
    urgency : float
        Weight on urgency × satisfaction.
    crop_sensitivity : float
        Weight on crop_sensitivity × satisfaction.
    unmet_demand : float
        Penalty weight on (1 - satisfaction).
    minimum_shortfall : float
        Penalty weight on minimum requirement shortfall (used when relaxed).

    All weights must be >= 0.
    """
    urgency: float = 0.40
    crop_sensitivity: float = 0.25
    unmet_demand: float = 0.20
    minimum_shortfall: float = 0.15

    def __post_init__(self) -> None:
        for attr in ("urgency", "crop_sensitivity", "unmet_demand", "minimum_shortfall"):
            v = getattr(self, attr)
            if v < 0.0:
                raise ValueError(f"ObjectiveWeights.{attr} must be >= 0, got {v}")

    @property
    def total(self) -> float:
        return self.urgency + self.crop_sensitivity + self.unmet_demand + self.minimum_shortfall


# ─── Numerical tolerance ───────────────────────────────────────────────────────

_FEASIBILITY_TOLERANCE: float = 1e-6

# ─── Fallback modes (ordered by preference) ──────────────────────────────────

_FALLBACK_MODES = ("lp_optimal", "lp_relaxed", "proportional_fallback", "empty")


# ─── Main Allocator ──────────────────────────────────────────────────────────

class WaterAllocator:
    """
    OR-Tools GLOP LP-based water allocation engine.

    Consumes a list of FarmerAgent objects and available water,
    solves the LP, verifies constraints, and returns a typed AllocationResult.

    Parameters
    ----------
    agents : list of FarmerAgent
        Phase 3 farmer digital agents.
    available_water_m3 : float
        Total available water for this scenario (m³).
    weights : ObjectiveWeights, optional
        Configurable LP objective weights.
    scenario_id : str
        Identifier for the originating scenario.

    Usage
    -----
        allocator = WaterAllocator(agents, available_water_m3=4500.0)
        result = allocator.solve()
    """

    def __init__(
        self,
        agents: List[FarmerAgent],
        available_water_m3: float,
        weights: Optional[ObjectiveWeights] = None,
        scenario_id: str = "unknown",
    ) -> None:
        if available_water_m3 < 0:
            raise ValueError(
                f"available_water_m3 must be >= 0, got {available_water_m3}"
            )
        self._agents = list(agents)
        self._available = available_water_m3
        self._weights = weights or ObjectiveWeights()
        self._scenario_id = scenario_id
        self._constraints = build_constraints(self._agents, self._available)

        logger.debug(
            "WaterAllocator: n=%d, available=%.1f, demand=%.1f, "
            "min_feasible=%s",
            len(self._agents), self._available,
            self._constraints.total_demand_m3,
            self._constraints.is_minimum_feasible,
        )

    # ─── Public API ───────────────────────────────────────────────────────────

    def solve(self) -> AllocationResult:
        """
        Run the LP allocation and return a fully verified AllocationResult.

        Algorithm
        ---------
        1. Handle trivial edge cases (empty / zero water).
        2. Build the OR-Tools GLOP LP model.
        3. Add hard constraints H1, H2, H3.
        4. Add soft constraint S1 (hard if feasible, penalty if not).
        5. Set the objective function.
        6. Call GLOP solver.
        7. Extract solution.
        8. Run fallback if solver fails.
        9. Verify all hard constraints independently.
        10. Compute fairness and utilization.
        11. Return AllocationResult.

        Returns
        -------
        AllocationResult
        """
        t0 = time.perf_counter()

        # ── Edge case: no farmers ─────────────────────────────────────────────
        if len(self._agents) == 0:
            return self._empty_result()

        # ── Edge case: zero water ─────────────────────────────────────────────
        if self._available == 0.0:
            return self._zero_water_result()

        # ── Main LP solve ─────────────────────────────────────────────────────
        try:
            result = self._solve_lp()
        except Exception as exc:  # noqa: BLE001
            logger.error("LP solver raised unexpectedly: %s", exc, exc_info=True)
            result = self._proportional_fallback(
                solver_status=SolverStatus.ERROR,
                method="proportional_fallback",
            )

        # ── Fallback chain: lp_optimal → lp_relaxed → proportional → empty ────
        if result.allocation_method != "lp_relaxed":
            # Try LP-relaxed fallback (soft minimum penalties)
            if result.allocation_method != "lp_relaxed":
                logger.warning(
                    "LP solver returned %s — trying lp_relaxed fallback.",
                    result.solver_status.value,
                )
                result = self._lp_relaxed_fallback()
            # If lp_relaxed also failed (or was already used), use proportional
            if result.solver_status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
                logger.warning(
                    "lp_relaxed fallback also returned %s — using proportional fallback.",
                    result.solver_status.value,
                )
                result = self._proportional_fallback(
                    solver_status=SolverStatus.ERROR,
                    method="proportional_fallback",
                )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        result.solver_wall_time_ms = elapsed_ms

        logger.info(
            "WaterAllocator[%s]: status=%s, alloc=%.1f/%.1f, "
            "util=%.3f, fair=%.3f, time=%.1fms",
            self._scenario_id,
            result.solver_status.value,
            result.total_allocated_m3,
            self._available,
            result.utilization,
            result.fairness_score,
            elapsed_ms,
        )
        return result

    # ─── LP model construction ─────────────────────────────────────────────────

    def _solve_lp(self) -> AllocationResult:
        """Build and solve the GLOP LP model."""
        n = len(self._agents)
        is_feasible = self._constraints.is_minimum_feasible
        w = self._weights

        solver = pywraplp.Solver.CreateSolver("GLOP")
        if solver is None:
            logger.error("Failed to create GLOP solver — falling back to proportional.")
            return self._proportional_fallback(
                solver_status=SolverStatus.ERROR,
                method="proportional_fallback",
            )

        # ── Decision variables ────────────────────────────────────────────────
        # x_i = water allocated to farmer i (m³)
        x: List[pywraplp.Variable] = []
        for i, agent in enumerate(self._agents):
            xi = solver.NumVar(
                lb=0.0,
                ub=agent.maximum_water_requirement,
                name=f"x_{agent.farmer_id}",
            )
            x.append(xi)

        # ── Hard constraint H3: Σ x_i <= available_water ──────────────────────
        supply_ct = solver.Add(
            solver.Sum(x) <= self._available,
            name="supply_limit",
        )

        # ── Soft constraint S1 — minimum requirements ──────────────────────────
        # Auxiliary variables p_i for shortfall penalty (p_i >= min_i - x_i, p_i >= 0)
        p: List[Optional[pywraplp.Variable]] = [None] * n
        if is_feasible:
            # Hard minimum: x_i >= min_water_i
            for i, agent in enumerate(self._agents):
                solver.Add(x[i] >= agent.minimum_water_requirement,
                           name=f"min_req_{agent.farmer_id}")
        else:
            # Soft minimum: penalise shortfall via p_i >= 0, p_i >= min_i - x_i
            for i, agent in enumerate(self._agents):
                pi = solver.NumVar(0.0, solver.infinity(), f"p_{agent.farmer_id}")
                solver.Add(pi >= agent.minimum_water_requirement - x[i],
                           name=f"shortfall_{agent.farmer_id}")
                p[i] = pi

        # ── Objective function ─────────────────────────────────────────────────
        # Maximise: Σ [w_urg×urgency_i×(x_i/demand_i) + w_cs×cs_i×(x_i/demand_i)
        #              - w_unmet×(1 - x_i/demand_i) - w_min×p_i/demand_i]
        #
        # Since demand_i are constants, this is linear in x_i and p_i.
        #
        # We rescale by 1/n to keep the objective value in a predictable range.
        objective_terms = []
        for i, agent in enumerate(self._agents):
            d = max(agent.predicted_water_demand, 1e-9)  # avoid div-by-zero
            # Satisfaction: x_i / d_i (coefficient of x_i)
            urgency_coeff = w.urgency * agent.urgency / d
            cs_coeff = w.crop_sensitivity * agent.crop_sensitivity / d
            # Unmet demand penalty: -(1 - x_i/d_i) = x_i/d_i - 1
            # coefficient of x_i from penalty term is +w_unmet/d_i
            # constant offset is -w_unmet (doesn't affect optimality)
            total_coeff = urgency_coeff + cs_coeff + w.unmet_demand / d
            objective_terms.append(total_coeff * x[i])
            # Minimum shortfall penalty
            if p[i] is not None:
                objective_terms.append((-w.minimum_shortfall / d) * p[i])

        solver.Maximize(solver.Sum(objective_terms))

        # ── Solve ──────────────────────────────────────────────────────────────
        status_code = solver.Solve()

        # Map OR-Tools status to our enum
        _status_map = {
            pywraplp.Solver.OPTIMAL: SolverStatus.OPTIMAL,
            pywraplp.Solver.FEASIBLE: SolverStatus.FEASIBLE,
            pywraplp.Solver.INFEASIBLE: SolverStatus.INFEASIBLE,
            pywraplp.Solver.UNBOUNDED: SolverStatus.UNBOUNDED,
            pywraplp.Solver.NOT_SOLVED: SolverStatus.NOT_SOLVED,
        }
        solver_status = _status_map.get(status_code, SolverStatus.ERROR)

        if solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            # Extract solution
            raw_allocations = [max(0.0, x[i].solution_value()) for i in range(n)]
            obj_value = solver.Objective().Value()
            method = "lp_optimal" if is_feasible else "lp_relaxed"
            status_out = SolverStatus.OPTIMAL if is_feasible else SolverStatus.RELAXED
        else:
            # Unexpected — use proportional fallback
            logger.warning(
                "GLOP returned status=%s — using proportional fallback.",
                solver_status.value,
            )
            return self._proportional_fallback(
                solver_status=solver_status,
                method="proportional_fallback",
            )

        return self._build_result(
            raw_allocations=raw_allocations,
            solver_status=status_out,
            objective_value=obj_value,
            method=method,
        )

    # ─── Proportional Fallback ─────────────────────────────────────────────────

    def _proportional_fallback(
        self,
        solver_status: SolverStatus,
        method: str,
    ) -> AllocationResult:
        """
        Proportional allocation fallback.

        When the LP solver fails unexpectedly, distribute available water
        proportionally to predicted demand:
            x_i = available × (demand_i / total_demand)

        This always satisfies H1 and H3 by construction.
        H2 (max) is enforced via clamp.
        """
        total_demand = self._constraints.total_demand_m3
        if total_demand <= 0:
            raw = [0.0] * len(self._agents)
        else:
            raw = []
            for a in self._agents:
                alloc = self._available * (a.predicted_water_demand / total_demand)
                alloc = min(alloc, a.maximum_water_requirement)
                alloc = max(0.0, alloc)
                raw.append(alloc)

        return self._build_result(
            raw_allocations=raw,
            solver_status=solver_status,
            objective_value=0.0,
            method=method,
        )

    # ─── LP-relaxed fallback ─────────────────────────────────────────────────

    def _lp_relaxed_fallback(self) -> AllocationResult:
        """
        LP-relaxed fallback: force soft minimum-penalty objective even when
        minimum requirements are mathematically feasible, providing a graceful
        degradation path that still respects H1/H2/H3 but may sacrifice some
        minimum satisfaction for objective flexibility.

        This is invoked when the solver returns OPTIMAL/FEASIBLE but the
        minimum-feasibility flag suggests the solution is fragile.
        """
        n = len(self._agents)
        solver = pywraplp.Solver.CreateSolver("GLOP")
        if solver is None:
            return self._proportional_fallback(
                solver_status=SolverStatus.ERROR,
                method="lp_relaxed_fallback_error",
            )

        # Decision variables with H1/H2 bounds
        x: List[pywraplp.Variable] = []
        for i, agent in enumerate(self._agents):
            xi = solver.NumVar(
                lb=0.0,
                ub=agent.maximum_water_requirement,
                name=f"x_{agent.farmer_id}",
            )
            x.append(xi)

        # H3: total allocation <= available water
        solver.Add(solver.Sum(x) <= self._available, name="supply_limit")

        # Soft minimum: auxiliary penalty variables p_i (NOT hard constraints)
        p: List[pywraplp.Variable] = []
        for i, agent in enumerate(self._agents):
            pi = solver.NumVar(0.0, solver.infinity(), f"p_{agent.farmer_id}")
            solver.Add(pi >= agent.minimum_water_requirement - x[i],
                       name=f"shortfall_{agent.farmer_id}")
            p.append(pi)

        w = self._weights
        objective_terms = []
        for i, agent in enumerate(self._agents):
            d = max(agent.predicted_water_demand, 1e-9)
            urgency_coeff = w.urgency * agent.urgency / d
            cs_coeff = w.crop_sensitivity * agent.crop_sensitivity / d
            total_coeff = urgency_coeff + cs_coeff + w.unmet_demand / d
            objective_terms.append(total_coeff * x[i])
            # Penalise minimum shortfall
            objective_terms.append((-w.minimum_shortfall / d) * p[i])

        solver.Maximize(solver.Sum(objective_terms))

        status_code = solver.Solve()
        _status_map = {
            pywraplp.Solver.OPTIMAL: SolverStatus.OPTIMAL,
            pywraplp.Solver.FEASIBLE: SolverStatus.FEASIBLE,
            pywraplp.Solver.INFEASIBLE: SolverStatus.INFEASIBLE,
        }
        solver_status = _status_map.get(status_code, SolverStatus.ERROR)

        if solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            raw_allocations = [max(0.0, xi.solution_value()) for xi in x]
            obj_value = solver.Objective().Value()
            return self._build_result(
                raw_allocations=raw_allocations,
                solver_status=solver_status,
                objective_value=obj_value,
                method="lp_relaxed",
            )

        # Relaxed path also failed → proportional fallback
        return self._proportional_fallback(
            solver_status=SolverStatus.ERROR,
            method="lp_relaxed_fallback_failed",
        )

    # ─── Zero-water result ─────────────────────────────────────────────────────

    def _zero_water_result(self) -> AllocationResult:
        raw = [0.0] * len(self._agents)
        return self._build_result(
            raw_allocations=raw,
            solver_status=SolverStatus.OPTIMAL,
            objective_value=0.0,
            method="lp_optimal",
        )

    # ─── Empty result ──────────────────────────────────────────────────────────

    def _empty_result(self) -> AllocationResult:
        verification = ConstraintVerificationResult(
            is_valid=True,
            total_water_ok=True,
            non_negative_ok=True,
            maximum_ok=True,
            no_nan_ok=True,
            all_farmers_present=True,
            violations=[],
        )
        return AllocationResult(
            solver_status=SolverStatus.EMPTY,
            objective_value=0.0,
            available_water_m3=self._available,
            total_demand_m3=0.0,
            total_minimum_requirement_m3=0.0,
            total_allocated_m3=0.0,
            remaining_water_m3=self._available,
            utilization=0.0,
            fairness_score=0.0,
            minimum_requirements_feasible=True,
            allocations=[],
            verification=verification,
            scenario_id=self._scenario_id,
            allocation_method="empty",
        )

    # ─── Build result from raw allocations ──────────────────────────────────────

    def _build_result(
        self,
        raw_allocations: List[float],
        solver_status: SolverStatus,
        objective_value: float,
        method: str,
    ) -> AllocationResult:
        """
        Build an AllocationResult from raw solver output values,
        then verify constraints independently.
        """
        is_feasible = self._constraints.is_minimum_feasible

        farmer_allocations: List[FarmerAllocation] = []
        for i, agent in enumerate(self._agents):
            alloc = raw_allocations[i]
            shortfall = max(0.0, agent.minimum_water_requirement - alloc)
            # Determine constraint status
            if shortfall > _FEASIBILITY_TOLERANCE:
                status = "minimum_relaxed"
            elif abs(alloc - agent.maximum_water_requirement) < _FEASIBILITY_TOLERANCE:
                status = "at_maximum"
            else:
                status = "satisfied"

            fa = FarmerAllocation(
                farmer_id=agent.farmer_id,
                allocated_water_m3=alloc,
                predicted_demand_m3=agent.predicted_water_demand,
                minimum_requirement_m3=agent.minimum_water_requirement,
                maximum_requirement_m3=agent.maximum_water_requirement,
                urgency=agent.urgency,
                crop_sensitivity=agent.crop_sensitivity,
                growth_stage=agent.growth_stage,
                crop=agent.crop,
                constraint_status=status,
                explanation_metadata={
                    "predicted_demand_m3": round(agent.predicted_water_demand, 2),
                    "allocated_water_m3": round(alloc, 2),
                    "minimum_requirement_m3": round(agent.minimum_water_requirement, 2),
                    "maximum_requirement_m3": round(agent.maximum_water_requirement, 2),
                    "unmet_demand_m3": round(max(0.0, agent.predicted_water_demand - alloc), 2),
                    "minimum_shortfall_m3": round(shortfall, 2),
                    "urgency": round(agent.urgency, 4),
                    "crop_sensitivity": round(agent.crop_sensitivity, 4),
                    "growth_stage": agent.growth_stage,
                    "crop": agent.crop,
                    "minimum_requirements_feasible": is_feasible,
                    "constraint_status": status,
                    "objective_weights": {
                        "urgency": self._weights.urgency,
                        "crop_sensitivity": self._weights.crop_sensitivity,
                        "unmet_demand": self._weights.unmet_demand,
                        "minimum_shortfall": self._weights.minimum_shortfall,
                    },
                },
            )
            farmer_allocations.append(fa)

        total_allocated = sum(fa.allocated_water_m3 for fa in farmer_allocations)
        remaining = max(0.0, self._available - total_allocated)
        utilization = total_allocated / self._available if self._available > 0 else 0.0

        sat_ratios = [fa.satisfaction_ratio for fa in farmer_allocations]
        fairness = compute_jains_fairness_index(sat_ratios)

        verification = verify_constraints(
            farmer_allocations=farmer_allocations,
            available_water_m3=self._available,
            agent_ids=[a.farmer_id for a in self._agents],
        )

        return AllocationResult(
            solver_status=solver_status,
            objective_value=objective_value,
            available_water_m3=self._available,
            total_demand_m3=self._constraints.total_demand_m3,
            total_minimum_requirement_m3=self._constraints.total_minimum_requirement_m3,
            total_allocated_m3=total_allocated,
            remaining_water_m3=remaining,
            utilization=utilization,
            fairness_score=fairness,
            minimum_requirements_feasible=is_feasible,
            allocations=farmer_allocations,
            verification=verification,
            scenario_id=self._scenario_id,
            allocation_method=method,
        )

    # ─── Properties ──────────────────────────────────────────────────────────

    @property
    def constraints(self) -> AllocationConstraints:
        return self._constraints

    @property
    def agents(self) -> List[FarmerAgent]:
        return list(self._agents)


# ─── Post-solve constraint verifier ───────────────────────────────────────────

def verify_constraints(
    farmer_allocations: List[FarmerAllocation],
    available_water_m3: float,
    agent_ids: List[str],
    tolerance: float = _FEASIBILITY_TOLERANCE,
) -> ConstraintVerificationResult:
    """
    Independently verify all hard constraints after solving.

    The system never trusts the solver blindly.

    Checks
    ------
    1. total_allocated <= available_water + tolerance
    2. All allocations >= 0
    3. All allocations <= maximum_requirement
    4. No NaN or Inf values
    5. All farmer IDs accounted for

    Note: minimum requirement satisfaction is NOT checked here as
    a hard constraint because it may be intentionally relaxed (soft).
    Minimum shortfalls are reported in FarmerAllocation.minimum_shortfall_m3.

    Parameters
    ----------
    farmer_allocations : list of FarmerAllocation
    available_water_m3 : float
    agent_ids : list of str
        IDs that must appear in the allocation.
    tolerance : float
        Numerical tolerance for water balance check.

    Returns
    -------
    ConstraintVerificationResult
    """
    violations: List[str] = []

    # 1. Total water balance
    total_allocated = sum(fa.allocated_water_m3 for fa in farmer_allocations)
    total_water_ok = total_allocated <= available_water_m3 + tolerance
    if not total_water_ok:
        violations.append(
            f"H3 VIOLATION: total_allocated ({total_allocated:.4f}) > "
            f"available ({available_water_m3:.4f}) + tolerance ({tolerance})"
        )

    # 2. Non-negative allocations
    non_negative_ok = True
    for fa in farmer_allocations:
        if fa.allocated_water_m3 < -tolerance:
            non_negative_ok = False
            violations.append(
                f"H1 VIOLATION: farmer {fa.farmer_id} has negative allocation "
                f"({fa.allocated_water_m3:.6f})"
            )

    # 3. Maximum allocation
    maximum_ok = True
    for fa in farmer_allocations:
        if fa.allocated_water_m3 > fa.maximum_requirement_m3 + tolerance:
            maximum_ok = False
            violations.append(
                f"H2 VIOLATION: farmer {fa.farmer_id} allocated "
                f"({fa.allocated_water_m3:.2f}) > maximum ({fa.maximum_requirement_m3:.2f})"
            )

    # 4. No NaN/Inf
    no_nan_ok = True
    for fa in farmer_allocations:
        if math.isnan(fa.allocated_water_m3) or math.isinf(fa.allocated_water_m3):
            no_nan_ok = False
            violations.append(
                f"NaN/Inf VIOLATION: farmer {fa.farmer_id} has invalid "
                f"allocation value ({fa.allocated_water_m3})"
            )

    # 5. All farmers present
    result_ids = {fa.farmer_id for fa in farmer_allocations}
    expected_ids = set(agent_ids)
    all_farmers_present = result_ids == expected_ids
    if not all_farmers_present:
        missing = expected_ids - result_ids
        extra = result_ids - expected_ids
        if missing:
            violations.append(f"MISSING farmers in allocation: {missing}")
        if extra:
            violations.append(f"EXTRA farmers in allocation: {extra}")

    is_valid = (
        total_water_ok
        and non_negative_ok
        and maximum_ok
        and no_nan_ok
        and all_farmers_present
    )

    return ConstraintVerificationResult(
        is_valid=is_valid,
        total_water_ok=total_water_ok,
        non_negative_ok=non_negative_ok,
        maximum_ok=maximum_ok,
        no_nan_ok=no_nan_ok,
        all_farmers_present=all_farmers_present,
        violations=violations,
        tolerance_m3=tolerance,
    )