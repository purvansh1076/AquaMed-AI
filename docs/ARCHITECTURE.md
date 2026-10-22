# AquaMediAI — Architecture

## 1. Overall System Architecture

AquaMediAI follows a **three-layer architecture** separating data generation, business logic, and user interface:

```
┌─────────────────────────────────────────────────────────────────────┐
│                            USER LAYER                                 │
│  ┌─────────────────┐  HTTP/HTTPS  ┌──────────────────────────────┐ │
│  │  React Frontend │  ──────────▶  │  FastAPI Application (Backend) │ │
│  │  (Vite + TS)    │              │  ┌──────────────────────────┐   │ │
│  └─────────────────┘              │  │  ML Prediction Layer     │   │ │
│                                    │  │  (predictor.py)         │   │ │
│                                    │  ├──────────────────────────┤   │ │
│                                    │  │  Allocation Engine     │   │ │
│                                    │  │  (lp_allocator.py)      │   │ │
│                                    │  ├──────────────────────────┤   │ │
│                                    │  │  Negotiation Engine   │   │ │
│                                    │  │  (negotiation_engine.py)│   │ │
│                                    │  └──────────────────────────┘   │ │
│                                    │              ▲                  │ │
│                                    │              │                  │ │
│                                    │  ┌──────────────────────────┐ │ │
│                                    │  │  Conflict Detector     │ │ │
│                                    │  │  (conflict_detector.py)│ │ │
│                                    │  └──────────────────────────┘ │ │
│                                    │              │                  │ │
│                                    │  ┌──────────────────────────┐ │ │
│                                    │  │  Configuration         │ │ │
│                                    │  │  (config.py)            │ │ │
│                                    │  └──────────────────────────┘ │ │
│  └────────────────────────────────────┘              └────────────┘ │
│                        │                              ▲           │
│                        │                              │           │
│                        │                              │           │
│                        ▼                              │           │
│                ┌─────────────────────────────┐              │           │
│                │   Data & Artifacts Layer    │              │           │
│                │  ┌──────────────────────┐     │              │           │
│                │  │  Synthetic Data      │     │              │           │
│                │  │  (data_generator.py) │     │              │           │
│                │  └──────────────────────┘     │              │           │
│                │  ┌──────────────────────┐     │              │           │
│                │  │  Model Artifacts     │     │              │           │
│                │  │  (xgb_model.joblib,   │     │              │           │
│                │  │   rf_model.joblib,     │     │              │           │
│                │  │   encoders.joblib)     │     │              │           │
│                │  └──────────────────────┘     │              │           │
│                │  ┌──────────────────────┐     │              │           │
│                │  │  Evaluation Results  │     │              │           │
│                │  │  (evaluation_results.json)││              │           │
│                │  └──────────────────────┘     │              │           │
│                └─────────────────────────────┘              │           │
│                                      ▲                 │           │
│                                      │                 │           │
│                              Generated     │           │
│                              at build/run time│           │
│                                      │                 │           │
│                      ┌───────────────────────┐          │           │
│                      │   PostgreSQL (optional)   │          │           │
│                      │  for API tests / health    │          │           │
│                      │  (psycopg2-binary required)│        │           │
│                      └───────────────────────┘          │           │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Component Diagram

### 2.1 Data Generator (`backend/app/ml/data_generator.py`)
- **Input**: Scenario type, seed=42, farm area ranges, weather parameter ranges
- **Process**: Generates weather (temperature, humidity, wind, rainfall), computes ET₀ via FAO-56 Penman-Monteith parameters, derives `ET_c = ET_0 × K_c`, computes `demand_m3 = ET_c × farm_area_hectares × 10`
- **Output**: CSV/parquet dataset with 3000 samples, 8 scenario types, ±15% noise, train/val/test splits (70/15/15)
- **Key Functions**: `generate_dataset()`, `ScenarioType` enum

### 2.2 Feature Engineering (`backend/app/ml/feature_engineering.py`)
- **Input**: Raw dataset columns
- **Process**: Encodes categorical features (crop_type, soil_type, growth_stage, season) using `OneHotEncoder`/`OrdinalEncoder` fitted on train split only; engineered features: `area_x_etc`, `urgency_x_stress`, `et0_x_kc`, `rain_deficit`, `flexibility_window`; scales numeric features via `StandardScaler` (train-fit only)
- **Output**: Processed feature matrix (22 columns), fitted encoders persisted to `encoders.joblib`
- **Key Guard**: No leakage — encoders fitted on train, transform used for val/test

### 2.3 ML Training Pipeline (`backend/app/ml/trainer.py`)
- **Input**: `n_samples`, `seed`
- **Process**: Calls `SyntheticDataGenerator.generate_dataset()`, splits into train/val/test (70/15/15 stratified by scenario_type), trains `RandomForestRegressor` (n_estimators=200, max_depth=15, random_state=42) and `XGBRegressor` (n_estimators=300, lr=0.05, max_depth=6, random_state=42), evaluates MAE/RMSE/R² on all splits, persists artifacts via `joblib.dump()`, writes `evaluation_results.json`
- **Output**: `TrainingArtifacts` named tuple (rf_result, xgb_result, encoders, feature_columns, best_model_name, dataset_summary)

### 2.4 Water Demand Predictor (`backend/app/ml/predictor.py`)
- **Input**: Farmer profile (22 feature values)
- **Process**: Loads artifacts via `WaterDemandPredictor.from_artifacts()`, validates feature alignment, applies same preprocessing (encoding/scaling) fitted on train data, returns `predicted_demand_m3` via RF or XGBoost model
- **Output**: Prediction result with finiteness check and synthetic data disclaimer

### 2.5 Conflict Detector (`backend/app/conflict_detector.py`)
- **Input**: List of FarmerAgent objects, their allocations
- **Process**: Computes conflict score components (resource shortage ratio, irrigation window overlap, canal capacity ratio, minimum requirement ratio, crop stress score); maps overall ratio to severity (0→LOW, 0.25→LOW, 0.5→MEDIUM, 0.75→HIGH, >0.99→CRITICAL); identifies 5 conflict types
- **Output**: Conflict report with severity, per-type breakdown, affected farmer IDs

### 2.6 GLOP Allocator (`backend/app/allocation/lp_allocator.py`)
- **Input**: List of FarmerAgent objects, available_water_m3, optional ObjectiveWeights
- **Process**: Builds OR-Tools GLOP LP model with decision variables x_i (m³ allocated); adds hard constraints H1 (x_i >= 0), H2 (x_i <= max_water_i), H3 (Σx_i <= available_water); adds soft constraint S1 (minimum requirements with penalty when Σmin_req > available_water); sets objective: Σ[w_urg×urgency_i×s_i + w_cs×crop_sensitivity_i×s_i - w_unmet×(1-s_i) - w_min×shortfall_i/demand_i] where s_i = x_i/demand_i; solves; extracts solution; runs fallback chain if INFEASIBLE: lp_optimal → lp_relaxed → proportional → empty; verifies constraints independently post-solve
- **Output**: AllocationResult (allocations, verification, fairness, utilization, method, objective_value)

### 2.7 Negotiation Engine (`backend/app/negotiation/negotiation_engine.py`)
- **Input**: List of FarmerAgent objects, available_water_m3, NegotiationConfig
- **Process**: 
  1. Runs initial WaterAllocator to get baseline allocation
  2. Evaluates farmer responses via threshold-based logic (ACCEPT ≥0.65 ∧ ≥ batna+0.02, REQUEST_CHANGE ∈ [0.35,0.65), REJECT <0.35) with BATNA protection (utility < batna_utility → REJECT overrides all thresholds)
  3. If all ACCEPT → return AGREED
  4. Otherwise, enter negotiation loop (max 5 rounds):
     - Mediator computes concessions for dissatisfied farmers (flexibility_factor × urgency_factor × concession_scale)
     - Mediator steps accepting farmers' asks toward target demand (mediator_step_fraction)
     - Runs WaterAllocator with candidate preferences
     - Computes log Nash objective Σlog(max(surplus_i, 1e-6))
     - Accepts candidate if is_nash_improvement (min_delta=1e-4) OR concession_progress_threshold (0.1) is met
     - Stagnation after 2 consecutive rounds without improvement → NO_FEASIBLE_IMPROVEMENT
     - All farmers ACCEPT → AGREED; max rounds → MAX_ROUNDS_REACHED
  5. Returns Agreement with best feasible allocation found, concessions trail, fairness, utilization, Nash history
- **Output**: Agreement (final_allocation, agreement_status, termination_reason, round_nash_history, round_fairness_history, concessions, is_physically_valid)

### 2.8 FastAPI Application (`backend/app/main.py` — inferred from test coverage)
- **15 endpoint groups** tested: root, health, scenarios, predictions, conflicts, allocations, negotiations, validation, determinism, farmer data, error handling, JSON serialization, explanations, scenario types, OpenAPI schema
- **Dependencies**: FastAPI, uvicorn, SQLAlchemy, psycopg2-binary
- **Startup**: Creates SQLAlchemy engine (fails gracefully if psycopg2 missing or PostgreSQL unreachable); lifespan context manager

### 2.9 React Frontend (`frontend/`)
- **Framework**: React 18+, TypeScript, Vite 5
- **Components**: Farmer view, Expert view, Scenario selector, Prediction display, Allocation viewer, Negotiation interface, SHAP explainability panel, Multilingual labels (en/hi/gu)
- **API Client**: httpx-based client calling FastAPI endpoints
- **State Management**: React hooks (useState, useEffect); simple prop drilling
- **Tests**: 53 vitest tests covering API client, component rendering, format validation, determinism, error states
- **Build**: Vite production build → `frontend/dist/` (no errors)

## 3. Data Flow

### 3.1 Training Pipeline Flow
```
SyntheticDataGenerator.generate_dataset()
        ↓
        Stratified split (70/15/15 by scenario_type)
        │                   │
        │                   ├── train (2100) ──→ fit encoders (OneHot, Ordinal, StandardScaler)
        │                   ├── val (450)     ──→ compute metrics (RF, XGB)
        │                   └── test (451)    ──→ compute final metrics
        ↓
