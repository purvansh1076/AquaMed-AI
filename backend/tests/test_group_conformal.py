import numpy as np

from app.ml.group_conformal import GroupConformalPredictor


def test_group_conformal_fallback():
    gcp = GroupConformalPredictor(min_group_size=100)
    residuals = np.array([10.0, 20.0, 30.0] * 10)
    scales = np.ones_like(residuals)
    groups = np.array(["wheat"] * 15 + ["rice"] * 15)
    gcp.calibrate(residuals, scales, groups)
    # small groups -> fallback to global
    iv = gcp.predict_interval(100.0, farm_area_ha=1.0, group="wheat")
    assert iv["lower_bound_m3"] <= 100.0 <= iv["upper_bound_m3"]


def test_group_conformal_large_group():
    gcp = GroupConformalPredictor(min_group_size=5)
    residuals = np.array([5.0] * 20 + [50.0] * 20)
    scales = np.ones_like(residuals)
    groups = np.array(["a"] * 20 + ["b"] * 20)
    gcp.calibrate(residuals, scales, groups)
    assert "a" in gcp.group_q
    assert "b" in gcp.group_q
