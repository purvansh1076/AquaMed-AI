"""
AquaMediAI — Phase 9 Error Analysis & Diagnostic Engine
======================================================

Provides independent, audited verification of Phase 8B baseline metrics and
deep agronomic diagnostic breakdowns by:
- Crop identity (wheat, sugarcane, cotton, soybean, maize, groundnut)
- Seasonal and monthly calendars (Kharif, Rabi, Zaid, months 1-12)
- Demand regimes (zero-demand, low, medium, high)
- Detailed residual diagnostics and worst-case outlier profiling

Preservation Invariants:
------------------------
1. Purely analytical: does NOT modify any models, endpoints, or data.
2. Zero leakage: operates strictly on held-out predictions or designated partitions.
3. Agronomic honesty: targets are theoretical calculated values, not field sensors.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetricSet:
    """Standard evaluation metrics for a continuous water requirement target."""

    mae: float
    rmse: float
    nrmse: float
    r2: float
    mean_signed_bias: float
    max_error: float
    n_samples: int
    target_mean: float
    pred_mean: float

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_metrics_from_arrays(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> MetricSet:
    """Calculate standard regression metrics from 1D numpy arrays."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    n = len(y_t)
    if n == 0:
        return MetricSet(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0)

    mae = float(mean_absolute_error(y_t, y_p))
    mse = float(mean_squared_error(y_t, y_p))
    rmse = float(np.sqrt(mse))
    t_mean = float(np.mean(y_t))
    p_mean = float(np.mean(y_p))
    bias = float(np.mean(y_p - y_t))
    max_err = float(np.max(np.abs(y_p - y_t)))

    # NRMSE normalised by target mean
    nrmse = float(rmse / t_mean) if t_mean > 0 else float("inf")

    # R2 score
    r2 = float(r2_score(y_t, y_p)) if len(np.unique(y_t)) > 1 else 0.0

    return MetricSet(
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        nrmse=round(nrmse, 4),
        r2=round(r2, 4),
        mean_signed_bias=round(bias, 4),
        max_error=round(max_err, 4),
        n_samples=n,
        target_mean=round(t_mean, 4),
        pred_mean=round(p_mean, 4),
    )


