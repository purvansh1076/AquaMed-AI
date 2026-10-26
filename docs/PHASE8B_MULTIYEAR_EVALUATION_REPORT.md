# AquaMediAI Phase 8B — Multi-Year Candidate ML Training & Evaluation Report

**Date**: October 2026  
**Status**: Completed (Multi-Year Offline Candidate Training & Evaluation Verified)  
**Pilot Region**: Ahmednagar District, Central Maharashtra, India (Pravara & Mula Canal Command, Centroid: 19.09° N, 74.74° E, Elevation: 540 m)  
**Primary Target**: Theoretical daily net crop-water requirement ($m^3/\text{day}$)  
**Selected Candidate**: `Candidate XGBoost` (Version: `candidate_v2`)  
**Final Status / Decision**: `GO_FOR_OFFLINE_SURROGATE`

---

## 1. Executive Summary & Scientific Disclaimer

Phase 8B evaluates whether candidate machine learning models (Random Forest and XGBoost) can accurately approximate the theoretical daily net crop-water requirement ($m^3/\text{day}$) across the expanded 5-year multi-year dataset (2021–2025) for the Ahmednagar pilot region.

> [!CAUTION]
> ### Crucial Agronomic & Scientific Notice
> **The target values evaluated in this pipeline represent theoretical crop-water demands calculated deterministically using the FAO-56 Penman-Monteith single-crop coefficient method and USDA-SCS effective precipitation equation.**
> - They are **NOT** measured ground-truth farm-gate water deliveries or soil moisture sensor records.
> - High model accuracy ($R^2 = 0.8013$, low MAE) demonstrates **surrogate fidelity to the biophysical mathematical equations across multi-year weather patterns**, not proven field accuracy against real-world agricultural practices.
> - Candidate models are strictly isolated in `backend/data/models/candidate_v2/`. They are **NOT deployed or activated in production**. The deterministic agronomic baseline remains the active reference in the live system.

All 775 backend tests pass (including 6 new Phase 8B multi-year tests). Production model artifacts (`rf_model.joblib`, `xgb_model.joblib`, `encoders.joblib`, `evaluation_results.json`) and Phase 7 candidate artifacts (`candidate_v1`) remain 100% unaltered, verified by SHA-256 cryptographic digests.

---

## 2. Dataset Verification & Strict Annual Split Design

The candidate training and evaluation pipeline utilized `backend/data/processed/candidate_v2_dataset.csv`, verified for zero date gaps, zero duplicate keys, zero missing cells, and exact mathematical target reproducibility.

### 2.1 Partition Boundaries

A strict annual chronological partition was enforced without date shuffling:

```
Multi-Year Timeline (2021 ──► 2025) ─────────────────────────────────────────────────────────────►
[── Training Partition: 3 Full Years ──] [── Validation: 1 Full Year ──] [── Final Test: 1 Full Year ──]
  2021-01-01 ───► 2023-12-31               2024-01-01 ───► 2024-12-31      2025-01-01 ───► 2025-12-31
  1,095 unique dates (2,928 rows)          366 unique dates (978 rows)     365 unique dates (976 rows)
```

| Partition | Calendar Years | Unique Dates | Record Count | Purpose | Date Boundaries (YYYY-MM-DD) |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Training** | 2021, 2022, 2023 | **1,095** | **2,928** | Model fitting & preprocessor fitting only | 2021-01-01 to 2023-12-31 |
| **Validation** | 2024 (Leap Year) | **366** | **978** | Model selection & hyperparameter audit | 2024-01-01 to 2024-12-31 |
| **Final Test** | 2025 | **365** | **976** | Single out-of-year verification (untouched) | 2025-01-01 to 2025-12-31 |
| **Total** | **5 Full Years** | **1,826** | **4,882** | **100% Complete Time Series** | **2021-01-01 to 2025-12-31** |

### 2.2 Date-Grouped Invariants Verified
- **Mutual Exclusivity**: $\text{TrainDates} \cap \text{ValDates} = \emptyset$, $\text{TrainDates} \cap \text{TestDates} = \emptyset$, $\text{ValDates} \cap \text{TestDates} = \emptyset$.
- **Strict Chronological Sequence**: $\max(\text{TrainDates}) = \text{"2023-12-31"} < \min(\text{ValDates}) = \text{"2024-01-01"} < \max(\text{ValDates}) = \text{"2024-12-31"} < \min(\text{TestDates}) = \text{"2025-01-01"}$.
- **Preprocessing Isolation**: The `ColumnTransformer` (StandardScaler for numerics, OneHotEncoder for categoricals) was fitted **strictly on the 2,928 training samples**. It transformed the 2024 validation and 2025 test samples without any data leakage.

