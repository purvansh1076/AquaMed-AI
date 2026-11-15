# AquaMedi AI — ML Baseline Report (Phase B)

## Reproducible baseline

- Script: `backend/scripts/evaluate_baseline.py`
- Seed: 42, n_samples: 3000, split 70/15/15 stratified by scenario_type.
- Artifacts preserved (SHA-256 in `backend/data/models/baseline_metrics_phase_b.json`).

## XGBoost (test split, n=451)

- MAE: 18.63 m³/day
- RMSE: 29.27 m³/day
- R²: 0.9699

## Random Forest (test split, n=451)

See `baseline_metrics_phase_b.json` for full metrics.

## Conformal prediction (normalized, Phase A)

- Coverage: 0.9024 (target 0.90)
- Mean width: 80.54 m³
- Median width: 90.37 m³
- Raw (pre-Phase A) coverage: 0.9800, mean width 141.50 m³

Conclusion: normalized conformal achieves near-nominal coverage with substantially tighter intervals.

## Limitations

- Synthetic data only; metrics reflect fit to synthetic signal.
- Single seed; repeated CV recommended for variance estimate.
