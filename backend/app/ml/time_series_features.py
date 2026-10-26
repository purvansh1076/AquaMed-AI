"""
AquaMediAI — Causal Time-Series Feature Engineering for Weather Data
=====================================================================

Constructs defensible, physically meaningful time-series features from
daily meteorological observations.

Design Principles:
1. STRICT CAUSALITY: Lags and rolling aggregates only use observations from
   t-1 and prior. No lookahead or future data leakage.
2. CYCLICAL CALENDAR: Day-of-year is encoded via trigonometric harmonic functions
   (sine/cosine) to represent seasonal solar periodicity without artificial December-to-January discontinuities.
3. ANTECEDENT HYDROLOGY: 1-day lag, 3-day sum, and 7-day sum of precipitation
   act as proxies for antecedent root-zone moisture recharge.
"""

from __future__ import annotations

import math
from typing import List

import numpy as np
import pandas as pd


def compute_causal_weather_features(df_weather: pd.DataFrame) -> pd.DataFrame:
    """
    Generate causal meteorological features from a chronological daily weather DataFrame.

    Parameters
    ----------
    df_weather : pd.DataFrame
        Must contain columns:
        ['date', 'temperature_celsius', 'T2M_MAX', 'T2M_MIN',
         'humidity_percent', 'wind_speed_m_per_s', 'rainfall_mm',
         'solar_radiation_mj_per_m2', 'day_of_year']

    Returns
    -------
    pd.DataFrame
        Enriched DataFrame with lag, rolling, and cyclical features.
    """
    df = df_weather.sort_values("date").copy().reset_index(drop=True)

    # 1. Thermal range: diurnal temperature swing reflects atmospheric dryness
    if "T2M_MAX" in df.columns and "T2M_MIN" in df.columns:
        df["diurnal_temp_range_celsius"] = df["T2M_MAX"] - df["T2M_MIN"]
    else:
        df["diurnal_temp_range_celsius"] = 0.0

    # 2. Cyclical day of year encodings (seasonal solar radiation cycle)
    doy = df["day_of_year"].astype(float)
    df["doy_sin"] = np.sin(2.0 * math.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2.0 * math.pi * doy / 365.25)

    # 3. Antecedent Precipitation (Strictly Causal: shift by 1 day)
    # Yesterday's rainfall
    df["rainfall_lag1_mm"] = df["rainfall_mm"].shift(1).fillna(0.0)

    # Rolling cumulative rainfall over preceding 3 and 7 days (excluding today)
    # Using shift(1) guarantees no current-day or future leakage
    df["rainfall_antecedent_3d_mm"] = (
        df["rainfall_mm"].shift(1).rolling(window=3, min_periods=1).sum().fillna(0.0)
    )
    df["rainfall_antecedent_7d_mm"] = (
        df["rainfall_mm"].shift(1).rolling(window=7, min_periods=1).sum().fillna(0.0)
    )

    # 4. Thermal Persistence: Rolling mean temperature over preceding 3 and 7 days
    temp_col = "temperature_celsius" if "temperature_celsius" in df.columns else "T2M"
    df["temp_rolling_mean_3d_celsius"] = (
        df[temp_col].shift(1).rolling(window=3, min_periods=1).mean().bfill()
    )
    df["temp_rolling_mean_7d_celsius"] = (
        df[temp_col].shift(1).rolling(window=7, min_periods=1).mean().bfill()
    )

    # 5. Solar Radiation rolling average (atmospheric cloudiness trend)
    rad_col = (
        "solar_radiation_mj_per_m2"
        if "solar_radiation_mj_per_m2" in df.columns
        else "ALLSKY_SFC_SW_DWN"
    )
    df["solar_rad_rolling_mean_3d"] = (
        df[rad_col].shift(1).rolling(window=3, min_periods=1).mean().bfill()
    )

    # 6. Vapor Pressure Deficit Proxy (VPD is non-linear; temp * (1 - RH/100))
    rh_col = "humidity_percent" if "humidity_percent" in df.columns else "RH2M"
    rh_frac = (df[rh_col] / 100.0).clip(0.0, 1.0)
    df["vpd_proxy_kpa"] = 0.6108 * np.exp((17.27 * df[temp_col]) / (df[temp_col] + 237.3)) * (1.0 - rh_frac)

    return df


DEFENSIBLE_MODEL_FEATURES: List[str] = [
    # Meteorological state (measured daily)
    "temperature_celsius",
    "diurnal_temp_range_celsius",
    "humidity_percent",
    "wind_speed_m_per_s",
    "solar_radiation_mj_per_m2",
    "vpd_proxy_kpa",
    # Antecedent hydrology (strictly causal)
    "rainfall_lag1_mm",
    "rainfall_antecedent_3d_mm",
    "rainfall_antecedent_7d_mm",
    # Thermal & radiation persistence
    "temp_rolling_mean_3d_celsius",
    "temp_rolling_mean_7d_celsius",
    "solar_rad_rolling_mean_3d",
    # Cyclical calendar harmonics
    "doy_sin",
    "doy_cos",
]
