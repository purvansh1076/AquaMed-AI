# AquaMedi AI — Advanced Conformal Report

## Group-conditional conformal

`backend/app/ml/group_conformal.py` implements per-group calibration with fallback to global q for small groups (min_group_size=30).

## Tests

`backend/tests/test_group_conformal.py` (2 tests).
