# AquaMedi AI — ML Research Recommendations

**Document:** `AQUAMEDI_AI_ML_RESEARCH_RECOMMENDATIONS.md`
**Type:** Recommendation-only
**Repository:** `purvansh1076/AquaMed-AI`, branch `main`

---

## 1. Current ML implementation (verified)

- Dataset: `backend/app/ml/data_generator.py:SyntheticDataGenerator.generate_dataset`, 3,000 rows default, 8 scenario types, 9 crops, 5 soils, FAO-56 Kc table, USDA SCS effective rainfall, ±10% Gaussian noise on demand.
- Split: `backend/app/ml/feature_engineering.py:train_val_test_split`, 70/15/15, stratified by `scenario_type`, seed 42.
- Features: `ENGINEERED_FEATURE_COLS`, 22 features (13 raw numeric + 4 encoded categoricals + 5 interactions).
- Models: `backend/app/ml/trainer.py` — RandomForest (200 trees, max_depth 15) and XGBoost (300, lr 0.05, max_depth 6, subsample 0.8, colsample 0.8, L1/L2, early stopping 20). Best by test MAE.
- Metrics: `compute_metrics` → MAE, RMSE, R² on train/val/test.
- Persistence: `rf_model.joblib`, `xgb_model.joblib`, `encoders.joblib`, `evaluation_results.json`.
- Runtime calibration: `trainer.py:load_model` restores XGBoost `base_score` to 214.17618.
- Conformal: `conformal_predictor.py:ConformalPredictor.predict_interval`, split conformal, `DEFAULT_Q_HAT_M3 = 45.68`, area scaling `0.8 + 0.2 × clamp(area, 0.5, 5.0)`.
- Explainability: `explainer.py`, `prediction_explainer.py`, SHAP TreeExplainer.

Reported (verified in `evaluation_results.json` and independent audit): XGBoost test R² ≈ 0.9699, MAE ≈ 18.63 m³, RMSE ≈ 29.27 m³ on 451 test samples.

---

## 2. Is the current evaluation scientifically defensible?

Partially. Strengths: train-only encoder fitting, held-out test set, stratification by scenario, no leakage of `_row_id`. Weaknesses:

1. Single split (seed 42) → no variance estimate; metrics may be optimistic.
2. Synthetic target generated from the same FAO-56 formula the agronomic baseline uses → high R² partly reflects formula memorization, not field accuracy.
3. `et0_x_kc` interaction duplicates `etc_mm_per_day` (perfect collinearity), which can inflate feature importance without adding information.
4. Conformal coverage claim (90.47%) was computed against the raw unscaled quantile; actual coverage with area scaling is ~97.3% (over-conservative).
5. No group-based or time-aware validation; data is i.i.d. synthetic, so chronological split (`chronological_split.py`) is available but unused in the main pipeline.

---

## 3. Recommended ML improvements (prioritized)

### A. Conformal prediction (highest scientific value)

- **R-ML-01 (Priority A/B): Normalize conformal calibration.**
  - Current: `scaled_q_hat = q_hat × s(A)` with `s(A) = 0.8 + 0.2 × clamp(A, 0.5, 5.0)`, where `q_hat = 45.68` was calibrated on raw residuals.
  - Proposed: compute non-conformity scores `R_i = |y_i − ŷ_i| / s(A_i)` on the validation set; take `q_norm = Quantile(R_i, ceil((n+1)α)/n)`; at test time use margin `q_norm × s(A)`. Expected: ~90% coverage, ~40 m³ half-width (vs. ~72 m³).
  - Affected: `conformal_predictor.py`, new calibration step in `trainer.py`.
  - References: Lei et al. (2018); Angelopoulos & Bates (2021).

- **R-ML-02 (Priority B): Scale intervals by growth stage** (flowering-stage variance > harvest-stage). Affected: `conformal_predictor.py:predict_interval`.

- **R-ML-03 (Priority B): Report coverage and mean width** as first-class metrics (currently only point metrics). Add `prediction_interval_coverage`, `mean_interval_width`, calibration plots.

### B. Evaluation methodology

