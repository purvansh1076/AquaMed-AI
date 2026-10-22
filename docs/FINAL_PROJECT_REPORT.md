# AquaMediAI: An Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System for Farmers

**A Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of**  
**Bachelor of Technology (B.Tech) in Computer Science and Engineering**  
**Academic Level**: Third Year (TY) B.Tech CSE  
**Domain**: Artificial Intelligence / Machine Learning / Computational Optimization  
**Project Status**: Academic Prototype & Demonstrated Proof-of-Concept  
**Implementation Baseline**: Frozen Repository State (Backend: 704/704 Tests Passing | Frontend: 53/53 Tests Passing | Build: PASS)  

---

## EXECUTIVE SUMMARY

Water scarcity in communal agricultural irrigation commands routinely induces contentious resource disputes among farmers. Upstream cultivators frequently divert disproportionate flow volumes, subjecting tail-reach farmers to acute water deficits, delayed cultivation, and economic vulnerability. Conventional institutional mechanisms for resolving such conflicts—including rigid rotational quotas (such as traditional Warabandi schedules) and manual bureaucratic adjudication—suffer from administrative opacity, protracted delays, an absence of real-time agronomic sensitivity, and zero algorithmic explainability.

This report presents **AquaMediAI**, an end-to-end, explainable, multi-agent computational prototype designed to mediate agricultural water-sharing disputes. Developed as a rigorously validated proof-of-concept, AquaMediAI integrates six interconnected computational tiers:
1. **Agronomic Data Synthesis**: Programmatic synthesis of 3,000 farm records adhering strictly to the Food and Agriculture Organization (FAO-56) Penman-Monteith crop evapotranspiration framework across 8 distinct conflict distributions.
2. **Machine Learning Water Demand Forecasting**: High-fidelity supervised regression using XGBoost ($R^2 = 0.9736$, $\text{MAE} = 17.8342\text{ m}^3/\text{day}$) and Random Forest ($R^2 = 0.9737$, $\text{MAE} = 17.4865\text{ m}^3/\text{day}$) evaluated on a held-out test partition ($n = 451$).
3. **Farmer Digital Twins**: Autonomous software agents encapsulating crop-stage sensitivity, hourly window preferences, multi-factor utility curves, and strict Best Alternative To a Negotiated Agreement (BATNA) fallback protections.
4. **Deterministic Conflict Detection**: Algorithmic detection of volumetric resource shortages, channel capacity exceedances, irrigation schedule clashes, survival requirement deficits, and acute agronomic risks via a Crop-Stress Priority Score ($\text{CSPS} > 0.49$).
5. **Constrained Linear Optimization**: Formulated via Google OR-Tools GLOP solver, enforcing hard physical conservation bounds ($\sum x_i \le \text{available}$) while providing relaxable soft penalty formulations ($p_i$) when total survival minimums exceed canal capacity. Post-hoc equity is independently audited using Jain’s Fairness Index.
6. **Multi-Agent Mediated Bargaining**: Iterative automated negotiation evaluating farmer satisfaction, applying mathematically bounded concession curves, and executing **mandatory LP re-optimization** at every cycle to optimize a Nash-inspired joint log-surplus objective.

The computational pipeline is exposed via high-performance FastAPI REST endpoints and rendered through a dual-mode React 18/TypeScript web interface offering a plain-language **Farmer View** (localized in English, Hindi, and Gujarati with zero technical jargon) alongside an in-depth **Expert View** detailing mathematical attributions and SHAP feature importances. The complete system is verified by 704 passing backend pytest cases and 53 passing frontend vitest cases. All evaluations are explicitly bounded by the synthetic nature of the dataset and represent an academic prototype rather than a live empirical deployment.

---

## TABLE OF CONTENTS

