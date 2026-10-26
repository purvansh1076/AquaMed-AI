"""
AquaMediAI — FAO-56 Penman-Monteith Reference Evapotranspiration (ET₀) Engine
=============================================================================

Implements the standard FAO-56 Penman-Monteith method for computing daily
reference evapotranspiration (ET₀) from agroclimatological parameters.

Reference
---------
Allen, R.G., Pereira, L.S., Raes, D., & Smith, M. (1998).
Crop evapotranspiration — Guidelines for computing crop water requirements.
FAO Irrigation and Drainage Paper No. 56. FAO, Rome, Italy.
"""

from __future__ import annotations

import math
from typing import Dict, Optional


def calculate_fao56_et0(
    lat_deg: float,
    day_of_year: int,
    t_min: float,
    t_max: float,
    t_mean: float,
    rh_mean: float,
    wind_2m: float,
    rs_mj: float,
    elevation_m: float = 540.0,
) -> float:
    """
    Calculate daily FAO-56 reference evapotranspiration (ET₀ in mm/day).

    Parameters
    ----------
    lat_deg : float
        Latitude in decimal degrees (positive North, negative South).
    day_of_year : int
        Calendar day of year (1–366).
    t_min : float
        Daily minimum air temperature (°C).
    t_max : float
        Daily maximum air temperature (°C).
    t_mean : float
        Daily mean air temperature (°C).
    rh_mean : float
        Daily mean relative humidity (%).
    wind_2m : float
        Daily mean wind speed at 2 m above ground (m/s).
    rs_mj : float
        Daily downward shortwave solar radiation at surface (MJ/m²/day).
    elevation_m : float, optional
        Altitude above sea level (meters). Default 540.0 (Central Maharashtra).

    Returns
    -------
    float
        Daily reference evapotranspiration ET₀ in mm/day (clamped to >= 0.0).
    """
    # 0. Unit safety & physical bounds
    lat_rad = math.radians(lat_deg)
    rh_clamped = max(1.0, min(100.0, rh_mean))
    wind_clamped = max(0.1, wind_2m)  # FAO-56 minimum wind speed threshold
    rs_clamped = max(0.0, rs_mj)

    # 1. Atmospheric pressure P (kPa) — FAO-56 Eq. 7
    P = 101.3 * (((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26)

    # 2. Psychrometric constant gamma (kPa/°C) — FAO-56 Eq. 8
    gamma = 0.000665 * P

    # 3. Saturation vapor pressure es (kPa) — FAO-56 Eq. 11, 12
    e_tmax = 0.6108 * math.exp((17.27 * t_max) / (t_max + 237.3))
    e_tmin = 0.6108 * math.exp((17.27 * t_min) / (t_min + 237.3))
    es = (e_tmax + e_tmin) / 2.0

    # 4. Actual vapor pressure ea (kPa) — FAO-56 Eq. 17
    ea = es * (rh_clamped / 100.0)

    # 5. Slope of vapor pressure curve delta (kPa/°C) — FAO-56 Eq. 13
    delta = (4098.0 * (0.6108 * math.exp((17.27 * t_mean) / (t_mean + 237.3)))) / (
        (t_mean + 237.3) ** 2
    )

    # 6. Extraterrestrial radiation Ra (MJ/m²/day) — FAO-56 Eq. 21, 23, 24
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
    decl = 0.409 * math.sin(2.0 * math.pi * day_of_year / 365.0 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(decl))))
    Gsc = 0.0820  # Solar constant (MJ/m²/min)
    Ra = (
        (24.0 * 60.0 / math.pi)
        * Gsc
        * dr
        * (
            ws * math.sin(lat_rad) * math.sin(decl)
            + math.cos(lat_rad) * math.cos(decl) * math.sin(ws)
        )
    )

    # 7. Clear-sky solar radiation Rso (MJ/m²/day) — FAO-56 Eq. 37
    Rso = (0.75 + 2e-5 * elevation_m) * Ra

    # 8. Net shortwave radiation Rns (MJ/m²/day) — FAO-56 Eq. 38 (albedo = 0.23 for reference grass)
    Rns = (1.0 - 0.23) * rs_clamped

    # 9. Net longwave radiation Rnl (MJ/m²/day) — FAO-56 Eq. 39
    sigma = 4.903e-9  # Stefan-Boltzmann constant (MJ/K⁴/m²/day)
    cloudiness = rs_clamped / max(0.1, Rso)
    cloud_factor = 1.35 * min(1.0, max(0.3, cloudiness)) - 0.35
    humidity_factor = max(0.05, 0.34 - 0.14 * math.sqrt(max(0.0, ea)))
    temp_factor = (((t_max + 273.16) ** 4) + ((t_min + 273.16) ** 4)) / 2.0
    Rnl = sigma * temp_factor * humidity_factor * cloud_factor

    # 10. Net radiation Rn (MJ/m²/day) — FAO-56 Eq. 40
    Rn = Rns - Rnl

    # 11. Soil heat flux G (MJ/m²/day) — FAO-56 Eq. 42 (G ≈ 0 for daily intervals)
    G = 0.0

    # 12. FAO-56 Penman-Monteith Equation — FAO-56 Eq. 6
    num = 0.408 * delta * (Rn - G) + gamma * (900.0 / (t_mean + 273.0)) * wind_clamped * (es - ea)
    denom = delta + gamma * (1.0 + 0.34 * wind_clamped)

    et0 = num / denom
    return max(0.0, float(et0))


