# AquaMedi AI — Phase E Architecture

## Workstreams

- E1 Advanced ML validation (repeated CV).
- E2 Advanced uncertainty (group-conditional conformal).
- E3 Fairness-aware optimization (max-min LP).
- E4 Regional agronomic validation (ET0 bounds + FAO-56).
- E5 Research benchmarking.

## Key additions

- `backend/scripts/repeated_cv.py`
- `backend/app/ml/group_conformal.py`
- `backend/app/allocation/lp_allocator.py:solve_fairness_aware`
- `backend/tests/test_group_conformal.py`, `test_maxmin_fairness.py`, `test_et0_bounds.py`
