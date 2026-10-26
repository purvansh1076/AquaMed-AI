"""
AquaMediAI — Phase 10 Independent Candidate v3 Audit Unit Tests
===============================================================

Offline unit tests verifying:
1. Independent recomputation of Candidate v3 metrics from saved predictions.
2. Zero-demand classification accuracy, precision, recall, F1, and confusion matrix.
3. Strict disjointness of annual partitions and validation threshold isolation.
4. Total absence of forbidden target leakage columns in Candidate v3.
5. Verification of the 7 false-positive zero cases and environmental context.
6. Cryptographic preservation of all baseline model artifacts (Production, v1, v2).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.config import get_settings
from app.ml.phase10_audit import Phase10Auditor


@pytest.fixture
def auditor() -> Phase10Auditor:
    return Phase10Auditor()


def test_independent_candidate_v3_metric_recomputation(auditor: Phase10Auditor):
    """Verify independent metric recomputation from saved 2025 test predictions."""
    res = auditor.audit_recomputed_metrics()

    assert res["sample_count"] == 976
    assert len(res["discrepancies"]) == 0, f"Discrepancies found: {res['discrepancies']}"

    m = res["recomputed"]
    # Verify overall metrics match Phase 9 report
    assert abs(m["overall_mae"] - 1.3865) < 0.001
    assert abs(m["overall_rmse"] - 2.3985) < 0.001
    assert abs(m["overall_r2"] - 0.9902) < 0.001
    assert abs(m["overall_bias"] - (-0.3216)) < 0.001

    # Non-negative check
    assert res["has_negative_predictions"] is False


def test_zero_demand_classification_and_confusion_matrix(auditor: Phase10Auditor):
    """Verify zero-demand classification metrics and exact confusion matrix counts."""
    res = auditor.audit_recomputed_metrics()
    m = res["recomputed"]

    assert abs(m["accuracy"] - 0.9918) < 0.001
    assert abs(m["precision_zero"] - 0.9690) < 0.001
    assert abs(m["recall_zero"] - 0.9955) < 0.001
    assert abs(m["f1_zero"] - 0.9821) < 0.001

    assert m["false_positive_zero_count"] == 7
    assert m["false_negative_zero_count"] == 1
    assert m["true_zero_count"] == 219
    assert m["true_positive_demand_count"] == 749

    # Zero-demand and positive-demand subset MAEs
    assert abs(m["zero_subset_mae"] - 0.0162) < 0.001
    assert abs(m["positive_subset_mae"] - 1.7853) < 0.001


def test_crop_specific_metrics_integrity(auditor: Phase10Auditor):
    """Verify crop-level metrics consistency."""
    res = auditor.audit_recomputed_metrics()
    crops = res["crop_metrics"]

    assert set(crops.keys()) == {"wheat", "sugarcane", "cotton", "soybean", "maize", "groundnut"}
    assert crops["cotton"]["n_samples"] == 170
    assert crops["sugarcane"]["n_samples"] == 365
    assert crops["wheat"]["n_samples"] == 121
    assert crops["cotton"]["mae"] < 1.0  # Big improvement over candidate v2's 7.01 m3/day
    assert crops["wheat"]["mae"] < 2.0


def test_temporal_splits_and_threshold_isolation(auditor: Phase10Auditor):
    """Verify annual date disjointness and validation-only threshold tuning."""
    res = auditor.audit_splits_and_isolation()

    assert res["dates_disjoint"] is True
    assert res["train_date_count"] == 1095  # 2021-2023
    assert res["val_date_count"] == 366     # 2024 leap year
    assert res["test_date_count"] == 365    # 2025

    # Threshold was calibrated strictly on 2024 validation data
    assert res["threshold_calibrated_on_val"] is True
    assert res["calibrated_threshold"] == 0.2


def test_feature_schema_leakage_absence(auditor: Phase10Auditor):
    """Verify complete absence of forbidden target components in candidate v3."""
    res = auditor.audit_feature_leakage_and_availability()

    assert res["zero_forbidden_features"] is True
    assert len(res["forbidden_features_found"]) == 0
    assert res["contains_same_day_rainfall"] is True
    assert res["contains_antecedent_lags"] is True


def test_false_positive_zeros_contextual_investigation(auditor: Phase10Auditor):
    """Verify the 7 false-positive zero cases all had substantial same-day rain."""
    res = auditor.audit_false_positive_zeros_and_outliers()

    assert res["fp_zero_count"] == 7
    for c in res["false_positive_zero_cases"]:
        # In all 7 cases, gross rain was > 3.0 mm
        assert c["rainfall_mm"] >= 3.0
        # In all 7 cases, residual deficit was <= 0.8 mm (<= 8.0 m3/day)
        assert c["residual_deficit_mm"] <= 1.0

    # Largest residual outlier check
    top_outlier = res["top_outliers"][0]
    assert top_outlier["date"] == "2025-05-12"
    assert top_outlier["crop_type"] == "sugarcane"
    assert abs(top_outlier["abs_error"] - 23.30) < 0.1


def test_all_baseline_hashes_preserved(auditor: Phase10Auditor):
    """Verify that all 11 production, v1, and v2 artifacts remain 100% unaltered."""
    res = auditor.verify_all_baseline_hashes()
    assert res["all_intact"] is True
    for key, is_valid in res["details"].items():
        assert is_valid is True, f"Hash check failed for {key}"