run_training_pipeline()
        ↓
Train RandomForest (n_estimators=200, max_depth=15)   ──→ rf_model.joblib
       and XGBoost (n_estimators=300, lr=0.05, max_depth=6)  → xgb_model.joblib
        ↓
Encode features, compute MAE/RMSE/R² per split          → evaluation_results.json
        ↓
Persist to data/models/                               │
        │                                       └── Used by predictor.py
        ↓
WaterDemandPredictor.from_artifacts()              │
        ↓
Predict water_demand_m3 for new farmer profile     │
```

### 3.2 Allocation Flow
```
WaterAllocator(agents, available_water_m3)
        ↓
Build GLOP LP model
        │
        ├── H1: x_i >= 0 (non-negative)
        ├── H2: x_i <= max_water_i (max per farmer)
        ├── H3: Σx_i <= available_water (supply limit)
        ├── S1: minimum requirements (soft, penalty if infeasible)
        └── Objective: Σ[w_urg×urgency_i×s_i + w_cs×cs_i×s_i - w_unmet×(1-s_i) - w_min×shortfall_i/demand_i]
        ↓
solver.Solve()
        │
        ├── OPTIMAL/FEASIBLE → extract allocations, verify constraints
        ├── INFEASIBLE → proportional fallback
        └── ERROR → proportional fallback
        ↓
