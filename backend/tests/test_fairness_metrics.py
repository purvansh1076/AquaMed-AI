from app.allocation.fairness import (
    demand_satisfaction_ratios,
    jains_fairness_index,
    minimum_satisfaction,
    mean_satisfaction,
    allocation_efficiency,
    water_deficit,
    allocation_disparity,
    fairness_summary,
)


def test_jains_perfect_fairness():
    ratios = [0.5, 0.5, 0.5]
    assert abs(jains_fairness_index(ratios) - 1.0) < 1e-9


def test_jains_zero_demand_handled():
    ratios = demand_satisfaction_ratios([0.0, 10.0], [0.0, 20.0])
    assert ratios[0] == 1.0
    assert ratios[1] == 0.5


def test_fairness_summary_basic():
    alloc = [10.0, 20.0]
    demand = [20.0, 40.0]
    s = fairness_summary(alloc, demand, 30.0, 60.0)
    assert 0 <= s["jains_fairness_index"] <= 1
    assert s["allocation_efficiency"] == 0.5
    assert s["water_deficit"] == 30.0
    assert s["allocation_disparity"] == 0.0


def test_disparity():
    assert abs(allocation_disparity([0.2, 0.8]) - 0.6) < 1e-9


def test_minimum_mean():
    assert minimum_satisfaction([0.1, 0.9]) == 0.1
    assert abs(mean_satisfaction([0.1, 0.9]) - 0.5) < 1e-9
