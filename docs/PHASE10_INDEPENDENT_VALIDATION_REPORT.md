# AquaMediAI Phase 10 — Independent Candidate v3 Audit Report

**Date**: October 2026  
**Auditor**: Independent Machine Learning Audit & Agronomic Systems Verification Team  
**Scope**: Candidate v3 Offline Artifacts (`backend/data/models/candidate_v3/`)  
**Pilot Region**: Ahmednagar District, Central Maharashtra, India (Pravara & Mula Canal Systems, Centroid: 19.09° N, 74.74° E, Elevation: 540 m)  
**Primary Target Variable**: Theoretical daily net crop-water requirement ($m^3/\text{day}$)  
**Final Audit Verdict**: `VALIDATION_PASSED_AS_OFFLINE_SURROGATE` | `CONDITIONAL_GO_FOR_SHADOW_MODE_DESIGN`  

---

## 1. Executive Summary & Mandatory Scientific Disclaimer

Phase 10 conducts an independent, read-only audit of the **Candidate v3 Two-Stage Model** artifacts produced in Phase 9. No models were retrained, modified, promoted, or activated in the live API.

> [!CAUTION]
> ### Crucial Agronomic & Scientific Notice
> **All target values evaluated in this pipeline represent theoretical crop-water demands calculated deterministically using the FAO-56 Penman-Monteith single-crop coefficient method and USDA-SCS effective precipitation equation.**
> - They are **NOT** measured ground-truth farm-gate water deliveries, metered canal discharges, or soil moisture sensor readings.
> - High model accuracy ($R^2 = 0.9902$, $\text{MAE} = 1.39\text{ m}^3/\text{day}$) demonstrates **surrogate mathematical fidelity to biophysical mathematical equations**, not empirical real-world predictive validity against farmer behavior or soil dynamics.
> - Production models (`rf_model.joblib`, `xgb_model.joblib`, `encoders.joblib`) remain 100% active and unaltered in the live API. Candidate v3 remains strictly isolated in `backend/data/models/candidate_v3/`.

---

## 2. Independent Metric Recomputation & Discrepancy Verification

All evaluation metrics were independently recomputed directly from the row-level predictions in [`backend/data/models/candidate_v3/test_predictions_v3.csv`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/data/models/candidate_v3/test_predictions_v3.csv) across the complete 2025 test partition ($n=976$ samples across 365 calendar dates):

### 2.1 Independent Recomputation Table (2025 Test Partition, $n=976$)

| Evaluation Metric | Phase 9 Reported | Phase 10 Recomputed | Absolute Delta | Audit Finding |
| :--- | :---: | :---: | :---: | :--- |
| **Overall Mean Absolute Error (MAE)** | $1.3865\text{ m}^3/\text{day}$ | **$1.3865\text{ m}^3/\text{day}$** | 0.0000 | **EXACT MATCH** |
| **Overall Root Mean Squared Error (RMSE)**| $2.3985\text{ m}^3/\text{day}$ | **$2.3985\text{ m}^3/\text{day}$** | 0.0000 | **EXACT MATCH** |
| **Explained Variance ($R^2$)** | 0.9902 | **0.9902** | 0.0000 | **EXACT MATCH** |
| **Mean Signed Bias** | $-0.3216\text{ m}^3/\text{day}$ | **$-0.3215\text{ m}^3/\text{day}$** | 0.0001 | **MATCH (Floating-point precision)** |
| **Maximum Absolute Residual** | $23.2997\text{ m}^3/\text{day}$ | **$23.3037\text{ m}^3/\text{day}$** | 0.0040 | **MATCH (4-decimal rounding in CSV)** |
| **Stage 1 Classification Accuracy** | 99.18% | **99.18%** (968/976) | 0.00% | **EXACT MATCH** |
| **Stage 1 Zero-Demand Precision** | 96.90% | **96.90%** (219/226) | 0.00% | **EXACT MATCH** |
| **Stage 1 Zero-Demand Recall** | 99.55% | **99.55%** (219/220) | 0.00% | **EXACT MATCH** |
| **Stage 1 Zero-Demand $F_1$ Score** | 0.9821 | **0.9821** | 0.0000 | **EXACT MATCH** |
| **False-Positive Zero Cases ($\text{FP}_{\text{zero}}$)**| 7 cases | **7 cases** | 0 | **EXACT MATCH** |
| **False-Negative Zero Cases ($\text{FN}_{\text{zero}}$)**| 1 case | **1 case** | 0 | **EXACT MATCH** |
| **Positive-Demand Subset MAE** ($n=756$)| $1.7853\text{ m}^3/\text{day}$ | **$1.7853\text{ m}^3/\text{day}$** | 0.0000 | **EXACT MATCH** |
| **Positive-Demand Subset RMSE** | $2.7222\text{ m}^3/\text{day}$ | **$2.7221\text{ m}^3/\text{day}$** | 0.0001 | **MATCH (Rounding)** |
| **Positive-Demand Subset $R^2$** | 0.9842 | **0.9842** | 0.0000 | **EXACT MATCH** |
| **Zero-Demand Subset MAE** ($n=220$) | $0.0162\text{ m}^3/\text{day}$ | **$0.0162\text{ m}^3/\text{day}$** | 0.0000 | **EXACT MATCH** |
| **Zero-Demand Subset RMSE** | $0.2403\text{ m}^3/\text{day}$ | **$0.2400\text{ m}^3/\text{day}$** | 0.0003 | **MATCH (Rounding)** |