- **R-ML-04 (Priority B): Repeated cross-validation.** Run `run_training_pipeline` with seeds {42, 7, 123, 2024, 99} and report mean ± std. Affected: `trainer.py`, `evaluation_reporter.py`.
- **R-ML-05 (Priority B): Group/stratified evaluation.** Report MAE/RMSE/R² by crop, season, scenario type. Candidate v3 already produces `error_breakdown_by_crop_season.json`; promote to main pipeline. Affected: `evaluation_reporter.py`, `trainer.py`.
- **R-ML-06 (Priority C): Time-aware validation** where appropriate (use `chronological_split.py` / `date_grouped_split.py`) to test temporal generalization. Only meaningful if a time dimension is added to the synthetic data.

### C. Feature engineering and selection

- **R-ML-07 (Priority B): Feature ablation.** Quantify contribution of each of the 22 features; remove `et0_x_kc` if redundant. Affected: `feature_engineering.py`, `candidate_v3_experiments.py`.
- **R-ML-08 (Priority C): Feature selection** via permutation importance and SHAP; keep a documented minimal feature set.

### D. Model quality and lifecycle

- **R-ML-09 (Priority B): Hyperparameter optimization with Optuna** — only after R-ML-04/05 establish a defensible baseline. Affected: `trainer.py`.
- **R-ML-10 (Priority B): Model versioning + manifest.** Persist version, seed, dataset hash, metrics, git commit. Affected: new `ml/model_registry.py`.
- **R-ML-11 (Priority C): Drift monitoring.** PSI on input features vs. training; alert threshold. Affected: `predictor.py`, new module.
- **R-ML-12 (Priority C): Prediction uncertainty visualization.** Show conformal band on prediction charts. Affected: frontend `PredictionsPage.tsx`, `ShapFeatureChart.tsx`.

### E. Model choice

- Keep XGBoost as primary. Random Forest remains the baseline. Do not add LightGBM/CatBoost unless they beat XGBoost on stratified metrics (R-ML-05). Justification: current data is tabular with 22 features and 3,000 rows; XGBoost already achieves R² ≈ 0.97 with early stopping. Adding models increases maintenance without demonstrated gain.

---

## 4. Scientific evaluation framework

Report (at minimum) on the test split:

- MAE (m³/day) — primary, interpretable absolute error.
- RMSE (m³/day) — penalizes large errors; relevant for irrigation scheduling.
- R² — goodness of fit on synthetic signal.
- MAPE — only where demand > 0 (avoid division by zero); note scale sensitivity.
- Prediction interval coverage (%) — should be ~90% after R-ML-01.
- Mean interval width (m³) — efficiency of uncertainty.
- Calibration analysis — coverage by decile of predicted demand.
- Performance by crop, season, scenario type.

Always label results as synthetic-data fit, not field accuracy.

---

## 5. Metrics to avoid / pitfalls

- Do not report training-set metrics as headline results.
- Do not compute MAPE when demand can be near zero.
- Do not claim conformal coverage without stating whether area scaling was applied.
- Do not present synthetic R² as real-world accuracy.

---

## 6. Suggested experiments (realistic for B.Tech, 2–4 weeks)

1. **Conformal recalibration experiment:** compare raw vs. normalized coverage/width on the held-out test set (n=451).
2. **Repeated-CV stability:** 5 seeds × (MAE, RMSE, R²) mean ± std for XGBoost and RF.
3. **Feature ablation:** remove each of the 5 interaction features; measure ΔMAE.
4. **Stratified error:** MAE by crop and scenario type; identify worst-performing slices.
5. **Hyperparameter sweep (optional):** Optuna 50 trials on XGBoost; report best params and ΔMAE.

---

## 7. References

- Allen, R.G. et al. (1998). FAO Irrigation and Drainage Paper No. 56.
- Vovk, V. et al. (2005). Algorithmic Learning in a Random World.
- Angelopoulos, A.N. & Bates, S. (2021). A Gentle Introduction to Conformal Prediction.
- Lei, J. et al. (2018). Distribution-Free Predictive Inference for Regression.
- Chen, T. & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System.