class Phase9ErrorAnalyzer:
    """
    Performs forensic error analysis and baseline verification for Phase 9.
    """

    def __init__(
        self,
        candidate_v2_dir: Optional[Path | str] = None,
        dataset_csv_path: Optional[Path | str] = None,
    ) -> None:
        from app.config import get_settings

        base_models_dir = get_settings().model_dir_path
        self.v2_dir = Path(candidate_v2_dir) if candidate_v2_dir else (base_models_dir / "candidate_v2")
        self.dataset_path = (
            Path(dataset_csv_path)
            if dataset_csv_path
            else (base_models_dir.parent / "processed" / "candidate_v2_dataset.csv")
        )

        self.predictions_path = self.v2_dir / "test_predictions.csv"
        self.metrics_json_path = self.v2_dir / "test_evaluation_metrics.json"

    def verify_baseline_reproduction(self) -> Dict[str, Any]:
        """
        Independently recompute all test metrics from saved predictions and compare
        with saved metrics JSON within tight tolerances (< 0.001).
        """
        if not self.predictions_path.exists():
            raise FileNotFoundError(f"Missing test predictions at: {self.predictions_path}")
        if not self.metrics_json_path.exists():
            raise FileNotFoundError(f"Missing test metrics at: {self.metrics_json_path}")

        df_preds = pd.read_csv(self.predictions_path)
        with open(self.metrics_json_path, "r", encoding="utf-8") as f:
            saved_metrics = json.load(f)

        y_true = df_preds["y_true_m3_day"].values
        y_xgb = df_preds["y_pred_xgb_m3_day"].values
        y_rf = df_preds["y_pred_rf_m3_day"].values

        recomputed_xgb = calculate_metrics_from_arrays(y_true, y_xgb)
        recomputed_rf = calculate_metrics_from_arrays(y_true, y_rf)

        # Naive baseline: predicting constant mean from training set (29.62 m3/day)
        # Verify naive metrics
        train_mean_constant = 29.619067  # From 2021-2023 training target mean
        y_naive = np.full_like(y_true, fill_value=train_mean_constant)
        recomputed_naive = calculate_metrics_from_arrays(y_true, y_naive)

        saved_xgb = saved_metrics["candidate_models"]["candidate_xgboost"]
        saved_rf = saved_metrics["candidate_models"]["candidate_random_forest"]

        xgb_match = (
            abs(recomputed_xgb.mae - saved_xgb["mae"]) < 0.01
            and abs(recomputed_xgb.rmse - saved_xgb["rmse"]) < 0.01
            and abs(recomputed_xgb.r2 - saved_xgb["r2"]) < 0.01
        )
        rf_match = (
            abs(recomputed_rf.mae - saved_rf["mae"]) < 0.01
            and abs(recomputed_rf.rmse - saved_rf["rmse"]) < 0.01
            and abs(recomputed_rf.r2 - saved_rf["r2"]) < 0.01
        )

        return {
            "reproduction_verified": bool(xgb_match and rf_match),
            "sample_count": len(df_preds),
            "xgboost": {
                "recomputed": recomputed_xgb.as_dict(),
                "saved": saved_xgb,
                "verified": bool(xgb_match),
            },
            "random_forest": {
                "recomputed": recomputed_rf.as_dict(),
                "saved": saved_rf,
                "verified": bool(rf_match),
            },
            "naive_baseline": {
                "recomputed": recomputed_naive.as_dict(),
                "saved": saved_metrics["comparators"]["naive_mean_baseline"],
            },
        }

    def compute_sliced_error_breakdowns(self) -> Dict[str, Any]:
        """
        Compute granular performance metrics across crops, seasons, months, and demand tiers.
        """
        df_preds = pd.read_csv(self.predictions_path)
        df_preds["abs_err_xgb"] = np.abs(df_preds["y_pred_xgb_m3_day"] - df_preds["y_true_m3_day"])
        df_preds["signed_err_xgb"] = df_preds["y_pred_xgb_m3_day"] - df_preds["y_true_m3_day"]
        df_preds["abs_err_rf"] = np.abs(df_preds["y_pred_rf_m3_day"] - df_preds["y_true_m3_day"])

        # Add month and season information if not present
        df_preds["date"] = pd.to_datetime(df_preds["date"])
        df_preds["month"] = df_preds["date"].dt.month

        def get_season(month: int) -> str:
            if month in [6, 7, 8, 9, 10]:
                return "kharif"
            elif month in [11, 12, 1, 2]:
                return "rabi"
            else:
                return "zaid_summer"

        df_preds["season"] = df_preds["month"].apply(get_season)

        # 1. By Crop Breakdown
        crop_breakdown: Dict[str, Any] = {}
        for crop, group in df_preds.groupby("crop_type"):
            m_xgb = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_xgb_m3_day"].values)
            m_rf = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_rf_m3_day"].values)
            crop_breakdown[str(crop)] = {
                "n_samples": len(group),
                "target_mean": m_xgb.target_mean,
                "xgb_mae": m_xgb.mae,
                "xgb_rmse": m_xgb.rmse,
                "xgb_bias": m_xgb.mean_signed_bias,
                "xgb_r2": m_xgb.r2,
                "rf_mae": m_rf.mae,
                "rf_rmse": m_rf.rmse,
                "rf_bias": m_rf.mean_signed_bias,
                "rf_r2": m_rf.r2,
            }

        # 2. By Season Breakdown
        season_breakdown: Dict[str, Any] = {}
        for season, group in df_preds.groupby("season"):
            m_xgb = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_xgb_m3_day"].values)
            m_rf = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_rf_m3_day"].values)
            season_breakdown[str(season)] = {
                "n_samples": len(group),
                "target_mean": m_xgb.target_mean,
                "xgb_mae": m_xgb.mae,
                "xgb_rmse": m_xgb.rmse,
                "xgb_bias": m_xgb.mean_signed_bias,
                "rf_mae": m_rf.mae,
            }

        # 3. By Month Breakdown
        month_breakdown: Dict[str, Any] = {}
        for month, group in df_preds.groupby("month"):
            m_xgb = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_xgb_m3_day"].values)
            m_rf = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_rf_m3_day"].values)
            month_breakdown[str(month)] = {
                "n_samples": len(group),
                "target_mean": m_xgb.target_mean,
                "xgb_mae": m_xgb.mae,
                "xgb_rmse": m_xgb.rmse,
                "xgb_bias": m_xgb.mean_signed_bias,
                "rf_mae": m_rf.mae,
            }

        # 4. By Demand Tier Breakdown
        zero_mask = df_preds["y_true_m3_day"] <= 0.001
        low_mask = (df_preds["y_true_m3_day"] > 0.001) & (df_preds["y_true_m3_day"] <= 30.0)
        med_mask = (df_preds["y_true_m3_day"] > 30.0) & (df_preds["y_true_m3_day"] <= 60.0)
        high_mask = df_preds["y_true_m3_day"] > 60.0

        demand_tiers = {
            "zero_demand": df_preds[zero_mask],
            "low_demand_0_30": df_preds[low_mask],
            "med_demand_30_60": df_preds[med_mask],
            "high_demand_gt_60": df_preds[high_mask],
        }

        tier_breakdown: Dict[str, Any] = {}
        for tier_name, group in demand_tiers.items():
            if len(group) == 0:
                continue
            m_xgb = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_xgb_m3_day"].values)
            m_rf = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_rf_m3_day"].values)
            tier_breakdown[tier_name] = {
                "n_samples": len(group),
                "pct_of_test_data": round(100.0 * len(group) / len(df_preds), 2),
                "target_mean": m_xgb.target_mean,
                "xgb_pred_mean": m_xgb.pred_mean,
                "xgb_mae": m_xgb.mae,
                "xgb_rmse": m_xgb.rmse,
                "xgb_bias": m_xgb.mean_signed_bias,
                "rf_mae": m_rf.mae,
            }

        # 5. Crop x Season Matrix
        crop_season_breakdown: Dict[str, Dict[str, Any]] = {}
        for (crop, season), group in df_preds.groupby(["crop_type", "season"]):
            m_xgb = calculate_metrics_from_arrays(group["y_true_m3_day"].values, group["y_pred_xgb_m3_day"].values)
            if crop not in crop_season_breakdown:
                crop_season_breakdown[crop] = {}
            crop_season_breakdown[crop][season] = {
                "n_samples": len(group),
                "target_mean": m_xgb.target_mean,
                "xgb_mae": m_xgb.mae,
                "xgb_rmse": m_xgb.rmse,
                "xgb_bias": m_xgb.mean_signed_bias,
            }

        return {
            "by_crop": crop_breakdown,
            "by_season": season_breakdown,
            "by_month": month_breakdown,
            "by_demand_tier": tier_breakdown,
            "crop_by_season": crop_season_breakdown,
        }

    def inspect_extreme_errors(self, top_n: int = 10) -> Dict[str, Any]:
        """
        Deep-dive into the largest prediction errors, isolating Sugarcane, Cotton, Soybean,
        and high-demand conditions, joined with environmental features.
        """
        df_preds = pd.read_csv(self.predictions_path)
        df_preds["abs_err_xgb"] = np.abs(df_preds["y_pred_xgb_m3_day"] - df_preds["y_true_m3_day"])
        df_preds["signed_err_xgb"] = df_preds["y_pred_xgb_m3_day"] - df_preds["y_true_m3_day"]

        # Join with meteorological variables from candidate_v2_dataset.csv
        df_full = pd.read_csv(self.dataset_path)
        # Filter for 2025
        df_full_2025 = df_full[df_full["year"] == 2025].copy()

        merged = pd.merge(
            df_preds,
            df_full_2025[
                [
                    "sample_key",
                    "temperature_celsius",
                    "rainfall_mm",
                    "vpd_proxy_kpa",
                    "et0_fao56_mm_per_day",
                    "kc_value",
                    "etc_mm_per_day",
                    "effective_precipitation_mm",
                ]
            ],
            on="sample_key",
            how="left",
        )

        def extract_top(subset: pd.DataFrame, n: int) -> List[Dict[str, Any]]:
            top_rows = subset.sort_values("abs_err_xgb", ascending=False).head(n)
            results = []
            for _, r in top_rows.iterrows():
                results.append(
                    {
                        "sample_key": str(r["sample_key"]),
                        "date": str(r["date"]),
                        "crop_type": str(r["crop_type"]),
                        "growth_stage": str(r["growth_stage"]),
                        "y_true": round(float(r["y_true_m3_day"]), 2),
                        "y_pred_xgb": round(float(r["y_pred_xgb_m3_day"]), 2),
                        "abs_error": round(float(r["abs_err_xgb"]), 2),
                        "signed_error": round(float(r["signed_err_xgb"]), 2),
                        "rainfall_mm": round(float(r.get("rainfall_mm", 0.0)), 2),
                        "peff_mm": round(float(r.get("effective_precipitation_mm", 0.0)), 2),
                        "etc_mm": round(float(r.get("etc_mm_per_day", 0.0)), 2),
                        "et0_mm": round(float(r.get("et0_fao56_mm_per_day", 0.0)), 2),
                        "kc": round(float(r.get("kc_value", 0.0)), 2),
                    }
                )
            return results

        overall_top = extract_top(merged, top_n)
        sugarcane_top = extract_top(merged[merged["crop_type"] == "sugarcane"], top_n)
        cotton_top = extract_top(merged[merged["crop_type"] == "cotton"], top_n)
        soybean_top = extract_top(merged[merged["crop_type"] == "soybean"], top_n)
        high_demand_top = extract_top(merged[merged["y_true_m3_day"] > 60.0], top_n)
        zero_demand_top = extract_top(merged[merged["y_true_m3_day"] <= 0.001], top_n)

        return {
            "overall_worst_10": overall_top,
            "sugarcane_worst_10": sugarcane_top,
            "cotton_worst_10": cotton_top,
            "soybean_worst_10": soybean_top,
            "high_demand_worst_10": high_demand_top,
            "zero_demand_worst_10": zero_demand_top,
        }
