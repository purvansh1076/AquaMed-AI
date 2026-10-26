"""
AquaMediAI — Phase 10 Independent Audit & Verification Engine
============================================================

Provides independent, audited recomputation and verification of:
1. Candidate v3 Two-Stage Model metrics from saved 2025 predictions.
2. Split boundaries and zero-demand threshold calibration isolation.
3. Feature leakage and prediction-time meteorological availability.
4. Detailed inspection of false-positive zero cases and extreme residual outliers.
5. Cryptographic hash integrity for all production and historical candidate models.

Preservation Invariants:
------------------------
- Read-only audit: does NOT retrain or overwrite any models.
- Does NOT alter production, candidate_v1, candidate_v2, or candidate_v3 artifacts.
- Target honesty: targets are theoretical calculated values, not field measurements.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from app.config import get_settings
from app.ml.candidate_features import FORBIDDEN_LEAKAGE_FEATURES
from app.ml.candidate_trainer import KNOWN_PRODUCTION_HASHES
from app.ml.candidate_v3_experiments import (
    KNOWN_CANDIDATE_V2_HASHES,
    NUMERIC_FEATURES_SET_C,
    CATEGORICAL_FEATURES_SET_C,
    verify_all_existing_artifacts_unmodified,
)
from app.ml.multiyear_trainer import KNOWN_CANDIDATE_V1_HASHES

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class Phase10Auditor:
    """Independent auditor for Candidate v3 and repository integrity."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_models_dir = settings.model_dir_path
        self.v3_dir = self.base_models_dir / "candidate_v3"
        self.v2_dir = self.base_models_dir / "candidate_v2"
        self.processed_dir = self.base_models_dir.parent / "processed"

        self.test_preds_path = self.v3_dir / "test_predictions_v3.csv"
        self.metrics_json_path = self.v3_dir / "two_stage_metrics.json"
        self.dataset_path = self.processed_dir / "candidate_v2_dataset.csv"

    def audit_recomputed_metrics(self) -> Dict[str, Any]:
        """
        Independently recompute all test evaluation metrics from saved predictions
        and compare against Phase 9 reported metrics.
        """
        if not self.test_preds_path.exists():
            raise FileNotFoundError(f"Missing test predictions at: {self.test_preds_path}")
        if not self.metrics_json_path.exists():
            raise FileNotFoundError(f"Missing metrics JSON at: {self.metrics_json_path}")

        df_preds = pd.read_csv(self.test_preds_path)
        with open(self.metrics_json_path, "r", encoding="utf-8") as f:
            saved_metrics = json.load(f)

        y_true = df_preds["y_true_m3_day"].values
        y_pred = df_preds["y_pred_two_stage_xgb_set_c"].values

        # Overall regression metrics
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        bias = float(np.mean(y_pred - y_true))
        max_err = float(np.max(np.abs(y_pred - y_true)))

        # Zero-demand classification metrics
        zero_thresh = float(saved_metrics["zero_threshold"])
        y_true_zero = (y_true <= zero_thresh).astype(int)
        y_pred_zero = (y_pred <= zero_thresh).astype(int)

        acc = float(accuracy_score(y_true_zero, y_pred_zero))
        prec = float(precision_score(y_true_zero, y_pred_zero, zero_division=0))
        rec = float(recall_score(y_true_zero, y_pred_zero, zero_division=0))
        f1 = float(f1_score(y_true_zero, y_pred_zero, zero_division=0))

        cm = confusion_matrix(y_true_zero, y_pred_zero, labels=[0, 1])
        tn, fp_zero, fn_zero, tp_zero = cm.ravel()

        # Subset regression metrics
        pos_mask = y_true > zero_thresh
        pos_mae = float(mean_absolute_error(y_true[pos_mask], y_pred[pos_mask]))
        pos_rmse = float(np.sqrt(mean_squared_error(y_true[pos_mask], y_pred[pos_mask])))
        pos_r2 = float(r2_score(y_true[pos_mask], y_pred[pos_mask]))

        zero_mask = y_true <= zero_thresh
        zero_mae = float(mean_absolute_error(y_true[zero_mask], y_pred[zero_mask]))
        zero_rmse = float(np.sqrt(mean_squared_error(y_true[zero_mask], y_pred[zero_mask])))

        # Sliced metrics by crop
        crop_metrics: Dict[str, Dict[str, float]] = {}
        for crop, grp in df_preds.groupby("crop_type"):
            yt = grp["y_true_m3_day"].values
            yp = grp["y_pred_two_stage_xgb_set_c"].values
            crop_metrics[str(crop)] = {
                "n_samples": len(grp),
                "target_mean": round(float(np.mean(yt)), 4),
                "mae": round(float(mean_absolute_error(yt, yp)), 4),
                "rmse": round(float(np.sqrt(mean_squared_error(yt, yp))), 4),
                "r2": round(float(r2_score(yt, yp)), 4),
                "bias": round(float(np.mean(yp - yt)), 4),
            }

        # Sliced metrics by demand tier
        low_mask = (y_true > zero_thresh) & (y_true <= 30.0)
        med_mask = (y_true > 30.0) & (y_true <= 60.0)
        high_mask = y_true > 60.0

        def tier_dict(mask: np.ndarray) -> Dict[str, float]:
            yt, yp = y_true[mask], y_pred[mask]
            if len(yt) == 0:
                return {"n_samples": 0, "mae": 0.0, "rmse": 0.0, "r2": 0.0}
            return {
                "n_samples": int(len(yt)),
                "target_mean": round(float(np.mean(yt)), 4),
                "mae": round(float(mean_absolute_error(yt, yp)), 4),
                "rmse": round(float(np.sqrt(mean_squared_error(yt, yp))), 4),
                "r2": round(float(r2_score(yt, yp)), 4) if len(np.unique(yt)) > 1 else 0.0,
            }

        tier_metrics = {
            "zero_demand": tier_dict(zero_mask),
            "low_demand_0_30": tier_dict(low_mask),
            "med_demand_30_60": tier_dict(med_mask),
            "high_demand_gt_60": tier_dict(high_mask),
        }

        # Compare recomputed against Phase 9 reported
        discrepancies: List[Dict[str, Any]] = []

        def check_discrepancy(metric_name: str, recomputed_val: float, reported_val: float, tolerance: float = 0.01) -> None:
            delta = abs(recomputed_val - reported_val)
            if delta > tolerance:
                discrepancies.append({
                    "metric": metric_name,
                    "recomputed": round(recomputed_val, 4),
                    "reported": round(reported_val, 4),
                    "delta": round(delta, 4),
                })

        check_discrepancy("overall_mae", mae, saved_metrics["overall_mae"])
        check_discrepancy("overall_rmse", rmse, saved_metrics["overall_rmse"])
        check_discrepancy("overall_r2", r2, saved_metrics["overall_r2"])
        check_discrepancy("overall_bias", bias, saved_metrics["overall_bias"])
        check_discrepancy("accuracy", acc, saved_metrics["accuracy"])
        check_discrepancy("precision_zero", prec, saved_metrics["precision_zero"])
        check_discrepancy("recall_zero", rec, saved_metrics["recall_zero"])
        check_discrepancy("f1_zero", f1, saved_metrics["f1_zero"])
        check_discrepancy("positive_subset_mae", pos_mae, saved_metrics["positive_subset_mae"])
        check_discrepancy("zero_subset_mae", zero_mae, saved_metrics["zero_subset_mae"])

        return {
            "sample_count": len(df_preds),
            "recomputed": {
                "overall_mae": round(mae, 4),
                "overall_rmse": round(rmse, 4),
                "overall_r2": round(r2, 4),
                "overall_bias": round(bias, 4),
                "overall_max_error": round(max_err, 4),
                "accuracy": round(acc, 4),
                "precision_zero": round(prec, 4),
                "recall_zero": round(rec, 4),
                "f1_zero": round(f1, 4),
                "false_positive_zero_count": int(fp_zero),
                "false_negative_zero_count": int(fn_zero),
                "true_zero_count": int(tp_zero),
                "true_positive_demand_count": int(tn),
                "positive_subset_mae": round(pos_mae, 4),
                "positive_subset_rmse": round(pos_rmse, 4),
                "positive_subset_r2": round(pos_r2, 4),
                "zero_subset_mae": round(zero_mae, 4),
                "zero_subset_rmse": round(zero_rmse, 4),
            },
            "reported": saved_metrics,
            "discrepancies": discrepancies,
            "crop_metrics": crop_metrics,
            "demand_tier_metrics": tier_metrics,
            "has_negative_predictions": bool((y_pred < 0.0).any()),
        }

    def audit_false_positive_zeros_and_outliers(self) -> Dict[str, Any]:
        """
        Inspect the 7 false-positive zero cases and top residual outliers,
        joining with original meteorological features.
        """
        df_preds = pd.read_csv(self.test_preds_path)
        df_full = pd.read_csv(self.dataset_path)
        df_2025 = df_full[df_full["year"] == 2025].copy()

        merged = pd.merge(
            df_preds,
            df_2025[[
                "sample_key",
                "temperature_celsius",
                "rainfall_mm",
                "effective_precipitation_mm",
                "et0_fao56_mm_per_day",
                "kc_value",
                "etc_mm_per_day",
                "vpd_proxy_kpa",
            ]],
            on="sample_key",
            how="left",
        )

        # 1. Inspect the 7 False-Positive Zero cases (predicted 0, true > 0)
        zero_thresh = 0.001
        fp_zero_mask = (merged["y_pred_two_stage_xgb_set_c"] <= zero_thresh) & (merged["y_true_m3_day"] > zero_thresh)
        fp_zero_rows = merged[fp_zero_mask].copy()

        fp_cases: List[Dict[str, Any]] = []
        for _, r in fp_zero_rows.iterrows():
            fp_cases.append({
                "sample_key": str(r["sample_key"]),
                "date": str(r["date"]),
                "crop_type": str(r["crop_type"]),
                "growth_stage": str(r["growth_stage"]),
                "y_true": round(float(r["y_true_m3_day"]), 2),
                "y_pred": round(float(r["y_pred_two_stage_xgb_set_c"]), 2),
                "rainfall_mm": round(float(r["rainfall_mm"]), 2),
                "peff_mm": round(float(r["effective_precipitation_mm"]), 2),
                "etc_mm": round(float(r["etc_mm_per_day"]), 2),
                "residual_deficit_mm": round(float(r["etc_mm_per_day"] - r["effective_precipitation_mm"]), 2),
            })

        # 2. Top 5 largest absolute errors
        merged["abs_error"] = np.abs(merged["y_pred_two_stage_xgb_set_c"] - merged["y_true_m3_day"])
        top_errors = merged.sort_values("abs_error", ascending=False).head(5)

        outliers: List[Dict[str, Any]] = []
        for _, r in top_errors.iterrows():
            outliers.append({
                "sample_key": str(r["sample_key"]),
                "date": str(r["date"]),
                "crop_type": str(r["crop_type"]),
                "growth_stage": str(r["growth_stage"]),
                "y_true": round(float(r["y_true_m3_day"]), 2),
                "y_pred": round(float(r["y_pred_two_stage_xgb_set_c"]), 2),
                "abs_error": round(float(r["abs_error"]), 2),
                "rainfall_mm": round(float(r["rainfall_mm"]), 2),
                "peff_mm": round(float(r["effective_precipitation_mm"]), 2),
                "etc_mm": round(float(r["etc_mm_per_day"]), 2),
            })

        return {
            "false_positive_zero_cases": fp_cases,
            "fp_zero_count": len(fp_cases),
            "top_outliers": outliers,
        }

    def audit_splits_and_isolation(self) -> Dict[str, Any]:
        """
        Verify that splits (Train 2021-2023, Val 2024, Test 2025) are strictly disjoint
        and that threshold selection occurred strictly on 2024 validation data.
        """
        df_full = pd.read_csv(self.dataset_path)

        train_dates = set(df_full[df_full["year"].isin([2021, 2022, 2023])]["date"].unique())
        val_dates = set(df_full[df_full["year"] == 2024]["date"].unique())
        test_dates = set(df_full[df_full["year"] == 2025]["date"].unique())

        disjoint = (
            len(train_dates & val_dates) == 0
            and len(train_dates & test_dates) == 0
            and len(val_dates & test_dates) == 0
        )

        with open(self.v3_dir / "split_metadata.json", "r", encoding="utf-8") as f:
            split_meta = json.load(f)

        with open(self.v3_dir / "two_stage_config.json", "r", encoding="utf-8") as f:
            ts_cfg = json.load(f)

        with open(self.v3_dir / "validation_ablations.json", "r", encoding="utf-8") as f:
            val_ablations = json.load(f)

        val_threshold_logged = val_ablations["two_stage_xgb_set_c"]["calibrated_threshold"]
        config_threshold = ts_cfg["decision_threshold"]

        threshold_match = (val_threshold_logged == config_threshold == 0.2)

        return {
            "dates_disjoint": disjoint,
            "train_date_count": len(train_dates),
            "val_date_count": len(val_dates),
            "test_date_count": len(test_dates),
            "split_metadata": split_meta,
            "threshold_calibrated_on_val": threshold_match,
            "calibrated_threshold": config_threshold,
        }

    def audit_feature_leakage_and_availability(self) -> Dict[str, Any]:
        """
        Verify exclusion of forbidden target-derived features and evaluate
        prediction-time operational availability.
        """
        with open(self.v3_dir / "feature_schema.json", "r", encoding="utf-8") as f:
            schema = json.load(f)

        all_features = schema["numeric_features"] + schema["categorical_features"]

        forbidden_found = [f for f in FORBIDDEN_LEAKAGE_FEATURES if f in all_features]

        return {
            "all_features": all_features,
            "total_feature_count": len(all_features),
            "zero_forbidden_features": len(forbidden_found) == 0,
            "forbidden_features_found": forbidden_found,
            "contains_same_day_rainfall": "rainfall_mm" in all_features,
            "contains_antecedent_lags": "rainfall_lag1_mm" in all_features,
        }

    def verify_all_baseline_hashes(self) -> Dict[str, Any]:
        """Verify cryptographic digests of production, v1, and v2 artifacts."""
        status = verify_all_existing_artifacts_unmodified(self.base_models_dir)
        all_intact = all(status.values())
        return {
            "all_intact": all_intact,
            "details": status,
        }
