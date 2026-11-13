"""
Independent (audit-only) cross-check of FAO-56 Penman-Monteith.

This re-implements the equation in a separate code path and compares to the
production implementation. It does NOT establish absolute correctness against
a trusted external reference; it guards against regressions.
"""
from __future__ import annotations

import math

from app.data.fao56_penman_monteith import calculate_fao56_et0


def _independent_et0(lat_deg, day_of_year, t_min, t_max, t_mean, rh_mean, wind_2m, rs_mj, elevation_m):
    lat_rad = math.radians(lat_deg)
    rh = max(1.0, min(100.0, rh_mean))
    wind = max(0.1, wind_2m)
    rs = max(0.0, rs_mj)
    P = 101.3 * (((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26)
    gamma = 0.000665 * P
    e_tmax = 0.6108 * math.exp((17.27 * t_max) / (t_max + 237.3))
    e_tmin = 0.6108 * math.exp((17.27 * t_min) / (t_min + 237.3))
    es = (e_tmax + e_tmin) / 2.0
    ea = es * (rh / 100.0)
    delta = (4098.0 * (0.6108 * math.exp((17.27 * t_mean) / (t_mean + 237.3)))) / ((t_mean + 237.3) ** 2)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
    decl = 0.409 * math.sin(2.0 * math.pi * day_of_year / 365.0 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(decl))))
    Ra = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (ws * math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.sin(ws))
    Rso = (0.75 + 2e-5 * elevation_m) * Ra
    Rns = 0.77 * rs
    cloudiness = rs / max(0.1, Rso)
    cloud_factor = 1.35 * min(1.0, max(0.3, cloudiness)) - 0.35
    humidity_factor = max(0.05, 0.34 - 0.14 * math.sqrt(max(0.0, ea)))
    temp_factor = (((t_max + 273.16) ** 4) + ((t_min + 273.16) ** 4)) / 2.0
    Rnl = 4.903e-9 * temp_factor * humidity_factor * cloud_factor
    Rn = Rns - Rnl
    G = 0.0
    num = 0.408 * delta * (Rn - G) + gamma * (900.0 / (t_mean + 273.0)) * wind * (es - ea)
    denom = delta + gamma * (1.0 + 0.34 * wind)
    et0 = num / denom
    return max(0.0, float(et0))


CASES = [
    (19.0, 120, 22.0, 38.0, 30.0, 45.0, 2.0, 22.0, 540.0),
    (28.0, 1, 10.0, 20.0, 15.0, 70.0, 1.5, 12.0, 200.0),
    (10.0, 200, 18.0, 30.0, 24.0, 55.0, 3.0, 18.0, 100.0),
]


def test_et0_cross_check():
    for case in CASES:
        prod = calculate_fao56_et0(*case)
        ref = _independent_et0(*case)
        assert abs(prod - ref) < 1e-9


def test_et0_monotonic_temperature():
    base = calculate_fao56_et0(19.0, 120, 22.0, 38.0, 30.0, 45.0, 2.0, 22.0, 540.0)
    hotter = calculate_fao56_et0(19.0, 120, 26.0, 42.0, 34.0, 45.0, 2.0, 22.0, 540.0)
    assert hotter >= base
