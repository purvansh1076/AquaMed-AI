# AquaMedi AI — Data Leakage Audit (Phase B)

## Method

Script: `backend/scripts/audit_data_leakage.py` (seed 42, n=3000, 70/15/15 split).

## Results

- Duplicate rows: 0
- Train/val row overlap: 0
- Train/test row overlap: 0
- Val/test row overlap: 0
- All rows marked `is_synthetic=True`.
- Target highly correlated with `minimum_requirement_m3` (0.993) and `etc_mm_per_day` (0.632), consistent with synthetic generation (ETc × area), not leakage.

## Conclusion

No train/test contamination or duplicate rows detected. Target derivation from agronomic formula is by design (synthetic data) and documented as such. Encoders are fit on training split only (`feature_engineering.py:fit_encoders`).