---

## 3. Validation Performance & Model Selection (2024 Partition)

Candidate models were evaluated on the complete 2024 validation year ($n=978$ samples across all 366 days, including leap-day Feb 29) to select the winning candidate:

| Model / Baseline | Category | Val MAE ($m^3/\text{day}$) | Val RMSE ($m^3/\text{day}$) | Val NRMSE | Val $R^2$ | Mean Signed Bias | MAE Reduction vs Naive |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Deterministic FAO-56 Reference** | Ground Truth Formula | 0.00 | 0.00 | 0.0000 | 1.0000 | 0.00 | Target Reference |
| **Candidate XGBoost** | ML Regressor | **7.96** | **12.03** | **0.4308** | **0.7693** | -1.80 | **57.73% reduction** |
| **Candidate RandomForest** | ML Regressor | 8.42 | 12.72 | 0.4554 | 0.7422 | -1.51 | 55.33% reduction |
| **Naive Mean Baseline** | Train Target Mean ($29.62\text{ m}^3$) | 18.84 | 25.07 | 0.8978 | -0.0019 | +8.64 | Reference Benchmark |

### Selection Decision
**Candidate XGBoost** was selected as the superior multi-year surrogate because it achieved:
- Lower Validation MAE ($7.96\text{ m}^3/\text{day}$ vs $8.42\text{ m}^3/\text{day}$)
- Lower Validation RMSE ($12.03\text{ m}^3/\text{day}$ vs $12.72\text{ m}^3/\text{day}$)
- Higher explained variance ($R^2 = 0.7693$ vs $0.7422$)

---

## 4. Final Out-of-Year Test Evaluation (Untouched 2025 Partition)

The selected candidate model (and comparators) were evaluated on the untouched 2025 calendar year ($n=976$ samples across all 365 days):

### 4.1 Overall Test Benchmark Comparison Table

| Model / Baseline | Category | Test MAE ($m^3/\text{day}$) | Test RMSE ($m^3/\text{day}$) | Test NRMSE | Test $R^2$ | Mean Signed Bias | Max Error | MAE Reduction vs Naive |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Deterministic FAO-56 Reference** | Ground-Truth Target Generator | **0.00** | **0.00** | 0.0000 | 1.0000 | 0.00 | 0.00 | Formula Benchmark |
| **Candidate XGBoost** *(Selected)* | ML Surrogate Model | **6.67** | **10.82** | **0.3884** | **0.8013** | **+0.16** | **53.85** | **63.67% reduction** |
| **Candidate RandomForest** | ML Surrogate Model | **6.71** | **11.29** | 0.4054 | 0.7836 | +0.47 | 65.22 | 63.42% reduction |
| **Naive Mean Baseline** | Constant Train Mean ($29.62\text{ m}^3$) | 18.36 | 24.30 | 0.8724 | -0.0022 | +8.54 | 105.23 | Reference Benchmark |

### 4.2 Sliced Diagnostics on 2025 Test Partition

#### A. Sliced Error by Crop Type
- **Wheat** ($n=121$, Rabi): XGB MAE = **$2.35\text{ m}^3/\text{day}$**, RF MAE = $2.01\text{ m}^3/\text{day}$ (Target Mean: $29.64\text{ m}^3/\text{day}$).
- **Cotton** ($n=170$, Kharif): XGB MAE = **$7.01\text{ m}^3/\text{day}$**, RF MAE = $7.13\text{ m}^3/\text{day}$ (Target Mean: $21.07\text{ m}^3/\text{day}$).
- **Groundnut** ($n=117$, Kharif): XGB MAE = **$7.05\text{ m}^3/\text{day}$**, RF MAE = $7.37\text{ m}^3/\text{day}$ (Target Mean: $17.37\text{ m}^3/\text{day}$).
- **Maize** ($n=107$, Kharif/Rabi): XGB MAE = **$7.28\text{ m}^3/\text{day}$**, RF MAE = $7.47\text{ m}^3/\text{day}$ (Target Mean: $18.11\text{ m}^3/\text{day}$).
- **Soybean** ($n=96$, Kharif): XGB MAE = **$7.87\text{ m}^3/\text{day}$**, RF MAE = $8.06\text{ m}^3/\text{day}$ (Target Mean: $18.70\text{ m}^3/\text{day}$).
- **Sugarcane** ($n=365$, Perennial): XGB MAE = **$7.32\text{ m}^3/\text{day}$**, RF MAE = $7.30\text{ m}^3/\text{day}$ (Target Mean: $39.05\text{ m}^3/\text{day}$).

