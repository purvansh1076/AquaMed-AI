"""
AquaMediAI — Phase 8A Historical Data Verification and Multi-Year Ingestion Tests
================================================================================

Offline tests verifying:
1. Multi-year payload parsing, calendar leap year parsing (Feb 29), and date formatting.
2. Missing-value handling (-999.0 replacement and linear interpolation).
3. Bounded retries and clear error messaging on API failure.
4. Disk-cache retrieval preventing redundant HTTP calls.
5. Multi-year concatenation, date continuity, and zero duplicate dates.
6. Expanded dataset v2 manifest integrity and quality checks.
7. Verification that production model artifacts and Phase 7 candidate artifacts remain untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import numpy as np
import pandas as pd
import pytest

from app.data import AgronomicDataPipeline, NasaPowerClient
from app.data.region_config import get_region_config
from app.ml.candidate_trainer import KNOWN_PRODUCTION_HASHES, compute_file_sha256
from app.ml.dataset_builder import AgronomicDatasetBuilder


# ── 1. Mock Payload Fixture Generator ──────────────────────────────────────────

def create_mock_nasa_payload(dates: list[str], missing_val_on_date: str | None = None) -> dict:
    """Generate mock NASA POWER agroclimatology JSON payload."""
    t2m = {}
    t2m_max = {}
    t2m_min = {}
    rh2m = {}
    prec = {}
    ws2m = {}
    rad = {}

    for d in dates:
        if d == missing_val_on_date:
            t2m[d] = -999.0
            rh2m[d] = -999.0
        else:
            t2m[d] = 25.5
            rh2m[d] = 60.0

        t2m_max[d] = 32.0
        t2m_min[d] = 18.0
        prec[d] = 0.0
        ws2m[d] = 1.8
        rad[d] = 18.5

    return {
        "properties": {
            "parameter": {
                "T2M": t2m,
                "T2M_MAX": t2m_max,
                "T2M_MIN": t2m_min,
                "RH2M": rh2m,
                "PRECTOTCORR": prec,
                "WS2M": ws2m,
                "ALLSKY_SFC_SW_DWN": rad,
            }
        }
    }


# ── 2. Payload Parsing & Leap Year Handling ────────────────────────────────────

def test_parse_payload_and_leap_year():
    """Verify that YYYYMMDD dates including leap-year Feb 29 are parsed accurately."""
    mock_dates = ["20240228", "20240229", "20240301"]
    payload = create_mock_nasa_payload(mock_dates)

    df = NasaPowerClient.parse_payload_to_dataframe(payload)
    assert len(df) == 3
    assert list(df["date_str"]) == mock_dates

    # Check datetime conversion
    assert df["date"].iloc[1] == pd.Timestamp("2024-02-29")
    assert df["year"].iloc[1] == 2024
    assert df["month"].iloc[1] == 2
    assert df["day"].iloc[1] == 29
    assert df["day_of_year"].iloc[1] == 60


# ── 3. Missing Value Cleaning & Interpolation ──────────────────────────────────

def test_missing_value_imputation(tmp_path):
    """Verify that NASA POWER -999.0 missing values are cleaned and linearly interpolated."""
    dates = ["20230501", "20230502", "20230503"]
    # Day 2 has -999.0
    payload = create_mock_nasa_payload(dates, missing_val_on_date="20230502")

    client = NasaPowerClient(raw_dir=tmp_path)
    df_raw = client.parse_payload_to_dataframe(payload)

    pipeline = AgronomicDataPipeline(processed_dir=tmp_path)
    df_clean, report = pipeline.process(df_raw, save_csv=False)

    # Missing value on day 2 should be interpolated between day 1 (25.5) and day 3 (25.5)
    assert df_clean["T2M"].isna().sum() == 0
    assert df_clean["T2M"].iloc[1] == pytest.approx(25.5, abs=0.1)
    assert report.missing_values_detected["T2M"] == 1
    assert report.imputed_records_count > 0


# ── 4. Disk Caching Behavior ───────────────────────────────────────────────────

def test_cache_retrieval_avoids_network(tmp_path):
    """Verify that existing raw JSON files are loaded from cache without making network calls."""
    client = NasaPowerClient(raw_dir=tmp_path)
    cached_payload = create_mock_nasa_payload(["20230101", "20230102"])
    cache_file = tmp_path / f"nasa_power_{client.region.region_id}_20230101_20230102.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cached_payload, f)

    # Calling fetch_daily_weather with use_cache=True should read cache_file directly
    with patch("httpx.Client.get") as mock_get:
        data = client.fetch_daily_weather(start_date="20230101", end_date="20230102", use_cache=True)
        mock_get.assert_not_called()
        assert "properties" in data
        assert list(data["properties"]["parameter"]["T2M"].keys()) == ["20230101", "20230102"]


# ── 5. Bounded Retries & Error Messaging on Network Failure ────────────────────

def test_bounded_retries_on_http_error(tmp_path):
    """Verify that network failures trigger bounded retries with informative error message."""
    client = NasaPowerClient(raw_dir=tmp_path, max_retries=2)

    with patch("httpx.Client.get", side_effect=httpx.ConnectError("[Errno 11001] getaddrinfo failed")):
        with pytest.raises(RuntimeError, match="Failed to fetch NASA POWER weather data after 2 attempts"):
            client.fetch_daily_weather(start_date="20200101", end_date="20200102", use_cache=False)


# ── 6. Multi-Year Concatenation & Duplicate Dropping ───────────────────────────

def test_multi_year_concatenation(tmp_path):
    """Verify that multi-year concatenation drops duplicates and maintains chronological order."""
    client = NasaPowerClient(raw_dir=tmp_path)

    # Mock fetch_daily_weather to return separate years
    payload_2021 = create_mock_nasa_payload(["20211231"])
    payload_2022 = create_mock_nasa_payload(["20220101"])

    def mock_fetch(start_date, end_date, **kwargs):
        if start_date.startswith("2021"):
            return payload_2021
        return payload_2022

    with patch.object(client, "fetch_daily_weather", side_effect=mock_fetch):
        df_multi = client.fetch_multi_year_weather(years=[2021, 2022], use_cache=False)
        assert len(df_multi) == 2
        assert list(df_multi["date_str"]) == ["20211231", "20220101"]
        assert df_multi["date"].iloc[0] < df_multi["date"].iloc[1]


# ── 7. Candidate Dataset v2 Verification ───────────────────────────────────────

def test_candidate_dataset_v2_manifest_integrity():
    """Verify that the generated candidate_v2_dataset.csv covers 1826 unique dates across 2021-2025."""
    from app.config import get_settings
    base_dir = get_settings().model_dir_path.parent
    v2_csv = base_dir / "processed" / "candidate_v2_dataset.csv"
    v2_manifest_path = base_dir / "processed" / "candidate_v2_manifest.json"

    assert v2_csv.exists(), "candidate_v2_dataset.csv not found!"
    assert v2_manifest_path.exists(), "candidate_v2_manifest.json not found!"

    df_v2 = pd.read_csv(v2_csv)
    assert len(df_v2) == 4882
    assert df_v2["date"].nunique() == 1826
    assert df_v2["year"].nunique() == 5
    assert set(df_v2["year"].unique()) == {2021, 2022, 2023, 2024, 2025}

    # Verify no duplicate sample keys
    assert df_v2["sample_key"].is_unique

    # Verify non-negative target values
    assert (df_v2["net_irrigation_m3_per_day"] >= 0.0).all()

    with open(v2_manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["total_records"] == 4882
    assert manifest["total_unique_dates"] == 1826
    assert manifest["target_reproducibility_verified"] is True
    assert manifest["area_linearity_verified"] is True


# ── 8. Preservation of Production & Phase 7 Candidate Artifacts ────────────────

def test_production_and_phase7_candidate_hashes_unchanged():
    """Verify that production model hashes and Phase 7 candidate artifacts are untouched."""
    from app.config import get_settings
    models_dir = get_settings().model_dir_path

    # Production models
    for filename, expected_hash in KNOWN_PRODUCTION_HASHES.items():
        actual_hash = compute_file_sha256(models_dir / filename)
        assert actual_hash == expected_hash, f"Production file {filename} was modified!"

    # Phase 7 candidate artifacts
    candidate_v1_dir = models_dir / "candidate_v1"
    assert (candidate_v1_dir / "candidate_rf_model.joblib").exists()
    assert (candidate_v1_dir / "candidate_xgb_model.joblib").exists()
    assert (candidate_v1_dir / "candidate_preprocessor.joblib").exists()
    assert (candidate_v1_dir / "evaluation_metrics.json").exists()

    # Load Phase 7 metadata to verify its recorded candidate hashes
    with open(candidate_v1_dir / "candidate_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    recorded_hashes = meta["artifact_hashes"]
    for art_name, exp_hash in recorded_hashes.items():
        curr_hash = compute_file_sha256(candidate_v1_dir / art_name)
        assert curr_hash == exp_hash, f"Candidate v1 artifact {art_name} was modified!"