Constraint verification (independent post-solve)
        │
        ├── H1/H2/H3 checked independently
        ├── Jain's fairness computed
        └── AllocationResult returned
        ↓
Used by negotiation engine as initial allocation + re-optimization after each concession
```

### 3.3 Negotiation Flow
```
NegotiationEngine(agents, available_water_m3, config)
        │
        ├── Step 1: Initial allocation via WaterAllocator
        │        ↓
        │   evaluate_initial_responses()
        │        ↓
        │   if all ACCEPT → AGREED (round 1)
        │        ↓
        │   otherwise → enter negotiation loop
        │
        ├── Step 2: Mediator.mediate() per round
        │   ├── Identify dissatisfied farmers (REQUEST_CHANGE, REJECT)
        │   ├── compute_concession() for each dissatisfied farmer
        │        flexibility * (1-urgency) * concession_scale
        │   ├── Step toward target for ACCEPT farmers (mediator_step_fraction)
        │   ├── Build candidate agents (current_ask → predicted_water_demand)
        │   ├── WaterAllocator.solve() ← MANDATORY (never bypass)
        │   ├── compute_log_nash_objective(Σlog(max(surplus_i, 1e-6)))
        │   ├── is_nash_improvement(new, best, min_delta=1e-4)
        │   ├── _check_concession_progress() → fraction >= 0.1?
        │   └── Return (Proposal, concessions)
        │        ↓
        │   Check acceptance: _is_agreement_reached()
        │   Check stagnation: stagnation_count >= 2 AND no concession progress
        │        ↓                                        │
        │   AGREED          ← all farmers ACCEPT           │
        │   NO_FEASIBLE_IMPROVEMENT ← stagnation limit   │
        │   MAX_ROUNDS_REACHED ← 5 rounds exhausted      │
        ↓
