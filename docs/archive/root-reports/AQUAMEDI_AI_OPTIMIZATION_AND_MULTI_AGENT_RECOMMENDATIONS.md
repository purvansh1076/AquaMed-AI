# AquaMedi AI — Optimization and Multi-Agent Recommendations

**Document:** `AQUAMEDI_AI_OPTIMIZATION_AND_MULTI_AGENT_RECOMMENDATIONS.md`
**Type:** Recommendation-only

---

## 1. Current optimization implementation (verified)

- Solver: Google OR-Tools GLOP (`backend/app/allocation/lp_allocator.py:WaterAllocator._solve_lp`).
- Variables: `x_i ∈ ℝ≥0` (m³ allocated to farmer i), bounds `[0, maximum_water_requirement]`.
- Hard constraints: H1 non-negativity, H2 `x_i ≤ max_water_i`, H3 `Σ (x_i / η_i) ≤ available_water` (conveyance efficiency η, default 1.0).
- Soft constraint: S1 `x_i ≥ min_water_i` — hard when `Σ min ≤ available`, else converted to shortfall penalty `p_i ≥ min_i − x_i`, `p_i ≥ 0`.
- Objective: maximize `Σ [w_urg·urgency·(x/d) + w_cs·cs·(x/d) + w_unmet·(x/d) − w_min·(p/d)]` with weights (0.40, 0.25, 0.20, 0.15).
- Fairness: Jain's index computed post-hoc in `constraints.py:compute_jains_fairness_index`.
- Fallback: proportional by demand, then empty.
- Independent verification: `verify_constraints` (water balance, non-negativity, max, NaN/Inf, farmer presence).
- Conveyance loss: `conveyance_efficiencies` dict supported.

## 2. Verified defect (highest priority)

**F-09 — `WaterAllocator.solve()` replaces an optimal solution with the relaxed fallback.**

In `solve()` (lines ~255–274), after `_solve_lp()` returns `allocation_method == "lp_optimal"`, the condition `if result.allocation_method != "lp_relaxed"` is true, so `_lp_relaxed_fallback()` is invoked and its result overwrites the optimal one. Consequence: even feasible (minimum-satisfiable) scenarios are reported as `lp_relaxed` with soft minimums, potentially below minimum requirements, and the true optimum is discarded.

**Fix:** only call `_lp_relaxed_fallback()` when `_solve_lp()` fails to produce OPTIMAL/FEASIBLE, or when an explicit degraded mode is requested. Affected: `lp_allocator.py:solve`. Tests: `tests/test_lp_allocator.py`.

## 3. Optimization recommendations

- **R-OPT-01 (Priority A):** Fix F-09.
- **R-OPT-02 (Priority B):** Expose `ObjectiveWeights` as tunable and add a fairness term or a fairness-constrained variant; compute a Pareto frontier by sweeping weights (fairness vs. efficiency). Affected: `lp_allocator.py:ObjectiveWeights`, `constraints.py`. Do not replace GLOP with NSGA-II/MILP without evidence.
- **R-OPT-03 (Priority B):** Report GLOP shadow prices (dual values) for the supply and canal constraints as the marginal value of additional water/capacity. Affected: `lp_allocator.py` (`solver.dual_value`), `allocation_types.py`.
- **R-OPT-04 (Priority B):** Add canal capacity as a hard constraint per irrigation window (currently only in conflict detection). Affected: `lp_allocator.py`, `constraints.py`.
- **R-OPT-05 (Priority C):** Robust optimization over supply realizations (scenario set); report worst-case allocation. Affected: `WaterAllocator`, `scenario_service.py`.
- **R-OPT-06 (Priority C):** Stochastic optimization — only after real weather distributions exist.
- **R-OPT-07 (Priority B):** Relaxation transparency in UI (which farmers are below minimum, by how much) — data already in `minimum_shortfall_m3`.

## 4. Current multi-agent / negotiation implementation (verified)

- `backend/app/agents/farmer_agent.py`, `digital_twin.py`, `utility.py`: utility `U_i` (water satisfaction, timing, urgency protection, min-req satisfaction, stress penalty), BATNA utility, stage criticality.
- `backend/app/negotiation/mediator.py`, `negotiation_engine.py`, `bargaining.py`: log-surplus objective `Σ log(max(surplus_i, 1e-6))`, termination (agreement, max rounds, stagnation, failure), Merkle certificate.
- The code explicitly disclaims axiomatic Nash bargaining; this honesty should be preserved.

## 5. Verified issues in negotiation

- **F-12 (Priority B):** `NegotiationEngine.run` uses `responses=initial_responses if round_num == 2 else current_responses`; `current_responses` is defined only after the first mediator call. Initialize `current_responses = initial_responses` before the loop and pass the correct previous responses.
- **F-13 (Priority C):** `_check_concession_progress` measures aggregate water reduction, not farmer concession; rewrite to track per-farmer utility/allocation concession relative to each farmer's request.

## 6. Multi-agent recommendations

- **R-MA-01 (Priority B):** Fix F-12.
- **R-MA-02 (Priority B):** Convergence metrics — per-round Nash objective, fairness, acceptances, concession amount; convergence flag when objective change < 1e-4 for 2 rounds. Affected: `negotiation_types.py:NegotiationRound`, `negotiation_engine.py`.
- **R-MA-03 (Priority B):** Pareto-efficiency verification after termination (can any farmer improve without harming another?) with a boolean + witness. Affected: new helper in `bargaining.py`.
- **R-MA-04 (Priority B):** Agent-level explanations (why each farmer accepted/rejected: utility vs. BATNA, shortfall) in plain language. Affected: `negotiation_explainer.py`, frontend negotiation page.
- **R-MA-05 (Priority C):** Counterfactual negotiation (remove one farmer / alter BATNA) to show sensitivity. Affected: `NegotiationEngine` new method.
- **R-MA-06 (Priority C):** Fix F-13.
- **R-MA-07 (Priority B):** Negotiation history visualization (round-by-round fairness + Nash trajectories) — data already in `round_fairness_history` / `round_nash_history`. Affected: frontend `FairnessTrajectoryChart.tsx`, negotiation page.
- **R-MA-08 (Priority B):** Fairness comparison before vs. after mediation (initial LP Jain's index vs. final). Affected: agreement output + frontend.

## 7. What to keep (do not replace)

- Keep GLOP (linear, <15 ms, constraints are linear).
- Keep the Nash-bargaining-inspired heuristic framing; do not claim axiomatic NBS.
- Keep Jain's index as a measured (not enforced) fairness metric, but consider adding a fairness term/constraint as an opt-in (R-OPT-02).

## 8. Suggested experiments (realistic, 2–3 weeks)

1. Fix F-09, then re-run: compare initial LP vs. negotiated allocation on Jain's fairness index and number of accepting farmers across the 8 scenario types × 5 seeds.
2. Pareto frontier: sweep `ObjectiveWeights` (urgency vs. fairness) and plot fairness vs. efficiency.
3. Sensitivity: vary available water from 40% to 120% of demand; report allocations and solver status.
4. Convergence: rounds to agreement vs. number of farmers (2–10).

## 9. References

- Nash, J.F. (1950). The Bargaining Problem. Econometrica 18(2): 155–162.
- Raiffa, H. (1982). The Art and Science of Negotiation.
- Jain, R. et al. (1984). A Quantitative Measure of Fairness.
- OR-Tools documentation (Google): LP/MIP solvers.
