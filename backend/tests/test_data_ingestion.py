"""
AquaMediAI — Automated Tests for Agricultural Data Ingestion & FAO-56 Engine
=============================================================================

All tests run OFFLINE using bundled local fixtures.
Zero reliance on live external APIs.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.data import (
    PREDEFINED_REGIONS,
    AgronomicDataPipeline,
    NasaPowerClient,
    calculate_crop_water_requirements,
    calculate_effective_precipitation_usda,
    calculate_fao56_et0,
    get_region_config,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "nasa_power_ahmednagar_sample.json"


@pytest.fixture(scope="module")
def offline_raw_payload() -> dict:
    """Load the bundled offline NASA POWER test fixture."""
    assert FIXTURE_PATH.exists(), f"Required fixture missing: {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── 1. Region Configuration Tests ────────────────────────────────────────────

def test_default_region_config():
    """Default region should be Ahmednagar, Central Maharashtra."""
    cfg = get_region_config()
    assert cfg.region_id == "maharashtra_ahmednagar"
    assert 18.0 <= cfg.latitude <= 20.0
    assert 73.0 <= cfg.longitude <= 76.0
    assert cfg.elevation_m > 0
    assert "sugarcane" in cfg.major_crops


def test_invalid_region_raises_error():
    """Requesting an unknown region ID must raise ValueError with available choices."""
    with pytest.raises(ValueError, match="Unknown region_id"):
        get_region_config("invalid_region_name")


def test_all_predefined_regions_valid():
    """All predefined regions must have valid coordinates and non-empty attributes."""
    for rid, cfg in PREDEFINED_REGIONS.items():
        assert cfg.region_id == rid
        assert -90.0 <= cfg.latitude <= 90.0
        assert -180.0 <= cfg.longitude <= 180.0
        assert cfg.elevation_m >= 0
        assert len(cfg.predominant_soils) > 0
        assert len(cfg.major_crops) > 0


# ─── 2. NASA POWER Client (Offline) Tests ─────────────────────────────────────

def test_nasa_power_client_parses_offline_fixture(offline_raw_payload):
    """Client parses JSON payload into tabular daily time series."""
    df = NasaPowerClient.parse_payload_to_dataframe(offline_raw_payload)
    assert not df.empty
    assert len(df) == 14  # 14 days in sample fixture
    assert "date" in df.columns
    assert "T2M" in df.columns
    assert "T2M_MAX" in df.columns
    assert "T2M_MIN" in df.columns
    assert "RH2M" in df.columns
    assert "PRECTOTCORR" in df.columns
    assert "WS2M" in df.columns
    assert "ALLSKY_SFC_SW_DWN" in df.columns
    # Must be sorted chronologically
    assert df["date"].is_monotonic_increasing


def test_nasa_power_client_offline_fetch(monkeypatch, tmp_path):
    """fetch_daily_weather in offline mode loads fixture without HTTP calls."""
    monkeypatch.setenv("NASA_POWER_OFFLINE", "1")
    client = NasaPowerClient(raw_dir=tmp_path)
    data = client.fetch_daily_weather(offline_fixture_path=FIXTURE_PATH)
    assert "properties" in data
    assert "parameter" in data["properties"]


# ─── 3. FAO-56 Penman-Monteith ET₀ Engine Tests ────────────────────────────────

def test_fao56_et0_typical_winter_values():
    """In cool dry winter (Ahmednagar in January), daily ET₀ should be 2.5–4.5 mm/day."""
    et0 = calculate_fao56_et0(
        lat_deg=19.09,
        day_of_year=1,
        t_min=12.15,
        t_max=29.3,
        t_mean=19.7,
        rh_mean=58.44,
        wind_2m=1.48,
        rs_mj=17.55,
        elevation_m=540.0,
    )
    assert 2.5 <= et0 <= 4.5
    assert isinstance(et0, float)


def test_fao56_et0_typical_summer_values():
    """In hot pre-monsoon summer (April/May), daily ET₀ should be 7.0–11.0 mm/day."""
    et0 = calculate_fao56_et0(
        lat_deg=19.09,
        day_of_year=120,
        t_min=24.0,
        t_max=42.0,
        t_mean=33.0,
        rh_mean=25.0,
        wind_2m=3.5,
        rs_mj=26.0,
        elevation_m=540.0,
    )
    assert 7.0 <= et0 <= 12.0


def test_fao56_et0_non_negative_on_zero_radiation():
    """Under overcast / zero solar radiation conditions, ET₀ remains non-negative."""
    et0 = calculate_fao56_et0(
        lat_deg=19.09,
        day_of_year=200,
        t_min=20.0,
        t_max=22.0,
        t_mean=21.0,
        rh_mean=98.0,
        wind_2m=0.5,
        rs_mj=0.0,
        elevation_m=540.0,
    )
    assert et0 >= 0.0


# ─── 4. Effective Precipitation & Crop Water Requirements ─────────────────────

def test_effective_precipitation_usda_small_rainfall():
    """Rainfall under 3 mm evaporates and produces zero effective recharge."""
    assert calculate_effective_precipitation_usda(0.0) == 0.0
    assert calculate_effective_precipitation_usda(1.5) == 0.0
    assert calculate_effective_precipitation_usda(2.9) == 0.0


def test_effective_precipitation_usda_moderate_rainfall():
    """Moderate rainfall follows USDA SCS formula."""
    p_eff = calculate_effective_precipitation_usda(30.0)
    assert 0.0 < p_eff < 30.0
    # Expected: 30 * (125 - 0.2*30)/125 = 30 * 119 / 125 = 28.56
    assert pytest.approx(p_eff, 0.01) == 28.56


def test_crop_water_requirements_dry_day():
    """On a dry day, net irrigation equals ETc."""
    res = calculate_crop_water_requirements(
        et0_mm=4.0,
        kc_value=1.15,
        precipitation_mm=0.0,
        application_efficiency=0.70,
    )
    assert pytest.approx(res["etc_mm"], 0.01) == 4.60
    assert res["effective_precipitation_mm"] == 0.0
    assert pytest.approx(res["net_irrigation_mm"], 0.01) == 4.60
    assert res["gross_irrigation_mm"] > res["net_irrigation_mm"]


def test_crop_water_requirements_heavy_rain_day():
    """When effective rainfall exceeds ETc, net irrigation requirement drops to zero."""
    res = calculate_crop_water_requirements(
        et0_mm=3.0,
        kc_value=0.70,
        precipitation_mm=50.0,
        application_efficiency=0.70,
    )
    assert res["etc_mm"] == pytest.approx(2.10, 0.01)
    assert res["effective_precipitation_mm"] > res["etc_mm"]
    assert res["net_irrigation_mm"] == 0.0
    assert res["gross_irrigation_mm"] == 0.0


# ─── 5. Agronomic Processing Pipeline Tests ────────────────────────────────────

def test_agronomic_pipeline_processes_clean_dataframe(offline_raw_payload, tmp_path):
    """Pipeline processes raw payload into clean DataFrame and validation report."""
    df_raw = NasaPowerClient.parse_payload_to_dataframe(offline_raw_payload)
    pipeline = AgronomicDataPipeline(region="maharashtra_ahmednagar", processed_dir=tmp_path)

    df_clean, report = pipeline.process(df_raw, save_csv=True)

    assert len(df_clean) == 14
    assert "et0_fao56_mm_per_day" in df_clean.columns
    assert "effective_precipitation_mm" in df_clean.columns
    assert "season" in df_clean.columns
    assert (df_clean["season"] == "rabi").all()  # January is Rabi

    # Validation report checks
    assert report.total_records == 14
    assert report.status == "PASSED"
    assert report.mean_et0_mm_per_day > 2.0
    assert report.total_precipitation_mm >= 0.0

    # Clean CSV file existence
    saved_file = tmp_path / "clean_daily_weather_maharashtra_ahmednagar.csv"
    assert saved_file.exists()
    assert saved_file.stat().st_size > 0


def test_agronomic_pipeline_handles_missing_values(offline_raw_payload, tmp_path):
    """Pipeline detects -999.0 and interpolates without failing."""
    df_raw = NasaPowerClient.parse_payload_to_dataframe(offline_raw_payload)
    # Inject NASA missing value into a temperature record
    df_raw.loc[3, "T2M"] = -999.0

    pipeline = AgronomicDataPipeline(region="maharashtra_ahmednagar", processed_dir=tmp_path)
    df_clean, report = pipeline.process(df_raw, save_csv=False)

    # Missing value must be interpolated and not -999
    assert df_clean.loc[3, "T2M"] > 0
    assert report.imputed_records_count >= 1
    assert report.missing_values_detected["T2M"] == 1
