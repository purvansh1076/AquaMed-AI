# AquaMedi AI — Known Limitations & Scientific Boundaries

**Document Version:** 2.0.0 (Phase T Release Edition)  
**Last Updated:** November 2026  
**Status:** Comprehensive Verification of Engineering, Scientific, and Operational Boundaries  

---

## 1. Scientific & Agronomic Boundaries

### 1.1 Synthetic Data Foundation Only
- **Scope:** Complete prediction, optimization, and mediation pipelines.
- **Limitation:** All farmer records, environmental indicators, water demands, allocation simulations, and negotiation sessions are generated algorithmically using synthetic parameter distributions grounded in standard FAO-56 Penman-Monteith formulas. No actual farmer water-usage logs, smart canal flowmeter telemetry, or historical telemetry have been ingested.
- **Impact:** Reported statistical metrics ($R^2 = 0.9699$, $\text{MAE} = 18.63\text{ m}^3$) demonstrate fit against synthetic FAO-56 target signals only. They do not constitute empirical evidence of field accuracy or real-world generalization across heterogeneous farming micro-climates.
- **Operational Requirement:** Any real-world agricultural deployment requires independent ground-truth data collection and model retraining before serving operational decisions.

### 1.2 Regional Evapotranspiration ($ET_0$) Calibration Outstanding
- **Scope:** Penman-Monteith reference evapotranspiration module (`backend/app/ml/data_generator.py`).
- **Limitation:** While independent mathematical verification tests (`test_et0_independent.py`, `test_fao56_reference.py`) confirm exact adherence to FAO-56 standard formulas, regional empirical calibration against India Meteorological Department (IMD) or Central Water Commission (CWC) automatic weather stations has not been conducted.
- **Impact:** Local micro-climates, wind profiles, solar radiation anomalies, and regional humidity patterns in specific river basins may deviate from standard parameter assumptions.
- **Operational Requirement:** Calibration of $ET_0$ constants against regional weather station archives is required prior to canal operations.

### 1.3 Single-Crop Homogeneity Assumption
- **Scope:** ML feature schema, agent digital twins, allocation constraints.
- **Limitation:** Each farmer digital twin models exactly **one crop type** per allocation cycle with a static seasonal crop coefficient ($K_c$). Intercropping, multi-crop parcels, mixed-crop irrigation schedules, and dynamic intra-seasonal phenological transitions (e.g., initial $\to$ crop development $\to$ mid-season $\to$ late-season) within a single farmer's parcel are not represented.
- **Impact:** Farms with divided parcels growing multiple crops simultaneously must be simplified into separate synthetic farmer profiles or aggregate representations.

### 1.4 SHAP Explanations on Synthetic Data
- **Scope:** Model interpretability engine (`backend/app/ml/explainability.py`).
- **Limitation:** TreeSHAP feature attributions explain the decision surface of the trained XGBoost model on synthetic data. They demonstrate algorithmic interpretability and explainability transparency, but the discovered feature weights reflect the synthetic generator rather than true agronomic causality.

---

## 2. Operational & Field Boundaries

### 2.1 No Physical Field Pilot Executed
- **Scope:** Entire platform.
- **Limitation:** AquaMedi AI has been verified exclusively through in silico simulation benchmarks, unit tests, and local browser execution. No physical pilot has been deployed on an operating irrigation canal system.
- **Impact:** **No claims of actual physical water savings, crop yield improvements, or real farmer conflict resolution can be made.** Any percentages reported in simulation reports represent theoretical algorithmic improvements over synthetic baselines under idealized assumptions.

### 2.2 Lack of Real-Time IoT & Telemetry Integration
- **Scope:** Ingestion pipeline and scenario engine.
- **Limitation:** The platform currently operates on batch scenarios and REST request payloads. There is no live connector to physical SCADA systems, remote telemetry units (RTUs), automated sluice gates, or soil moisture sensor networks.
- **Impact:** Canal gate adjustments and allocation enforcement must be performed manually by irrigation engineers or extension officers.

---

## 3. Mathematical & Optimization Boundaries