#### B. Sliced Error by Calendar Month
- **Cool-Dry Winter Months (Nov, Dec, Jan, Feb)**:
  - November: XGB MAE = **$1.91\text{ m}^3/\text{day}$** (Target Mean: $22.15\text{ m}^3$)
  - December: XGB MAE = **$1.33\text{ m}^3/\text{day}$** (Target Mean: $28.48\text{ m}^3$)
  - January: XGB MAE = **$2.27\text{ m}^3/\text{day}$** (Target Mean: $29.03\text{ m}^3$)
  - February: XGB MAE = **$2.41\text{ m}^3/\text{day}$** (Target Mean: $33.38\text{ m}^3$)
  - In dry winter months without rain shutdowns, the surrogate achieves near-perfect fidelity ($< 2.5\text{ m}^3/\text{day}$ MAE).
- **Monsoon & Pre-Monsoon Transition (May, June, July, August)**:
  - May: XGB MAE = $14.01\text{ m}^3/\text{day}$ (Extreme atmospheric demand with sporadic convective showers)
  - June: XGB MAE = $11.36\text{ m}^3/\text{day}$ (Monsoon onset)
  - July: XGB MAE = $8.94\text{ m}^3/\text{day}$
  - August: XGB MAE = $9.97\text{ m}^3/\text{day}$

#### C. Sliced Error by Demand Tier
- **Zero-Demand Subset ($n=220$, $22.5\%$ of 2025 samples)**:
  - XGB MAE = $10.42\text{ m}^3/\text{day}$. During heavy monsoon storms where $P_{eff} \ge ET_c$, tree regressors tend to over-predict non-zero numbers rather than snapping to exact 0.0.
- **Low Demand Tier ($0\text{--}30\text{ m}^3/\text{day}$, $n=368$)**: XGB MAE = **$4.85\text{ m}^3/\text{day}$** (Target Mean: $20.50\text{ m}^3/\text{day}$).
- **Medium Demand Tier ($30\text{--}60\text{ m}^3/\text{day}$, $n=323$)**: XGB MAE = **$6.23\text{ m}^3/\text{day}$** (Target Mean: $42.96\text{ m}^3/\text{day}$).
- **High Demand Tier ($>60\text{ m}^3/\text{day}$, $n=65$)**: XGB MAE = **$6.46\text{ m}^3/\text{day}$** (Target Mean: $88.70\text{ m}^3/\text{day}$).

#### D. Top Feature Importances (Candidate XGBoost)
1. `crop_type_sugarcane` (38.8%): Dominant perennial high-water-intensity crop.
2. `vpd_proxy_kpa` (16.2%): Atmospheric dryness and vapor pressure deficit driving transpiration.
3. `growth_stage_flowering` (11.5%): Peak crop coefficient ($K_c$) phenological stage.
4. `doy_cos` (7.4%): Solar declination and seasonal astronomical geometry.
5. `temperature_celsius` (5.6%): Thermal energy driving evaporative demand.

---

## 5. Artifact Inventory & Cryptographic Preservation

All Phase 8B outputs are isolated in `backend/data/models/candidate_v2/`:

