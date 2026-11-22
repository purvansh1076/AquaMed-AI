import pytest

from app.ml.agronomic_baseline import DeterministicAgronomicBaseline


def test_fao56_benchmark_sugarcane():
    engine = DeterministicAgronomicBaseline(default_application_efficiency=0.70)
    res = engine.calculate_daily_demand(
        farm_area_hectares=3.5,
        et0_mm_per_day=5.20,
        kc_value=1.15,
        rainfall_mm=0.0,
    )
    assert abs(res.etc_mm_per_day - 5.98) < 1e-6
    assert abs(res.volumetric_demand_m3_per_day - 299.0) < 1e-3


def test_mm_to_m3_conversion():
    # 1 mm over 1 ha = 10 m3
    engine = DeterministicAgronomicBaseline(default_application_efficiency=1.0)
    res = engine.calculate_daily_demand(
        farm_area_hectares=1.0,
        et0_mm_per_day=1.0,
        kc_value=1.0,
        rainfall_mm=0.0,
    )
    assert abs(res.volumetric_demand_m3_per_day - 10.0) < 1e-6


def test_effective_rainfall_reduces_demand():
    engine = DeterministicAgronomicBaseline(default_application_efficiency=1.0)
    res = engine.calculate_daily_demand(
        farm_area_hectares=1.0,
        et0_mm_per_day=5.0,
        kc_value=1.0,
        rainfall_mm=10.0,
    )
    assert res.volumetric_demand_m3_per_day < 50.0