### 3.1 Default LP Optimizes Weighted Utility, Not Pure Fairness
- **Scope:** Google OR-Tools GLOP Allocator (`backend/app/allocation/lp_allocator.py`).
- **Limitation:** The primary Linear Programming objective function maximizes aggregate weighted farmer satisfaction and minimizes penalties. Jain's Fairness Index is measured and reported **post-hoc**. When farmer weights (urgency, crop stress sensitivity) diverge sharply, the resulting allocation may prioritize vulnerable crops at the expense of equitable volumetric distribution.
- **Mitigation:** A standalone Max-Min Fairness LP solver (`solve_maxmin_fairness()`) has been implemented and verified in Phase E, but it is currently offered as an alternative strategy rather than the default primary solve.

### 3.2 Bounded Multi-Agent Negotiation
- **Scope:** Negotiation Mediator (`backend/app/negotiation/negotiation_engine.py`).
- **Limitation:** Multi-agent negotiation is bounded to a default maximum of 5 rounds (`max_rounds = 5`). If concession trajectories are shallow or BATNA disagreement thresholds cannot be reconciled within 5 rounds, the mediator terminates with `MAX_ROUNDS_REACHED` or `NO_FEASIBLE_IMPROVEMENT`.
- **Impact:** Extreme water scarcity where total available supply cannot satisfy baseline BATNA utilities will result in unanimous rejection by design (BATNA protection).

### 3.3 Group Conformal Predictor Field Coverage
- **Scope:** Conformal prediction engine (`backend/app/ml/group_conformal.py`).
- **Limitation:** While group-conditional conformal prediction incorporates finite-sample corrections ($k = \lceil (n_g+1)(1-\alpha) \rceil / n_g$) and passes unit tests, empirical subgroup coverage has only been validated on synthetic splits. Stratified empirical coverage across rare crops or small sample sizes ($n < 30$) falls back to the global non-conformity quantile.

---

## 4. Software Engineering & Infrastructure Boundaries

### 4.1 In-Memory Single-Node Authentication Rate Limiter
- **Scope:** Expert login rate limiting (`backend/app/api/auth.py`).
- **Limitation:** Failed login attempt counters and lockout timers are maintained in an in-memory dictionary.
- **Impact:** In a multi-worker production deployment behind a load balancer (e.g. multiple Gunicorn/Uvicorn workers or multiple Kubernetes pods), each process maintains its own independent state unless sticky sessions are configured.
- **Mitigation / Next Step:** Implement a centralized Redis-backed token bucket or rate limiter for clustered production environments.

### 4.2 Synchronous SQLAlchemy Database Operations
- **Scope:** Database session management (`backend/app/db/session.py`).
- **Limitation:** Database interactions utilize synchronous psycopg2 / SQLAlchemy sessions rather than an asynchronous driver (`asyncpg`).
- **Impact:** Under extreme concurrent API loads, worker thread pool starvation could occur. Current performance is well suited for administrative expert usage, but massive concurrent farmer traffic requires async migration or connection pooling optimization.

### 4.3 Absence of Formal High-Concurrency Load Testing
- **Scope:** Deployment infrastructure.
- **Limitation:** The test suite verifies functionality (862 backend tests, 95 frontend tests), but formal stress, soak, and load testing (e.g., using Locust or k6) under thousands of concurrent virtual users has not been performed.

### 4.4 Frontend Bundle Chunk Size
- **Scope:** Frontend distribution (`frontend/dist/assets/`).
- **Limitation:** The production JavaScript bundle is ~1.02 MB (gzip ~272 KB), exceeding Vite's default 500 kB chunk warning threshold.
- **Impact:** Slightly longer initial load time on low-bandwidth rural mobile networks.
- **Mitigation / Next Step:** Implement React `lazy()` dynamic imports to split the Expert analytics dashboard from the lightweight Farmer Portal.

---

## 5. Summary Declaration

AquaMedi AI v1.0.0 is an advanced, fully verified research prototype. All engineering components operate strictly according to their formal software contracts. **It must not be presented or deployed as a certified agronomic tool or autonomous water control system without regional empirical calibration and approved physical pilot trials.**
