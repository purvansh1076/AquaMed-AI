"""
AquaMediAI — Approach A: Deterministic Agronomic Baseline Calculator
====================================================================

Implements a deterministic, physically grounded calculation of crop water
requirements based on FAO-56 standards.

This module serves as the primary benchmark (Approach A) against which
any machine-learning model (Approach B) must be compared.

Key Invariants:
1. Closed-form, mathematically deterministic equations.
2. Complete transparency: all physical assumptions and efficiency constants are explicit.
3. No statistical training, no overfitting, zero data leakage.
4. Guaranteed physical bounds (non-negative demand, physical conservation).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from app.data.fao56_penman_monteith import calculate_effective_precipitation_usda


@dataclass(frozen=True)
class AgronomicDemandResult:
    """
    Detailed results of the deterministic agronomic water requirement calculation.
    """

    et0_mm_per_day: float
    kc_value: float
    etc_mm_per_day: float
    gross_precipitation_mm: float
    effective_precipitation_mm: float
    net_irrigation_depth_mm: float
    application_efficiency: float
    gross_irrigation_depth_mm: float
    farm_area_hectares: float
    volumetric_demand_m3_per_day: float
    method: str = "FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DeterministicAgronomicBaseline:
    """
    Deterministic calculation engine for crop water demand.

    Parameters
    ----------
    default_application_efficiency : float
        Canal/field application efficiency (default 0.70 for gravity surface canals,
        0.85-0.90 for pressurized drip irrigation).
    """

    def __init__(self, default_application_efficiency: float = 0.70) -> None:
        if not (0.1 <= default_application_efficiency <= 1.0):
            raise ValueError("application_efficiency must be between 0.1 and 1.0.")
        self.default_efficiency = default_application_efficiency

    def calculate_daily_demand(
        self,
        farm_area_hectares: float,
        et0_mm_per_day: float,
        kc_value: float,
        rainfall_mm: float = 0.0,
        application_efficiency: Optional[float] = None,
    ) -> AgronomicDemandResult:
        """
        Compute daily crop irrigation requirement deterministically.

        Formulation
        -----------
        1. ETc = ET0 * Kc
        2. Peff = USDA_SCS(rainfall_mm)
        3. Inet = max(0.0, ETc - Peff)
        4. Igross = Inet / application_efficiency
        5. Vdemand = Igross * farm_area_hectares * 10.0 (m³/day)

        Parameters
        ----------
        farm_area_hectares : float
            Cultivated farm plot size (hectares, must be > 0).
        et0_mm_per_day : float
            Reference evapotranspiration (mm/day, must be >= 0).
        kc_value : float
            Crop coefficient for current stage (dimensionless, must be > 0).
        rainfall_mm : float
            Daily gross rainfall (mm, >= 0).
        application_efficiency : float, optional
            Efficiency override [0.1, 1.0].

        Returns
        -------
        AgronomicDemandResult
        """
        if farm_area_hectares <= 0.0:
            raise ValueError(f"farm_area_hectares must be > 0, got {farm_area_hectares}")
        if et0_mm_per_day < 0.0:
            raise ValueError(f"et0_mm_per_day must be >= 0, got {et0_mm_per_day}")
        if kc_value <= 0.0:
            raise ValueError(f"kc_value must be > 0, got {kc_value}")
        if rainfall_mm < 0.0:
            raise ValueError(f"rainfall_mm must be >= 0, got {rainfall_mm}")

        eff = application_efficiency if application_efficiency is not None else self.default_efficiency
        if not (0.1 <= eff <= 1.0):
            raise ValueError(f"application_efficiency must be in [0.1, 1.0], got {eff}")

        # 1. Crop Evapotranspiration ETc
        etc = et0_mm_per_day * kc_value

        # 2. Effective Rainfall Peff
        p_eff = calculate_effective_precipitation_usda(rainfall_mm)

        # 3. Net Irrigation Requirement (Depth in mm)
        i_net = max(0.0, etc - p_eff)

        # 4. Gross Irrigation Requirement (accounting for conveyance & application losses)
        i_gross = i_net / eff

        # 5. Volumetric Water Demand (m³/day)
        # 1 mm over 1 ha = 10 m³
        v_demand = i_gross * farm_area_hectares * 10.0

        return AgronomicDemandResult(
            et0_mm_per_day=round(et0_mm_per_day, 4),
            kc_value=round(kc_value, 4),
            etc_mm_per_day=round(etc, 4),
            gross_precipitation_mm=round(rainfall_mm, 4),
            effective_precipitation_mm=round(p_eff, 4),
            net_irrigation_depth_mm=round(i_net, 4),
            application_efficiency=round(eff, 4),
            gross_irrigation_depth_mm=round(i_gross, 4),
            farm_area_hectares=round(farm_area_hectares, 4),
            volumetric_demand_m3_per_day=round(v_demand, 4),
        )
