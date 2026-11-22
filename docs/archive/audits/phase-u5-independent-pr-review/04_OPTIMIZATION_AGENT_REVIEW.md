# Phase U5 — Audit Report 04: Optimization Engine & Multi-Agent Negotiation Review

**Document ID:** `AQUA-AUDIT-U5-04`  
**Date:** 2026-11-15  
**Review Type:** Algorithmic Safety & Mechanism Design Audit  
**Components:** `backend/app/allocation/`, `backend/app/agents/`  

---

## 1. Executive Summary

This report evaluates the optimization algorithms and multi-agent negotiation mechanisms governing water allocation in AquaMedi AI. The audit assessed physical conservation guarantees, linear programming (LP) solvers, fairness metrics, agent communication protocols, and termination dynamics under resource deficits.

---

## 2. Linear Programming (LP) Allocation Engine

Water allocation across multiple agricultural parcels is formulated as an optimization problem solved using the `scipy.optimize.linprog` HiGHS solver (`backend/app/allocation/lp_allocator.py`).

### 2.1 Optimization Objective
The primary objective maximizes total agricultural utility weighted by crop vulnerability and economic productivity:
$$\max \sum_{i=1}^N w_i x_i - \sum_{i=1}^N \lambda_i (D_i - x_i)^2$$
where:
- $x_i$ is the volume allocated to parcel $i$.
- $D_i$ is the agronomic crop water requirement.
- $w_i$ is the crop priority weight (e.g., higher for perishable or high-value crops during sensitive growth stages).
- $\lambda_i$ penalizes deficit severe enough to induce crop failure.

### 2.2 Strict Physical Conservation Constraint
The fundamental physical law of water allocation is conservation:
$$\sum_{i=1}^N x_i \le W_{\text{available}}$$
where $W_{\text{available}}$ is the total canal or reservoir discharge capacity.

**Defensive Tolerance Hardening:**  
Numerical solvers operate with small feasibility tolerances (e.g., $10^{-7}$). To eliminate the risk of allocating even a fraction of a liter beyond physical availability due to floating-point rounding, the allocator implements an explicit post-solve scaling safeguard:
```python
total_allocated = sum(allocations.values())
if total_allocated > available_water:
    scale = available_water / total_allocated
    allocations = {k: v * scale for k, v in allocations.items()}
```
This guarantees that allocated water can never exceed physical capacity under any computational circumstance.

---

## 3. Fairness-Aware Allocation & Deficit Distribution

Under drought conditions ($W_{\text{available}} < \sum D_i$), unconstrained linear optimization tends to cut off tail-end farmers entirely if their crop weight is lower. To prevent this inequity, AquaMedi AI implements **Max-Min Fairness** (`backend/app/allocation/fairness.py`):

1. **Guaranteed Minimum Floor:**
   Every parcel is assigned a survival floor $x_i^{\min} = \gamma \cdot D_i$ (where $\gamma \in [0.2, 0.4]$ is a survival threshold prevent permanent crop death).
2. **Lexicographic Max-Min Optimization:**
   The algorithm maximizes the satisfaction ratio of the least-satisfied farmer:
   $$\max \min_{i} \left( \frac{x_i}{D_i} \right)$$
3. **Robust Fallback Model:**
   If strict minimum floors cannot be satisfied simultaneously (catastrophic drought), the allocator transitions gracefully to an LP-relaxed soft-penalty model. This guarantees that the solver never throws an unhandled `InfeasibleError`.

---

## 4. Multi-Agent Negotiation Framework

When initial algorithmic allocations result in dissatisfaction or boundary disputes, the multi-agent negotiation system (`backend/app/agents/`) orchestrates bilateral and mediated bargaining:

### 4.1 Agent Roles
- **Farmer Agent (`FarmerAgent`):** Represents the individual farmer's self-interest, minimizing yield loss and maximizing quota satisfaction based on local soil moisture forecasts.
- **Mediator / Water Authority Agent (`AuthorityAgent`):** Enforces catchment-wide conservation constraints, prevents upstream overuse, and ensures equitable delivery to tail-end users.

### 4.2 Negotiation Dynamics & Concession Curves
Negotiation operates over discrete rounds with strictly bounded termination:
- Maximum rounds: $T_{\max} = 10$.
- Concession strategy: Time-dependent decay functions (Boulware and Conceder curves) ensure convergence before round limits.
- Pareto efficiency: Proposed exchanges between farmers must improve or maintain social welfare ($\Delta \text{Welfare} \ge 0$).

### 4.3 Agent Message Schema Hardening
Agent interactions use strongly-typed Pydantic schemas (`backend/app/agents/messages.py`):
- Sender and receiver identity validation: Rejects self-directed messages (`sender_id != receiver_id`).
- Cryptographic timestamps and round counters prevent replay attacks and message ordering anomalies.
- All messages are serialized deterministically to support audit trails.

---

## 5. Conflict Resolution & Audit Logging

- **Conflict Detection:** Triggers automatically when demand discrepancy exceeds threshold $\tau = 15\%$ or when upstream/downstream delivery schedules clash.
- **Audit Trails:** All negotiation transcripts, proposed trade-offs, and final mediator rulings are logged with structured schemas for administrative review.

---

## 6. Verdict

**Algorithmic Status: PASS (Physical Conservation & Algorithmic Convergence Verified)**
