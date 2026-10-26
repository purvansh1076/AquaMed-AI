"""
AquaMediAI — NASA POWER Agroclimatology API Client
===================================================

Client for retrieving daily agroclimatology weather observations from the
NASA POWER (Prediction Of Worldwide Energy Resources) API.

Reference
---------
NASA Langley Research Center (LaRC) POWER Project
https://power.larc.nasa.gov/
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd

from app.data.region_config import RegionConfig, get_region_config

logger = logging.getLogger(__name__)

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Standard agroclimatology parameters required for FAO-56 Penman-Monteith
DEFAULT_WEATHER_PARAMS: List[str] = [
    "T2M",               # Temperature at 2 Meters (°C)
    "T2M_MAX",           # Maximum Temperature at 2 Meters (°C)
    "T2M_MIN",           # Minimum Temperature at 2 Meters (°C)
    "RH2M",              # Relative Humidity at 2 Meters (%)
    "PRECTOTCORR",       # Precipitation Corrected (mm/day)
    "WS2M",              # Wind Speed at 2 Meters (m/s)
    "ALLSKY_SFC_SW_DWN", # All-sky Surface Shortwave Downward Irradiance (MJ/m²/day)
]


class NasaPowerClient:
    """
    Client for fetching and parsing daily weather data from NASA POWER.

    Parameters
    ----------
    region : RegionConfig or str, optional
        Target agricultural region configuration or region ID.
    timeout_seconds : float
        HTTP request timeout in seconds.
    raw_dir : Path or str, optional
        Directory where unmodified raw API payloads are saved.
    max_retries : int
        Maximum retries for network / transient failures (default: 3).
    """

    def __init__(
        self,
        region: RegionConfig | str | None = None,
        timeout_seconds: float = 45.0,
        raw_dir: Path | str | None = None,
        max_retries: int = 3,
    ) -> None:
        if isinstance(region, str) or region is None:
            self.region = get_region_config(region)
        else:
            self.region = region

        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        from app.config import get_settings
        self.raw_dir = Path(raw_dir) if raw_dir else get_settings().data_dir_path
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch_daily_weather(
        self,
        start_date: str = "20230101",
        end_date: str = "20231231",
        parameters: Optional[List[str]] = None,
        save_raw: bool = True,
        use_cache: bool = True,
        offline_fixture_path: Optional[Path | str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve raw daily weather observations from NASA POWER API or local fixture.

        Parameters
        ----------
        start_date : str
            Start date formatted as 'YYYYMMDD' (e.g. '20230101').
        end_date : str
            End date formatted as 'YYYYMMDD' (e.g. '20231231').
        parameters : list of str, optional
            List of parameter keys to fetch. Defaults to DEFAULT_WEATHER_PARAMS.
        save_raw : bool
            Whether to write unmodified payload to raw_dir.
        use_cache : bool
            Whether to read cached raw JSON from raw_dir if it already exists.
        offline_fixture_path : Path or str, optional
            If provided or if NASA_POWER_OFFLINE=1, loads data from this local file.

        Returns
        -------
        dict
            Raw JSON response payload from NASA POWER.
        """
        offline_env = os.environ.get("NASA_POWER_OFFLINE", "").strip().lower() in ("1", "true", "yes")

        # 1. Offline Mode
        if offline_fixture_path or offline_env:
            fixture_file = Path(offline_fixture_path) if offline_fixture_path else None
            if not fixture_file or not fixture_file.exists():
                standard_fixture = (
                    Path(__file__).resolve().parent.parent.parent
                    / "tests"
                    / "fixtures"
                    / "nasa_power_ahmednagar_sample.json"
                )
                if standard_fixture.exists():
                    fixture_file = standard_fixture
                else:
                    raise FileNotFoundError(f"Offline fixture not found: {fixture_file}")

            logger.info("Loading NASA POWER data from offline fixture: %s", fixture_file)
            with open(fixture_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data

        raw_filename = f"nasa_power_{self.region.region_id}_{start_date}_{end_date}.json"
        raw_path = self.raw_dir / raw_filename

        # 2. Local Disk Cache Check
        if use_cache and raw_path.exists() and raw_path.stat().st_size > 50:
            logger.info("Using cached raw NASA POWER payload from: %s", raw_path)
            try:
                with open(raw_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                if "properties" in cached_data and "parameter" in cached_data["properties"]:
                    return cached_data
                logger.warning("Cached raw file %s is malformed; refetching...", raw_path)
            except Exception as e:
                logger.warning("Failed to read cache %s (%s); refetching...", raw_path, e)

        # 3. Live HTTP Request with Bounded Retries
        params = parameters or DEFAULT_WEATHER_PARAMS
        param_str = ",".join(params)
        query_params = {
            "parameters": param_str,
            "community": "AG",
            "longitude": f"{self.region.longitude:.4f}",
            "latitude": f"{self.region.latitude:.4f}",
            "start": start_date,
            "end": end_date,
            "format": "JSON",
        }

        logger.info(
            "Querying NASA POWER API for region '%s' (lat=%.2f, lon=%.2f, %s to %s)…",
            self.region.region_id,
            self.region.latitude,
            self.region.longitude,
            start_date,
            end_date,
        )

        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.get(NASA_POWER_BASE_URL, params=query_params)
                    if resp.status_code >= 400:
                        snippet = resp.text[:300] if resp.text else "(empty)"
                        raise httpx.HTTPStatusError(
                            f"HTTP {resp.status_code} Error: {snippet}",
                            request=resp.request,
                            response=resp,
                        )
                    data = resp.json()

                if "properties" not in data or "parameter" not in data["properties"]:
                    raise ValueError(f"NASA POWER payload missing 'properties.parameter': {list(data.keys())}")

                # Save raw unmodified payload for auditability
                if save_raw:
                    with open(raw_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    logger.info("Saved raw unmodified payload (%d bytes) to: %s", raw_path.stat().st_size, raw_path)

                return data

            except (httpx.TransportError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError) as exc:
                last_err = exc
                wait_sec = 2 ** attempt
                logger.warning(
                    "NASA POWER API attempt %d/%d failed: %s. Retrying in %ds…",
                    attempt,
                    self.max_retries,
                    exc,
                    wait_sec,
                )
                if attempt < self.max_retries:
                    time.sleep(wait_sec)

        raise RuntimeError(
            f"Failed to fetch NASA POWER weather data after {self.max_retries} attempts for "
            f"region '{self.region.region_id}' ({start_date} to {end_date}): {last_err}"
        ) from last_err

    def fetch_multi_year_weather(
        self,
        years: List[int],
        save_raw: bool = True,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch and concatenate daily weather across multiple calendar years.

        Parameters
        ----------
        years : list of int
            List of calendar years to retrieve (e.g. [2021, 2022, 2023, 2024, 2025]).
        save_raw : bool
            Save each year's raw JSON response to disk.
        use_cache : bool
            Load from disk cache if raw file already exists.

        Returns
        -------
        pd.DataFrame
            Chronologically concatenated daily weather time series with no duplicate dates.
        """
        yearly_dfs: List[pd.DataFrame] = []
        for yr in sorted(years):
            start_date = f"{yr}0101"
            end_date = f"{yr}1231"
            payload = self.fetch_daily_weather(
                start_date=start_date,
                end_date=end_date,
                save_raw=save_raw,
                use_cache=use_cache,
            )
            df_yr = self.parse_payload_to_dataframe(payload)
            logger.info("Year %d: parsed %d daily records (%s to %s)", yr, len(df_yr), start_date, end_date)
            yearly_dfs.append(df_yr)

        if not yearly_dfs:
            return pd.DataFrame()

        df_combined = pd.concat(yearly_dfs, ignore_index=True)
        # Drop duplicates if any overlap
        initial_count = len(df_combined)
        df_combined = df_combined.drop_duplicates(subset=["date_str"]).sort_values("date").reset_index(drop=True)
        if len(df_combined) < initial_count:
            logger.warning("Dropped %d duplicate date records during multi-year concatenation.", initial_count - len(df_combined))

        return df_combined

    @staticmethod
    def parse_payload_to_dataframe(payload: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert NASA POWER JSON payload into a clean pandas DataFrame.

        NASA POWER formats parameter values as {parameter_name: {YYYYMMDD: value, ...}}.
        This method pivots the nested dictionary into tabular time series format.
        """
        if "properties" not in payload or "parameter" not in payload["properties"]:
            raise ValueError("Malformed NASA POWER payload: missing 'properties.parameter' key.")

        param_dict = payload["properties"]["parameter"]
        if not param_dict:
            return pd.DataFrame()

        # Build DataFrame with date index
        df = pd.DataFrame(param_dict)
        df.index.name = "date_str"
        df = df.reset_index()

        # Parse date and add calendar features
        df["date"] = pd.to_datetime(df["date_str"], format="%Y%m%d")
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["day_of_year"] = df["date"].dt.dayofyear

        # Sort chronologically
        df = df.sort_values("date").reset_index(drop=True)
        return df