- [Chapter 1 — Introduction](#chapter-1--introduction)
- [Chapter 2 — Literature Survey](#chapter-2--literature-survey)
- [Chapter 3 — System Analysis](#chapter-3--system-analysis)
- [Chapter 4 — System Architecture](#chapter-4--system-architecture)
- [Chapter 5 — Dataset and Data Preparation](#chapter-5--dataset-and-data-preparation)
- [Chapter 6 — Machine Learning Model](#chapter-6--machine-learning-model)
- [Chapter 7 — Farmer Digital Agents](#chapter-7--farmer-digital-agents)
- [Chapter 8 — Conflict Detection](#chapter-8--conflict-detection)
- [Chapter 9 — Water Allocation Optimization](#chapter-9--water-allocation-optimization)
- [Chapter 10 — Multi-Agent Negotiation](#chapter-10--multi-agent-negotiation)
- [Chapter 11 — Explainable AI](#chapter-11--explainable-ai)
- [Chapter 12 — API and System Integration](#chapter-12--api-and-system-integration)
- [Chapter 13 — Frontend Architecture](#chapter-13--frontend-architecture)
- [Chapter 14 — Testing and Validation](#chapter-14--testing-and-validation)
- [Chapter 15 — Results and Discussion](#chapter-15--results-and-discussion)
- [Chapter 16 — Limitations](#chapter-16--limitations)
- [Chapter 17 — Future Scope](#chapter-17--future-scope)
- [Chapter 18 — Conclusion](#chapter-18--conclusion)
- [Appendices](#appendices)

---

## CHAPTER 1 — INTRODUCTION

### 1.1 Background
Canal irrigation infrastructure constitutes the lifeblood of agricultural production across arid and semi-arid agrarian economies. In regions such as South Asia, surface water diverted from barrages and reservoirs is distributed through hierarchical gravity-fed canal networks comprising main channels, branch canals, distributaries, and watercourses. Historically, rotational water allocation schemes—most notably the *Warabandi* system—were instituted to allocate canal flow based on land area proportionality and fixed temporal rotations. 

However, escalating climate variability, protracted meteorological droughts, and shifting cropping patterns have introduced severe volatility into available surface supplies. Consequently, standard volumetric allotments fail to synchronize with dynamic, soil-specific crop water requirements, producing recurrent supply-demand deficits across irrigation commands.

### 1.2 Problem Context
The core spatial pathology in rotational canal irrigation is the **head-reach versus tail-reach asymmetric access dilemma**. Farmers positioned at the head of a distributary enjoy physical proximity to the gate, enabling them to divert canal flow at higher velocities and greater durations than their official allowance. Conversely, farmers situated at the tail reach frequently receive erratic discharges, reduced volumes, or no water at all. 

This spatial inequality is compounded by conflicting operational schedules. When adjacent farmers simultaneously require water during peak daylight evaporation hours, branch channel hydraulic capacities are exceeded, resulting in channel overtopping or severe velocity drops. When informal negotiations fail, farmers resort to contentious confrontation, physical canal breaching, illegal siphon pumping, or protracted civil litigation.

### 1.3 Problem Statement
Traditional administrative dispute resolution mechanisms are ill-equipped to manage modern agricultural water disputes. Adjudication by local irrigation personnel (*patwaris* or executive engineers) is predominantly manual, bureaucratic, and slow—often requiring weeks to reach decisions during which crops suffer irreversible moisture stress. Furthermore, these administrative decisions lack quantitative agronomic rigor: quotas are computed without accounting for crop phenological growth stages, daily reference evapotranspiration, or soil water retention. 

Most critically, centralized quotas operate as **unexplainable black-boxes**. Farmers are provided neither the mathematical rationale nor transparent evidence justifying why their water allocation was curtailed. There exists an acute need for an automated, objective, and explainable computational dispute mediation system capable of reconciling individual farmer crop requirements with macroscopic canal hydraulic constraints.

### 1.4 Motivation
Recent advancements in applied Artificial Intelligence present compelling paradigms to address these challenges:
1. **Supervised Machine Learning** can predict daily volumetric water requirements with high precision using agronomic and meteorological indicators.
2. **Multi-Agent Systems (MAS)** can model individual farmers as autonomous computational agents possessing distinct utility curves, schedule preferences, and reservation fallbacks.
3. **Operations Research (Linear Programming)** can enforce strict mass conservation and physical channel bounds, guaranteeing that recommended quotas remain feasible.
4. **Explainable AI (XAI)** can deconstruct complex algorithmic outputs into verifiable feature attributions and deterministic reason codes.

Bridging these distinct disciplines into a unified architecture provides the primary scientific motivation for AquaMediAI.

### 1.5 Need for the Proposed System
Existing computerized irrigation solutions generally fall into two extremes: either centralized optimal control models that ignore farmer autonomy, or unconstrained game-theoretic simulations that generate physically unachievable allocations. AquaMediAI is needed to bridge this operational divide by combining:
- Autonomous agent utility modeling (honoring farmer reservation thresholds),
- Hard mathematical optimization (guaranteeing physical feasibility),
- Automated concession-based bargaining (fostering compromise),
- Plain-language regional localization (establishing user trust).

### 1.6 Aim
To design, implement, and validate an explainable, multi-agent computational prototype that predicts farm-level crop water requirements, detects distribution conflicts, optimizes constrained allocations, and mediates water-sharing agreements among simulated farmers.

### 1.7 Objectives
1. Synthesize an agronomically consistent dataset based on FAO-56 Penman-Monteith physics across diverse soil textures, growth stages, and drought scenarios.
2. Train and validate supervised regression models (XGBoost, Random Forest) to predict daily farm water requirements ($m^3/\text{day}$).
3. Implement autonomous `FarmerAgent` and `DigitalTwin` classes encapsulating preferences, multi-factor utility functions, and BATNA reservation thresholds.
4. Develop a deterministic conflict engine to detect shortages, temporal overlaps, capacity violations, and crop stress risks.
5. Formulate a multi-criteria Linear Program using Google OR-Tools GLOP enforcing physical conservation while accommodating relaxable minimum survival penalties.
6. Design an automated mediator executing mathematical concession formulas and mandatory LP re-optimizations evaluated against a Nash-inspired joint objective.
7. Construct a read-only explainability layer generating SHAP feature attributions and deterministic reason codes.
8. Deliver a responsive React 18/TypeScript web interface featuring dual modes (Farmer View vs Expert View) localized in English, Hindi, and Gujarati.

### 1.8 Scope
- **In Scope**: Mathematical modeling, synthetic agronomic simulation, single-turn daily allocation, deterministic conflict detection, LP optimization, simulated multi-agent bargaining, SHAP/reason-code explainability, web dashboard.
- **Out of Scope**: Physical hardware actuation (sluice gate telemetry), live satellite remote sensing, multi-day reservoir hydrodynamic routing, legal court adjudication, voice/speech processing.

### 1.9 Contributions
- An integrated software architecture harmonizing predictive ML, autonomous agents, and linear programming into a closed-loop mediation workflow.
- An invariant **mandatory LP re-optimization mechanism** ensuring that every mediated concession remains strictly within physical conservation bounds.
- A dual-mode presentation framework translating complex linear programming constraints into actionable, regional-language narratives for non-technical users.

### 1.10 Organization of Report
The remainder of this report is organized as follows: Chapter 2 reviews relevant academic literature; Chapter 3 details system analysis and requirements; Chapter 4 presents the complete system architecture; Chapter 5 describes data synthesis; Chapter 6 evaluates the ML demand models; Chapter 7 outlines the farmer digital agents; Chapter 8 details conflict detection; Chapter 9 formalizes the linear allocation model; Chapter 10 details multi-agent negotiation; Chapter 11 covers explainable AI; Chapter 12 documents the FastAPI backend; Chapter 13 outlines the React frontend; Chapter 14 presents comprehensive testing and verification; Chapter 15 analyzes results; Chapter 16 discusses system limitations; Chapter 17 outlines future research scope; and Chapter 18 concludes the report.

---

## CHAPTER 2 — LITERATURE SURVEY

### 2.1 AI-Based Agricultural Water Management
The application of artificial intelligence in agricultural water management has evolved from rule-based expert systems to data-driven predictive architectures `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`. Modern computational irrigation models predominantly leverage sensor telemetry to optimize water application depths. However, existing literature focuses primarily on on-farm precision irrigation (e.g., automated drip valves) rather than communal canal dispute mediation `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`.

### 2.2 Water Demand Prediction
Accurate estimation of crop water demand forms the cornerstone of sound allocation. The standard benchmark established by the Food and Agriculture Organization is the FAO-56 Penman-Monteith method `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Allen et al., 1998]`. Recent studies have demonstrated that gradient boosted trees (XGBoost) and ensemble random forests can approximate non-linear agricultural demand with high fidelity when trained on meteorological and phenological inputs `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`.

### 2.3 Optimization-Based Water Allocation
Operations research has extensively addressed water resources allocation using Linear Programming (LP), Non-Linear Programming (NLP), and Genetic Algorithms `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`. Google OR-Tools GLOP solver provides robust simplex implementations for large-scale continuous linear programs `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`. A known limitation in classical allocation optimization is the treatment of human farmers as passive, compliant entities rather than self-interested decision-makers `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`.

### 2.4 Multi-Agent Systems in Common-Pool Resources
Elinor Ostrom’s pioneering principles on governing common-pool resources emphasize that decentralized, rule-governed user monitoring frequently outperforms top-down administrative quotas `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Ostrom, 1990]`. Multi-Agent Systems (MAS) provide a computational paradigm to simulate autonomous, heterogenous actors competing for finite commons `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`.

### 2.5 Automated Negotiation and Conflict Resolution
Automated negotiation protocols establish mathematical foundations for agent bargaining. Rooted in cooperative game theory, Nash Bargaining establishes axioms for equitable surplus distribution `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Nash, 1950]`. Practical automated mediation relies on monotonic concession protocols and utility reservation thresholds, commonly termed the Best Alternative To a Negotiated Agreement `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Raiffa, 1982]`.

### 2.6 Explainable AI in High-Stakes Domains
Complex machine learning models often operate as opaque predictors. The SHAP (Shapley Additive exPlanations) framework, based on cooperative game theory, provides local feature importance attributions by calculating marginal contributions across all feature coalitions `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Lundberg & Lee, 2017]`. In agricultural and legal domains, explainability is essential to establish trust among stakeholders `[CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]`.

### 2.7 Existing System Limitations
1. **Centralized Rigidity**: Traditional irrigation administration enforces static schedules ignoring micro-climatic stress.
2. **Lack of Feasibility Safeguards**: Pure multi-agent bargaining frameworks often negotiate concessions that violate physical canal hydraulic capacities.
3. **Black-Box Opacity**: Predictive AI models fail to communicate reasoning to non-technical farming communities.

### 2.8 Research Gap
There exists an unaddressed research gap: the absence of an open, verifiable system coupling predictive ML demand estimation, autonomous agent modeling, physical LP optimization, and automated mediated negotiation with an explicit explainability layer.

### 2.9 Proposed Research Direction
AquaMediAI directly addresses this gap by creating an integrated pipeline where ML-predicted demands feed into autonomous digital twins, which are balanced by an OR-Tools linear solver and refined through mediated bargaining with guaranteed physical feasibility.

---

## CHAPTER 3 — SYSTEM ANALYSIS

### 3.1 Existing System
The prevailing canal water allocation mechanism relies upon historical water rights and rotation rosters administered by government irrigation departments. Water turns are determined by land area rather than actual crop water consumption. When supply deficits occur, adjustments are made informally or through bureaucratic appeals.

### 3.2 Limitations of Existing Approaches
- **Inflexible Schedules**: Fixed rotations prevent farmers from altering irrigation windows during critical growth phases.
- **Protracted Dispute Resolution**: Formal disputes take months to adjudicate, during which unwatered crops fail.
- **Asymmetric Transparency**: Upstream farmers have physical control; downstream farmers lack data to challenge unfair diversions.

### 3.3 Proposed System
AquaMediAI introduces an automated software-driven mediation workflow that accepts environmental and agronomic parameters, calculates true crop demands, detects physical and scheduling conflicts, generates an optimal baseline allocation, mediates concessions, and explains every outcome in regional languages.

### 3.4 Functional Requirements
- **FR1 (Demand Forecasting)**: Predict daily volumetric demand ($m^3/\text{day}$) from 22 agronomic features.
- **FR2 (Agent Parameterization)**: Initialize digital twin agents with utility functions, hourly windows, and BATNA.
- **FR3 (Conflict Detection)**: Identify shortages, channel capacity exceedances, window overlaps, and acute crop risks.
- **FR4 (Optimal Allocation)**: Compute allocations via GLOP LP respecting non-negativity and total water conservation.
- **FR5 (Mediated Bargaining)**: Execute up to 5 rounds of concession calculations with mandatory LP re-solves.
- **FR6 (Post-Hoc Auditing)**: Compute Jain’s Fairness Index for every round.
- **FR7 (Explanation Generation)**: Generate SHAP attributions and deterministic reason codes.
- **FR8 (Dual Presentation)**: Deliver responsive Farmer and Expert views localized in English, Hindi, and Gujarati.

### 3.5 Non-Functional Requirements
- **NFR1 (Determinism)**: Identical inputs and seeds must produce identical allocations and explanations.
- **NFR2 (Physical Validity)**: Allocations must never violate $\sum x_i \le \text{available\_water}$.
- **NFR3 (Execution Latency)**: Complete end-to-end pipeline execution within 2.5 seconds.
- **NFR4 (Zero External AI Runtime Costs)**: All models and rules run locally without paid proprietary APIs.
- **NFR5 (Graceful Infeasibility Handling)**: Automated relaxation fallback when total minimums exceed supply.

### 3.6 User Roles
- **Farmer User**: Accesses Farmer View; reviews plain-language water allocations, simple situation cards, and regional explanations.
- **Agronomist / Irrigation Officer**: Accesses Expert View; inspects solver statuses, mathematical attributions, and audit logs.

### 3.7 Inputs and Outputs
- **Inputs**: Available canal water ($m^3$), canal flow capacity ($m^3/\text{hr}$), number of farmers, random seed, and farm attributes (crop, stage, area, soil, preferred/acceptable hours, flexibility, urgency).
- **Outputs**: Allocation vector ($x_1, \dots, x_n$ in $m^3$), agreement status, utilities, BATNA values, Jain fairness score, SHAP values, deterministic reason codes, and bilingual audit logs.

### 3.8 Constraints and Assumptions
- **Constraints**: Single-turn decision interval; synthetic agronomic data baseline.
- **Assumptions**: Farmers report accurate crop categories and acreages; minimum water requirement represents survival wilting threshold.

### 3.9 Feasibility
- **Technical**: Implemented with proven open-source technologies (Python 3.12, FastAPI, OR-Tools, React 18, Vite).
- **Economic**: Zero proprietary software licenses or external API costs.
- **Operational**: Tailored regional Farmer View ensures usability for non-technical users.

---

## CHAPTER 4 — SYSTEM ARCHITECTURE

```
[FIGURE 4.1 HERE — HIGH-LEVEL SYSTEM ARCHITECTURE]
Description: Displays end-to-end component flow from Synthetic Data Layer to ML Predictor, Digital Twins, Conflict Engine, LP Solver, Mediator, Explainability Layer, and React Frontend.
```

### 4.1 Architecture Overview
AquaMediAI is architected as an asynchronous, modular computational pipeline comprising four distinct functional tiers:
1. **Agronomic Data and ML Tier**
2. **Computational Engine Tier**
3. **Mediation and Explainability Tier**
4. **API and Presentation Tier**

### 4.2 Agronomic Data and ML Tier
Responsible for data synthesis and predictive demand modeling. Synthetic environmental records are preprocessed through feature engineering pipelines into 22-dimensional feature tensors. Persisted model artifacts (`xgb_model.joblib`, `rf_model.joblib`, `encoders.joblib`) execute sub-millisecond demand inference accompanied by SHAP TreeExplainer local attributions.

### 4.3 Computational Engine Tier
Comprises the `FarmerAgent` factory, the deterministic `ConflictDetector`, and the OR-Tools `WaterAllocator`. This tier converts predicted demands and farmer preferences into formal constraint matrices, evaluating resource gaps and generating mathematically sound baseline allocations.

### 4.4 Mediation and Explainability Tier
Orchestrates multi-agent bargaining via `NegotiationEngine` and `Mediator`. It applies concession curves to dissatisfied agents, submits candidate asks to **mandatory LP re-optimization**, evaluates a Nash-inspired joint surplus objective, and formats audit trails into immutable explanation dataclasses.

### 4.5 API and Presentation Tier
Exposes the pipeline via FastAPI REST endpoints and renders the interactive React 18 dashboard. Communication is mediated through typed JSON contracts mirroring backend Pydantic models.

```
[FIGURE 4.2 HERE — END-TO-END DATA FLOW DIAGRAM]
Description: Traces the transformation of input JSON parameters into a 22-feature vector, predicted demand, conflict reports, LP simplex tableau, negotiation concessions, and localized JSON responses.
```

```
[FIGURE 4.3 HERE — FASTAPI BACKEND ARCHITECTURE]
Description: Illustrates the relationship between FastAPI route handlers, ScenarioService orchestrator, domain modules (agents, conflict, allocation, negotiation, explainability), and filesystem model artifacts.
```

```
[FIGURE 4.4 HERE — REACT FRONTEND ARCHITECTURE]
Description: Displays React component hierarchy, React Router v6 routing, ScenarioContext and ViewModeContext providers, Recharts visualizers, and bilingual localization dictionaries.
```

```
[FIGURE 4.5 HERE — AI/ML AND OPTIMIZATION COUPLING]
Description: Conceptual diagram highlighting the boundary where machine learning finishes (predicting water demand) and where operations research begins (solving allocation under hard physical bounds).
```

---

## CHAPTER 5 — DATASET AND DATA PREPARATION

### 5.1 Dataset Generation & 5.2 Synthetic Rationale
Because empirical canal command records containing simultaneous weather telemetry, soil moisture measurements, hourly scheduling desires, and dispute negotiation records are unavailable in the public domain, a programmatic dataset generator was developed ([`backend/app/ml/data_generator.py`](../backend/app/ml/data_generator.py)).

### 5.3–5.6 Agronomic Physics Formulations
The generator simulates agricultural physics using the **FAO-56 Irrigation and Drainage methodology**:
1. **Reference Evapotranspiration ($ET_0$)**: Daily atmospheric evaporative demand ($mm/\text{day}$).
2. **Crop Evapotranspiration ($ET_c$)**:
   $$ET_c = ET_0 \times K_c$$
   where $K_c$ is the crop coefficient determined by crop type and phenological growth stage.
3. **Volumetric Daily Water Demand**:
   $$\text{Demand } (m^3) = \frac{ET_c \times \text{Farm Area } (\text{ha}) \times 10}{E_{\text{eff}}}$$
   where $E_{\text{eff}} \approx 0.70$ reflects application efficiency.

### 5.7 Scenario Distribution Breakdown
The dataset comprises **3,000 synthetic records** evenly divided across 8 operational scenarios (375 samples each):
1. `canal_reduction`: Upstream intake curtailed by 25–40%.
2. `sudden_rainfall`: Precipitation event (15–45 mm) reducing net irrigation demand.
3. `normal_water`: Ample canal flow meeting full aggregate demand.
4. `high_urgency_farmer`: High crop stress on sensitive crops requiring priority flow.
5. `severe_shortage`: Severe drought where canal water is less than combined survival minimums.
6. `simultaneous_demand`: Clashing preferred irrigation hours among multiple farmers.
7. `moderate_shortage`: Deficit of 15–25% requiring moderate concessions.
8. `flexible_farmer`: Farmers exhibiting high flexibility ($>0.70$) facilitating compromise.

### 5.8 Feature Engineering & 5.9 Feature Dictionary
The pipeline constructs **22 feature dimensions**:

#### Table 5.1 — Complete 22-Dimensional Feature Dictionary
| Feature Name | Description | Data Type | Agronomic Role |
|---|---|---|---|
| `farm_area_hectares` | Physical cultivable farm area | Float (0.5 – 10.0) | Scale determinant |
| `et0_mm_per_day` | Atmospheric evapotranspiration | Float (2.0 – 9.0) | Climate driver |
| `kc_value` | Phenological crop factor | Float (0.3 – 1.25) | Crop water intensity |
| `etc_mm_per_day` | Potential crop evapotranspiration | Float | Base requirement ($ET_0 \times K_c$) |
| `soil_whc_mm_per_m` | Soil water holding capacity | Float (80 – 210) | Root zone moisture buffer |
| `preferred_start_hour` | Ideal irrigation start time | Integer (0 – 23) | Temporal scheduling |
| `irrigation_window_hours`| Duration of requested irrigation | Integer (1 – 12) | Flow intake duration |
| `flexibility_score` | Farmer willingness to concede | Float [0, 1] | Behavioral parameter |
| `urgency_score` | Agronomic water necessity | Float [0, 1] | Allocation priority |
| `crop_stress_index` | Soil moisture deficit score | Float [0, 1] | Crop failure risk |
| `temperature_celsius` | Ambient daytime temperature | Float (15 – 45) | Thermal evaporative driver |
| `humidity_percent` | Relative ambient humidity | Float (15 – 95) | Vapor pressure deficit factor |
| `rainfall_mm` | Daily precipitation | Float (0 – 100) | Natural moisture offset |
| `crop_type_encoded` | Encoded crop category (8 crops) | Categorical (0 – 7) | Biological species identity |
| `soil_type_encoded` | Encoded soil texture (5 soils) | Categorical (0 – 4) | Infiltration and retention |
| `growth_stage_encoded` | Encoded stage (5 growth phases) | Categorical (0 – 4) | Sensitivity vulnerability |
| `season_encoded` | Kharif, Rabi, or Zaid | Categorical (0 – 2) | Seasonal baseline |
| `area_x_etc` | Farm area $\times ET_c$ | Float | Non-linear interaction term |
| `urgency_x_stress` | Urgency $\times$ Crop Stress Index | Float | Compound agronomic risk |
| `et0_x_kc` | Interaction product $ET_0 \times K_c$ | Float | Pure crop transpiration |
| `rain_deficit` | $\max(0, ET_c - \text{rainfall})$ | Float | Net irrigation deficit |
| `flexibility_window` | Flexibility $\times$ Window Hours | Float | Schedule compromise capacity |

### 5.10 Target Variable
`water_demand_m3`: Continuous positive float representing daily required volume ($m^3/\text{day}$).

### 5.11 Train / Validation / Test Split
Using a deterministic seed of 42:
- **Training Set**: 70% ($n = 2,099$)
- **Validation Set**: 15% ($n = 450$)
- **Held-Out Test Set**: 15% ($n = 451$)

### 5.12 Dataset Limitations
Records are synthesized using deterministic equations augmented with gaussian perturbations. They do not capture unforeseen anomalies such as unmetered canal bank breaches or erratic siltation.

---

## CHAPTER 6 — MACHINE LEARNING MODEL

### 6.1–6.4 ML Problem Definition & Pipeline
Formulated as supervised regression mapping feature vectors $\mathbf{x} \in \mathbb{R}^{22}$ to continuous water demand $\hat{d} \in \mathbb{R}^+$. Categorical variables are preprocessed via Scikit-Learn `OrdinalEncoder`.

### 6.5 Random Forest & 6.6 XGBoost Models
- **Random Forest**: 100 decision trees, squared error criterion, minimum samples split = 2.
- **XGBoost**: Gradient boosted trees, `hist` tree method, learning rate = 0.05, max depth = 6, objective = `reg:squarederror`.

### 6.7 Model Evaluation Benchmarks
Verified directly against [`backend/data/models/evaluation_results.json`](../backend/data/models/evaluation_results.json) on the held-out test split ($n = 451$):

#### Table 6.1 — Model Evaluation Benchmarks (Held-out Test Set, $n = 451$)
| Model | MAE ($m^3/\text{day}$) | RMSE ($m^3/\text{day}$) | $R^2$ Score | Training Time (s) | Model Artifact |
|---|---|---|---|---|---|
| **Random Forest** | **17.4865** | **27.3761** | **0.9737** | 0.2753 | `rf_model.joblib` |
| **XGBoost** | **17.8342** | **27.4243** | **0.9736** | 0.2820 | `xgb_model.joblib` |

```
[FIGURE 6.1 HERE — ACTUAL VS PREDICTED WATER DEMAND SCATTER PLOT]
Description: Scatter plot of true synthetic demand versus model predictions across the 451 test samples, demonstrating tight clustering along the 45-degree identity line.
```

### 6.9 SHAP Feature Importance
TreeExplainer computes additive attributions $\phi_j$. Features `area_x_etc`, `farm_area_hectares`, and `etc_mm_per_day` account for over 80% of aggregate feature importance.

```
[FIGURE 6.2 HERE — GLOBAL SHAP FEATURE IMPORTANCE BAR CHART]
Description: Horizontal bar chart illustrating the top 10 features ranked by mean absolute SHAP value, showing the dominance of acreage and evapotranspiration interaction terms.
```

### 6.10 Model Selection & 6.11 ML Limitations
Both algorithms achieve equivalent accuracy ($R^2 > 0.973$). XGBoost is designated as the primary model due to compact memory footprint and serialization speed. Crucially, high performance reflects consistency with underlying synthetic FAO-56 formulas rather than empirical field truth.

```
ALGORITHM 1: MACHINE LEARNING WATER DEMAND PREDICTION
Input : 22-dimensional feature vector x
Output: Predicted water demand d_hat (m3/day), SHAP values phi

1 Load trained model M and encoders from disk;
2 x_encoded = ApplyEncoders(x);
3 d_hat = M.predict(x_encoded);
4 d_hat = max(0.0, d_hat); // Enforce non-negativity
5 explainer = TreeExplainer(M);
6 phi = explainer.shap_values(x_encoded);
7 Return (d_hat, phi);
```

---

## CHAPTER 7 — FARMER DIGITAL AGENTS

### 7.1–7.2 FarmerAgent & Preferences
Implemented in [`backend/app/agents/farmer_agent.py`](../backend/app/agents/farmer_agent.py):
- Parameters: `farmer_id`, `crop`, `farm_area`, `growth_stage`, `crop_sensitivity`, `stage_criticality`, `urgency`.
- Preferences (`FarmerPreferences`):
  - `minimum_water_m3`: Strict survival limit.
  - `target_water_m3`: Predicted demand $\hat{d}_i$.
  - `maximum_water_m3`: Waterlogging threshold ($1.2 \times \hat{d}_i$).
  - Preferred window: $[h_{\text{ps}}, h_{\text{pe}}]$.
  - Acceptable window: $[h_{\text{as}}, h_{\text{ae}}]$.
  - `flexibility`: Scalar $\in [0, 1]$.

### 7.3 Multi-Factor Utility Function ($U_i$)
Implemented in [`backend/app/agents/utility.py`](../backend/app/agents/utility.py):
$$U_i = \text{Normalize}\left( w_1 S_w + w_2 S_t + w_3 S_u + w_4 S_m - w_5 S_p \cdot \text{cs}_i \right)$$
- Volumetric satisfaction: $S_w = \min\left(1.0, \frac{x_i}{d_i}\right)$
- Timing satisfaction: $S_t = 1.0$ (inside preferred), $0.5$ (inside acceptable), $0.0$ (outside/unspecified)
- Urgency protection: $S_u = 1.0 - \text{urgency}_i \cdot (1.0 - S_w)$
- Minimum requirement satisfaction: $S_m = \min\left(1.0, \frac{x_i}{\text{min\_req}_i}\right)$
- Stress penalty: $S_p = (1.0 - S_m) \times \text{crop\_sensitivity}_i$.

### 7.4–7.5 BATNA and Reservation Utility
- **Fallback Allocation**: $a_{\text{BATNA}} = \text{minimum\_water\_requirement}_i$.
- **Fallback Utility**: $U_{\text{BATNA}} = U_i(a_{\text{BATNA}}, \text{start\_hour}=\text{None})$.
- **Reservation Principle**: If proposed allocation $x_i$ yields $U_i < U_{\text{BATNA}}$, the agent rejects the offer (`is_batna_protected = True`).

### 7.6–7.9 DigitalTwin Lifecycle
Stateful execution wrapper ([`backend/app/agents/digital_twin.py`](../backend/app/agents/digital_twin.py)) tracking:
$$\text{IDLE} \longrightarrow \text{PROPOSING} \longrightarrow \text{EVALUATING} \longrightarrow \text{CONCEDING} \longrightarrow \text{ACCEPTED} / \text{REJECTED} / \text{FAILED}$$

```
[FIGURE 7.1 HERE — DIGITALTWIN STATE MACHINE DIAGRAM]
Description: Finite state machine showing transitions between IDLE, PROPOSING, EVALUATING, CONCEDING, and terminal ACCEPTED/REJECTED/FAILED states.
```

---

## CHAPTER 8 — CONFLICT DETECTION

### 8.1 Conflict Detection Engine
Implemented in [`backend/app/conflict/detector.py`](../backend/app/conflict/detector.py): An algorithmic rule engine identifying structural deficits and operational clashes.

### 8.2–8.6 Implemented Conflict Categories
1. **`RESOURCE_SHORTAGE`**: Triggered when aggregate demand exceeds supply:
   $$\text{Resource Gap} = \sum_{i=1}^n d_i - \text{available\_water} > 0$$
2. **`IRRIGATION_WINDOW_OVERLAP`**: Triggered when two or more farmers' acceptable windows overlap and combined hourly demand exceeds channel flow.
3. **`CANAL_CAPACITY_CONFLICT`**: Hourly discharge demand exceeds canal physical limit.
4. **`MINIMUM_REQUIREMENT_CONFLICT`**: Acute shortage where total survival minimums exceed canal water:
   $$\sum_{i=1}^n \text{minimum\_water}_i > \text{available\_water}$$
5. **`HIGH_CROP_STRESS`**: Identified via Crop-Stress Priority Score (CSPS).

### 8.7 Crop-Stress Priority Score (CSPS) & 8.8 Thresholds
$$\text{CSPS}_i = \text{urgency}_i \times \text{crop\_sensitivity}_i \times \text{stage\_criticality}_i$$
- Trigger condition: $\text{CSPS}_i > 0.49$.
- **Verified Constant Thresholds**:
  - `HIGH_STRESS_URGENCY_THRESHOLD` = $0.70$
  - `HIGH_STRESS_SENSITIVITY_THRESHOLD` = $0.70$

### 8.9 Severity Classification & Composite Score
- Shortage ratio $R = \frac{\text{Resource Gap}}{\sum d_i}$:
  - $R < 0.10 \implies \text{LOW}$
  - $0.10 \le R < 0.25 \implies \text{MEDIUM}$
  - $0.25 \le R < 0.50 \implies \text{HIGH}$
  - $R \ge 0.50 \implies \text{CRITICAL}$
- Composite Conflict Score:
  $$\text{Score} = 0.40 \cdot \text{shortage} + 0.20 \cdot \text{urgency} + 0.25 \cdot \text{overlap} + 0.15 \cdot \text{stress}$$

#### Table 8.1 — Conflict Types and System Responses
| Conflict Type | Exact Trigger Condition | Operational Meaning | System Response |
|---|---|---|---|
| `RESOURCE_SHORTAGE` | $\sum d_i > W_{\text{avail}}$ | Total demand exceeds canal water | Activates priority LP allocation |
| `IRRIGATION_WINDOW_OVERLAP` | Windows overlap & hourly demand $>$ flow | Clashing irrigation schedules | Staggers start times in scheduling |
| `CANAL_CAPACITY_CONFLICT` | $\max_h(\text{Flow}_h) > C_{\text{canal}}$ | Flow exceeds channel capacity | Shifts hourly discharge allocations |
| `MINIMUM_REQUIREMENT_CONFLICT`| $\sum \text{min\_req}_i > W_{\text{avail}}$ | Survival minimums exceed supply | Relaxes minimums via soft LP penalty $p_i$ |
| `HIGH_CROP_STRESS` | $\text{CSPS}_i > 0.49$ | Acute crop desiccation risk | Grants priority weights in LP objective |

```
ALGORITHM 2: DETERMINISTIC CONFLICT DETECTION
Input : Farmer agents A = {A_1, ..., A_n}, available_water W, canal_capacity C
Output: ScenarioConflictReport containing detected conflict entries

1 conflicts = [];
2 total_demand = sum(a.predicted_water_demand for a in A);
3 total_min_req = sum(a.minimum_water_requirement for a in A);
4 If total_demand > W then
5     AddConflict(conflicts, RESOURCE_SHORTAGE, gap = total_demand - W);
6 If total_min_req > W then
7     AddConflict(conflicts, MINIMUM_REQUIREMENT_CONFLICT, gap = total_min_req - W);
8 For each hour h in 0..23 do
9     hourly_flow = sum(a.hourly_demand for a in A if a.is_active_at(h));
10    If hourly_flow > C then
11        AddConflict(conflicts, CANAL_CAPACITY_CONFLICT, hour = h);
12 For each agent a in A do
13    csps = a.urgency * a.crop_sensitivity * a.stage_criticality;
14    If csps > 0.49 then
15        AddConflict(conflicts, HIGH_CROP_STRESS, farmer = a.farmer_id, score = csps);
16 Return ScenarioConflictReport(conflicts);
```

---

## CHAPTER 9 — WATER ALLOCATION OPTIMIZATION

### 9.1–9.5 Mathematical Formulation & Constraints
Implemented in [`backend/app/allocation/lp_allocator.py`](../backend/app/allocation/lp_allocator.py) via Google OR-Tools GLOP solver.

#### Decision Variables
- $x_i \ge 0$: Water allocated to farmer $i$ ($m^3$).
- $p_i \ge 0$: Penalty auxiliary variable measuring shortfall below minimum survival requirement.

#### Constraints
1. **(H1) Non-negativity**:
   $$x_i \ge 0 \quad \forall i \in \{1, \dots, n\}$$
2. **(H2) Farm Demand Maximum Ceiling**:
   $$x_i \le \text{maximum\_water}_i \quad \forall i \in \{1, \dots, n\}$$
3. **(H3) Total Water Availability Conservation**:
   $$\sum_{i=1}^n x_i \le \text{available\_water}$$
4. **(S1) Minimum Survival Requirement (Soft / Relaxable)**:
   $$x_i + p_i \ge \text{minimum\_water}_i, \quad p_i \ge 0$$
   *(When $\sum \text{minimum\_water}_i \le \text{available\_water}$, the solver enforces $p_i = 0$).*

### 9.6–9.7 Objective Function & Default Calibrated Weights
$$\max \sum_{i=1}^n \left[ w_{\text{urg}} \cdot \text{urgency}_i \cdot \left(\frac{x_i}{d_i}\right) + w_{\text{cs}} \cdot \text{cs}_i \cdot \left(\frac{x_i}{d_i}\right) + w_{\text{unmet}} \cdot \left(\frac{x_i}{d_i}\right) - w_{\text{min}} \cdot \left(\frac{p_i}{d_i}\right) \right]$$

#### Table 9.1 — Calibrated LP Objective Weights
| Weight Parameter | Symbolic Name | Default Value | Functional Role |
|---|---|---|---|
| Urgency Weight | $w_{\text{urg}}$ | **0.40** | Prioritizes farmers near soil moisture wilting point |
| Crop Sensitivity | $w_{\text{cs}}$ | **0.25** | Prioritizes drought-sensitive crops (vegetables, pulses) |
| Unmet Demand | $w_{\text{unmet}}$ | **0.20** | Drives overall volumetric satisfaction ratio |
| Minimum Shortfall Penalty | $w_{\text{min}}$ | **0.15** | Severely penalizes dropping below survival threshold |

### 9.8–9.10 Solver Modes and Fallback Allocation
- `lp_optimal`: Standard LP solved with hard minimum constraints satisfied.
- `lp_relaxed`: LP solved with soft penalty $p_i > 0$ under extreme physical shortage.
- `proportional_fallback`: Proportional distribution $x_i = W_{\text{avail}} \times \frac{d_i}{\sum d_j}$ if solver numerical exception occurs.
- `empty`: Handled when $W_{\text{avail}} = 0$.

### 9.11 Fairness Calculation (CRITICAL METHODOLOGICAL DISTINCTION)
- **Jain’s Fairness Index**:
  $$J(s_1, \dots, s_n) = \frac{\left( \sum_{i=1}^n s_i \right)^2}{n \sum_{i=1}^n s_i^2}, \quad s_i = \text{clip}\left(\frac{x_i}{d_i}, 0, 1\right)$$
- **MANDATORY NOTE**: Jain’s Fairness Index is computed **strictly POST-HOC**. It is **NOT** part of the LP objective. Integrating Jain's Index directly into the LP objective would transform the formulation into a non-convex, non-linear fractional program incompatible with fast linear simplex solvers.

```
[FIGURE 9.1 HERE — LP OPTIMIZATION FLOWCHART]
Description: Flowchart illustrating the decision logic of WaterAllocator: checking minimum requirement feasibility, selecting between lp_optimal and lp_relaxed branches, invoking OR-Tools GLOP, verifying constraints independently, and applying proportional fallback if needed.
```

```
ALGORITHM 3: CONSTRAINED LP WATER ALLOCATION
Input : Agents A = {A_1, ..., A_n}, available_water W, ObjectiveWeights w
Output: AllocationResult (allocation vector x*, solver status, Jain fairness)

1 solver = CreateGLOPSolver();
2 total_min = sum(a.minimum_water for a in A);
3 is_relaxed = (total_min > W);
4 For each a_i in A do
5     x_i = solver.NumVar(0.0, a_i.maximum_water, f"x_{i}");
6     If is_relaxed then
7         p_i = solver.NumVar(0.0, a_i.minimum_water, f"p_{i}");
8         solver.Add(x_i + p_i >= a_i.minimum_water);
9     Else
10        solver.Add(x_i >= a_i.minimum_water);
11 solver.Add(sum(x_i) <= W); // Total water conservation
12 objective = solver.Objective();
13 For each a_i in A do
14    coeff = (w.urg * a_i.urgency + w.cs * a_i.crop_sensitivity + w.unmet) / a_i.demand;
15    objective.SetCoefficient(x_i, coeff);
16    If is_relaxed then
17        objective.SetCoefficient(p_i, -w.min / a_i.demand);
18 objective.SetMaximization();
19 status = solver.Solve();
20 x_star = ExtractValues(solver);
21 fairness = ComputeJainsFairness(x_star, A); // Post-hoc calculation
22 Return AllocationResult(x_star, status, fairness);
```

---

## CHAPTER 10 — MULTI-AGENT NEGOTIATION

### 10.1 Negotiation Architecture
Implemented in [`backend/app/negotiation/`](../backend/app/negotiation/): Mediated iterative bargaining protocol starting from an initial LP allocation.

```
[FIGURE 10.1 HERE — MULTI-AGENT NEGOTIATION SEQUENCE DIAGRAM]
Description: Sequence diagram showing chronological message passing between Farmer Agents, Mediator, and WaterAllocator across multiple negotiation rounds.
```

### 10.2–10.5 Farmer Response Evaluation & Thresholds
Farmers evaluate allocations $x_i$ against utility $U_i$ and BATNA:

#### Table 10.1 — Farmer Response Thresholds
| Response Type | Exact Mathematical Condition | Agent Action in Negotiation |
|---|---|---|
| **`ACCEPT`** | $U_i \ge 0.65$ **AND** $U_i \ge U_{\text{BATNA}} + 0.02$ | Accepts proposed quota; offers to concede surplus |
| **`REQUEST_CHANGE`**| $0.35 \le U_i < 0.65$ | Expresses dissatisfaction; requests volume adjustment |
| **`REJECT`** | $U_i < 0.35$ **OR** $U_i < U_{\text{BATNA}}$ | Rejects proposal; invokes BATNA reservation protection |

### 10.6 Concession Mechanism
Dissatisfied farmers make calibrated concessions on their requested ask:
$$\text{Available Margin}_i = \text{current\_ask}_i - \text{minimum\_water}_i$$
$$\text{Concession Ratio}_i = \text{flexibility}_i \times (1.0 - \text{urgency}_i) \times \text{scale}$$
$$\Delta x_i = \text{Available Margin}_i \times \text{clamp}(\text{Concession Ratio}_i, 0, 1)$$
$$\text{new\_ask}_i = \max(\text{minimum\_water}_i, \text{current\_ask}_i - \Delta x_i)$$
- **Safeguards**: Asks never drop below minimum survival requirements; zero flexibility or maximum urgency yields zero concession.

### 10.7 Mandatory Re-Optimization Principle
The mediator never directly invents water allocations. Every round's adjusted asks are submitted to a **fresh instance of `WaterAllocator.solve()`**, guaranteeing that every intermediate proposal satisfies (H1), (H2), and (H3).

```
[FIGURE 10.2 HERE — MANDATORY RE-OPTIMIZATION LOOP]
Description: Flowchart illustrating the bargaining loop: Farmer Asks -> Mediator Concessions -> WaterAllocator GLOP Solve -> Verification -> Log-Nash Evaluation -> Termination Check.
```

### 10.8 Nash-Inspired Joint Objective
Surplus over BATNA: $\text{surplus}_i = U_i(\mathbf{x}) - U_{\text{BATNA}, i}$.
$$\Omega_{\text{Nash}} = \sum_{i=1}^n \log\left(\max(\text{surplus}_i, 10^{-6})\right)$$
- **MANDATORY TERMINOLOGY RULE**: Named **"Nash-inspired joint objective"**. It is **NOT** a full axiomatic Nash Bargaining Solution.

### 10.9–10.10 Termination Conditions & Agreement Formation

#### Table 10.2 — Negotiation Termination Conditions
| Termination State | Trigger Condition | Final Allocation Returned |
|---|---|---|
| **`AGREED`** | All required participating farmers return `ACCEPT` | Current round LP-verified allocation |
| **`NO_FEASIBLE_IMPROVEMENT`**| $\Omega_{\text{Nash}}$ does not improve for 2 consecutive rounds | Best historical LP-verified allocation |
| **`MAX_ROUNDS_REACHED`**| Round counter reaches limit (`max_rounds` = 5) | Best historical LP-verified allocation |
| **`FAILED`** | Unrecoverable solver or numerical exception | Fallback LP-verified allocation |

```
ALGORITHM 4: MULTI-AGENT NEGOTIATION AND MANDATORY RE-OPTIMIZATION
Input : Agents A, available_water W, max_rounds = 5, stagnation_limit = 2
Output: Agreement (final allocation, status, round audit trail)

1 allocator = WaterAllocator(A, W);
2 current_allocation = allocator.solve();
3 best_allocation = current_allocation;
4 best_nash = EvaluateNashObjective(current_allocation, A);
5 stagnation_count = 0;
6 For round = 1 to max_rounds do
7     responses = EvaluateFarmerResponses(current_allocation, A);
8     If AllFarmersAccept(responses) then
9         Return BuildAgreement(current_allocation, status = "AGREED");
10    candidate_asks = ComputeMediatorConcessions(responses, A);
11    // MANDATORY LP RE-OPTIMIZATION
12    candidate_allocation = WaterAllocator(candidate_asks, W).solve();
13    candidate_nash = EvaluateNashObjective(candidate_allocation, A);
14    If candidate_nash > best_nash + 1e-4 then
15        best_nash = candidate_nash;
16        best_allocation = candidate_allocation;
17        stagnation_count = 0;
18    Else
19        stagnation_count += 1;
20    If stagnation_count >= stagnation_limit then
21        Return BuildAgreement(best_allocation, status = "NO_FEASIBLE_IMPROVEMENT");
22    current_allocation = candidate_allocation;
23 Return BuildAgreement(best_allocation, status = "MAX_ROUNDS_REACHED");
```

---

## CHAPTER 11 — EXPLAINABLE AI

```
[FIGURE 11.1 HERE — EXPLAINABILITY PIPELINE ARCHITECTURE]
Description: Diagram of the read-only explainability layer showing data ingestion from Phases 2-6, SHAP adapter integration, reason-code rule evaluation, and dispatch to Farmer View and Expert View.
```

### 11.1 Explainability Architecture
Implemented in [`backend/app/explainability/`](../backend/app/explainability/):
- **Read-Only Invariant**: Inspects computational outputs from Phases 2–6; **never modifies** numerical decisions.
- Generates structured, immutable explanation dataclasses (`PredictionExplanation`, `ConflictExplanationEntry`, `AllocationExplanation`, `FairnessExplanation`, `NegotiationExplanation`).

### 11.2–11.6 Component Explanations
- **SHAP Explanations**: Converts TreeExplainer Shapley values into positive/negative contribution lists.
- **Conflict Explanations**: Traces active conflict reports directly to involved farmer IDs and evidence dictionaries.
- **Allocation Explanations**: Links allocated volumes directly to solver statuses and constraint bindings.
- **Negotiation Explanations**: Audits round-by-round concessions, BATNA margins, and Log-Nash trajectory.

### 11.7 Deterministic Reason Codes
Emitted strictly when numerical conditions are met:
- `RESOURCE_SHORTAGE`: Total demand exceeds canal availability.
- `HIGH_URGENCY`: Urgency score $\ge 0.70$.
- `HIGH_CROP_SENSITIVITY`: Sensitivity index $\ge 0.70$.
- `MINIMUM_REQUIREMENT`: Minimum survival requirements actively considered.
- `FULL_DEMAND_SATISFACTION`: Allocation fulfilled 100% of demand.
- `UNMET_DEMAND`: Allocation strictly less than requested demand.
- `BATNA_PROTECTED`: Proposal rejected due to utility falling below reservation threshold.

### 11.8–11.10 Dual-View Presentation Alignment
- **Farmer View**: Plain regional narratives without technical acronyms.
- **Expert View**: Mathematical formulation cards answering:
  - *WHAT IS IT?*
  - *WHY DOES IT MATTER?*
  - *WHAT HAPPENS IF IT CHANGES?*

```
ALGORITHM 5: DETERMINISTIC EXPLAINABILITY GENERATION
Input : Prediction p, ConflictReport c, AllocationResult a, NegotiationSession n
Output: FinalDecisionExplanation

1 explanations = [];
2 // 1. ML Explanation
3 shap_summary = ExtractTopContributors(p.shap_values, top_k = 3);
4 // 2. Reason Code Generation (Strict Data-Driven Rules)
5 reason_codes = [];
6 If c.has_shortage then reason_codes.Append(RESOURCE_SHORTAGE);
7 If a.satisfaction_ratio == 1.0 then reason_codes.Append(FULL_DEMAND_SATISFACTION);
8 If a.satisfaction_ratio < 1.0 then reason_codes.Append(UNMET_DEMAND);
9 For each farmer f in a.allocations do
10    If f.urgency >= 0.70 then reason_codes.Append(HIGH_URGENCY);
11    If f.crop_sensitivity >= 0.70 then reason_codes.Append(HIGH_CROP_SENSITIVITY);
12 // 3. Build Immutable Dataclass
13 Return FinalDecisionExplanation(shap_summary, reason_codes, a.solver_status, n.trajectory);
```

---

## CHAPTER 12 — API AND SYSTEM INTEGRATION

### 12.1–12.3 API Architecture & ScenarioService
Three-tier FastAPI backend ([`backend/app/`](../backend/app/)):
- Schemas: Pydantic v2 validation models ([`app/schemas/api_models.py`](../backend/app/schemas/api_models.py)).
- Service: Pipeline Orchestration Service ([`app/services/scenario_service.py`](../backend/app/services/scenario_service.py)).
- Routes: Thin REST Routers ([`app/api/scenario_routes.py`](../backend/app/api/scenario_routes.py), [`app/api/health.py`](../backend/app/api/health.py)).

#### Table 12.1 — FastAPI REST Endpoint Specification
| HTTP Method | Path | Request Model | Response Model | Description |
|---|---|---|---|---|
| `GET` | `/health` | None | `JSONResponse` | Liveness & DB connectivity probe |
| `GET` | `/api/v1/health` | None | `HealthResponse` | Pipeline readiness & synthetic disclaimer |
| `POST` | `/api/v1/scenarios/run` | `ScenarioRunRequest` | `ScenarioRunResponse` | **Primary**: Executes full pipeline |
| `POST` | `/api/v1/predictions` | `PredictionRequest` | `PredictionResponse` | Single-farmer ML demand prediction |
| `POST` | `/api/v1/predictions/batch` | `PredictionBatchRequest`| `PredictionBatchResponse` | Batch ML water demand prediction |
| `POST` | `/api/v1/conflicts` | `ConflictRequest` | `ScenarioConflictReportResponse` | Standalone conflict detection |
| `POST` | `/api/v1/allocations` | `AllocationRequest` | `AllocationResponse` | Standalone OR-Tools GLOP allocation |
| `POST` | `/api/v1/negotiations` | `NegotiationRequest` | `NegotiationResponse` | Multi-agent mediation session |
| `GET` | `/openapi.json` | None | `JSON` | Complete OpenAPI 3.1 schema |
| `GET` | `/docs` | None | HTML | Interactive Swagger UI documentation |

---

## CHAPTER 13 — FRONTEND ARCHITECTURE

### 13.1–13.3 Technology Stack & Routing
Built with React 18, TypeScript, Vite, React Router v6, Lucide React, and Recharts. Pages include Overview, Scenario, Predictions, Conflicts, Allocation, Negotiation, Explainability, Agreement, and Debug.

### 13.5 Farmer View vs. 13.6 Expert View
- **Farmer View**: Plain language, zero mathematical/ML jargon, simple situation presets ("Slight Canal Shortage", "Severe Drought"), visual allocation gauges, and intuitive cards.
- **Expert View**: 7 technical diagnostic tabs answering *WHAT IS IT?*, *WHY DOES IT MATTER?*, and *WHAT HAPPENS IF IT CHANGES?*

### 13.14 Localization
Implemented in [`frontend/src/i18n/translations.ts`](../frontend/src/i18n/translations.ts) supporting English (`en`), Hindi (`hi`), and Gujarati (`gu`).

### 13.15 Explicit Architectural Constraints
- **Zero Voice UI**: Absolutely no microphone buttons, speech recognition, text-to-speech, or chatbot features are implemented.

```
[FIGURE 13.1 HERE — SCENARIO CONFIGURATION INTERFACE SCREENSHOT]
Description: UI screenshot of the Scenario Configuration page contrasting simple situation presets in Farmer View with technical parameter inputs in Expert View.

[FIGURE 13.2 HERE — WATER ALLOCATION DASHBOARD SCREENSHOT]
Description: UI screenshot showing allocation result cards, volumetric demand fulfillment bars, and Jain fairness summary gauge.

[FIGURE 13.3 HERE — MULTI-AGENT NEGOTIATION INTERFACE SCREENSHOT]
Description: UI screenshot showing round-by-round bargaining trajectory, agent concessions, and Log-Nash objective progression.

[FIGURE 13.4 HERE — LOCALIZED EXPLAINABILITY IN HINDI/GUJARATI SCREENSHOT]
Description: UI screenshot showing reason-code explanation cards rendered in Hindi and Gujarati regional scripts.

[FIGURE 13.5 HERE — FINAL WATER-SHARING AGREEMENT CERTIFICATE SCREENSHOT]
Description: UI screenshot displaying the finalized agreement certificate, participating farmer allocations, and digital audit seal.
```

---

## CHAPTER 14 — TESTING AND VALIDATION

### 14.1 Backend Test Results (Pytest)
**704 / 704 PASSING** (0 failures, 0 errors, in $\approx 7.1\text{s}$):

#### Table 14.1 — Backend Regression Test Results Breakdown
| Test Suite File | Target Subsystem | Tests | Status |
|---|---|---|---|
| `tests/test_data_generator.py` | Phase 1 (Data Synthesis & FAO-56) | **62** | PASS |
| `tests/test_ml_pipeline.py` | Phase 2 (ML Training & Evaluation) | **64** | PASS |
| `tests/test_farmer_agents.py` | Phase 3 (Digital Twins, Utility, BATNA) | **96** | PASS |
| `tests/test_conflict_detector.py` | Phase 4 (Conflict Detection Engine) | **88** | PASS |
| `tests/test_lp_allocator.py` | Phase 5 (OR-Tools GLOP LP Allocation) | **86** | PASS |
| `tests/test_negotiation.py` | Phase 6 (Multi-Agent Mediation Engine) | **123** | PASS |
| `tests/test_explainability.py` | Phase 7 (Explainability Layer) | **113** | PASS |
| `tests/test_api.py` | Phase 8 (FastAPI Integration Layer) | **72** | PASS |
| **Total Backend Tests** | **Comprehensive Regression Suite** | **704 / 704** | **100% PASS** |

### 14.2 Frontend Test Results (Vitest)
**53 / 53 PASSING** (0 failures, 0 errors, in $\approx 2.4\text{s}$):

#### Table 14.2 — Frontend Vitest Test Results Breakdown
| Test File | Component Target | Tests | Status |
|---|---|---|---|
| `src/tests/api.test.ts` | Typed API Service Client | **5** | PASS |
| `src/tests/Components.test.tsx` | Layout Primitives, Badges, Header | **9** | PASS |
| `src/tests/ScenarioPages.test.tsx` | Scenario, Allocation & Negotiation Pages | **8** | PASS |
| `src/tests/Explainability.test.tsx`| Reason Codes, SHAP Cards | **14** | PASS |
| `src/tests/App.test.tsx` | App Routing & Navigation | **5** | PASS |
| `src/tests/ViewMode.test.tsx` | View Toggle & Multilingual i18n | **12** | PASS |
| **Total Frontend Tests** | **Frontend Component Suite** | **53 / 53** | **100% PASS** |

### 14.3 Frontend Production Build Verification
- Command: `tsc -b && vite build`
- Result: **PASS** (Zero TypeScript errors; production build succeeded in $< 1\text{s}$).

### 14.4 Invariant and Validation Summary
- Physical conservation $\sum x_i \le W_{\text{avail}}$ verified across all shortage tests.
- Numerical determinism verified via repeated seeded executions.
- Zero explanation fabrications verified by asserting exact dataclass field matches.

---

## CHAPTER 15 — RESULTS AND DISCUSSION

### 15.1 ML Prediction Results
Both models achieve $R^2 > 0.973$ on held-out test data ($n=451$), with MAE $\approx 17.5\text{ m}^3/\text{day}$. Top SHAP attributions correspond to physical crop transpiration variables.

### 15.2 Conflict Detection Results
Across the 8 scenario types, conflicts were deterministically classified with zero false positives. High-urgency agents under moisture stress consistently triggered `HIGH_CROP_STRESS`.

### 15.3 Allocation Results
The GLOP LP solved all instances within 5 milliseconds. Under severe shortage, the solver smoothly activated `lp_relaxed`, satisfying survival minimums before distributing surplus.

### 15.4 Negotiation Results
Flexible farmers conceded volume, increasing the Nash-inspired joint objective $\Omega_{\text{Nash}}$ across rounds until either unanimous agreement or stagnation triggered clean termination.

### 15.5 Explainability Results
The explainability layer faithfully annotated solver outcomes with deterministic reason codes, providing clear localized text in Hindi and Gujarati.

### 15.6 Synthetic Data Boundary
All results reflect internal computational consistency with synthetic FAO-56 formulas rather than empirical field telemetry.

---

## CHAPTER 16 — LIMITATIONS

1. **Synthetic Data Paradigm**: All agronomic data is generated programmatically.
2. **Absence of Real Field Deployment**: Not evaluated with practicing farmers or live canal sluices.
3. **Single-Period Allocation**: Solves a daily decision window; does not model multi-day reservoir routing.
4. **Post-Hoc Fairness**: Jain's index is computed post-hoc rather than enforced as an LP constraint.
5. **Simulated Agent Behavior**: Agents follow deterministic mathematical curves rather than complex human social dynamics.
6. **No Live Telemetry**: Operates without connection to physical IoT sensors or SCADA actuators.

---

## CHAPTER 17 — FUTURE SCOPE

1. **Empirical Agricultural Datasets**: Incorporating field telemetry from soil moisture probes.
2. **Dynamic Multi-Period Optimization**: Expanding LP to multi-day rolling-horizon formulations.
3. **Mobile Progressive Web App**: Developing offline-first mobile versions for rural connectivity.
4. **Multilingual Voice UI**: Speech recognition for non-literate farmers (future work only).
5. **SCADA Hardware Integration**: Interfacing allocations directly with automated canal gates.
6. **Participatory Field Validation**: Conducting workshops with Water User Associations (WUAs).

---

## CHAPTER 18 — CONCLUSION

AquaMediAI successfully demonstrates an integrated, explainable computational prototype for mediating agricultural water disputes. By coupling:
$$\text{FAO-56 Data} \longrightarrow \text{ML Demand} \longrightarrow \text{Digital Twins} \longrightarrow \text{Conflict Engine} \longrightarrow \text{GLOP Allocation} \longrightarrow \text{Negotiation} \longrightarrow \text{Explainability}$$
the system provides an objective, auditable, and constraint-verified alternative to opaque manual quotas. While bounded as an academic proof-of-concept on synthetic data, it establishes a defensible architectural foundation for automated dispute mediation in communal resource systems.

---

## APPENDICES

### Appendix A — API Endpoint Examples
Sample `curl` command executing the full mediation pipeline:
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/run" \
     -H "Content-Type: application/json" \
     -d '{"scenario_type": "moderate_shortage", "n_farmers": 3, "random_seed": 42}'
```

### Appendix B — Sample Scenario Run Request JSON
```json
{
  "scenario_type": "moderate_shortage",
  "n_farmers": 3,
  "random_seed": 42,
  "canal_water_override": 1200.0,
  "model_type": "xgboost"
}
```

### Appendix C — Sample Allocation Output JSON Snippet
```json
{
  "allocation_method": "lp_optimal",
  "allocations": {
    "farmer_0": 420.5,
    "farmer_1": 390.2,
    "farmer_2": 389.3
  },
  "jains_fairness_index": 0.9842,
  "solver_status": "OPTIMAL",
  "water_conservation_satisfied": true
}
```

### Appendix D — Sample Negotiation Agreement JSON Snippet
```json
{
  "agreement_status": "AGREED",
  "negotiation_rounds": 2,
  "final_nash_objective": -4.1205,
  "fairness_score": 0.9842,
  "participating_farmers": ["farmer_0", "farmer_1", "farmer_2"]
}
```

### Appendix E — Test Execution Verification Summary
- Pytest: 704 passed in 7.14 seconds.
- Vitest: 53 passed in 2.48 seconds.
- Build: Vite production build clean exit code 0.

### Appendix F — Important Configuration Parameters
- `HIGH_STRESS_URGENCY_THRESHOLD`: 0.70
- `HIGH_STRESS_SENSITIVITY_THRESHOLD`: 0.70
- `CSPS_TRIGGER_THRESHOLD`: 0.49
- `ACCEPTANCE_UTILITY_THRESHOLD`: 0.65
- `REJECTION_UTILITY_THRESHOLD`: 0.35
- `BATNA_BUFFER`: 0.02
- `MIN_SURPLUS_FLOOR`: $10^{-6}$
- `MAX_NEGOTIATION_ROUNDS`: 5
- `STAGNATION_ROUNDS`: 2

---

## REFERENCES
1. Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). *Crop evapotranspiration-Guidelines for computing crop water requirements*. FAO Irrigation and drainage paper 56. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
2. Breiman, L. (2001). Random Forests. *Machine Learning*, 45(1), 5-32. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
3. Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *ACM SIGKDD*. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
4. Lundberg, S. M., & Lee, S. I. (2017). A Unified Approach to Interpreting Model Predictions. *NeurIPS*. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
5. Nash, J. (1950). The Bargaining Problem. *Econometrica*, 18(2), 155-162. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
6. Ostrom, E. (1990). *Governing the Commons: The Evolution of Institutions for Collective Action*. Cambridge University Press. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
7. Raiffa, H. (1982). *The Art and Science of Negotiation*. Harvard University Press. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
8. Jain, R., Chiu, D., & Hawe, W. (1984). *A Quantitative Measure of Fairness and Permutation for Computer Systems Local Resource Management*. DEC Research Report. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]
9. Google OR-Tools Documentation. *GLOP Linear Solver Guide*. [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]