### 2.2 Sample and Target Provenance Alignment
- **Date Range Alignment**: Exactly 365 unique dates spanning `2025-01-01` to `2025-12-31`. No missing dates, leap-day errors, or duplicate timestamps.
- **Crop Representation**: Sugarcane ($n=365$), Cotton ($n=170$), Wheat ($n=121$), Groundnut ($n=117$), Maize ($n=107$), Soybean ($n=96$) totaling 976 rows.
- **Physical Scale & Units**: All predictions and targets correspond to a canonical standard plot of $1.0\text{ ha}$ with volumetric units in cubic metres per day ($m^3/\text{day}$).
- **Non-Negative Guarantee**: Zero predictions are negative ($\min(\hat{y}) = 0.0000\text{ m}^3/\text{day}$, count of $\hat{y} < 0 = 0$).

---

## 3. Audit of Partitioning, Threshold Calibration, and Leakage Isolation

A code and data audit of [`backend/app/ml/candidate_v3_experiments.py`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/ml/candidate_v3_experiments.py) confirmed complete temporal and procedural separation:

```
Multi-Year Timeline (2021 ──► 2025) ─────────────────────────────────────────────────────────────►
[── Training Partition: 3 Full Years ──] [── Validation: 1 Full Year ──] [── Final Test: 1 Full Year ──]
  2021-01-01 ───► 2023-12-31               2024-01-01 ───► 2024-12-31      2025-01-01 ───► 2025-12-31
  2,928 rows (1,095 unique dates)          978 rows (366 unique dates)     976 rows (365 unique dates)
  - Preprocessor fitted strictly here      - Model selection strictly here - Evaluated ONCE for audit
  - Classifiers/Regressors fitted here     - Threshold tau calibrated here - ZERO tuning or lookahead
```

### Verified Procedural Invariants:
1. **Preprocessor Isolation**: The `ColumnTransformer` (StandardScaler on numeric columns, OneHotEncoder on categorical columns) was fitted **exclusively on the 2,928 training samples (2021–2023)**.
2. **Threshold Calibration Isolation**: The Stage 1 decision threshold $\tau = 0.20$ was chosen by sweeping candidate thresholds $\tau \in [0.2, 0.8]$ on the **2024 validation partition ($n=978$)** to minimize validation MAE ($1.4607\text{ m}^3/\text{day}$). The 2025 test set was not accessed during threshold selection.
3. **Model Selection Isolation**: Candidate configuration `two_stage_xgb_set_c` was selected over comparators because it achieved the lowest MAE on 2024 validation data. The 2025 test set was evaluated exactly once as an untouched holdout.

---

## 4. Feature Leakage & Prediction-Time Availability Audit

### 4.1 Target Component Exclusion Audit
The feature schema in [`backend/data/models/candidate_v3/feature_schema.json`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/data/models/candidate_v3/feature_schema.json) was audited against all forbidden leakage columns:

| Forbidden Column | Description | In Candidate v3 Schema? | Status |
| :--- | :--- | :---: | :---: |
| `net_irrigation_m3_per_day` | Target variable | **NO** | **SAFE** |
| `net_irrigation_depth_mm` | Depth equivalent of target | **NO** | **SAFE** |
| `etc_mm_per_day` | Direct formula component ($ET_0 \times K_c$) | **NO** | **SAFE** |
| `effective_precipitation_mm` | Direct formula component (USDA-SCS rainfall) | **NO** | **SAFE** |
| `area_x_etc` | Tautological target duplicate | **NO** | **SAFE** |
| `sample_key` / `date` | Identifiers / timestamps | **NO** | **SAFE** |

