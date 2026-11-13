"""
AquaMedi AI - Allocation fairness metrics.
"""
from __future__ import annotations

from typing import Dict, List, Sequence


def demand_satisfaction_ratios(
    allocations: Sequence[float],
    demands: Sequence[float],
) -> List[float]:
    ratios: List[float] = []
    for a, d in zip(allocations, demands):
        if d and d > 0:
            ratios.append(min(1.0, max(0.0, float(a) / float(d))))
        else:
            ratios.append(1.0 if a >= 0 else 0.0)
    return ratios


def jains_fairness_index(ratios: Sequence[float]) -> float:
    n = len(ratios)
    if n == 0:
        return 0.0
    s = sum(ratios)
    sq = sum(r * r for r in ratios)
    if sq == 0:
        return 0.0
    return float((s * s) / (n * sq))


def minimum_satisfaction(ratios: Sequence[float]) -> float:
    return float(min(ratios)) if ratios else 0.0


def mean_satisfaction(ratios: Sequence[float]) -> float:
    return float(sum(ratios) / len(ratios)) if ratios else 0.0


def allocation_efficiency(total_allocated: float, total_demand: float) -> float:
    if total_demand <= 0:
        return 1.0 if total_allocated >= 0 else 0.0
    return float(min(1.0, max(0.0, total_allocated / total_demand)))


def water_deficit(total_demand: float, total_allocated: float) -> float:
    return float(max(0.0, total_demand - total_allocated))


def allocation_disparity(ratios: Sequence[float]) -> float:
    if not ratios:
        return 0.0
    return float(max(ratios) - min(ratios))


def fairness_summary(
    allocations: Sequence[float],
    demands: Sequence[float],
    total_allocated: float,
    total_demand: float,
) -> Dict[str, float]:
    ratios = demand_satisfaction_ratios(allocations, demands)
    return {
        "jains_fairness_index": jains_fairness_index(ratios),
        "minimum_satisfaction": minimum_satisfaction(ratios),
        "mean_satisfaction": mean_satisfaction(ratios),
        "allocation_efficiency": allocation_efficiency(total_allocated, total_demand),
        "water_deficit": water_deficit(total_demand, total_allocated),
        "allocation_disparity": allocation_disparity(ratios),
    }