Build and return Agreement (best feasible allocation)
        │
        └── Concessions trail, Nash history, fairness, utilization
```

## 4. Constraint Verification Sequence

The system **never trusts the solver blindly**. After every LP solve, the following checks are independently verified:

1. **H1**: All allocations >= 0 (non-negative)
2. **H2**: All allocations <= maximum_requirement (physical limit)
3. **H3**: Total allocated <= available_water + tolerance (supply balance)
4. **Minimum requirements**: Not a hard constraint (soft, via penalty); shortfall reported in FarmerAllocation.minimum_shortfall_m3
5. **No NaN/Inf**: Explicitly checked for every allocation value

This verification is performed in `verify_constraints()` (lp_allocator.py:656-762) and `_verify_allocation_physics()` (negotiation_engine.py:513-548).

## 5. Configuration Flow

All settings are loaded from `.env` via `pydantic_settings.BaseSettings`:

- `app_env` (development/production/testing) — validated
- `app_debug` (bool) — controls SQL echo logging
- `database_url` (postgresql+psycopg2://...) — overridden by .env; used by SQLAlchemy engine
- `cors_origins` (comma-separated URLs) → `cors_origins_list` property
- `random_seed` (int=42) → reproducibility for data generation
- `model_dir` (str="data/models") → artifact persistence path
- `data_dir` (str="data/raw") → synthetic data path
- `log_level` (INFO/DEBUG/WARNING/ERROR/CRITICAL) — validated

## 6. Glossary

| Term | Definition |
|------|-----------|
| `ET_0` | Reference evapotranspiration (mm/day), computed from temperature, humidity, wind, radiation |
| `K_c` | Crop coefficient (dimensionless), varies by crop type and growth stage |
| `ET_c` | Crop evapotranspiration = ET_0 × K_c (mm/day) |
| `water_demand_m3` | Demand in cubic metres per day = ET_c × farm_area_hectares × 10 |
| `s_i` | Satisfaction ratio = x_i / predicted_demand_i (∈ [0,1]) |
| `surplus_i` | utility_i - batna_utility_i; positive → above BATNA, negative → below BATNA |
| `Jain's Index` | (Σs_i)² / (n × Σs_i²); measures fairness of allocation across farmers |
| `BATNA` | Best Alternative To a Negotiated Agreement; fallback utility if no consensus is reached |
| `Nash objective` | Σlog(max(surplus_i, 1e-6)); logarithmic sum of surpluses, higher is better |
| `concession_progress_threshold` | 0.1; minimum fraction of total water conceded to prevent premature stagnation termination |
| `min_nash_improvement` | 1e-4; minimum Nash objective delta to count as a genuine improvement |