# Phase U2 — Machine Learning & Scientific Pipeline Review Report

**Review Scope:** `backend/app/ml/`, `backend/data/models/`  
**Review Date:** 2026-11-15  
**Auditor:** AquaMedi AI Release Engineering  

---

## 1. Machine Learning Architecture Review

### 1.1 Model Selection & Production Lock
- **Primary Model:** XGBoost 2.0 Regressor locked for production inference ($R^2 = 0.9699$, $\text{MAE} = 18.63\text{ m}^3$, $\text{RMSE} = 29.27\text{ m}^3$).
- **Benchmark Model:** Random Forest Regressor preserved on disk for historical reference comparisons.
- **Deserialization Calibration (`backend/app/ml/trainer.py`):**
  Unpickled XGBoost models dynamically verify and calibrate `base_score` using the historical training target mean (214.17618) extracted from `evaluation_results.json`, resolving cross-version serialization discrepancies.

### 1.2 Conformal Prediction & Uncertainty Intervals
- **Split Conformal Predictor (`backend/app/ml/conformal_predictor.py`):**
  Constructs distribution-free prediction intervals calibrated at nominal 90% confidence ($\alpha = 0.10$). Employs farm area scaling:
  $$\hat{C}(x) = [\max(0, \hat{y} - q_{\text{norm}} \cdot s(A)), \hat{y} + q_{\text{norm}} \cdot s(A)]$$
  Verified empirical coverage: **90.24%** on test split.
- **Group-Conditional Conformal (`backend/app/ml/group_conformal.py`):**
  Applies exact finite-sample quantile calibration per crop type and phenological growth stage:
  $$k = \left\lceil (n_g + 1)(1 - \alpha) \right\rceil / n_g$$
  Falls back gracefully to global quantile for small group sizes ($n_g < 30$).

---

## 2. Agronomic & Hydrological Verification

### 2.1 FAO-56 Penman-Monteith Methodology
- Evaluates reference evapotranspiration ($ET_0$) as a function of temperature, radiation, wind speed, and vapor pressure.
- Independent validation in `test_et0_independent.py` verifies psychrometric constants, saturation vapor pressure gradients, and net radiation against FAO-56 Chapter 3 benchmark tables.

### 2.2 Scientific Integrity Boundaries
- **Synthetic Data Disclaimer:** All training features and targets are algorithmically simulated; no physical canal flowmeter or real farmer logs were utilized.
- **Regional Calibration Outstanding:** Penman-Monteith coefficients require regional calibration against ground-truth weather station data (IMD/CWC) prior to operational deployment.

---

## 3. Scientific Review Verdict

**Verdict: VERIFIED PASS**  
Mathematical formulas and ML pipelines are verified by unit and regression tests; scientific boundaries are transparently documented.
