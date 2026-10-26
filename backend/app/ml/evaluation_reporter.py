"""
AquaMediAI — Comparative Agronomic Evaluation Reporter
======================================================

Generates standardized, honest evaluation benchmarks comparing any ML model
against:
  1. The Naive Mean Baseline (sample average from training set)
  2. The Approach A Deterministic Agronomic Baseline
  3. The Candidate ML Model (Approach B)

Crucial Rule:
Always report physical units (m³/day), sample counts (n), and normalized errors.
Never claim high R² without checking for target collinearity or leakage.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import numpy as np


@dataclass(frozen=True)
class BenchmarkMetrics:
    model_name: str
    target_units: str
    n_samples: int
    mae: float
    rmse: float
    nrmse: float  # RMSE divided by target mean (relative error percentage)
    r2: float
    max_error: float

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComparativeEvaluationReport:
    target_name: str
    target_units: str
    n_evaluation_samples: int
    naive_mean_baseline: BenchmarkMetrics
    deterministic_agronomic_baseline: Optional[BenchmarkMetrics]
    candidate_model: BenchmarkMetrics
    improvement_over_naive_pct: float
    summary_verdict: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "target_name": self.target_name,
            "target_units": self.target_units,
            "n_evaluation_samples": self.n_evaluation_samples,
            "naive_mean_baseline": self.naive_mean_baseline.as_dict(),
            "deterministic_agronomic_baseline": (
                self.deterministic_agronomic_baseline.as_dict()
                if self.deterministic_agronomic_baseline
                else None
            ),
            "candidate_model": self.candidate_model.as_dict(),
            "improvement_over_naive_pct": round(self.improvement_over_naive_pct, 2),
            "summary_verdict": self.summary_verdict,
        }


def compute_benchmark_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    target_units: str = "m3/day",
) -> BenchmarkMetrics:
    """Compute standard regression metrics with physical units and relative NRMSE."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    if len(y_t) != len(y_p):
        raise ValueError(f"Length mismatch: len(y_true)={len(y_t)} vs len(y_pred)={len(y_p)}")
    if len(y_t) == 0:
        raise ValueError("Cannot evaluate empty arrays.")

    errors = np.abs(y_t - y_p)
    mae = float(np.mean(errors))
    mse = float(np.mean((y_t - y_p) ** 2))
    rmse = float(math.sqrt(mse))

    mean_target = float(np.mean(y_t))
    nrmse = float(rmse / mean_target) if abs(mean_target) > 1e-6 else 0.0

    # R2 computation
    ss_tot = float(np.sum((y_t - mean_target) ** 2))
    ss_res = float(np.sum((y_t - y_p) ** 2))
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-6 else 0.0

    max_err = float(np.max(errors))

    return BenchmarkMetrics(
        model_name=model_name,
        target_units=target_units,
        n_samples=len(y_t),
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        nrmse=round(nrmse, 4),
        r2=round(r2, 4),
        max_error=round(max_err, 4),
    )


def generate_comparative_report(
    y_test: np.ndarray,
    y_pred_model: np.ndarray,
    y_train: np.ndarray,
    y_pred_deterministic: Optional[np.ndarray] = None,
    candidate_model_name: str = "Candidate ML Model",
    target_name: str = "water_demand_m3",
    target_units: str = "m3/day",
) -> ComparativeEvaluationReport:
    """
    Generate a full comparative evaluation report comparing a model against
    naive mean and deterministic agronomic baselines.
    """
    # 1. Naive Mean Baseline: predicts the constant mean of y_train
    mean_val = float(np.mean(y_train))
    naive_preds = np.full_like(y_test, fill_value=mean_val, dtype=float)
    naive_metrics = compute_benchmark_metrics(y_test, naive_preds, "Naive Mean Baseline", target_units)

    # 2. Candidate Model Metrics
    model_metrics = compute_benchmark_metrics(y_test, y_pred_model, candidate_model_name, target_units)

    # 3. Deterministic Baseline Metrics (if provided)
    det_metrics = None
    if y_pred_deterministic is not None:
        det_metrics = compute_benchmark_metrics(
            y_test, y_pred_deterministic, "Deterministic Agronomic Baseline (Approach A)", target_units
        )

    # Calculate percentage MAE reduction relative to naive
    if naive_metrics.mae > 0:
        imp = ((naive_metrics.mae - model_metrics.mae) / naive_metrics.mae) * 100.0
    else:
        imp = 0.0

    verdict = (
        f"{candidate_model_name} outperforms Naive Mean Baseline by {imp:.1f}% MAE reduction."
        if imp > 0
        else f"{candidate_model_name} fails to beat simple Naive Mean Baseline."
    )

    return ComparativeEvaluationReport(
        target_name=target_name,
        target_units=target_units,
        n_evaluation_samples=len(y_test),
        naive_mean_baseline=naive_metrics,
        deterministic_agronomic_baseline=det_metrics,
        candidate_model=model_metrics,
        improvement_over_naive_pct=imp,
        summary_verdict=verdict,
    )
