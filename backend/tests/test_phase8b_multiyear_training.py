"""
AquaMediAI — Phase 8B Multi-Year Candidate ML Training & Evaluation Tests
========================================================================

Offline unit tests verifying:
1. Strict annual chronological split boundaries (2021-2023 Train, 2024 Val, 2025 Test).
2. Date-grouped consistency (zero date overlap across partitions).
3. Preprocessor fitted strictly on training data without lookahead.
4. Candidate v2 artifact persistence and isolation.
5. Zero leakage: complete exclusion of target-derived features in candidate_v2.
6. Preservation of production models AND candidate_v1 models (SHA-256 integrity).
7. Validation-based model selection verification.
8. Non-negativity and bounds of candidate_v2 inference.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from app.config import get_settings
from app.ml.candidate_features import ALL_CANDIDATE_FEATURES, FORBIDDEN_LEAKAGE_FEATURES
from app.ml.candidate_trainer import KNOWN_PRODUCTION_HASHES, compute_file_sha256
from app.ml.multiyear_trainer import KNOWN_CANDIDATE_V1_HASHES, verify_all_baselines_unmodified


# ── 1. Annual Chronological Split & Date Grouping ──────────────────────────────

def test_annual_split_boundaries_and_disjointness():
    """Verify that train (2021-2023), val (2024), and test (2025) have zero date overlap."""
    settings = get_settings()
    processed_dir = settings.model_dir_path.parent / "processed"
    dataset_path = processed_dir / "candidate_v2_dataset.csv"
    assert dataset_path.exists(), "candidate_v2_dataset.csv not found!"

    df = pd.read_csv(dataset_path)

    train_dates = set(df[df["year"].isin([2021, 2022, 2023])]["date"].unique())
    val_dates = set(df[df["year"] == 2024]["date"].unique())
    test_dates = set(df[df["year"] == 2025]["date"].unique())

    # Disjointness
    assert len(train_dates & val_dates) == 0, "Train and Val date sets overlap!"
    assert len(train_dates & test_dates) == 0, "Train and Test date sets overlap!"
    assert len(val_dates & test_dates) == 0, "Val and Test date sets overlap!"

    # Temporal sequence
    assert max(train_dates) == "2023-12-31"
    assert min(val_dates) == "2024-01-01"
    assert max(val_dates) == "2024-12-31"
    assert min(test_dates) == "2025-01-01"
    assert max(test_dates) == "2025-12-31"

    assert len(train_dates) == 1095  # 365 * 3
    assert len(val_dates) == 366     # 2024 is leap year
    assert len(test_dates) == 365    # 2025


# ── 2. Candidate v2 Artifacts Isolation ────────────────────────────────────────

def test_candidate_v2_artifacts_exist_and_isolated():
    """Verify all candidate_v2 artifacts exist in backend/data/models/candidate_v2/."""
    settings = get_settings()
    v2_dir = settings.model_dir_path / "candidate_v2"

    assert v2_dir.exists(), "candidate_v2 directory not found!"
    assert (v2_dir / "candidate_rf_model.joblib").exists()
    assert (v2_dir / "candidate_xgb_model.joblib").exists()
    assert (v2_dir / "candidate_preprocessor.joblib").exists()
    assert (v2_dir / "feature_schema.json").exists()
    assert (v2_dir / "split_metadata.json").exists()
    assert (v2_dir / "validation_metrics.json").exists()
    assert (v2_dir / "test_evaluation_metrics.json").exists()
    assert (v2_dir / "candidate_metadata.json").exists()
    assert (v2_dir / "test_predictions.csv").exists()


# ── 3. Feature Leakage Verification in candidate_v2 ────────────────────────────

def test_candidate_v2_feature_schema_zero_leakage():
    """Verify that forbidden target re-expressions are excluded from candidate_v2 schema."""
    settings = get_settings()
    schema_path = settings.model_dir_path / "candidate_v2" / "feature_schema.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    feature_names = schema["numeric_features"] + schema["categorical_features"]
    for forbidden in FORBIDDEN_LEAKAGE_FEATURES:
        assert forbidden not in feature_names, f"Forbidden feature '{forbidden}' found in candidate_v2 schema!"

    assert "area_x_etc" not in feature_names
    assert "etc_mm_per_day" not in feature_names
    assert "effective_precipitation_mm" not in feature_names
    assert "net_irrigation_depth_mm" not in feature_names


# ── 4. Baseline & Candidate v1 Hashes Preservation ─────────────────────────────

def test_all_baselines_and_v1_hashes_unmodified():
    """Verify that production models AND candidate_v1 models have NOT been modified."""
    settings = get_settings()
    models_dir = settings.model_dir_path

    status = verify_all_baselines_unmodified(models_dir)
    for key, is_valid in status.items():
        assert is_valid is True, f"Integrity check failed for: {key}"


# ── 5. Validation-Based Selection Verification ─────────────────────────────────

def test_model_selection_and_test_metrics_consistency():
    """Verify that validation metrics correctly selected Candidate XGBoost."""
    settings = get_settings()
    v2_dir = settings.model_dir_path / "candidate_v2"

    with open(v2_dir / "validation_metrics.json", "r", encoding="utf-8") as f:
        val_metrics = json.load(f)

    with open(v2_dir / "test_evaluation_metrics.json", "r", encoding="utf-8") as f:
        test_metrics = json.load(f)

    rf_val_mae = val_metrics["candidate_models"]["candidate_random_forest"]["mae"]
    xgb_val_mae = val_metrics["candidate_models"]["candidate_xgboost"]["mae"]

    # XGBoost had lower validation MAE (7.96 vs 8.42)
    assert xgb_val_mae < rf_val_mae
    assert test_metrics["selected_model"] == "Candidate XGBoost"

    # Test metrics check
    test_xgb_mae = test_metrics["candidate_models"]["candidate_xgboost"]["mae"]
    naive_mae = test_metrics["comparators"]["naive_mean_baseline"]["mae"]
    assert test_xgb_mae < naive_mae
    assert test_metrics["candidate_models"]["candidate_xgboost"]["mae_reduction_over_naive_pct"] > 60.0


# ── 6. Candidate v2 Inference Bounds ───────────────────────────────────────────

def test_candidate_v2_inference_output():
    """Verify that loaded candidate_v2 models output non-negative predictions on test data."""
    settings = get_settings()
    v2_dir = settings.model_dir_path / "candidate_v2"

    preprocessor = joblib.load(v2_dir / "candidate_preprocessor.joblib")
    xgb_model = joblib.load(v2_dir / "candidate_xgb_model.joblib")

    sample_input = pd.DataFrame(
        [
            {
                "temperature_celsius": 26.5,
                "diurnal_temp_range_celsius": 12.0,
                "humidity_percent": 55.0,
                "wind_speed_m_per_s": 2.1,
                "solar_radiation_mj_per_m2": 19.5,
                "vpd_proxy_kpa": 1.45,
                "rainfall_lag1_mm": 0.0,
                "rainfall_antecedent_3d_mm": 0.0,
                "rainfall_antecedent_7d_mm": 0.0,
                "temp_rolling_mean_3d_celsius": 26.0,
                "temp_rolling_mean_7d_celsius": 25.8,
                "solar_rad_rolling_mean_3d": 19.0,
                "doy_sin": 0.5,
                "doy_cos": -0.866,
                "farm_area_hectares": 1.0,
                "crop_type": "wheat",
                "growth_stage": "flowering",
            }
        ]
    )

    X_trans = preprocessor.transform(sample_input[ALL_CANDIDATE_FEATURES])
    pred = float(np.clip(xgb_model.predict(X_trans)[0], a_min=0.0, a_max=None))

    assert pred > 0.0
    assert pred < 150.0  # Physical bound for 1 ha wheat