Candidate v3 input features are strictly limited to observable meteorological variables (`temperature_celsius`, `diurnal_temp_range_celsius`, `humidity_percent`, `wind_speed_m_per_s`, `solar_radiation_mj_per_m2`, `vpd_proxy_kpa`, `rainfall_mm`, antecedent lags, harmonics, `farm_area_hectares`, `crop_type`, `growth_stage`, `season`, and non-linear meteorological interaction terms).

### 4.2 Prediction-Time Availability Audit of Same-Day Rainfall (`rainfall_mm`)

A primary finding of Phase 9 was that adding same-day gross rainfall `rainfall_mm` reduced test MAE from $6.58\text{ m}^3/\text{day}$ to $1.39\text{ m}^3/\text{day}$. The audit investigated whether `rainfall_mm` is realistically available at prediction time in the live application:

#### Case A: Historical & End-of-Day Irrigation Accounting Mode
- **Context**: Canal managers or agricultural officers review daily water consumption for past dates (e.g., yesterday, last month, end of season).
- **Availability**: **100% Available**. Measured daily precipitation from local weather stations (IMD Ahmednagar, NASA POWER, or local telemetry) is known.
- **Verdict**: Fully defensible and legitimate.

#### Case B: Forward Real-Time Morning Irrigation Scheduling Mode (e.g., 06:00 AM)
- **Context**: A farmer or canal operator requests water requirement for the current day at 06:00 AM before rain has fallen.
- **Availability**: **NOT Available as an observation**. Today's actual rainfall has not occurred yet.
- **Risk**: Supplying observed rainfall in this forward operational context constitutes **lookahead bias (treating unavailable future events as known facts)**.
- **Operational Requirement**: In a forward scheduling operational mode, the live system must supply a **numerical weather forecast** (`rainfall_forecast_mm` from IMD / ECMWF) or fallback to antecedent rainfall (`rainfall_lag1_mm`) with clear confidence intervals reflecting forecast uncertainty.

---

## 5. Audit of Two-Stage Zero-Demand Decision Rule & Outliers

### 5.1 Decision Rule Mechanics
The two-stage decision rule is:
$$\hat{y} = \begin{cases} 0.0 & \text{if } P(\text{Demand} = 0) \ge \tau \\ \max(0.0, \hat{y}_{\text{reg}}) & \text{otherwise} \end{cases}$$
With $\tau = 0.20$ calibrated on validation data.

### 5.2 Forensic Inspection of the 7 False-Positive Zero Cases ($\text{FP}_{\text{zero}}$)

False-positive zero cases represent instances where the model predicted $0.0\text{ m}^3/\text{day}$ but the theoretical target was positive. This represents potential under-irrigation / drought risk. An independent row-level inspection of all 7 cases revealed:

| Sample Key | Date | Crop & Stage | True Target ($m^3/\text{day}$) | Model Pred ($m^3/\text{day}$) | Gross Rain ($mm$) | Effective Rain ($mm$) | $ET_c$ ($mm$) | Residual Deficit | Agronomic Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `2025-07-21_soybean_vegetative_1.0ha` | 2025-07-21 | Soybean (Veg) | **0.13** | **0.00** | 3.70 | 3.68 | 3.69 | $0.01\text{ mm}$ ($13\text{ L/ha}$) | **Negligible** (Practically zero) |
| `2025-08-20_cotton_flowering_1.0ha` | 2025-08-20 | Cotton (Flower) | **0.44** | **0.00** | 3.61 | 3.59 | 3.63 | $0.04\text{ mm}$ ($44\text{ L/ha}$) | **Negligible** (Practically zero) |
| `2025-08-20_soybean_flowering_1.0ha`| 2025-08-20 | Soybean (Flower)| **0.44** | **0.00** | 3.61 | 3.59 | 3.63 | $0.04\text{ mm}$ ($44\text{ L/ha}$) | **Negligible** (Practically zero) |
| `2025-09-10_cotton_flowering_1.0ha` | 2025-09-10 | Cotton (Flower) | **1.95** | **0.00** | 4.98 | 4.94 | 5.14 | $0.20\text{ mm}$ ($195\text{ L/ha}$) | **Minor Deficit** (Rain satisfied 96%) |
| `2025-09-10_maize_flowering_1.0ha` | 2025-09-10 | Maize (Flower) | **1.95** | **0.00** | 4.98 | 4.94 | 5.14 | $0.20\text{ mm}$ ($195\text{ L/ha}$) | **Minor Deficit** (Rain satisfied 96%) |
| `2025-09-10_sugarcane_flowering_1.0ha`| 2025-09-10| Sugarcane (Flower)| **6.42** | **0.00** | 4.98 | 4.94 | 5.58 | $0.64\text{ mm}$ ($642\text{ L/ha}$) | **Low Deficit** (Rain satisfied 89%) |
| `2025-10-04_cotton_flowering_1.0ha` | 2025-10-04 | Cotton (Flower) | **7.99** | **0.00** | 3.28 | 3.26 | 4.06 | $0.80\text{ mm}$ ($799\text{ L/ha}$) | **Moderate Deficit** (Rain satisfied 80%)|

