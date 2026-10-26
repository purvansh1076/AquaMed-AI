# AquaMediAI Phase 12 — Local End-to-End Shadow Smoke Test Report

**Date**: October 25, 2026  
**Status**: Completed & Verified  
**Operating Mode**: Local Smoke Test & Verification  
**Default Configuration**: `ENABLE_CANDIDATE_V3_SHADOW=false` (Disabled by Default)  
**Safety Invariant**: Candidate v3 unpromoted, production artifacts unmodified, zero operational influence on allocations or negotiations.

---

## 1. Executive Summary

Phase 12 conducts an end-to-end local smoke test of the AquaMediAI backend, frontend, and Candidate v3 shadow evaluation infrastructure. 

The smoke tests verified:
1. Backend health endpoints (`/health`, `/api/v1/health`) return HTTP 200 with complete service status.
2. Production prediction endpoints under default configuration (`ENABLE_CANDIDATE_V3_SHADOW=false`) behave normally, returning `null` for shadow fields with identical legacy outputs.
3. In isolated shadow-enabled test configurations:
   - Candidate v3 artifacts load correctly.
   - Historical analysis (`observed_historical`) with observed rainfall produces valid shadow comparisons.
   - Forward scheduling (`forecast_forward`) without a forecast returns `status="unavailable"`, strictly rejecting silent lookahead substitution of observed rainfall.
   - Forward scheduling with genuine forecasts or documented antecedent fallbacks succeeds.
   - Corrupted or failing candidate artifacts do **not** fail the primary prediction.
   - Shadow execution has **zero** effect on water allocation, conflict detection, or farmer negotiations.
4. The 21-feature schema (`set_c_enriched`), volumetric units ($\text{m}^3/\text{day}$), and rainfall provenance are confirmed.
5. All 816 backend tests pass, all 57 frontend tests pass, and the frontend production build compiles cleanly.

---

## 2. Actual Endpoint Responses & Smoke Test Payloads

### 2.1 Task 1: Backend Startup & Health Endpoints

#### Root Health Endpoint: `GET /health`
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
```json
{
  "status": "healthy"
}
```

#### API v1 Health Endpoint: `GET /api/v1/health`
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

---

### 2.2 Task 2: Prediction Endpoint with Shadow Disabled (Default)

**Endpoint**: `POST /api/v1/predictions`  
**Configuration**: `ENABLE_CANDIDATE_V3_SHADOW=false` (default)  
**Request Payload**:
```json
{
  "farmer_data": {
    "farmer_id": "FARMER_SMOKE_01",
    "crop_type": "wheat",
    "soil_type": "loam",
    "growth_stage": "flowering",
    "season": "rabi",
    "farm_area_hectares": 3.0,
    "et0_mm_per_day": 4.5,
    "kc_value": 1.15,
    "etc_mm_per_day": 5.175,
    "soil_whc_mm_per_m": 125.0,
    "preferred_start_hour": 6,
    "irrigation_window_hours": 4,
    "flexibility_score": 0.5,
    "urgency_score": 0.6,
    "crop_stress_index": 0.45,
    "temperature_celsius": 27.5,
    "humidity_percent": 48.0,
    "rainfall_mm": 0.0,
    "soil_moisture_percent": 30.0,
    "wind_speed_m_per_s": 2.2,
    "solar_radiation_mj_m2": 19.0
  },
  "model_name": "XGBoost"
}
```

**Actual Response Payload**:
```json
{
  "farmer_id": "FARMER_SMOKE_01",
  "predicted_water_demand_m3": 5.0,
  "model_name": "XGBoost",
  "model_version": "1.0.0",
  "warning": "Predicted water demand (-54.91 m3/day) is below minimum physical threshold; clamped to 5.00 m3/day.",
  "input_summary": {
    "crop_type": "wheat",
    "soil_type": "loam",
    "growth_stage": "flowering",
    "season": "rabi",
    "farm_area_hectares": 3.0,
    "et0_mm_per_day": 4.5,
    "kc_value": 1.15,
    "temperature_celsius": 27.5,
    "rainfall_mm": 0.0
  },
  "shadow_agronomic_estimate_m3": 221.79,
  "shadow_comparison": {
    "status": "available",
    "agronomic_demand_m3": 221.79,
    "legacy_prediction_m3": 5.0,
    "difference_m3": -216.79,
    "difference_percent": -97.75,
    "method": "FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall",
    "application_efficiency": 0.7,
    "is_empirical_error": false,
    "input_validation": {
      "is_valid": true,
      "errors": []
    },
    "provenance_note": "Legacy ML models (RandomForest, XGBoost) were trained on synthetic data. The agronomic estimate is a deterministic physical calculation, NOT measured delivery.",
    "disclaimer": "Differences between legacy predictions and deterministic baseline are comparison metrics, NOT empirical model error, because no measured real-world delivery ground truth is available."
  },
  "shadow_candidate_v3_estimate_m3": null,
  "shadow_candidate_v3_comparison": null
}
```
*Verification*: Primary model and FAO-56 comparison operate normally; Candidate v3 shadow fields are `null` as required by the default safety configuration.

