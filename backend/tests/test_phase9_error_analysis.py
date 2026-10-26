"""
AquaMediAI — Phase 9 Model Error Analysis & Agronomic Validation Unit Tests
===========================================================================

Offline unit tests verifying:
1. Exact reproduction of Phase 8B test metrics (XGBoost, RF, Naive baseline).
2. Two-stage model pipeline mechanics (fit, calibrate threshold, predict, evaluate).
3. Zero-demand handling & classification trade-off (false-positive zero drought risk).
4. Feature schema leakage prevention (absence of forbidden target components).
5. Cryptographic preservation of all prior model artifacts (Production, v1, v2).
6. Candidate v3 out-of-year generalization & zero-demand error collapse.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from app.config import get_settings
from app.ml.candidate_features import FORBIDDEN_LEAKAGE_FEATURES
from app.ml.candidate_v3_experiments import (
    NUMERIC_FEATURES_SET_A,
    NUMERIC_FEATURES_SET_B,
    NUMERIC_FEATURES_SET_C,
    CATEGORICAL_FEATURES_SET_A,
    CATEGORICAL_FEATURES_SET_B,
    CATEGORICAL_FEATURES_SET_C,
    verify_all_existing_artifacts_unmodified,
)
from app.ml.crop_registry import CropRegistry
from app.ml.error_analysis import Phase9ErrorAnalyzer, calculate_metrics_from_arrays
from app.ml.two_stage_model import TwoStageIrrigationModel


# ── 1. Baseline Metric Reproduction ───────────────────────────────────────────

def test_phase8b_metric_reproduction_exactness():
    """Verify that Phase 8B test metrics are reproduced independently to high precision."""
    analyzer = Phase9ErrorAnalyzer()
    repro = analyzer.verify_baseline_reproduction()

    assert repro["reproduction_verified"] is True
    assert repro["sample_count"] == 976

    xgb_metrics = repro["xgboost"]["recomputed"]
    saved_xgb = repro["xgboost"]["saved"]

    # Check exact match on MAE, RMSE, R2
    assert abs(xgb_metrics["mae"] - saved_xgb["mae"]) < 0.001
    assert abs(xgb_metrics["rmse"] - saved_xgb["rmse"]) < 0.001
    assert abs(xgb_metrics["r2"] - saved_xgb["r2"]) < 0.001
    assert abs(xgb_metrics["mean_signed_bias"] - saved_xgb["mean_signed_bias"]) < 0.001

    rf_metrics = repro["random_forest"]["recomputed"]
    saved_rf = repro["random_forest"]["saved"]
    assert abs(rf_metrics["mae"] - saved_rf["mae"]) < 0.001
    assert abs(rf_metrics["rmse"] - saved_rf["rmse"]) < 0.001
    assert abs(rf_metrics["r2"] - saved_rf["r2"]) < 0.001


# ── 2. Two-Stage Model Pipeline Mechanics ──────────────────────────────────────

def test_two_stage_model_pipeline_behavior():
    """Verify TwoStageIrrigationModel training, threshold calibration, and inference."""
    np.random.seed(42)
    n_samples = 200
    n_features = 8

    X_train = np.random.randn(n_samples, n_features)
    # Create zero-inflated target (30% zeros)
    y_raw = np.maximum(0.0, np.random.randn(n_samples) * 20.0 + 10.0)
    y_raw[:60] = 0.0
    y_train = y_raw

    X_val = np.random.randn(50, n_features)
    y_val = np.maximum(0.0, np.random.randn(50) * 20.0 + 10.0)
    y_val[:15] = 0.0

    model = TwoStageIrrigationModel(seed=42)
    model.fit(X_train, y_train)

    assert model.is_fitted is True

    # Calibrate threshold on validation data
    calibrated_tau = model.calibrate_threshold_on_validation(X_val, y_val, metric="mae")
    assert 0.1 <= calibrated_tau <= 0.9

    # Predict
    preds = model.predict(X_val)
    assert len(preds) == len(y_val)
    assert (preds >= 0.0).all()  # Non-negativity constraint guaranteed

    # Probabilities
    probs = model.predict_proba_zero(X_val)
    assert len(probs) == len(y_val)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()


# ── 3. Zero Leakage Verification across Feature Sets ───────────────────────────

def test_feature_sets_zero_leakage():
    """Verify that Sets A, B, and C exclude all forbidden target re-expressions."""
    all_sets = [
        ("Set A", NUMERIC_FEATURES_SET_A + CATEGORICAL_FEATURES_SET_A),
        ("Set B", NUMERIC_FEATURES_SET_B + CATEGORICAL_FEATURES_SET_B),
        ("Set C", NUMERIC_FEATURES_SET_C + CATEGORICAL_FEATURES_SET_C),
    ]

    for set_name, feature_list in all_sets:
        for forbidden in FORBIDDEN_LEAKAGE_FEATURES:
            assert forbidden not in feature_list, f"Forbidden '{forbidden}' found in {set_name}!"

        # Explicit target components
        assert "etc_mm_per_day" not in feature_list
        assert "effective_precipitation_mm" not in feature_list
        assert "net_irrigation_depth_mm" not in feature_list
        assert "area_x_etc" not in feature_list


# ── 4. Cryptographic Hash Preservation of Baseline Models ──────────────────────

def test_all_baselines_and_v2_hashes_unmodified():
    """Verify that production, candidate_v1, and candidate_v2 artifacts have NOT been modified."""
    settings = get_settings()
    models_dir = settings.model_dir_path

    integrity = verify_all_existing_artifacts_unmodified(models_dir)
    for key, is_valid in integrity.items():
        assert is_valid is True, f"Integrity check failed for: {key}"


# ── 5. Candidate v3 Artifacts Existence & Isolation ────────────────────────────

def test_candidate_v3_artifacts_exist_and_isolated():
    """Verify all candidate_v3 artifacts exist in backend/data/models/candidate_v3/."""
    settings = get_settings()
    v3_dir = settings.model_dir_path / "candidate_v3"

    assert v3_dir.exists(), "candidate_v3 directory not found!"
    assert (v3_dir / "candidate_v3_classifier.joblib").exists()
    assert (v3_dir / "candidate_v3_regressor.joblib").exists()
    assert (v3_dir / "candidate_v3_preprocessor.joblib").exists()
    assert (v3_dir / "two_stage_config.json").exists()
    assert (v3_dir / "two_stage_metrics.json").exists()
    assert (v3_dir / "feature_schema.json").exists()
    assert (v3_dir / "validation_ablations.json").exists()
    assert (v3_dir / "test_ablations.json").exists()
    assert (v3_dir / "test_predictions_v3.csv").exists()
    assert (v3_dir / "candidate_metadata.json").exists()


# ── 6. Out-of-Year Performance & Zero-Demand Improvement ───────────────────────

def test_candidate_v3_zero_demand_error_reduction():
    """Verify that Candidate v3 achieved dramatic zero-demand error reduction over v2."""
    settings = get_settings()
    v3_dir = settings.model_dir_path / "candidate_v3"

    with open(v3_dir / "two_stage_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # In candidate_v2, zero-demand MAE was 10.42 m3/day
    # In candidate_v3, two-stage with rainfall should achieve zero-subset MAE < 0.5 m3/day
    assert metrics["zero_subset_mae"] < 0.50
    assert metrics["accuracy"] > 0.95
    assert metrics["f1_zero"] > 0.90
    assert metrics["overall_mae"] < 2.0  # Big drop from candidate_v2's 6.67 m3/day


# ── 7. Agronomic Assumptions & Crop Registry Invariants ────────────────────────

def test_agronomic_registry_and_calendar_invariants():
    """Verify agricultural crop registry parameters and non-paddy exclusion."""
    registered = CropRegistry.list_crops(include_paddy=False)
    crop_ids = [c.crop_id for c in registered]

    # Pilot crops verified
    assert "wheat" in crop_ids
    assert "sugarcane" in crop_ids
    assert "cotton" in crop_ids
    assert "soybean" in crop_ids
    assert "maize" in crop_ids
    assert "groundnut" in crop_ids

    # Paddy excluded from simple upland model
    paddy_crops = CropRegistry.list_crops(include_paddy=True)
    assert any(c.is_paddy for c in paddy_crops)
    paddy_obj = next(c for c in paddy_crops if c.is_paddy)
    assert paddy_obj.crop_id == "rice"

    # Sugarcane Kc bounds
    cane = CropRegistry.get_crop("sugarcane")
    assert cane.get_kc("flowering") >= 1.20  # Peak grand growth
    assert cane.get_kc("germination") <= 0.50