#### Key Agronomic Findings:
1. **Zero Dry-Day Failures**: In **100% of the 7 cases**, substantial precipitation ($3.28\text{ mm}$ to $4.98\text{ mm}$) fell on that day. The classifier did not predict zero on a dry day.
2. **Sub-Millimetre Deficits**: In 3 cases, the actual requirement was less than $0.05\text{ mm}$ of depth ($< 500\text{ litres/hectare}$), which is below the operational detection limit of canal gates.
3. **High Rain Coverage**: In the remaining 4 cases, rainfall satisfied $80\%$ to $96\%$ of crop evapotranspiration.

### 5.3 Forensic Inspection of the Largest Residual Outlier
- **Sample**: `2025-05-12_sugarcane_flowering_1.0ha` (Date: May 12, 2025)
- **Actual Target**: **$75.64\text{ m}^3/\text{day}$**
- **Model Prediction**: **$52.34\text{ m}^3/\text{day}$**
- **Residual Error**: **$23.30\text{ m}^3/\text{day}$**
- **Root Cause**: On May 12, gross precipitation was $2.89\text{ mm}$. Under the USDA-SCS equation, light rainfall below $3.0\text{ mm}$ under extreme summer temperatures (36°C) is assigned $0.00\text{ mm}$ effective precipitation due to rapid canopy interception and surface evaporation. The model recognized the $2.89\text{ mm}$ gross rain and slightly depressed its prediction, while the strict USDA-SCS equation discarded the rainfall entirely.

---

## 6. Cryptographic Baseline Hash Verification

All production model artifacts and historical candidate models were audited using cryptographic SHA-256 digests:

| Model Version | Artifact Filename | Expected SHA-256 Digest | Verified Disk SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Production** | `encoders.joblib` | `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD` | `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD` | **MATCH** |
| **Production** | `evaluation_results.json` | `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7` | `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7` | **MATCH** |
| **Production** | `rf_model.joblib` | `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75` | `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75` | **MATCH** |
| **Production** | `xgb_model.joblib` | `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56` | `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56` | **MATCH** |
| **Candidate v1** | `candidate_rf_model.joblib` | `37A7117EDEB522FAFC84D3F6A8CBB1A594C147BB4C7651C19B691D06C5BE8435` | `37A7117EDEB522FAFC84D3F6A8CBB1A594C147BB4C7651C19B691D06C5BE8435` | **MATCH** |
| **Candidate v1** | `candidate_xgb_model.joblib` | `49CD94B33FC7317C03845167755CD8814D1933839C22DD13CABEA756872976EB` | `49CD94B33FC7317C03845167755CD8814D1933839C22DD13CABEA756872976EB` | **MATCH** |
| **Candidate v1** | `candidate_preprocessor.joblib`| `E4A47B8442B39E9958E485F965A2ABC2E824E3BBE1E0F44D376FA46B47A553E5` | `E4A47B8442B39E9958E485F965A2ABC2E824E3BBE1E0F44D376FA46B47A553E5` | **MATCH** |
| **Candidate v1** | `evaluation_metrics.json` | `34A2FA1FFB52225B61C0C728CCEEB866D4A024156D794C928BB1446FC2908297` | `34A2FA1FFB52225B61C0C728CCEEB866D4A024156D794C928BB1446FC2908297` | **MATCH** |
| **Candidate v2** | `candidate_xgb_model.joblib` | `C9DF28D7045883D97E4C439D805D22071DD500156B57CA637137100E1617F65C` | `C9DF28D7045883D97E4C439D805D22071DD500156B57CA637137100E1617F65C` | **MATCH** |
| **Candidate v2** | `candidate_rf_model.joblib` | `2F5FE497BDF2072BC041B049EFD922DAE27ACC9C23FE24D881E7DD2142C6DB5E` | `2F5FE497BDF2072BC041B049EFD922DAE27ACC9C23FE24D881E7DD2142C6DB5E` | **MATCH** |
| **Candidate v2** | `candidate_preprocessor.joblib`| `FE5C0018F09C91C34E446BCEEE564B084513CFCC51A6667FAB85AE83120F8D80` | `FE5C0018F09C91C34E446BCEEE564B084513CFCC51A6667FAB85AE83120F8D80` | **MATCH** |

