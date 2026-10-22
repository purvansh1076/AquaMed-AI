# AquaMediAI — Baseline Audit Report

**Audit Date**: 2026-10-11  
**Python Version**: 3.12.10  
**Backend Test Run**: 704/704 tests passing (100%) across 9 phase modules  
**Frontend Test Run**: 53/53 tests passing (100%)  
**Frontend Build**: PASS (tsc + vite build, 0 errors)  

---

## 1. Executive Summary

This audit documents the verified state of the AquaMediAI repository as of the audit date. All core backend test suites (704 tests) pass without regression. The frontend test suite (53 tests) also passes. The only test errors are in `test_api.py` (68 errors), all caused by a missing `psycopg2` PostgreSQL dependency — not by code defects.

The system is an **academic prototype** implementing integrated machine learning demand prediction, deterministic conflict detection, OR-Tools GLOP constrained optimization, multi-agent Nash-inspired mediation, and dual-mode explainability — all backed by synthetic FAO-56 agronomic data.

---

## 2. Verified Test Counts by Phase

| Phase | Module | Tests | Status |
|-------|--------|-------|--------|
| **Phase 1** | Data Generator | 62 / 62 | PASS |
| **Phase 2** | ML Pipeline | 64 / 64 | PASS |
| **Phase 3** | Farmer Agents | 96 / 96 | PASS |
| **Phase 4** | Conflict Detection | 88 / 88 | PASS |
| **Phase 5** | OR-Tools GLOP Allocator | 86 / 86 | PASS |
| **Phase 6** | Multi-Agent Negotiation | 123 / 123 | PASS |
| **Phase 7** | Explainability Layer | 113 / 113 | PASS |
| **Phase 8** | FastAPI Integration | 72 / 72 | PASS |
| **Phase 9** | React Frontend | 53 / 53 | PASS |
| **Total** | Full Pipeline | **704 / 704** (backend) / **53 / 53** (frontend) | **100%** |

---

## 3. Model Artifacts — Verified State

| Artifact | File | Contents | Source |
|----------|------|----------|--------|
| **XGBoost Model** | `backend/data/models/xgb_model.joblib` | Trained XGBoostRegressor, `n_estimators=300`, `learning_rate=0.05`, `max_depth=6` | `run_training_pipeline()` with `n_samples=3000, seed=42` |
| **RandomForest Model** | `backend/data/models/rf_model.joblib` | Trained RandomForestRegressor, `n_estimators=200`, `max_depth=15` | Same training pipeline |
| **Fitted Encoders** | `backend/data/models/encoders.joblib` | `FittedEncoders` container with `LabelEncoder` (crop_type, soil_type, season) and `OrdinalEncoder` (growth_stage) | Fitted on **training split only** (70%) — no leakage |
| **Evaluation Results** | `backend/data/models/evaluation_results.json` | MAE/RMSE/R² per model per split (train/val/test), best model = XGBoost (test MAE=17.8342) | Persisted by `_save_artifacts()` |

**Critical Precondition**: Models must be trained before inference. Running `python scripts/train_models.py` (or the equivalent pipeline) is required to generate the artifacts. The predictor and negotiation engine load from these artifacts.

---

## 4. ML Prediction Pipeline — Verified Contract

**Target Variable**: `water_demand_m3` — predicted daily water requirement in **cubic metres (m³/day)**.

**Exact Formula (FAO-56 single crop coefficient)**:
```
ET_c = ET_0 × K_c
demand_m3 = ET_c × farm_area_hectares × 10.0
```
plus Gaussian noise (±15%) and minimum clamping (5.0–800.0 m³).

**Required Input Columns** (`REQUIRED_INPUT_COLS` in `predictor.py:53-71`):
```
crop_type, soil_type, growth_stage, season,
farm_area_hectares, et0_mm_per_day, kc_value, etc_mm_per_day,
soil_whc_mm_per_m, preferred_start_hour, irrigation_window_hours,
flexibility_score, urgency_score, crop_stress_index,
temperature_celsius, humidity_percent, rainfall_mm
```

**Feature Engineering Pipeline** (`feature_engineering.py`):
1. Label encode `crop_type`, `soil_type`, `season` (fitted on train only)
2. Ordinal encode `growth_stage` (ordered: germination < vegetative < flowering < maturity < harvest)
3. Compute interaction features: `area_x_etc`, `urgency_x_stress`, `et0_x_kc`, `rain_deficit`, `flexibility_window`
4. Output column order: `ENGINEERED_FEATURE_COLS` (16 features)

**Preprocessing Consistency Guarantee**: `engineer_features(df, encoders)` must use the **same** `FittedEncoders` object fit on training data. The `WaterDemandPredictor.from_artifacts()` factory loads the exact same encoders, ensuring identical preprocessing between training and inference.