| Artifact Name | SHA-256 Digest | Role |
| :--- | :--- | :--- |
| `candidate_xgb_model.joblib` | `F3B20FE52614E37A7BD45763B8B82B93DDE2C178120FE5EF4614A3644B2EF31B` | Winning Candidate XGBoost Regressor |
| `candidate_rf_model.joblib` | `ED756F3F5A8230D644F998BF289E73EC89E28FE47BBE5EC9C4E07B7575EE7D4A` | Candidate Random Forest Regressor |
| `candidate_preprocessor.joblib` | `0BCE55F6EE44BD85FD77A14CD999B7F7D2DE653B6EB6718EE02D629CECE7F904` | ColumnTransformer fitted strictly on 2021-2023 |
| `feature_schema.json` | JSON format | Documented candidate input feature specification |
| `dataset_manifest.json` | JSON format | Manifest for `candidate_v2_dataset.csv` |
| `split_metadata.json` | JSON format | Exact annual boundaries: 2021-2023, 2024, 2025 |
| `validation_metrics.json` | JSON format | 2024 validation metrics & selection logs |
| `test_evaluation_metrics.json` | JSON format | Complete 2025 out-of-year benchmark metrics |
| `test_predictions.csv` | CSV format | Row-by-row 2025 predictions and residuals |
| `residual_diagnostics.json` | JSON format | Residual mean, std, median, min, max |
| `feature_importance.json` | JSON format | Ranked feature importances for RF and XGBoost |
| `training_log.txt` | Text log | Complete execution trace with UTC timestamps |
| `candidate_metadata.json` | JSON format | Decision, rationale, and provenance metadata |

### 5.1 Verification of Unaltered Existing Models
Cryptographic SHA-256 checks confirmed that all production artifacts and Phase 7 `candidate_v1` artifacts remain completely unaltered:

- **Production Models**:
  - `encoders.joblib`: `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD` (MATCH)
  - `evaluation_results.json`: `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7` (MATCH)
  - `rf_model.joblib`: `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75` (MATCH)
  - `xgb_model.joblib`: `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56` (MATCH)
- **Phase 7 Candidate v1 Models**:
  - `candidate_rf_model.joblib`: `37A7117EDEB522FAFC84D3F6A8CBB1A594C147BB4C7651C19B691D06C5BE8435` (MATCH)
  - `candidate_xgb_model.joblib`: `49CD94B33FC7317C03845167755CD8814D1933839C22DD13CABEA756872976EB` (MATCH)
  - `candidate_preprocessor.joblib`: `E4A47B8442B39E9958E485F965A2ABC2E824E3BBE1E0F44D376FA46B47A553E5` (MATCH)
  - `evaluation_metrics.json`: `34A2FA1FFB52225B61C0C728CCEEB866D4A024156D794C928BB1446FC2908297` (MATCH)

---

## 6. Offline Test Suite Execution

All 6 offline unit tests in [`backend/tests/test_phase8b_multiyear_training.py`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/tests/test_phase8b_multiyear_training.py) passed:
- `test_annual_split_boundaries_and_disjointness`: **PASS** (verifies 2021-2023 Train, 2024 Val, 2025 Test disjointness).
- `test_candidate_v2_artifacts_exist_and_isolated`: **PASS** (verifies complete artifact set in `candidate_v2`).
- `test_candidate_v2_feature_schema_zero_leakage`: **PASS** (verifies complete exclusion of target-derived features).
- `test_all_baselines_and_v1_hashes_unmodified`: **PASS** (verifies 8 baseline SHA-256 hashes).
- `test_model_selection_and_test_metrics_consistency`: **PASS** (verifies XGBoost selection over RF on validation data).
- `test_candidate_v2_inference_output`: **PASS** (verifies non-negative inference within valid physical bounds).

**Full Backend Pytest Suite**: **775 passed, 0 failed, 5 warnings in 13.37s**.

---

## 7. Decision & Operational Recommendation

### Final Verdict: `GO_FOR_OFFLINE_SURROGATE`

1. **Why `GO_FOR_OFFLINE_SURROGATE`**:
   The multi-year evaluation demonstrates that **Candidate XGBoost** achieves genuine out-of-year temporal generalization ($R^2 = 0.8013$, $\text{MAE} = 6.67\text{ m}^3/\text{day}$, representing a **$63.67\%$ error reduction** over the naive baseline on 976 held-out future observations in 2025). The model functions as a fast, biophysically defensible offline emulator of the FAO-56 single-crop coefficient water balance.
2. **Why NOT Promoted to Live Production**:
   Because the target was algorithmically computed from NASA POWER weather and FAO-56 agronomic tables, high accuracy reflects **surrogate mathematical fidelity**, not empirical field validation. Promoting this candidate to replace the deterministic reference in the live system would misrepresent calculated water balances as measured farm deliveries.
3. **Operational Recommendation**:
   Retain the deterministic agronomic baseline as the primary active calculation engine in the live FastAPI backend and React frontend. Maintain `candidate_v2` in offline storage as an approved research surrogate.
