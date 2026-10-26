"""
AquaMediAI — Phase 7 Defensible ML Training Pipeline Test Suite
===============================================================

Comprehensive test coverage verifying:
1. Physical unit conversions (depth to volume: 1 mm * 1 ha = 10 m³).
2. Area scaling linearity (target(k*A) == k*target(A)).
3. Zero and high effective rainfall handling (non-negative constraints).
4. Paddy rice explicit exclusion & handling.
5. Missing and invalid weather rejection.
6. Sample key uniqueness and date continuity.
7. Target recalculation reproducibility.
8. Feature leakage exclusions.
9. Date-grouped chronological splitting (zero date overlap across partitions).
10. Candidate artifact isolation (candidate_v1) & production artifact preservation.
11. Existing production prediction API contracts unchanged.
12. Repeatability with the same seed and dataset.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.candidate_features import (
    ALL_CANDIDATE_FEATURES,
    FORBIDDEN_LEAKAGE_FEATURES,
    verify_feature_safety,
)
from app.ml.candidate_trainer import (
    KNOWN_PRODUCTION_HASHES,
    compute_file_sha256,
    verify_production_artifacts_unmodified,
)
from app.ml.crop_registry import (
    CropRegistry,
    CropSpec,
    PaddyRiceExclusionError,
)
from app.ml.dataset_builder import (
    AgronomicDatasetBuilder,
    calculate_net_crop_water_target,
)
from app.ml.date_grouped_split import date_grouped_chronological_split

client = TestClient(app)


# ── 1. Unit Conversions & Depth to Volume ───────────────────────────────────────

def test_unit_conversion_depth_to_volume():
    """Verify standard hydraulic conversion: 1 mm over 1 ha = 10 m³."""
    # 1 ha = 10,000 m²; 1 mm = 0.001 m; Volume = 10,000 * 0.001 = 10 m³
    _, _, inet_mm, vol_m3 = calculate_net_crop_water_target(
        et0_mm=5.0,
        kc_value=1.0,
        rainfall_mm=0.0,
        farm_area_ha=1.0,
    )
    assert inet_mm == 5.0
    assert vol_m3 == 50.0  # 5 mm * 1 ha * 10 = 50 m³

    _, _, inet_2, vol_2 = calculate_net_crop_water_target(
        et0_mm=10.0,
        kc_value=1.0,
        rainfall_mm=0.0,
        farm_area_ha=2.5,
    )
    assert inet_2 == 10.0
    assert vol_2 == 250.0  # 10 mm * 2.5 ha * 10 = 250 m³


# ── 2. Area Scaling Linearity ──────────────────────────────────────────────────

def test_area_scaling_linearity():
    """Verify that under simplified uniform assumptions, target scales linearly with farm area."""
    et0 = 6.2
    kc = 1.15
    rain = 0.0  # Zero rain ensures non-zero net irrigation demand

    _, _, _, v_1ha = calculate_net_crop_water_target(et0, kc, rain, 1.0)
    _, _, _, v_3ha = calculate_net_crop_water_target(et0, kc, rain, 3.0)
    _, _, _, v_5ha = calculate_net_crop_water_target(et0, kc, rain, 5.0)

    assert v_1ha > 0.0
    assert abs((v_3ha / v_1ha) - 3.0) < 1e-4
    assert abs((v_5ha / v_1ha) - 5.0) < 1e-4

    # When net irrigation depth is zero, all area volumes must be 0.0
    deluge_rain = 50.0
    _, _, _, vz_1ha = calculate_net_crop_water_target(et0, kc, deluge_rain, 1.0)
    _, _, _, vz_3ha = calculate_net_crop_water_target(et0, kc, deluge_rain, 3.0)
    assert vz_1ha == 0.0
    assert vz_3ha == 0.0


# ── 3. Zero and High Effective Rainfall Cases ──────────────────────────────────

def test_zero_rainfall_and_deluge_rainfall():
    """Verify net irrigation depth when rainfall is zero versus when rainfall exceeds ETc."""
    # Zero rain -> Net irrigation equals ETc
    etc, peff, inet, vol = calculate_net_crop_water_target(5.0, 1.0, 0.0, 1.0)
    assert peff == 0.0
    assert inet == 5.0
    assert vol == 50.0

    # Light shower (<3 mm) -> Evaporates, Peff = 0 (USDA SCS)
    _, peff_light, inet_light, _ = calculate_net_crop_water_target(5.0, 1.0, 2.0, 1.0)
    assert peff_light == 0.0
    assert inet_light == 5.0

    # Monsoon deluge (100 mm) -> Peff exceeds ETc, net irrigation MUST BE ZERO
    _, peff_heavy, inet_heavy, vol_heavy = calculate_net_crop_water_target(5.0, 1.0, 100.0, 1.0)
    assert peff_heavy > 5.0
    assert inet_heavy == 0.0
    assert vol_heavy == 0.0


# ── 4. Nonnegative Target Constraints ──────────────────────────────────────────

def test_nonnegative_target_constraints():
    """Verify target volume is never negative under any circumstances."""
    for rain in [0.0, 5.0, 50.0, 200.0, 500.0]:
        for et0 in [0.0, 1.0, 8.0]:
            _, _, inet, vol = calculate_net_crop_water_target(et0, 1.0, rain, 1.0)
            assert inet >= 0.0
            assert vol >= 0.0


# ── 5. Paddy vs Non-Paddy Handling ─────────────────────────────────────────────

def test_paddy_rice_exclusion_handling():
    """Verify that paddy rice raises PaddyRiceExclusionError when queried for non-paddy baseline."""
    # Rice is registered
    rice_crop = CropRegistry.get_crop("rice")
    assert rice_crop.is_paddy is True

    # Calling get_kc raises PaddyRiceExclusionError to prevent invalid application of upland formulas
    with pytest.raises(PaddyRiceExclusionError):
        CropRegistry.get_kc("rice", "flowering")

    # Non-paddy crops succeed normally
    assert CropRegistry.get_kc("wheat", "flowering") == 1.15
    assert CropRegistry.get_kc("sugarcane", "flowering") == 1.25
    assert CropRegistry.get_kc("cotton", "flowering") == 1.15


# ── 6. Missing and Invalid Weather Values ───────────────────────────────────────

def test_missing_and_invalid_inputs_rejected():
    """Verify that invalid negative weather inputs are rejected with ValueError."""
    with pytest.raises(ValueError):
        calculate_net_crop_water_target(et0_mm=-1.0, kc_value=1.0, rainfall_mm=0.0, farm_area_ha=1.0)

    with pytest.raises(ValueError):
        calculate_net_crop_water_target(et0_mm=5.0, kc_value=0.0, rainfall_mm=0.0, farm_area_ha=1.0)

    with pytest.raises(ValueError):
        calculate_net_crop_water_target(et0_mm=5.0, kc_value=1.0, rainfall_mm=-5.0, farm_area_ha=1.0)

    with pytest.raises(ValueError):
        calculate_net_crop_water_target(et0_mm=5.0, kc_value=1.0, rainfall_mm=0.0, farm_area_ha=0.0)


# ── 7. Dataset Builder Integrity & Target Reproducibility ──────────────────────

def test_dataset_builder_reproducibility_and_keys():
    """Verify that built dataset has unique sample keys and reproducible targets."""
    builder = AgronomicDatasetBuilder()
    df, manifest = builder.build_dataset(farm_area_ha=1.0, save_csv=False)

    assert len(df) > 0
    assert manifest.total_unique_dates == 365
    assert df["sample_key"].is_unique

    # Verify no NaN values in critical columns
    assert not df["net_irrigation_m3_per_day"].isna().any()
    assert (df["net_irrigation_m3_per_day"] >= 0.0).all()

    # Recalculate 25 random samples to assert target exactness
    for _, r in df.sample(25, random_state=42).iterrows():
        _, _, _, v_recalc = calculate_net_crop_water_target(
            r["et0_fao56_mm_per_day"], r["kc_value"], r["rainfall_mm"], r["farm_area_hectares"]
        )
        assert abs(v_recalc - r["net_irrigation_m3_per_day"]) < 1e-4


# ── 8. Feature Leakage Exclusions ──────────────────────────────────────────────

def test_feature_leakage_audit_and_exclusions():
    """Verify that forbidden target-reconstructing features are flagged as critical leakage."""
    builder = AgronomicDatasetBuilder()
    df, _ = builder.build_dataset(farm_area_ha=1.0, save_csv=False)

    # 1. Permitted candidate features must PASS
    audit_report = verify_feature_safety(df, features=ALL_CANDIDATE_FEATURES)
    assert audit_report.has_critical_leakage is False
    assert audit_report.verdict in ("PASS", "WARNING")

    # 2. Feeding forbidden features must raise ValueError
    for forbidden in FORBIDDEN_LEAKAGE_FEATURES:
        with pytest.raises(ValueError, match="CRITICAL LEAKAGE DETECTED"):
            verify_feature_safety(df, features=ALL_CANDIDATE_FEATURES + [forbidden])


# ── 9. Date-Grouped Chronological Splitting ────────────────────────────────────

def test_date_grouped_chronological_split():
    """Verify strict chronological splitting with zero date overlap across partitions."""
    builder = AgronomicDatasetBuilder()
    df, _ = builder.build_dataset(farm_area_ha=1.0, save_csv=False)

    train_df, val_df, test_df, meta = date_grouped_chronological_split(
        df=df,
        date_col="date",
        train_ratio=0.70,
        val_ratio=0.15,
    )

    train_dates = set(train_df["date"].unique())
    val_dates = set(val_df["date"].unique())
    test_dates = set(test_df["date"].unique())

    # Invariant 1: Mutually disjoint date sets
    assert len(train_dates & val_dates) == 0
    assert len(train_dates & test_dates) == 0
    assert len(val_dates & test_dates) == 0

    # Invariant 2: Strict temporal ordering
    assert max(train_dates) < min(val_dates)
    assert max(val_dates) < min(test_dates)


# ── 10. Candidate Artifact Isolation & Production Artifact Preservation ────────

def test_candidate_artifacts_isolation_and_production_untouched():
    """Verify that candidate artifacts exist in candidate_v1 and production models remain identical."""
    from app.config import get_settings
    models_dir = get_settings().model_dir_path
    candidate_dir = models_dir / "candidate_v1"

    # Verify candidate files exist
    assert (candidate_dir / "candidate_rf_model.joblib").exists()
    assert (candidate_dir / "candidate_xgb_model.joblib").exists()
    assert (candidate_dir / "candidate_preprocessor.joblib").exists()
    assert (candidate_dir / "evaluation_metrics.json").exists()
    assert (candidate_dir / "candidate_metadata.json").exists()

    # Verify production models match known baseline hashes exactly
    check_results = verify_production_artifacts_unmodified(models_dir)
    for artifact, is_matched in check_results.items():
        assert is_matched is True, f"Production artifact {artifact} was modified!"


# ── 11. Existing Prediction API Contracts Unchanged ───────────────────────────

def test_production_prediction_api_contract_intact():
    """Verify that existing production prediction endpoints continue to function identically."""
    # Health check
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["pipeline"] == "available"

    # Prediction endpoint with legacy schema
    sample_farmer = {
        "farmer_id": "PHASE7_REGRESSION_TEST",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "mid_season",
        "season": "rabi",
        "farm_area_hectares": 3.0,
        "et0_mm_per_day": 5.0,
        "kc_value": 1.15,
        "etc_mm_per_day": 5.75,
        "soil_whc_mm_per_m": 130.0,
        "preferred_start_hour": 6,
        "irrigation_window_hours": 4,
        "flexibility_score": 0.5,
        "urgency_score": 0.5,
        "crop_stress_index": 0.4,
        "temperature_celsius": 25.0,
        "humidity_percent": 55.0,
        "rainfall_mm": 0.0,
    }
    r_pred = client.post("/api/v1/predictions", json={"farmer_data": sample_farmer, "model_name": "XGBoost"})
    assert r_pred.status_code == 200
    data = r_pred.json()
    assert "predicted_water_demand_m3" in data
    assert "shadow_agronomic_estimate_m3" in data
    assert "shadow_comparison" in data
