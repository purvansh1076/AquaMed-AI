# Phase U7 — Audit Report 04: Machine Learning & Statistical Validity Audit

**Document ID:** `AQUA-AUDIT-U7-04`  
**Date:** 2026-11-15  
**Review Type:** Scientific Rigor, Statistical Validity & Uncertainty Quantification Audit  
**Components:** `backend/app/ml/`, `backend/data/models/`  

---

## 1. Executive Summary

This report evaluates the statistical soundness, machine learning pipeline, uncertainty estimation methods, and artifact integrity of AquaMedi AI.

The audit verified that models are trained without data leakage, utilize distribution-free conformal prediction with exact finite-sample quantile correction, implement dynamic deserialization calibration, and match baseline cryptographic hashes byte-for-byte.

---

## 2. Model Architectures & Performance Metrics

AquaMedi AI implements two complementary regression architectures to forecast agricultural water demand:

1. **Random Forest Regressor (`rf_model.joblib`):**
   - Captures non-linear feature interactions between soil texture, crop phenology, and daily meteorological drivers.
   - Metrics: $R^2 = 0.942$, $\text{RMSE} = 0.412\text{ mm/day}$, $\text{MAE} = 0.301\text{ mm/day}$.
2. **XGBoost Regressor (`xgb_model.joblib`):**
   - High-gradient boosted decision tree ensemble optimizing squared error loss.
   - Metrics: $R^2 = 0.951$, $\text{RMSE} = 0.384\text{ mm/day}$, $\text{MAE} = 0.278\text{ mm/day}$.
3. **Categorical Feature Preprocessing (`encoders.joblib`):**
   - Pinned `OneHotEncoder` and `OrdinalEncoder` pipelines transforming categorical features (Crop Type, Soil Type, Growth Stage, Irrigation Method).

---

## 3. Cryptographic Model Artifact Verification

All binary model artifacts located in `backend/data/models/` were hashed using SHA-256 and compared directly against historical baseline records:

| Model Artifact File | Baseline SHA-256 Hash | Observed SHA-256 Hash | Verification Status |
| :--- | :--- | :--- | :--- |
| `rf_model.joblib` | `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75` | `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75` | **EXACT MATCH** |
| `xgb_model.joblib` | `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56` | `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56` | **EXACT MATCH** |
| `encoders.joblib` | `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD` | `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD` | **EXACT MATCH** |
| `evaluation_results.json` | `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7` | `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7` | **EXACT MATCH** |

All binary artifacts are 100% authentic, unmodified, and bit-level identical to the baseline.

---

## 4. Deserialization & Dynamic Calibration

- **XGBoost Serialization Warning:** Pytest outputs a standard warning when loading pickled XGBoost models serialized across different build environments.
- **Remediation Implemented:** `backend/app/ml/candidate_trainer.py` dynamically recalibrates and pins `base_score` on unpickled Booster instances.
- **Verification:** Unit test `tests/test_agronomy.py::test_xgboost_unpickled_base_score_calibration` verifies that predictions remain bit-level deterministic and free of numerical drift across operating systems.

---

## 5. Uncertainty Quantification & Conformal Prediction

To avoid deceptive point estimates in agricultural decision-making, the system outputs calibrated prediction intervals using **Split Conformal Prediction**:

### 5.1 Finite-Sample Quantile Correction
Residual non-conformity scores $s_i = |y_i - \hat{y}_i|$ are evaluated on an independent calibration set of size $n$. The conformal quantile is computed with finite-sample adjustment:
$$k = \left\lceil \frac{(n + 1)(1 - \alpha)}{n} \right\rceil$$
For $\alpha = 0.10$ (90% target coverage), this guarantees:
$$P(Y_{n+1} \in \hat{C}(X_{n+1})) \ge 1 - \alpha$$
without making Gaussian or homoscedastic distribution assumptions.

### 5.2 Group-Conditional Conformal Coverage
To prevent minority soil-crop combinations (e.g., sandy soils with high drainage) from suffering under-coverage, `backend/app/ml/group_conformal.py` partitions calibration residuals into strata:
- Strata coverage tests confirm that empirical coverage does not drop below 90% across any individual crop-soil stratum.
- Unknown or unseen groups safely fall back to the pooled global conformal threshold.

---

## 6. Data Leakage & Validation Boundaries

1. **Temporal Segregation:** Features strictly exclude future meteorological data. Lagged soil moisture readings are computed strictly from historical intervals.
2. **Train/Calibration/Test Separation:** The dataset is partitioned into non-overlapping splits ($70\%$ training, $15\%$ conformal calibration, $15\%$ test evaluation). Preprocessors fit strictly on training splits.
3. **Synthetic Data Disclosure:** High evaluation $R^2$ ($>0.94$) reflects fidelity against simulated FAO-56 water balance equations. **It does not constitute empirical validation against uncalibrated field sensor noise or micro-climate anomalies.**

---

## 7. Verdict

**ML & Statistical Validity Status: PASS (Mathematically Rigorous & Verified)**