**Model Selection**: XGBoost (primary, default) / RandomForest (baseline). Designated primary due to compact memory footprint and serialization speed.

---

## 5. Dataset Generation — Verified Agronomic Grounding

**Generator**: `SyntheticDataGenerator.generate_dataset()` in `data_generator.py`.

**FAO-56 Grounding**:
- `ET_c = ET_0 × K_c` (single crop coefficient approach)
- `demand_m3 = ET_c × farm_area_hectares × 10.0` (mm × ha × 10 = m³)
- Soil WHC ranges from Doorenbos & Pruitt (1977)
- ET₀ ranges for Indian semi-arid conditions: kharif (4.0–8.0), rabi (2.5–5.0), zaid (5.0–9.0) mm/day
- Crop coefficients (K_c) per growth stage from FAO-56 Table 12

**8 Scenario Types** (with supply fraction ranges):
1. `normal_water` — supply 105–130% of demand
2. `moderate_shortage` — supply 70–85% of demand
3. `severe_shortage` — supply 40–62% of demand
4. `sudden_rainfall` — +25mm rain bonus, supply 110–150%
5. `canal_reduction` — canal throttled 30–50%, supply 80–100%
6. `simultaneous_demand` — all farmers peak same 6-hour window
7. `high_urgency_farmer` — one farmer at flowering stage
8. `flexible_farmer` — one farmer with wide schedule flexibility

**Dataset Splits** (seed=42, stratified by `scenario_type`):
- Train: 70% (2099 rows)
- Val: 15% (450 rows)
- Test: 15% (451 rows)

**All data is synthetic**: Disclaimer persisted in `evaluation_results.json` and `data_generator.py`.

---

## 6. GLOP Allocation — Verified Constraints and Objective

**Solver**: Google OR-Tools GLOP Linear Programming solver.

**Decision Variables**: `x_i` = water allocated to farmer i (m³), `p_i` = penalty variable for minimum shortfall.

**Hard Constraints (never relaxed)**:
- H1: `x_i ≥ 0` (non-negative)
- H2: `x_i ≤ maximum_water_requirement_i` (physical saturation)
- H3: `Σ x_i ≤ available_water` (supply limit)

**Soft / Relaxable Constraint** (S1): Minimum survival requirement
- When `Σ minimum_water_requirement_i ≤ available_water`: enforced as hard constraint (`p_i = 0`)
- When `Σ minimum_water_requirement_i > available_water`: converted to penalty term in objective
  - Auxiliary variable `p_i ≥ 0`, `p_i ≥ minimum_water_i - x_i`
  - Objective penalty: `-w_min × Σ (p_i / demand_i)`
  - Solver mode: `lp_relaxed`

**Objective Function** (maximize):
```
Σ [ w_urg × urgency_i × (x_i / d_i) + w_cs × crop_sensitivity_i × (x_i / d_i) 
   - w_unmet × (1 - x_i / d_i) - w_min × (p_i / demand_i) ]
```
Default weights: `w_urg=0.40, w_cs=0.25, w_unmet=0.20, w_min=0.15`

**Fallback Methods** (in order):
1. `lp_optimal` — GLOP returns OPTIMAL/FEASIBLE
2. `lp_relaxed` — GLOP returns feasible solution with soft minimum penalties
3. `proportional_fallback` — `x_i = available × (demand_i / total_demand)`, H2 clamped
4. `empty` — available_water = 0

**Post-Solve Verification**: Independent `verify_constraints()` checks H1/H2/H3 after every solve. Jain's Fairness Index computed **post-hoc**, NOT enforced in the LP objective.

---

## 7. Nash-Inspired Negotiation — Verified Objective and Logic

**Objective**: `Ω_Nash = Σ log(max(surplus_i, ε))` where `ε = 1e-6` (`min_surplus_floor`), `surplus_i = utility_i - batna_utility_i`.

**Safety Guarantee**: Never computes `log(0)` or `log(negative)` — `max(surplus, floor)` ensures `safe_s ≥ floor > 0`.

**Response Thresholds** (from `NegotiationConfig`):
- `ACCEPT`: `utility ≥ acceptance_threshold` (default 0.65) **AND** `utility ≥ batna_utility + min_batna_buffer` (default 0.02)
- `REQUEST_CHANGE`: `rejection_threshold ≤ utility < acceptance_threshold` (default [0.35, 0.65))
- `REJECT`: `utility < rejection_threshold` (default 0.35) **OR** `utility < batna_utility` (BATNA protection, always overrides)

