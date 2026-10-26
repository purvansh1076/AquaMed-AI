"""
AquaMediAI — Phase 9 Two-Stage Agronomic Irrigation Model
=========================================================

Implements a defensible two-stage architecture for predicting daily net crop-water
requirements:
  Stage 1: Binary Classifier to detect whether net irrigation requirement is zero
           (e.g., monsoon rain deluge or effective precipitation >= ETc).
  Stage 2: Positive-Demand Continuous Regressor trained exclusively on non-zero
           irrigation samples.

Agronomic Rationale & Invariants:
---------------------------------
1. ZERO-INFLATED PHENOMENON:
   In monsoon and pre-monsoon convective showers, effective rainfall exceeds crop
   evapotranspiration, causing net irrigation requirement to snap to exactly 0.0.
   Single-stage continuous regression trees produce positive residual blips (e.g. 5-15 m3/day)
   because MSE loss penalizes average distance, leading to poor zero snapping.
2. RISK-AWARE THRESHOLD TUNING:
   In agricultural irrigation:
   - False Positive Zero (predicting 0 when crop needed water): RISKS DROUGHT STRESS & YIELD LOSS.
   - False Negative Zero (predicting >0 when water was 0): WASTES WATER / OVER-IRRIGATES.
   Decision threshold tau is calibrated strictly on 2024 validation data to balance this trade-off.
3. PREPROCESSOR ISOLATION:
   Encoders and scalers are fitted ONLY on training data (2021-2023).
4. UNTOUCHED FINAL TEST:
   Evaluated once on 2025 test partition.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
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
from xgboost import XGBClassifier, XGBRegressor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TwoStageEvaluationMetrics:
    """Complete evaluation report for the two-stage model."""

    # Stage 1 (Classification) Metrics
    zero_threshold: float
    decision_threshold: float
    n_total: int
    n_true_zero: int
    n_true_positive: int
    pred_zero_count: int
    pred_positive_count: int
    accuracy: float
    precision_zero: float
    recall_zero: float
    f1_zero: float
    false_positive_zero_count: int  # Predicted 0, actually positive (drought risk)
    false_negative_zero_count: int  # Predicted positive, actually 0 (water waste)

    # Stage 2 (Positive Regressor) Metrics on true positive subset
    positive_subset_mae: float
    positive_subset_rmse: float
    positive_subset_r2: float

    # Zero Subset Performance (Residual on true zero demand)
    zero_subset_mae: float
    zero_subset_rmse: float

    # Combined Overall Performance
    overall_mae: float
    overall_rmse: float
    overall_r2: float
    overall_bias: float
    overall_max_error: float

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TwoStageIrrigationModel:
    """
    Two-stage estimator combining binary classification and positive-demand regression.
    """

    def __init__(
        self,
        classifier: Optional[Any] = None,
        regressor: Optional[Any] = None,
        zero_threshold: float = 0.001,
        decision_threshold: float = 0.50,
        seed: int = 42,
    ) -> None:
        self.zero_threshold = zero_threshold
        self.decision_threshold = decision_threshold
        self.seed = seed

        # Stage 1: Binary classifier (1 = Zero demand, 0 = Positive demand)
        self.classifier = classifier or XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=seed,
            eval_metric="logloss",
        )

        # Stage 2: Positive-demand regressor
        self.regressor = regressor or XGBRegressor(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=seed,
            objective="reg:squarederror",
        )

        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> TwoStageIrrigationModel:
        """
        Fit both stages strictly on training data.
        X: preprocessed feature matrix (n_samples, n_features)
        y: target array in m3/day
        """
        y_arr = np.asarray(y, dtype=np.float64)

        # 1. Define binary zero-demand label: 1 if y <= zero_threshold, else 0
        y_is_zero = (y_arr <= self.zero_threshold).astype(int)

        logger.info(
            f"Fitting Stage 1 Classifier on {len(y_arr)} samples "
            f"({np.sum(y_is_zero)} zero-demand, {len(y_arr) - np.sum(y_is_zero)} positive-demand)..."
        )
        self.classifier.fit(X, y_is_zero)

        # 2. Filter for strictly positive demand samples for Stage 2
        pos_mask = y_arr > self.zero_threshold
        X_pos = X[pos_mask]
        y_pos = y_arr[pos_mask]

        logger.info(f"Fitting Stage 2 Regressor on {len(y_pos)} positive-demand samples...")
        self.regressor.fit(X_pos, y_pos)

        self.is_fitted = True
        return self

    def predict_proba_zero(self, X: np.ndarray) -> np.ndarray:
        """Return probability of zero demand for each sample."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba_zero.")
        # Classes: [0 (positive), 1 (zero)]
        probas = self.classifier.predict_proba(X)
        if probas.shape[1] == 2:
            return probas[:, 1]
        return probas[:, 0]

    def predict(
        self,
        X: np.ndarray,
        decision_threshold: Optional[float] = None,
    ) -> np.ndarray:
        """
        Predict net irrigation demand in m3/day.
        If P(is_zero) >= threshold, returns 0.0.
        Else returns max(0.0, regressor.predict(X)).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")

        thresh = decision_threshold if decision_threshold is not None else self.decision_threshold
        prob_zero = self.predict_proba_zero(X)
        is_zero_pred = prob_zero >= thresh

        # Predict continuous positive demand
        raw_reg_preds = self.regressor.predict(X)
        pos_preds = np.clip(raw_reg_preds, a_min=0.0, a_max=None)

        final_preds = np.where(is_zero_pred, 0.0, pos_preds)
        return final_preds

    def calibrate_threshold_on_validation(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        candidate_thresholds: Optional[List[float]] = None,
        metric: str = "mae",
    ) -> float:
        """
        Calibrate decision threshold tau strictly on validation set.
        candidate_thresholds: list of tau values between 0.1 and 0.9.
        Returns the optimal decision threshold.
        """
        thresholds = candidate_thresholds or [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        y_v = np.asarray(y_val, dtype=np.float64)

        best_tau = self.decision_threshold
        best_score = float("inf") if metric in ["mae", "rmse"] else -float("inf")

        for tau in thresholds:
            y_pred = self.predict(X_val, decision_threshold=tau)
            if metric == "mae":
                score = mean_absolute_error(y_v, y_pred)
                if score < best_score:
                    best_score = score
                    best_tau = tau
            elif metric == "f1_zero":
                prob_zero = self.predict_proba_zero(X_val)
                y_pred_zero = (prob_zero >= tau).astype(int)
                y_true_zero = (y_v <= self.zero_threshold).astype(int)
                score = f1_score(y_true_zero, y_pred_zero, zero_division=0)
                if score > best_score:
                    best_score = score
                    best_tau = tau

        logger.info(f"Threshold calibrated on validation data: tau* = {best_tau} (best {metric}: {best_score:.4f})")
        self.decision_threshold = best_tau
        return best_tau

    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        decision_threshold: Optional[float] = None,
    ) -> TwoStageEvaluationMetrics:
        """
        Evaluate full two-stage performance on held-out test data.
        """
        thresh = decision_threshold if decision_threshold is not None else self.decision_threshold
        y_arr = np.asarray(y, dtype=np.float64)
        y_true_zero = (y_arr <= self.zero_threshold).astype(int)

        prob_zero = self.predict_proba_zero(X)
        pred_is_zero = (prob_zero >= thresh).astype(int)

        y_preds = self.predict(X, decision_threshold=thresh)

        # Classification metrics
        acc = float(accuracy_score(y_true_zero, pred_is_zero))
        prec = float(precision_score(y_true_zero, pred_is_zero, zero_division=0))
        rec = float(recall_score(y_true_zero, pred_is_zero, zero_division=0))
        f1 = float(f1_score(y_true_zero, pred_is_zero, zero_division=0))

        cm = confusion_matrix(y_true_zero, pred_is_zero, labels=[0, 1])
        # cm[0,0] = True Positive Demand (actually positive, pred positive)
        # cm[0,1] = False Positive Zero (actually positive, pred zero -> DROUGHT RISK!)
        # cm[1,0] = False Negative Zero (actually zero, pred positive -> WATER WASTE!)
        # cm[1,1] = True Zero (actually zero, pred zero)
        tn, fp_zero, fn_zero, tp_zero = cm.ravel()

        # Subset metrics: Positive demand samples
        pos_mask = y_arr > self.zero_threshold
        if np.sum(pos_mask) > 0:
            pos_mae = float(mean_absolute_error(y_arr[pos_mask], y_preds[pos_mask]))
            pos_rmse = float(np.sqrt(mean_squared_error(y_arr[pos_mask], y_preds[pos_mask])))
            pos_r2 = float(r2_score(y_arr[pos_mask], y_preds[pos_mask]))
        else:
            pos_mae, pos_rmse, pos_r2 = 0.0, 0.0, 0.0

        # Subset metrics: Zero demand samples
        zero_mask = y_arr <= self.zero_threshold
        if np.sum(zero_mask) > 0:
            zero_mae = float(mean_absolute_error(y_arr[zero_mask], y_preds[zero_mask]))
            zero_rmse = float(np.sqrt(mean_squared_error(y_arr[zero_mask], y_preds[zero_mask])))
        else:
            zero_mae, zero_rmse = 0.0, 0.0

        # Overall regression metrics
        overall_mae = float(mean_absolute_error(y_arr, y_preds))
        overall_rmse = float(np.sqrt(mean_squared_error(y_arr, y_preds)))
        overall_r2 = float(r2_score(y_arr, y_preds))
        overall_bias = float(np.mean(y_preds - y_arr))
        overall_max_err = float(np.max(np.abs(y_preds - y_arr)))

        return TwoStageEvaluationMetrics(
            zero_threshold=self.zero_threshold,
            decision_threshold=round(thresh, 4),
            n_total=len(y_arr),
            n_true_zero=int(np.sum(zero_mask)),
            n_true_positive=int(np.sum(pos_mask)),
            pred_zero_count=int(np.sum(pred_is_zero)),
            pred_positive_count=int(len(y_arr) - np.sum(pred_is_zero)),
            accuracy=round(acc, 4),
            precision_zero=round(prec, 4),
            recall_zero=round(rec, 4),
            f1_zero=round(f1, 4),
            false_positive_zero_count=int(fp_zero),
            false_negative_zero_count=int(fn_zero),
            positive_subset_mae=round(pos_mae, 4),
            positive_subset_rmse=round(pos_rmse, 4),
            positive_subset_r2=round(pos_r2, 4),
            zero_subset_mae=round(zero_mae, 4),
            zero_subset_rmse=round(zero_rmse, 4),
            overall_mae=round(overall_mae, 4),
            overall_rmse=round(overall_rmse, 4),
            overall_r2=round(overall_r2, 4),
            overall_bias=round(overall_bias, 4),
            overall_max_error=round(overall_max_err, 4),
        )

    def save_artifacts(self, target_dir: Path) -> None:
        """Save fitted models and parameters."""
        target_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.classifier, target_dir / "candidate_v3_classifier.joblib")
        joblib.dump(self.regressor, target_dir / "candidate_v3_regressor.joblib")
        config = {
            "model_type": "TwoStageIrrigationModel",
            "zero_threshold": self.zero_threshold,
            "decision_threshold": self.decision_threshold,
            "seed": self.seed,
            "classifier_type": self.classifier.__class__.__name__,
            "regressor_type": self.regressor.__class__.__name__,
        }
        with open(target_dir / "two_stage_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
