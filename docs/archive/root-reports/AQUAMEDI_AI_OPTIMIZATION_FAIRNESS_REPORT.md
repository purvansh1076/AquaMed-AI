# AquaMedi AI — Optimization Fairness Report (Phase C)

## Fairness metrics implemented

`backend/app/allocation/fairness.py`: Jain's index, demand satisfaction ratio, min/mean satisfaction, efficiency, deficit, disparity, summary.

## Strategy comparison

Script: `backend/scripts/compare_allocation_strategies.py` (equal, proportional, priority, LP) across normal/moderate/severe shortage. Results: `backend/data/models/allocation_strategy_comparison_phase_c.json`.

## Notes

- Jain's index measured post-hoc; not enforced in LP objective.
- Numerical conservation verified with tolerance.
- No fairness weights changed in the default LP objective.