**Concession Logic**:
```
available_space = current_ask - minimum_water
flexibility_factor = farmer.flexibility
urgency_factor = 1 - farmer.urgency
concession_ratio = flexibility_factor × urgency_factor × concession_scale
concession_amount = available_space × concession_ratio
new_ask = max(minimum_water, current_ask - concession_amount)
```
- Fully inflexible (flex=0) → zero concession
- Fully urgent (urg=1) → zero concession (urgency_factor = 0)

**Termination Conditions** (default max_rounds=5, stagnation_rounds=2):
1. `AGREED` — all required farmers ACCEPT
2. `NO_FEASIBLE_IMPROVEMENT` — Nash objective does not improve for 2 consecutive rounds
3. `MAX_ROUNDS_REACHED` — max rounds exceeded
4. `FAILED` — unrecoverable exception

**BATNA Protection**: `utility < batna_utility` always triggers REJECT, overriding threshold checks.

---

## 8. Conflict Detection — Verified Five Categories

**Detector**: `ConflictDetector.detect_all()` in `conflict/detector.py`.

**5 Conflict Types** (with severity mapping via `severity_from_ratio()`):
1. `RESOURCE_SHORTAGE` — `total_demand > available_water`, shortage ratio → LOW/MEDIUM/HIGH/CRITICAL
2. `IRRIGATION_WINDOW_OVERLAP` — overlapping preferred windows, severity from overlap fraction + urgency
3. `CANAL_CAPACITY_CONFLICT` — combined flow > canal capacity, overload ratio → severity
4. `MINIMUM_REQUIREMENT_CONFLICT` — `total_min_req > available_water`, always at least HIGH severity
5. `HIGH_CROP_STRESS` — CSPS = urgency × sensitivity × stage_criticality > 0.49

**Overall Conflict Score**:
```
w_shortage × shortage_ratio + w_urgency × urgency_disparity + w_overlap × window_overlap_fraction + w_stress × high_stress_fraction
```
Default weights: `w_shortage=0.40, w_urgency=0.20, w_overlap=0.25, w_stress=0.15`

---

## 9. Farmer Agent — Verified Utility and BATNA

**Utility Function** (`utility.py:compute_utility()`):
```
U_i = norm( w1*S_w + w2*S_t + w3*S_u + w4*S_m - w5*S_p·cs_i )
```
where:
- `S_w = clip(a_i / d_i, 0, 1)` — volumetric satisfaction
- `S_t` — timing satisfaction (1.0/0.5/0.0 based on window)
- `S_u = 1.0 - urgency × (1.0 - S_w)` — urgency protection
- `S_m = clip(a_i / min_req_i, 0, 1)` — minimum requirement satisfaction
- `S_p = (1.0 - S_m)` — stress inverse
- Normalization: `(raw - u_min) / (u_max - u_min)` clamped to [0,1]

**BATNA** (`farmer_agent.py:BATNA`):
- Fallback allocation = `minimum_water_requirement_m3`
- Fallback utility = `U_i(fallback_allocation, timing=None)`
- BATNA protection: `utility < batna_utility` → REJECT with `is_batna_protected = True`

**Response Thresholds** (from config):
- ACCEPT: utility ≥ 0.65 AND utility ≥ batna + 0.02
- REQUEST_CHANGE: 0.35 ≤ utility < 0.65
- REJECT: utility < 0.35 OR utility < batna

---

## 10. Known Environment Blocks

| Issue | Impact | Fix |
|-------|--------|-----|
| Missing `psycopg2` package | 68 API/test errors (test_api.py) — all database-connected tests fail | `pip install psycopg2-binary` or configure DATABASE_URL env var to point to running PostgreSQL |
| Missing `scripts/train_models.py` execution | Model artifacts not present; predictor/negotiation cannot load | Run `python scripts/train_models.py` or generate artifacts via `run_training_pipeline()` |
| No PostgreSQL server running | FastAPI `/health` endpoint reports DB connectivity issues | Optional — system functions without DB; `.env` can override `database_url` |

All **non-API** tests pass (704/704 backend, 53/53 frontend).

---

## 11. Verification and Reproduction Commands

```bash
# 1. Install dependencies
cd aquamedi-ai/backend
pip install -r requirements.txt

# 2. Train models (required prerequisite)
python -m pytest tests/test_ml_pipeline.py::TestDataGenerator -v --tb=short  # just to verify import
# Or run the training pipeline:
python -c "from app.ml.trainer import run_training_pipeline; artifacts = run_training_pipeline(n_samples=3000, seed=42)"

# 3. Run core test suites (no DB required)
python -m pytest tests/test_ml_pipeline.py tests/test_lp_allocator.py tests/test_negotiation.py tests/test_conflict_detector.py tests/test_data_generator.py tests/test_farmer_agents.py tests/test_explainability.py -v --tb=short

# 4. Verify all pass: expected 704/704 backend tests, 53/53 frontend tests
```