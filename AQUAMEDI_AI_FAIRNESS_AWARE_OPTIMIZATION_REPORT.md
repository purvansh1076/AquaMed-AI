# AquaMedi AI — Fairness-Aware Optimization Report

## Max-min fairness LP

`WaterAllocator.solve_fairness_aware()` maximizes minimum farmer satisfaction ratio subject to supply, demand bounds, non-negativity, conveyance. Does not replace `solve()`.

## Tests

`backend/tests/test_maxmin_fairness.py` (1 test).