**Hash Verification Result**: 100% of baseline artifacts are identical. Zero unintended file modification occurred.

---

## 7. Test Suite Execution

1. **Phase 9 Test Suite** ([`backend/tests/test_phase9_error_analysis.py`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/tests/test_phase9_error_analysis.py)):
   - `test_phase8b_metric_reproduction_exactness`: **PASSED**
   - `test_two_stage_model_pipeline_behavior`: **PASSED**
   - `test_feature_sets_zero_leakage`: **PASSED**
   - `test_all_baselines_and_v2_hashes_unmodified`: **PASSED**
   - `test_candidate_v3_artifacts_exist_and_isolated`: **PASSED**
   - `test_candidate_v3_zero_demand_error_reduction`: **PASSED**
   - `test_agronomic_registry_and_calendar_invariants`: **PASSED**
2. **Phase 10 Test Suite** ([`backend/tests/test_phase10_independent_validation.py`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/tests/test_phase10_independent_validation.py)):
   - `test_independent_candidate_v3_metric_recomputation`: **PASSED**
   - `test_zero_demand_classification_and_confusion_matrix`: **PASSED**
   - `test_crop_specific_metrics_integrity`: **PASSED**
   - `test_temporal_splits_and_threshold_isolation`: **PASSED**
   - `test_feature_schema_leakage_absence`: **PASSED**
   - `test_false_positive_zeros_contextual_investigation`: **PASSED**
   - `test_all_baseline_hashes_preserved`: **PASSED**
3. **Full Backend Pytest Suite**:
   - **789 passed, 0 failed, 5 warnings in 15.24s**.

---

## 8. Audit Conclusions & Operational Recommendation

### Final Audit Verdict: `VALIDATION_PASSED_AS_OFFLINE_SURROGATE` | `CONDITIONAL_GO_FOR_SHADOW_MODE_DESIGN`

1. **Fidelity Verification**: Candidate v3 is verified as an accurate offline mathematical emulator ($R^2 = 0.9902$, $\text{MAE} = 1.39\text{ m}^3/\text{day}$) of the FAO-56 Penman-Monteith single-crop water balance equations across 5 calendar years (2021–2025).
2. **Zero-Demand Stability**: The two-stage architecture solves the zero-demand failure mode of Candidate v2, reducing zero-demand MAE from $10.42\text{ m}^3/\text{day}$ to $0.016\text{ m}^3/\text{day}$ with $99.18\%$ classification accuracy.
3. **No Promotion to Active Primary Model**: Because target values are mathematical approximations rather than measured canal deliveries, Candidate v3 must NOT replace the deterministic baseline in the live system.

---

## 9. Recommended Integration Design & Shadow-Mode Test Plan

For future work, the following separate shadow-mode integration design is recommended:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Live FastAPI Request                            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
  ┌───────────────────────────┐                 ┌───────────────────────────┐
  │   Primary Active Engine   │                 │   Shadow Mode Surrogate   │
  │   Deterministic FAO-56    │                 │      Candidate v3         │
  │   Baseline (Approach A)   │                 │     (Two-Stage XGB)       │
  └─────────────┬─────────────┘                 └─────────────┬─────────────┘
                │                                             │
                ▼                                             ▼
    Active Dispatch Output                         Non-blocking Audit Log
  (Controls Canal Allocation)                     (Saved in shadow_audit)
```

### Key Elements of Shadow-Mode Design:
1. **Dual Rainfall Handling**:
   - For historical queries: input `rainfall_observed_mm`.
   - For same-day forward predictions: input `rainfall_forecast_mm` with upper/lower bounds.
2. **Non-Blocking Execution**:
   - Candidate v3 executes in the background alongside the active deterministic baseline.
   - It outputs an optional `shadow_v3_comparison` block in API responses without affecting allocation decisions.
3. **Operational Telemetry Logging**:
   - Log discrepancies between Candidate v3 and Deterministic FAO-56 to quantify surrogate drift under unusual weather patterns.
