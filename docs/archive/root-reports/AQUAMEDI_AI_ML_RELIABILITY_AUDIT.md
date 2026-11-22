# AquaMedi AI — ML Reliability Audit

## Verified

- Baseline reproduced (XGBoost test MAE 18.63, RMSE 29.27, R² 0.9699).
- Leakage audit: no duplicate rows, no split overlap.
- Feature schema: 22 engineered features; encoders fit on train only.
- Base-score calibration robust to list-like serialized values.

## Limitations

- Single seed; repeated CV not run.
- No group-conditional conformal.
- Synthetic data only.
