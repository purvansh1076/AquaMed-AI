# AquaMediAI — Authoritative Project State & Documentation Freeze

> **System Title**: AquaMediAI — An Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System for Farmers  
> **Project Scope**: B.Tech CSE Final Year Capstone Project / Academic Prototype  
> **Document Status**: FINAL STATE FREEZE — COMPLETE & VERIFIED  
> **Last Updated**: 2026-09-22  
> **Verification Baseline**: Backend 704/704 tests passing | Frontend 53/53 tests passing | Frontend build PASS  

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Problem Statement](#2-problem-statement)
3. [Research Motivation](#3-research-motivation)
4. [Proposed Solution](#4-proposed-solution)
5. [Complete Architecture](#5-complete-architecture)
6. [Phase-by-Phase Implementation](#6-phase-by-phase-implementation)
7. [Data Pipeline](#7-data-pipeline)
8. [ML Pipeline](#8-ml-pipeline)
9. [Actual Model Metrics](#9-actual-model-metrics)
10. [Farmer Agent Architecture](#10-farmer-agent-architecture)
11. [Conflict Detection Engine](#11-conflict-detection-engine)
12. [Mathematical Allocation Formulation](#12-mathematical-allocation-formulation)
13. [Allocation Constraints](#13-allocation-constraints)
14. [Allocation Objective](#14-allocation-objective)
15. [Fairness Calculation](#15-fairness-calculation)
16. [Negotiation Architecture](#16-negotiation-architecture)
17. [BATNA and Utility Formulation](#17-batna-and-utility-formulation)
18. [Concession Mechanism](#18-concession-mechanism)
19. [Nash-Inspired Objective](#19-nash-inspired-objective)
20. [Negotiation Termination](#20-negotiation-termination)
21. [Explainability Architecture](#21-explainability-architecture)
22. [FastAPI Architecture](#22-fastapi-architecture)
23. [Frontend Architecture](#23-frontend-architecture)
24. [Farmer View](#24-farmer-view)
25. [Expert View](#25-expert-view)
26. [Localization](#26-localization)
27. [API Endpoints](#27-api-endpoints)
28. [Testing Status](#28-testing-status)
29. [Current Verified Test Counts](#29-current-verified-test-counts)
30. [Known Limitations](#30-known-limitations)
31. [Future Scope](#31-future-scope)
32. [Final Project Status](#32-final-project-status)

---

## 1. Project Identity

- **Project Name**: AquaMediAI
- **Full Title**: "An Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System for Farmers"
- **Domain**: Artificial Intelligence / Machine Learning / Computational Optimization / Multi-Agent Systems
- **System Nature**: Academic Prototype & Research Demonstration
- **Core Technology Stack**:
  - **Backend**: Python 3.12, FastAPI, Google OR-Tools (GLOP LP Solver), XGBoost, scikit-learn, SHAP, Pydantic v2, Pytest
  - **Frontend**: React 18, TypeScript, Vite, Vanilla CSS / Tailwind utilities, Lucide React, Recharts, Vitest
- **Repository Root**: `aquamedi-ai/`

---

## 2. Problem Statement

In agricultural canal irrigation commands, water scarcity frequently triggers severe disputes among farmers. Key structural challenges include:
1. **Asymmetric Access (Head vs. Tail End)**: Head-reach farmers divert excess water, leaving tail-reach farmers with inadequate volume or untimely delivery.
2. **Conflicting Demands & Schedules**: Simultaneous irrigation windows overload canal branch capacity, leading to water theft or crop desiccation.
3. **Agronomic Disparities**: Diverse crops (e.g., high-water sugarcane vs. drought-sensitive flowering wheat) require differentiated urgency weighting, yet traditional allocation relies on rudimentary rotation or blunt land-area proportionality.
4. **Lack of Trust & Transparency**: Farmers distrust centralized administrative quotas because decisions lack transparent mathematical justification and clear explanations.

---

## 3. Research Motivation

- **Bridging ML, Game Theory, and Optimization**: Pure optimization (e.g., standard LP) treats human farmers as passive variables, ignoring personal autonomy, acceptable time slots, and reservation options (BATNA). Conversely, unconstrained multi-agent bargaining can converge on physically unachievable allocations that violate canal hydraulic limits.
- **The Imperative for Explainability**: Farmers and irrigation officers reject black-box AI recommendations. Every allocation and concession must be auditable, grounded in agronomic physics, and explainable in plain regional language.
- **System Integration**: Developing a unified computational architecture that smoothly couples:
  $$\text{Agronomic ML Demand} \longrightarrow \text{Digital Twins} \longrightarrow \text{Conflict Detection} \longrightarrow \text{LP Allocation} \longrightarrow \text{Mediation} \longrightarrow \text{Explainability}$$

---

## 4. Proposed Solution

AquaMediAI provides a deterministic, explainable, and multi-layered automated mediation framework:
1. **Predictive Water Demand Modeling**: Machine learning models estimate daily volumetric demand ($m^3/\text{day}$) using FAO-56 Penman-Monteith agronomic factors.
2. **Farmer Digital Twins**: Individual agents encapsulate farmer crop stages, urgency, schedule preferences, utility curves, and BATNA.
3. **Deterministic Conflict Detection**: Identifies volumetric deficits, canal capacity bottlenecks, schedule clashes, and acute crop stress risks.
4. **Constrained LP Water Allocation**: Google OR-Tools GLOP solver guarantees physical conservation and maximum ceilings while penalizing drops below minimum survival requirements.
5. **Multi-Agent Negotiation & Mediation**: Automated mediation adjusts farmer asks through calibrated concession formulas, evaluated against a joint Nash-inspired objective, with mandatory LP re-optimization at every iteration.
6. **Multi-Layer Explainability**: Deconstructs ML predictions via SHAP feature attributions and explains allocation/concession rationale via deterministic reason codes.
7. **Dual-Mode User Interface**: A Farmer View delivering plain-language cards in regional languages alongside an Expert View providing in-depth mathematical diagnostics.

---

## 5. Complete Architecture

```
                                  AQUAMEDIAI COMPLETE PIPELINE
                                  
   +-----------------------------------------------------------------------------------+
   |                            SYNTHETIC DATA LAYER (Phase 1)                         |
   |   FAO-56 Penman-Monteith Formula: ET_c = ET_0 * K_c * Area (3,000 Samples, 22 Feats)|
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                              ML DEMAND LAYER (Phase 2)                            |
   |   XGBoost (R2 = 0.9736) & Random Forest (R2 = 0.9737) + SHAP Feature Attribution   |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                         FARMER DIGITAL TWINS (Phase 3)                            |
   |   FarmerAgent: Preferences, Crop Sensitivity, Multi-Factor Utility U_i, BATNA     |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                         CONFLICT DETECTION ENGINE (Phase 4)                       |
   |   5 Conflict Types: Shortage, Window Overlap, Canal Capacity, Min-Req, Crop Stress |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                          OR-TOOLS GLOP LP ALLOCATION (Phase 5)                    |
   |   Hard Constraints (H1, H2, H3) + Soft Survival Requirements (S1 with Penalty p_i)|
   |   Post-Hoc Jain's Fairness Index Diagnostic: J = (sum s_i)^2 / (n * sum s_i^2)   |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                        MULTI-AGENT NEGOTIATION (Phase 6)                          |
   |   Farmer Utility Evaluation -> Mediator Concession Formula -> Mandatory LP Solve   |
   |   Joint Evaluation: Omega_Nash = sum log(max(surplus_i, 1e-6))                    |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                         EXPLAINABILITY LAYER (Phase 7)                            |
   |   Deterministic Reason Codes, Constraint Explanations, SHAP Waterfall Summaries    |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                         FASTAPI INTEGRATION LAYER (Phase 8)                       |
   |   REST Endpoints: /api/v1/scenarios/run, /predictions, /conflicts, /allocations   |
   +-----------------------------------------+-----------------------------------------+
                                             |
                                             v
   +-----------------------------------------------------------------------------------+
   |                         REACT + TYPESCRIPT FRONTEND (Phase 9)                     |
   |   Dual Presentation Modes: Farmer View (Plain Regional) & Expert View (Diagnostic)|
   |   Languages: English, Hindi, Gujarati | Zero Voice | 53 Tests | Production Build  |
   +-----------------------------------------------------------------------------------+
```

---

## 6. Phase-by-Phase Implementation

| Phase | Title | Scope & Artifacts | Verified Tests |
|---|---|---|---|
| **Phase 1** | Foundation & Synthetic Data | FAO-56 synthetic generator, 8 scenario distributions, agronomic feature engineering | **62 / 62** |
| **Phase 2** | ML Demand Prediction | Random Forest, XGBoost, evaluation metrics, SHAP TreeExplainer | **64 / 64** |
| **Phase 3** | Farmer Digital Agents | `FarmerAgent`, `FarmerPreferences`, multi-factor utility $U_i$, `BATNA`, `DigitalTwin` | **96 / 96** |
| **Phase 4** | Conflict Detection Engine | 5 conflict types, CSPS risk score, severity classification, window overlaps | **88 / 88** |
| **Phase 5** | OR-Tools GLOP Allocation | LP formulation, hard bounds, soft minimum penalty $p_i$, post-hoc Jain's fairness | **86 / 86** |
| **Phase 6** | Multi-Agent Negotiation | Mediator, response thresholds, concession logic, mandatory re-optimization, Log-Nash | **123 / 123** |
| **Phase 7** | Explainability Layer | Explanation dataclasses, deterministic reason codes, SHAP explanation adapters | **113 / 113** |
| **Phase 8** | FastAPI Integration Layer | REST API, Pydantic v2 schemas, `ScenarioService`, CORS, OpenAPI docs | **72 / 72** |
| **Phase 9** | React Frontend Dashboard | React 18, Vite, TypeScript, Farmer & Expert Views, en/hi/gu localization, Recharts | **53 / 53** |
| **Total** | **Full System Pipeline** | **End-to-End Integrated Architecture** | **757 / 757** |

---

## 7. Data Pipeline

The data layer (`backend/app/ml/data_generator.py`) programmatically synthesizes agronomic datasets rooted in agricultural physics:

### Agronomic Principles
- Base crop water requirements follow the **FAO-56 Irrigation and Drainage Paper**:
  $$ET_c = ET_0 \times K_c$$
  $$\text{Daily Demand } (m^3) = \frac{ET_c \times \text{Farm Area } (\text{ha}) \times 10}{E_{\text{eff}}}$$
  where $ET_0$ is reference evapotranspiration, $K_c$ is crop coefficient, and $E_{\text{eff}}$ is irrigation efficiency.

### Domain Coverage
- **Crops (8)**: Wheat, Rice, Maize, Cotton, Sugarcane, Groundnut, Mustard, Potato.
- **Growth Stages (5)**: Initial, Vegetative, Flowering, Yield Formation, Maturity.
- **Soil Types & WHC (5)**:
  - Clay: $200\text{ mm/m}$
  - Black Soil: $210\text{ mm/m}$
  - Loam: $150\text{ mm/m}$
  - Sandy Loam: $120\text{ mm/m}$
  - Sandy: $80\text{ mm/m}$

### Dataset Stratification
- Total Records: $3,000$ synthetic records generated across 8 canonical scenario distributions ($375$ records each):
  1. `canal_reduction`
  2. `sudden_rainfall`
  3. `normal_water`
  4. `high_urgency_farmer`
  5. `severe_shortage`
  6. `simultaneous_demand`
  7. `moderate_shortage`
  8. `flexible_farmer`
- All records carry explicit metadata: `SYNTHETIC DATA — All records generated algorithmically using FAO-56 ET0 * Kc * area method. No real farmer data.`

---

## 8. ML Pipeline

### Feature Engineering (`backend/app/ml/feature_engineering.py`)
- Dataset split: **70% Train** ($n=2,099$), **15% Validation** ($n=450$), **15% Test** ($n=451$) with fixed random seed $42$.
- **22 Feature Dimensions**:
  - Direct Numeric: `farm_area_hectares`, `et0_mm_per_day`, `kc_value`, `etc_mm_per_day`, `soil_whc_mm_per_m`, `preferred_start_hour`, `irrigation_window_hours`, `flexibility_score`, `urgency_score`, `crop_stress_index`, `temperature_celsius`, `humidity_percent`, `rainfall_mm`.
  - Categorical Encodings: `crop_type_encoded`, `soil_type_encoded`, `growth_stage_encoded`, `season_encoded`.
  - Interaction Terms: `area_x_etc`, `urgency_x_stress`, `et0_x_kc`, `rain_deficit`, `flexibility_window`.

### Persisted Artifacts (`backend/data/models/`)
- `rf_model.joblib`: Trained Random Forest Regressor
- `xgb_model.joblib`: Trained XGBoost Regressor
- `encoders.joblib`: Scikit-learn categorical preprocessors
- `evaluation_results.json`: Complete verified evaluation benchmark

---

## 9. Actual Model Metrics

Verified directly from the persistent benchmark artifact `backend/data/models/evaluation_results.json` on the held-out test split ($n = 451$):

| Model | Split | Sample Size ($n$) | MAE ($m^3/\text{day}$) | RMSE ($m^3/\text{day}$) | $R^2$ Score |
|---|---|---|---|---|---|
| **Random Forest** | Train | 2,099 | 7.1624 | 11.5208 | 0.9951 |
| **Random Forest** | Val | 450 | 17.7944 | 27.4387 | 0.9742 |
| **Random Forest** | **Test** | **451** | **17.4865** | **27.3761** | **0.9737** |
| **XGBoost** | Train | 2,099 | 9.3477 | 13.2354 | 0.9936 |
| **XGBoost** | Val | 450 | 18.3632 | 28.5315 | 0.9721 |
| **XGBoost** | **Test** | **451** | **17.8342** | **27.4243** | **0.9736** |

*Note: Training execution times were $\approx 0.28\text{ seconds}$ per model. Both algorithms demonstrate high fidelity to the underlying FAO-56 synthetic generation curves.*

---

## 10. Farmer Agent Architecture

Implemented in `backend/app/agents/`:
- **`FarmerAgent`**: Encapsulates farmer physical traits, crop sensitivity, stage criticality, urgency, and individual `FarmerPreferences`:
  - `minimum_water_m3`: FAO-56 survival threshold (crop wilting point limit).
  - `target_water_m3`: ML-predicted water requirement.
  - `maximum_water_m3`: Maximum intake capacity (preventing waterlogging).
  - Irrigation windows: Preferred (`preferred_start_hour` to `preferred_end_hour`) and Acceptable (`acceptable_start_hour` to `acceptable_end_hour`).
  - `flexibility`: Scalar $[0, 1]$ indicating willingness to concede volume or shift schedules.
- **`DigitalTwin`**: Represents stateful agent actors across negotiation rounds. Tracks transitions through states: `IDLE` $\rightarrow$ `PROPOSING` $\rightarrow$ `EVALUATING` $\rightarrow$ `CONCEDING` $\rightarrow$ `ACCEPTED` / `REJECTED` / `FAILED`.

---

## 11. Conflict Detection Engine

Implemented in `backend/app/conflict/detector.py`, the engine deterministically identifies five conflict categories:

1. **`RESOURCE_SHORTAGE`**: Triggered when aggregate predicted demand exceeds total canal availability:
   $$\text{Resource Gap} = \sum_{i=1}^n d_i - \text{available\_water} > 0$$
2. **`IRRIGATION_WINDOW_OVERLAP`**: Multiple farmers requesting water simultaneously within overlapping hours.
3. **`CANAL_CAPACITY_CONFLICT`**: Combined instantaneous flow rate exceeding the maximum canal discharge rate.
4. **`MINIMUM_REQUIREMENT_CONFLICT`**: Acute shortage where total survival minimums exceed canal supply:
   $$\sum_{i=1}^n \text{minimum\_water}_i > \text{available\_water}$$
5. **`HIGH_CROP_STRESS`**: Identified via the Crop-Stress Priority Score (CSPS):
   $$\text{CSPS}_i = \text{urgency}_i \times \text{crop\_sensitivity}_i \times \text{stage\_criticality}_i$$
   - Trigger condition: $\text{CSPS}_i > 0.49$
   - Key Reference Thresholds:
     - `HIGH_STRESS_URGENCY_THRESHOLD` = $0.70$
     - `HIGH_STRESS_SENSITIVITY_THRESHOLD` = $0.70$

### Severity Scale & Composite Scoring
- Shortage ratio $R = \frac{\text{Resource Gap}}{\sum d_i}$:
  - $R < 0.10 \implies \text{LOW}$
  - $0.10 \le R < 0.25 \implies \text{MEDIUM}$
  - $0.25 \le R < 0.50 \implies \text{HIGH}$
  - $R \ge 0.50 \implies \text{CRITICAL}$
- Composite Conflict Score:
  $$\text{Score} = 0.40 \cdot \text{shortage} + 0.20 \cdot \text{urgency} + 0.25 \cdot \text{overlap} + 0.15 \cdot \text{stress}$$

---

## 12. Mathematical Allocation Formulation

Implemented in `backend/app/allocation/lp_allocator.py` via **Google OR-Tools GLOP Linear Solver**.

### Decision Variables
- $x_i \ge 0$: Volume allocated to farmer $i$ ($m^3$).
- $p_i \ge 0$: Penalty auxiliary variable representing shortfall below the minimum requirement (activated when minimum requirements must be relaxed).

---

## 13. Allocation Constraints

### Hard Constraints (Never Violated)
1. **(H1) Non-negativity**:
   $$x_i \ge 0 \quad \forall i \in \{1, \dots, n\}$$
2. **(H2) Demand Ceiling**:
   $$x_i \le \text{maximum\_water}_i \quad \forall i \in \{1, \dots, n\}$$
3. **(H3) Total Water Availability Conservation**:
   $$\sum_{i=1}^n x_i \le \text{available\_water}$$

### Soft / Relaxable Minimum Survival Requirement (S1)
Under standard supply, the solver enforces $x_i \ge \text{minimum\_water}_i$. When $\sum \text{minimum\_water}_i > \text{available\_water}$, the problem is mathematically infeasible as a hard LP. The allocator transitions to `lp_relaxed` mode using the auxiliary penalty:
$$x_i + p_i \ge \text{minimum\_water}_i, \quad p_i \ge 0$$
where $p_i$ is heavily penalized in the objective function.

### Fallback Allocation Methods
1. `lp_optimal`: Standard LP solved with hard minimum constraints satisfied.
2. `lp_relaxed`: LP solved with soft minimum penalties due to severe physical shortage.
3. `proportional_fallback`: Proportional distribution $x_i = \text{available\_water} \times (d_i / \sum d_j)$ if solver numerical error occurs.
4. `empty`: Zero available water scenario.

---

## 14. Allocation Objective

$$\max \sum_{i=1}^n \left[ w_{\text{urg}} \cdot \text{urgency}_i \cdot \left(\frac{x_i}{d_i}\right) + w_{\text{cs}} \cdot \text{cs}_i \cdot \left(\frac{x_i}{d_i}\right) + w_{\text{unmet}} \cdot \left(\frac{x_i}{d_i}\right) - w_{\text{min}} \cdot \left(\frac{p_i}{d_i}\right) \right]$$

### Default Calibrated Weights
- **Urgency Weight ($w_{\text{urg}}$)**: $0.40$
- **Crop Sensitivity Weight ($w_{\text{cs}}$)**: $0.25$
- **Unmet Demand Fulfillment ($w_{\text{unmet}}$)**: $0.20$
- **Minimum Requirement Penalty ($w_{\text{min}}$)**: $0.15$

---

## 15. Fairness Calculation

Fairness is assessed via **Jain's Fairness Index**:
$$J(s_1, \dots, s_n) = \frac{\left(\sum_{i=1}^n s_i\right)^2}{n \sum_{i=1}^n s_i^2}$$
where $s_i = \text{clip}\left(\frac{x_i}{d_i}, 0, 1\right)$ represents farmer $i$'s demand satisfaction ratio.

### CRITICAL METHODOLOGICAL DISTINCTION
> **Jain's Fairness Index is calculated strictly POST-HOC.**  
> It is **NOT** part of the LP objective function.  
> Injecting Jain's Index into the objective would yield a non-linear, non-convex fractional programming problem incompatible with linear solvers like GLOP. The LP optimizes priority-weighted efficiency, after which Jain's Index is computed to transparently report distribution equity ($J \in [1/n, 1.0]$).

---

## 16. Negotiation Architecture

When conflicts exist, the multi-agent negotiation engine (`backend/app/negotiation/`) mediates between farmer digital twins:

```
FarmerAgent Initial Preferences
         │
         ▼
WaterAllocator (Initial LP Solve)
         │
         ▼
Per-Farmer Utility & BATNA Evaluation
         │
         ▼
Farmer Responses: ACCEPT / REQUEST_CHANGE / REJECT
         │
         ▼
Mediator Concession Calculation (Iterative adjustment of asks)
         │
         ▼
MANDATORY LP RE-OPTIMIZATION (WaterAllocator.solve())
         │
         ▼
Nash-Inspired Welfare Evaluation & Convergence Check
         │
         ▼
Final Validated Agreement
```

---

## 17. BATNA and Utility Formulation

### Multi-Factor Utility Function $U_i \in [0, 1]$
$$U_i = \text{norm}\left( w_1 S_w + w_2 S_t + w_3 S_u + w_4 S_m - w_5 S_p \cdot \text{cs}_i \right)$$
- $S_w = \min(1.0, x_i / d_i)$: Volumetric satisfaction.
- $S_t$: Timing satisfaction ($1.0$ if inside preferred window, $0.5$ if in acceptable window, $0.0$ if outside or unspecified).
- $S_u = 1.0 - \text{urgency}_i \cdot (1.0 - S_w)$: Urgency penalty for unmet volume.
- $S_m = \min(1.0, x_i / \text{minimum\_water}_i)$: Minimum survival fulfillment.
- $S_p = (1.0 - S_m)$: Crop stress penalty scaled by crop sensitivity $\text{cs}_i$.

### BATNA Definition
- Fallback Allocation: $a_{\text{BATNA}} = \text{minimum\_water\_requirement}_i$
- Fallback Utility: $U_{\text{BATNA}} = U_i(a_{\text{BATNA}}, \text{timing}=\text{None})$
- **BATNA Protection Rule**: If proposed allocation yields $U_i < U_{\text{BATNA}}$, the agent issues a `REJECT` with `is_batna_protected = True`.

### Response Thresholds
- **`ACCEPT`**: $U_i \ge 0.65$ **AND** $U_i \ge U_{\text{BATNA}} + 0.02$
- **`REQUEST_CHANGE`**: $0.35 \le U_i < 0.65$
- **`REJECT`**: $U_i < 0.35$ (or $U_i < U_{\text{BATNA}}$)

---

## 18. Concession Mechanism

For farmers issuing `REQUEST_CHANGE` or `REJECT`, the mediator computes concessions on their water ask:
$$\text{Available Margin} = \text{current\_ask}_i - \text{minimum\_water}_i$$
$$\text{Concession Ratio} = \text{flexibility}_i \times (1.0 - \text{urgency}_i) \times \text{scale}$$
$$\Delta x_i = \text{Available Margin} \times \text{clamp}(\text{Concession Ratio}, 0, 1)$$
$$\text{new\_ask}_i = \max(\text{minimum\_water}_i, \text{current\_ask}_i - \Delta x_i)$$

### Mathematical Guarantees
- A farmer's ask **NEVER** drops below their survival minimum (`minimum_water`).
- Zero flexibility ($\text{flexibility}=0$) guarantees zero concession.
- Maximum urgency ($\text{urgency}=1$) guarantees zero concession.

---

## 19. Nash-Inspired Objective

Surplus over BATNA for farmer $i$:
$$\text{surplus}_i = U_i(\text{allocation}) - U_{\text{BATNA}, i}$$

The joint negotiation outcome is evaluated using the log-surplus objective:
$$\Omega_{\text{Nash}} = \sum_{i=1}^n \log\left(\max(\text{surplus}_i, \epsilon)\right)$$
where $\epsilon = 10^{-6}$ (`min_surplus_floor`).

### RESEARCH ACCURACY DISCLAIMER
> **This is explicitly a "Nash-bargaining-inspired" heuristic, NOT a full axiomatic Nash Bargaining Solution (NBS).**  
> While classical NBS requires finding the theoretical maximum over a continuous convex agreement set under axiomatic conditions, AquaMediAI uses this log-sum formulation as a guidance metric to verify whether mediator concessions improve joint surplus without violating agent BATNAs.

---

## 20. Negotiation Termination

The iterative negotiation halts under four deterministic criteria:
1. **`AGREED`**: All participating farmers issue `ACCEPT`.
2. **`NO_FEASIBLE_IMPROVEMENT`**: Stagnation detected ($\Omega_{\text{Nash}}$ fails to improve for 2 consecutive rounds).
3. **`MAX_ROUNDS_REACHED`**: Session completes maximum configured rounds (`max_rounds` = 5) without unanimous acceptance.
4. **`FAILED`**: Unrecoverable runtime exception (returns verified fallback).

> **Invariance Rule**: Regardless of negotiation outcome, the mediator **always returns a physically valid allocation** verified through `WaterAllocator.solve()`. Unverified or physically infeasible allocations are never returned.

---

## 21. Explainability Architecture

Implemented in `backend/app/explainability/`:
- **Read-Only Guarantee**: The explainability layer inspects computational outputs from Phases 2–6 without modifying any allocations, utilities, or scores.
- **SHAP Feature Attributions**: Integrates TreeExplainer attributions to explain ML demand predictions relative to base evapotranspiration.
- **Deterministic Reason Codes**: Emitted only when exact numerical conditions are met:
  - `RESOURCE_SHORTAGE`: Total demand exceeds canal water.
  - `HIGH_URGENCY`: Urgency score $\ge 0.70$.
  - `HIGH_CROP_SENSITIVITY`: Sensitivity index $\ge 0.70$.
  - `MINIMUM_REQUIREMENT`: Minimum survival requirements were actively factored into allocation constraints.
  - `FULL_DEMAND_SATISFACTION`: Allocation fulfilled $100\%$ of predicted demand.
  - `UNMET_DEMAND`: Available water was insufficient to fulfill total request.
  - `BATNA_PROTECTED`: Farmer rejected proposal because utility was below fallback threshold.

---

## 22. FastAPI Architecture

Implemented in `backend/app/`:
- **Design Pattern**: Three-tier architecture (Pydantic Schemas $\rightarrow$ Thin Route Handlers $\rightarrow$ `ScenarioService` Orchestrator).
- **Determinism**: Supports fixed random seeds for academic reproducibility.
- **Error Handling**: Structured JSON error responses (`422` Validation Error, `503` Missing Model Artifact, `500` Pipeline Error).
- **CORS Support**: Configured for local development and production web clients.

---

## 23. Frontend Architecture

Implemented in `frontend/src/`:
- **Framework**: React 18 with TypeScript and Vite.
- **Routing (React Router v6)**:
  - `/` (Overview)
  - `/scenario` (Scenario Configuration)
  - `/predictions` (ML Demand Predictions)
  - `/conflicts` (Conflict Diagnostics)
  - `/allocation` (Water Allocation)
  - `/negotiation` (Multi-Agent Negotiation)
  - `/explainability` (System Explainability)
  - `/agreement` (Agreement Certificate)
  - `/debug` (Raw JSON Payload Inspection)
- **State Management**: React Context (`ScenarioContext`, `ViewModeContext`).
- **No Third-Party Bloat**: Built using standard Vanilla CSS / modern layout primitives and Recharts for interactive visualization.

---

## 24. Farmer View

A dedicated, accessible presentation mode tailored for non-technical farmers:
- **Zero Technical Jargon**: Eliminates references to "GLOP", "SHAP", "Nash surplus", "LP-optimal", or raw equations.
- **Intuitive Scenario Presets**: Simple, real-world options:
  - Slight Canal Shortage (10% deficit)
  - Normal Water Supply (Ample canal water)
  - Severe Drought (50% deficit)
  - Overlapping Schedules (Clashing irrigation hours)
- **Visual Feedback**: Clean water allocation cards, percentage gauges, volumetric figures ($m^3$), and human-readable badges.
- **Grounded Reason Explanations**:
  - *"💧 Minimum water need considered"* — The system considered the minimum water requirement while allocating the available water.
  - *"🌿 Crop is sensitive to water shortage"* — Allocation prioritized sensitive growth stages.
  - *"⚡ High urgency for irrigation"* — Urgent field conditions were prioritized.

---

## 25. Expert View

A comprehensive technical mode designed for agronomists, irrigation engineers, and AI evaluators:
- Exposes complete mathematical formulations across 7 structured tabs:
  1. **Technical Configuration**: Seed, model selector (XGBoost vs RF), canal overrides, API curl examples.
  2. **Demand Model & Feature Attribution**: Model $R^2$/MAE metrics, base value attributions, positive/negative SHAP bars.
  3. **Conflict Diagnostics**: Raw conflict classifications, CSPS formula breakdown, evidence dictionaries.
  4. **LP Optimization & Constraints**: Objective weights ($w_{\text{urg}}, w_{\text{cs}}, w_{\text{unmet}}, w_{\text{min}}$), constraint fulfillment audit (H1, H2, H3, S1), solver status.
  5. **Negotiation Diagnostics**: Utility trajectories, BATNA comparison tables, concession amounts, Log-Nash convergence curves.
  6. **Audit Trail & Explainability**: Machine reason codes, constraint status breakdowns, explanation dataclasses.
  7. **Raw System Payload**: Full, unparsed JSON payload (`/debug`).
- **Pedagogical Structure**: Every diagnostic card systematically explains:
  - **WHAT IS IT?**
  - **WHY DOES IT MATTER?**
  - **WHAT HAPPENS IF IT CHANGES?**

---

## 26. Localization

Complete internationalization (`frontend/src/i18n/translations.ts`) supporting three languages:
- **English (`en`)**
- **Hindi (`hi`)** — हिन्दी
- **Gujarati (`gu`)** — ગુજરાતી

### Coverage
- Navigation headers and sidebar items.
- Scenario names, descriptions, and situation cards.
- Conflict explanations and severity tags.
- Allocation terms, negotiation statuses, and agreement summaries.
- Farmer explainability reason codes and descriptions.
- Language preference is stored persistently in browser `localStorage`.

---

## 27. API Endpoints

| Method | Endpoint | Description | Request Body | Response Model |
|---|---|---|---|---|
| `GET` | `/health` | System liveness probe & DB status | None | `JSONResponse` |
| `GET` | `/api/v1/health` | Pipeline readiness & synthetic data disclaimer | None | `HealthResponse` |
| `POST` | `/api/v1/scenarios/run` | **Primary Endpoint**: Full end-to-end pipeline execution | `ScenarioRunRequest` | `ScenarioRunResponse` |
| `POST` | `/api/v1/predictions` | Single-farmer ML demand prediction | `PredictionRequest` | `PredictionResponse` |
| `POST` | `/api/v1/predictions/batch` | Batch ML water demand prediction | `PredictionBatchRequest` | `PredictionBatchResponse` |
| `POST` | `/api/v1/conflicts` | Detect conflicts on agent preferences | `ConflictRequest` | `ScenarioConflictReportResponse` |
| `POST` | `/api/v1/allocations` | OR-Tools GLOP water allocation | `AllocationRequest` | `AllocationResponse` |
| `POST` | `/api/v1/negotiations` | Execute multi-agent mediation session | `NegotiationRequest` | `NegotiationResponse` |
| `GET` | `/openapi.json` | OpenAPI 3.1 specification | None | `JSON` |
| `GET` | `/docs` | Interactive Swagger UI documentation | None | HTML |

---

## 28. Testing Status

The AquaMediAI system is covered by comprehensive automated test suites across both backend and frontend.

### Execution Commands
- **Backend Test Suite**:
  ```bash
  cd backend
  .\.venv\Scripts\pytest.exe -q
  ```
- **Frontend Test Suite**:
  ```bash
  cd frontend
  npm run test
  ```
- **Frontend Production Build Verification**:
  ```bash
  cd frontend
  npm run build
  ```

---

## 29. Current Verified Test Counts

### Backend Tests: 704 / 704 PASSING (100%)
- `tests/test_data_generator.py`: **62 tests** (Phase 1)
- `tests/test_ml_pipeline.py`: **64 tests** (Phase 2)
- `tests/test_farmer_agents.py`: **96 tests** (Phase 3)
- `tests/test_conflict_detector.py`: **88 tests** (Phase 4)
- `tests/test_lp_allocator.py`: **86 tests** (Phase 5)
- `tests/test_negotiation.py`: **123 tests** (Phase 6)
- `tests/test_explainability.py`: **113 tests** (Phase 7)
- `tests/test_api.py`: **72 tests** (Phase 8)

### Frontend Tests: 53 / 53 PASSING (100%)
- `src/tests/api.test.ts`: **5 tests**
- `src/tests/Components.test.tsx`: **9 tests**
- `src/tests/ScenarioPages.test.tsx`: **8 tests**
- `src/tests/Explainability.test.tsx`: **14 tests**
- `src/tests/App.test.tsx`: **5 tests**
- `src/tests/ViewMode.test.tsx`: **12 tests**

### Frontend Production Build: PASS
- `tsc -b && vite build` completes cleanly with **0 errors**.

---

## 30. Known Limitations

1. **Synthetic Data Paradigm**: All agronomic data is generated using FAO-56 Penman-Monteith formulas. The system has not been evaluated on empirical telemetry from real-world farm sensors or irrigation canal gates.
2. **Single-Period Allocation Horizon**: The optimization model solves a single-turn allocation window (daily / irrigation turn). It does not simulate continuous multi-day reservoir hydrodynamic routing or canal travel-time lags.
3. **Post-Hoc Fairness**: Jain's Fairness Index is measured after optimization; it is not enforced directly as a hard LP constraint.
4. **Heuristic Negotiation Convergence**: The negotiation objective is a Nash-inspired log-surplus metric rather than an axiomatic, closed-form Nash Bargaining Solution.
5. **Simulated Agent Behavior**: Digital twins concede based on deterministic mathematical curves rather than complex human emotional or political dynamics.
6. **No Real-Time Hardware Control**: The system outputs an advisory allocation agreement; it does not interface with physical sluice gate actuators or SCADA systems.

---

## 31. Future Scope

1. **Empirical Field Integration**: Connecting the pipeline to real-world Internet of Things (IoT) soil moisture probes and satellite-derived evapotranspiration feeds (e.g., OpenET, Sentinel-2).
2. **Multi-Period Hydrodynamic Routing**: Extending the LP/MIP formulation into a rolling-horizon model incorporating canal transit delays and reservoir storage capacity.
3. **Mobile Progressive Web App (PWA)**: Packaging the Farmer View as an offline-first PWA suitable for rural areas with low network bandwidth.
4. **Field Pilots with Water User Associations (WUAs)**: Conducting participatory research with irrigation officers and farming communities to assess human trust and usability.

---

## 32. Final Project Status

The AquaMediAI software development lifecycle is **COMPLETE**.

- **All 9 Development Phases**: COMPLETE & VERIFIED.
- **Backend Regression Suite**: 704 / 704 PASSING.
- **Frontend Regression Suite**: 53 / 53 PASSING.
- **Frontend Production Build**: PASSING.
- **Documentation**: Comprehensive and frozen.

**STATE: PROJECT DOCUMENTATION FREEZE COMPLETE**
