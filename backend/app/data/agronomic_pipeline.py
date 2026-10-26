"""
AquaMediAI — Daily Weather Data Cleaning & Agronomic Processing Pipeline
========================================================================

Transforms raw NASA POWER weather observations into a validated,
FAO-56 reference evapotranspiration (ET₀) and effective rainfall time series.

Outputs cleaned data to data/processed/, maintaining strict separation from
raw ingested payloads in data/raw/.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.data.fao56_penman_monteith import (
    calculate_effective_precipitation_usda,
    calculate_fao56_et0,
)
from app.data.region_config import RegionConfig, get_region_config

logger = logging.getLogger(__name__)

# NASA POWER uses -999.0 to indicate missing values
NASA_MISSING_VALUE = -999.0


@dataclass
class ValidationReport:
    """
    Validation audit summary for the ingested and processed weather dataset.
    """

    region_id: str
    region_name: str
    total_records: int
    date_start: str
    date_end: str
    missing_values_detected: Dict[str, int]
    imputed_records_count: int
    physical_bounds_violations: List[str]
    mean_et0_mm_per_day: float
    min_et0_mm_per_day: float
    max_et0_mm_per_day: float
    total_precipitation_mm: float
    total_effective_precipitation_mm: float
    status: str = "PASSED"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assign_indian_agricultural_season(month: int) -> str:
    """
    Classify calendar month into standard Indian agroclimatological seasons:
    - Kharif (Monsoon): June (6) to October (10)
    - Rabi (Post-Monsoon / Cool Dry): November (11) to March (3)
    - Zaid (Summer / Hot Dry): April (4) to May (5)
    """
    if 6 <= month <= 10:
        return "kharif"
    elif month in (11, 12, 1, 2, 3):
        return "rabi"
    else:
        return "zaid"


class AgronomicDataPipeline:
    """
    Validates, cleans, and computes FAO-56 agroclimatology features.

    Parameters
    ----------
    region : RegionConfig or str, optional
        Agricultural region configuration.
    processed_dir : Path or str, optional
        Directory where cleaned, processed CSVs are saved.
    """

    def __init__(
        self,
        region: RegionConfig | str | None = None,
        processed_dir: Path | str | None = None,
    ) -> None:
        if isinstance(region, str) or region is None:
            self.region = get_region_config(region)
        else:
            self.region = region

        from app.config import get_settings
        base_dir = get_settings().model_dir_path.parent  # backend/data
        self.processed_dir = Path(processed_dir) if processed_dir else (base_dir / "processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        df_raw: pd.DataFrame,
        save_csv: bool = True,
        output_filename: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, ValidationReport]:
        """
        Execute data cleaning, quality validation, and FAO-56 ET₀ computation.

        Parameters
        ----------
        df_raw : pd.DataFrame
            Raw DataFrame parsed from NASA POWER client.
        save_csv : bool
            Whether to write cleaned output to processed_dir.
        output_filename : str, optional
            Custom CSV filename. Defaults to clean_daily_weather_{region_id}.csv.

        Returns
        -------
        (cleaned_df, validation_report)
        """
        if df_raw.empty:
            raise ValueError("Cannot process empty raw weather DataFrame.")

        df = df_raw.copy()
        violations: List[str] = []
        missing_counts: Dict[str, int] = {}

        # 1. Clean NASA POWER missing value indicators (-999.0)
        numeric_cols = [
            c for c in ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "PRECTOTCORR", "WS2M", "ALLSKY_SFC_SW_DWN"]
            if c in df.columns
        ]

        for col in numeric_cols:
            is_missing = (df[col] <= NASA_MISSING_VALUE + 1.0) | df[col].isna()
            cnt = int(is_missing.sum())
            missing_counts[col] = cnt
            if cnt > 0:
                df.loc[is_missing, col] = np.nan

        # Linear interpolation for isolated missing weather days
        imputed_count = int(df[numeric_cols].isna().sum().sum())
        if imputed_count > 0:
            df[numeric_cols] = df[numeric_cols].interpolate(method="linear").bfill().ffill()
            logger.info("Imputed %d missing weather cells via linear interpolation.", imputed_count)

        # 2. Physical boundary checks
        # Temperature sanity
        if (df["T2M_MIN"] > df["T2M_MAX"]).any():
            violations.append("T2M_MIN exceeds T2M_MAX on some days; auto-adjusting to preserve ordering.")
            t_min_fixed = np.minimum(df["T2M_MIN"], df["T2M_MAX"])
            t_max_fixed = np.maximum(df["T2M_MIN"], df["T2M_MAX"])
            df["T2M_MIN"] = t_min_fixed
            df["T2M_MAX"] = t_max_fixed

        # Relative humidity bounds [0, 100]
        df["RH2M"] = df["RH2M"].clip(lower=0.0, upper=100.0)

        # Wind speed non-negative
        df["WS2M"] = df["WS2M"].clip(lower=0.1)

        # Solar radiation non-negative
        df["ALLSKY_SFC_SW_DWN"] = df["ALLSKY_SFC_SW_DWN"].clip(lower=0.0)

        # Precipitation non-negative
        df["PRECTOTCORR"] = df["PRECTOTCORR"].clip(lower=0.0)

        # 3. Add Agronomic Context
        df["region_id"] = self.region.region_id
        df["season"] = df["month"].apply(assign_indian_agricultural_season)

        # 4. Compute FAO-56 Penman-Monteith Reference Evapotranspiration (ET₀)
        et0_values: List[float] = []
        eff_rain_values: List[float] = []

        for _, row in df.iterrows():
            et0 = calculate_fao56_et0(
                lat_deg=self.region.latitude,
                day_of_year=int(row["day_of_year"]),
                t_min=float(row["T2M_MIN"]),
                t_max=float(row["T2M_MAX"]),
                t_mean=float(row["T2M"]),
                rh_mean=float(row["RH2M"]),
                wind_2m=float(row["WS2M"]),
                rs_mj=float(row["ALLSKY_SFC_SW_DWN"]),
                elevation_m=self.region.elevation_m,
            )
            eff_rain = calculate_effective_precipitation_usda(float(row["PRECTOTCORR"]))

            et0_values.append(round(et0, 4))
            eff_rain_values.append(round(eff_rain, 4))

        df["et0_fao56_mm_per_day"] = et0_values
        df["effective_precipitation_mm"] = eff_rain_values

        # 5. Build Standard Column Aliases matching project conventions
        df["temperature_celsius"] = df["T2M"]
        df["humidity_percent"] = df["RH2M"]
        df["wind_speed_m_per_s"] = df["WS2M"]
        df["rainfall_mm"] = df["PRECTOTCORR"]
        df["solar_radiation_mj_per_m2"] = df["ALLSKY_SFC_SW_DWN"]

        # 6. Save Clean Dataset to data/processed/
        clean_filename = output_filename or f"clean_daily_weather_{self.region.region_id}.csv"
        clean_path = self.processed_dir / clean_filename
        if save_csv:
            df.to_csv(clean_path, index=False)
            logger.info("Saved cleaned weather dataset (%d rows) to: %s", len(df), clean_path)

        # 7. Generate Audit Validation Report
        report = ValidationReport(
            region_id=self.region.region_id,
            region_name=self.region.region_name,
            total_records=len(df),
            date_start=str(df["date"].min().date()),
            date_end=str(df["date"].max().date()),
            missing_values_detected=missing_counts,
            imputed_records_count=imputed_count,
            physical_bounds_violations=violations,
            mean_et0_mm_per_day=float(df["et0_fao56_mm_per_day"].mean()),
            min_et0_mm_per_day=float(df["et0_fao56_mm_per_day"].min()),
            max_et0_mm_per_day=float(df["et0_fao56_mm_per_day"].max()),
            total_precipitation_mm=float(df["rainfall_mm"].sum()),
            total_effective_precipitation_mm=float(df["effective_precipitation_mm"].sum()),
            status="PASSED" if not violations else "PASSED_WITH_WARNINGS",
        )

        return df, report
