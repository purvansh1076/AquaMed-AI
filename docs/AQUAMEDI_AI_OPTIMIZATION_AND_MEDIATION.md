# AQUAMEDI AI — OPTIMIZATION & MULTI-AGENT MEDIATION SPECIFICATION
**Document Reference**: `AQUA-OPT-MED-2026-V1`  
**Specialists**: Mathematical Optimization Specialist & Multi-Agent Systems Researcher  

---

## 1. Linear Programming Water Allocation Engine

### 1.1 Mathematical Formulation
The allocation module in [lp_allocator.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/allocation/lp_allocator.py) uses the Google OR-Tools GLOP simplex solver.

#### Decision Variables:
$$x_i \in \mathbb{R}_{\ge 0} \quad (\text{Allocated water volume to farmer } i \text{ in m}^3)$$

#### Hard Physical Constraints:
1. **Non-negativity ($H_1$)**:
   $$x_i \ge 0 \quad \forall i \in \{1, \dots, N\}$$
2. **Crop Capacity Maximum ($H_2$)**:
   $$x_i \le Q_{max, i} = D_i \quad (\text{Prevents soil saturation & root rot})$$
3. **Canal Conveyance Supply Limit ($H_3$)**:
   $$\sum_{i=1}^N \frac{x_i}{\eta_i} \le Q_{total}$$
   where $\eta_i \in (0, 1]$ is the reach transit efficiency (accounting for seepage and evaporation loss along the canal).

#### Soft Minimum Survival Requirement ($S_1$):
When feasible:
$$x_i \ge Q_{min, i} = \alpha_i D_i \quad (\alpha_i \approx 0.3 \text{ to } 0.5)$$
When total minimum demand exceeds supply ($\sum Q_{min, i} > Q_{total}$), $S_1$ is converted into an auxiliary shortfall penalty variable $p_i \ge \max(0, Q_{min, i} - x_i)$.

#### Multi-Objective Function:
$$\max \sum_{i=1}^N \left[ w_{urg} u_i \left(\frac{x_i}{D_i}\right) + w_{cs} c_i \left(\frac{x_i}{D_i}\right) - w_{unmet} \left(1 - \frac{x_i}{D_i}\right) - w_{min} \left(\frac{p_i}{D_i}\right) \right]$$

---

## 2. Multi-Agent Negotiation Protocol

The mediation engine in [negotiation_engine.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/agents/negotiation_engine.py) models each farmer as an autonomous economic agent.

### 2.1 Individual Utility Function
$$U_i(x_i) = \left(\frac{x_i}{D_i}\right)^{\beta_i}$$
where $\beta_i$ reflects crop risk aversion. High-urgency crops (e.g. flowering sugarcane) have higher $\beta_i$, making utility drop steeply under deficit allocation.

### 2.2 Concession Mechanism
In round $r$, if a consensus is not reached, dissatisfied agents calculate concession:
$$\Delta x_i^{(r)} = \delta_i \times (x_i^{(r)} - Q_{min, i}) \times \text{flexibility}_i \times (1 - \text{urgency}_i)$$
Concessions are re-optimized via GLOP to guarantee that water conservation is physically maintained.

### 2.3 Cooperative Game-Theoretic Evaluation (Nash Product)
The system tracks the Nash Bargaining Product across all rounds:
$$\mathcal{N} = \prod_{i=1}^N \max(10^{-6}, U_i(x_i) - d_i)$$
where $d_i$ is the disagreement survival utility ($U_i(Q_{min, i})$).

### 2.4 Jain's Fairness Index
$$J(x) = \frac{\left( \sum_{i=1}^N s_i \right)^2}{N \sum_{i=1}^N s_i^2} \quad \text{where } s_i = \frac{x_i}{D_i}$$
$J \in [1/N, 1.0]$. $J = 1.0$ indicates perfectly egalitarian satisfaction across all farmers regardless of canal reach.
