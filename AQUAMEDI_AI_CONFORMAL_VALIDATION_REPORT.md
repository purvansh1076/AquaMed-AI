# AquaMedi AI — Conformal Validation Report (Phase B)

## Implementation

- `backend/app/ml/conformal_predictor.py`
- Normalized mode (Phase A): margin = `q_norm * (0.8 + 0.2 * clamp(area, 0.5, 5.0))`, `q_norm = 25.6610`.
- Raw mode: margin = `q_hat * scale`, `q_hat = 45.68`.

## Empirical evaluation (held-out test, n=451)

- Normalized: coverage 0.9024, mean width 80.54 m³, median 90.37 m³.
- Raw: coverage 0.9800, mean width 141.50 m³, median 160.28 m³.

## Notes

- Coverage evaluated on a single held-out split; repeated evaluation recommended.
- Exchangeability assumed for i.i.d. synthetic data; temporal/spatial dependence not modeled.
- Growth-stage scaling not yet applied (recommended future work).
