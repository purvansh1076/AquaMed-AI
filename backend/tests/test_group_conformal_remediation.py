import math
import numpy as np

from app.ml.group_conformal import GroupConformalPredictor


def test_finite_sample_level_small():
    gcp = GroupConformalPredictor(confidence_level=0.90)
    # n=10 -> ceil(11*0.9)/10 = ceil(9.9)/10 = 10/10 = 1.0
    assert gcp._finite_sample_quantile_level(10, 0.10) == 1.0


def test_finite_sample_level_large():
    gcp = GroupConformalPredictor(confidence_level=0.90)
    n = 100
    level = gcp._finite_sample_quantile_level(n, 0.10)
    k = math.ceil((n + 1) * 0.90)
    assert abs(level - k / n) < 1e-12


def test_group_conformal_unknown_group_fallback():
    gcp = GroupConformalPredictor(min_group_size=5)
    residuals = np.array([5.0] * 10)
    scales = np.ones_like(residuals)
    groups = np.array(["a"] * 10)
    gcp.calibrate(residuals, scales, groups)
    iv = gcp.predict_interval(100.0, farm_area_ha=1.0, group="unknown")
    assert iv["lower_bound_m3"] <= 100.0 <= iv["upper_bound_m3"]