---

### 2.3 Task 3: Isolated Shadow Mode Smoke Verification

All tests in this section run within an isolated runtime environment (`ENABLE_CANDIDATE_V3_SHADOW=true`).

#### 3A. Historical Analysis with Observed Rainfall
- **Input**: `rainfall_input_mode="observed_historical"`, `rainfall_observed_mm=12.0`
- **Candidate v3 Output**: `candidate_estimate_m3=0.0`, `status="available"`
- **Deterministic Reference**: `0.0 m3/day` (12 mm rainfall satisfies daily requirements)
- **Disagreement**: `0.0 m3/day`
- **Rainfall Source**: `"rainfall_observed_mm"`

```json
{
  "shadow_candidate_v3_estimate_m3": 0.0,
  "shadow_candidate_v3_comparison": {
    "status": "available",
    "candidate_version": "candidate_v3_twostage_xgb",
    "candidate_estimate_m3": 0.0,
    "deterministic_reference_m3": 0.0,
    "absolute_disagreement_m3": 0.0,
    "signed_disagreement_m3": 0.0,
    "input_mode": "observed_historical",
    "rainfall_source": "rainfall_observed_mm",
    "rainfall_mm_used": 12.0,
    "is_valid": true,
    "reasons": [],
    "disclaimer": "Candidate v3 shadow output is an offline research surrogate approximating theoretical FAO-56 calculations. It does NOT represent measured field deliveries and does NOT control dispatch.",
    "reference_estimate_m3": 0.0,
    "error_reason": null
  }
}
```

#### 3B. Forward Morning Scheduling with Genuine Forecast
- **Input**: `rainfall_input_mode="forecast_forward"`, `rainfall_forecast_mm=4.5`
- **Candidate v3 Output**: `candidate_estimate_m3=32.43 m3/day`
- **Deterministic Reference**: `30.32 m3/day`
- **Disagreement**: `absolute_disagreement_m3=2.11 m3/day`
- **Rainfall Source**: `"rainfall_forecast_mm"`

```json
{
  "shadow_candidate_v3_estimate_m3": 32.43,
  "shadow_candidate_v3_comparison": {
    "status": "available",
    "candidate_version": "candidate_v3_twostage_xgb",
    "candidate_estimate_m3": 32.43,
    "deterministic_reference_m3": 30.32,
    "absolute_disagreement_m3": 2.11,
    "signed_disagreement_m3": 2.11,
    "input_mode": "forecast_forward",
    "rainfall_source": "rainfall_forecast_mm",
    "rainfall_mm_used": 4.5,
    "is_valid": true,
    "reasons": []
  }
}
```

#### 3C. Forward Scheduling Missing Forecast (Anti-Lookahead Rule)
- **Input**: `rainfall_input_mode="forecast_forward"`, `rainfall_forecast_mm=null`, `rainfall_observed_mm=15.0`
- **Result**: `status="unavailable"`, `candidate_estimate_m3=null`
- **Diagnostic Reason**: *"Forward scheduling mode requires a weather forecast (rainfall_forecast_mm). Missing rainfall forecast. Future observed rainfall cannot be assumed."*
- *Verification*: The system strictly rejected using future observed rainfall in a forward scheduling context.

#### 3D. Forward Scheduling with Antecedent Fallback
- **Input**: `rainfall_input_mode="forecast_forward"`, `rainfall_forecast_mm=null`, `rainfall_lag1_mm=2.0`
- **Result**: `status="available"`, `candidate_estimate_m3=80.51 m3/day`
- **Rainfall Source**: `"rainfall_lag1_mm (antecedent fallback)"`

#### 3E. Artifact Corruption / Exception Failover
- **Fault Injected**: Mocked unhandled exception inside candidate adapter (`RuntimeError: Simulated filesystem artifact corruption`).
- **Response**: HTTP 200 OK.
- **Primary Prediction**: `predicted_water_demand_m3=5.0` (unaffected).
- **Shadow Comparison**:
  ```json
  {
    "shadow_candidate_v3_estimate_m3": null,
    "shadow_candidate_v3_comparison": {
      "status": "failed",
      "candidate_version": "candidate_v3",
      "error_reason": "Shadow execution failed: Simulated filesystem artifact corruption",
      "reasons": [
        "Shadow execution failed: Simulated filesystem artifact corruption"
      ]
    }
  }
  ```
- *Verification*: Shadow failures never crash or disrupt the primary prediction service.

#### 3F. Allocation and Negotiation Non-Interference Verification
Two complete scenario runs were executed on `scenario_type="moderate_shortage"`, `n_farmers=4`, `seed=42`: one with shadow mode enabled and one with shadow mode disabled.

