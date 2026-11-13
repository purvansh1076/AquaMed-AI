# Group Conformal Remediation

## Correction

Implemented finite-sample quantile level: ceil((n+1)*(1-alpha))/n, capped at 1.0.

## Tests

- test_group_conformal_remediation.py (3 tests) pass.

## Limitations

- No independent empirical coverage evaluation yet.
- min_group_size=30 may be small.