def calculate_effective_precipitation_usda(precipitation_mm: float) -> float:
    """
    Calculate effective precipitation (P_eff in mm) via USDA Soil Conservation Service (SCS) method.

    Light rain showers (<3 mm) evaporate directly from canopy/soil surface and
    do not recharge the root zone. Intense storms generate surface runoff.

    Parameters
    ----------
    precipitation_mm : float
        Gross daily precipitation (mm).

    Returns
    -------
    float
        Effective precipitation in mm (retained in root zone).
    """
    p = max(0.0, precipitation_mm)
    if p < 3.0:
        return 0.0
    if p <= 250.0:
        p_eff = p * (125.0 - 0.2 * p) / 125.0
    else:
        p_eff = 125.0 + 0.1 * p
    return max(0.0, float(p_eff))


def calculate_crop_water_requirements(
    et0_mm: float,
    kc_value: float,
    precipitation_mm: float,
    application_efficiency: float = 0.70,
) -> Dict[str, float]:
    """
    Compute agronomic crop water requirement components.

    Parameters
    ----------
    et0_mm : float
        Reference evapotranspiration (mm/day).
    kc_value : float
        Crop coefficient for current stage (dimensionless).
    precipitation_mm : float
        Daily gross precipitation (mm).
    application_efficiency : float, optional
        Canal / surface irrigation efficiency (default 0.70 for gravity surface canals).

    Returns
    -------
    dict
        Dictionary containing:
        - etc_mm: Crop evapotranspiration (ET₀ × Kc)
        - effective_rain_mm: Precipitation retained in root zone
        - net_irrigation_mm: max(0, ETc - P_eff)
        - gross_irrigation_mm: net_irrigation_mm / application_efficiency
    """
    etc_mm = max(0.0, et0_mm * kc_value)
    p_eff_mm = calculate_effective_precipitation_usda(precipitation_mm)
    net_irrigation_mm = max(0.0, etc_mm - p_eff_mm)
    eff = max(0.1, min(1.0, application_efficiency))
    gross_irrigation_mm = net_irrigation_mm / eff

    return {
        "et0_mm": round(et0_mm, 4),
        "kc_value": round(kc_value, 4),
        "etc_mm": round(etc_mm, 4),
        "gross_precipitation_mm": round(precipitation_mm, 4),
        "effective_precipitation_mm": round(p_eff_mm, 4),
        "net_irrigation_mm": round(net_irrigation_mm, 4),
        "gross_irrigation_mm": round(gross_irrigation_mm, 4),
    }