| Metric | Shadow Disabled (Baseline) | Shadow Enabled (Test) | Match Result |
| :--- | :--- | :--- | :--- |
| **Total Water Demand** | $232.34\,\text{m}^3$ | $232.34\,\text{m}^3$ | **EXACT MATCH** |
| **Available Water** | $739.99\,\text{m}^3$ | $739.99\,\text{m}^3$ | **EXACT MATCH** |
| **Total Allocated Water** | $232.34\,\text{m}^3$ | $232.34\,\text{m}^3$ | **EXACT MATCH** |
| **Per-Farmer Allocations** | `[5.00, 5.00, 93.86, 128.48]` | `[5.00, 5.00, 93.86, 128.48]` | **EXACT MATCH** |
| **Negotiation Agreement** | `agreed` | `agreed` | **EXACT MATCH** |
| **Fairness Score** | $0.803$ | $0.803$ | **EXACT MATCH** |
| **Shadow Diagnostics Present** | N/A | Included in `predictions` | **VERIFIED** |

---

## 3. Feature Schema & Unit Verification

The feature schema was checked directly from `backend/data/models/candidate_v3/feature_schema.json`:
- **Selected Feature Set**: `set_c_enriched`
- **Total Features**: 21
- **Numeric Features (18)**:
  `temperature_celsius`, `diurnal_temp_range_celsius`, `humidity_percent`, `wind_speed_m_per_s`, `solar_radiation_mj_per_m2`, `vpd_proxy_kpa`, `rainfall_lag1_mm`, `rainfall_antecedent_3d_mm`, `rainfall_antecedent_7d_mm`, `temp_rolling_mean_3d_celsius`, `temp_rolling_mean_7d_celsius`, `solar_rad_rolling_mean_3d`, `doy_sin`, `doy_cos`, `farm_area_hectares`, `rainfall_mm`, `temp_vpd_interaction`, `antecedent_rain_ratio`.
- **Categorical Features (3)**:
  `crop_type`, `growth_stage`, `season`.
- **Leakage Audit Verdict**: `ZERO_LEAKAGE_CONFIRMED`.
- **Target Unit**: $\text{m}^3/\text{day}$ (volumetric demand).
- **Weather Units**: Rainfall in $\text{mm}$, temperature in $^\circ\text{C}$, VPD in $\text{kPa}$, solar radiation in $\text{MJ}/\text{m}^2$.

---

## 4. Test Suite Execution Results

### 4.1 Backend Pytest Suite
```bash
.venv\Scripts\python.exe -m pytest backend/tests/
```
**Outcome**: **816 passed**, 5 warnings in 21.55s.  
All existing Phase 1–10 tests, Phase 11 shadow integration tests (18 tests), and Phase 12 smoke tests (9 tests) passed with zero regressions.

### 4.2 Frontend Vitest Suite
```bash
npm run test -- --run
```
**Outcome**: **57 passed** across 7 test files in 38.83s.  
All component, explainability, scenario, and presentation mode tests passed cleanly.

### 4.3 Frontend Production Build
```bash
npm run build
```
**Outcome**: Clean build via `tsc -b && vite build` in 5.12s:
- `dist/index.html`: 0.76 kB
- `dist/assets/index-_SEg_cS5.css`: 26.39 kB
- `dist/assets/index-CDD8He6j.js`: 862.86 kB

---

## 5. Files Changed & Added

| File | Status | Description |
| :--- | :--- | :--- |
| `backend/scripts/smoke_test_phase12.py` | Added | End-to-end standalone smoke test script executing all tasks and printing JSON diagnostics. |
| `backend/tests/test_phase12_smoke_test.py` | Added | 9 pytest automated smoke tests verifying health, default behavior, shadow modes, failovers, non-interference, and schema. |
| `docs/PHASE12_LOCAL_SMOKE_TEST_REPORT.md` | Added | This verification document. |

*Note*: No production models, candidate artifacts, or existing configuration defaults were modified. `ENABLE_CANDIDATE_V3_SHADOW` remains `false`.

---

## 6. Exact Local Reproduction Commands

```bash
# 1. Activate virtual environment
cd "C:\Users\lenovo\OneDrive\Attachments\Desktop\Technical Seminar\aquamedi-ai"
.venv\Scripts\activate

# 2. Run the Phase 12 standalone smoke test script
python backend/scripts/smoke_test_phase12.py

# 3. Run the Phase 12 pytest smoke test suite
pytest backend/tests/test_phase12_smoke_test.py -v

# 4. Run all validation suites (Phase 9, 10, 11, 12)
pytest backend/tests/test_phase9_error_analysis.py backend/tests/test_phase10_independent_validation.py backend/tests/test_phase11_shadow_integration.py backend/tests/test_phase12_smoke_test.py -v

# 5. Run the complete backend test suite
pytest backend/tests/

# 6. Run frontend tests and build
cd frontend
npm run test -- --run
npm run build
```
