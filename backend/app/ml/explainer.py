"""
AquaMediAI — SHAP Explainability Module
========================================

Uses SHAP (SHapley Additive exPlanations) to explain water-demand predictions
from tree-based models (RandomForest, XGBoost).

SHAP Reference
--------------
Lundberg, S.M. & Lee, S.I. (2017). A Unified Approach to Interpreting Model
Predictions. *Advances in Neural Information Processing Systems*, 30.
https://doi.org/10.48550/arXiv.1705.07874

Design Notes
------------
- Uses ``shap.TreeExplainer`` — exact SHAP values for tree ensembles (not
  approximation).
- A background dataset of 200 training samples is used for the explainer
  baseline.  This is standard practice and does not introduce data leakage.
- Output is structured for direct consumption by the React dashboard
  (Phase 9) — no UI-specific formatting here.

IMPORTANT
---------
This module only explains predictions on the SYNTHETIC dataset.
No real farmer data is processed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─── Output data structures ───────────────────────────────────────────────────

@dataclass
class FeatureContribution:
    """
    SHAP contribution for a single feature in a single prediction.

    Attributes
    ----------
    feature : str
        Feature name (from ENGINEERED_FEATURE_COLS).
    raw_value : float
        The actual numeric value of the feature used in prediction.
    shap_value : float
        SHAP value — how much this feature pushed the prediction
        above (positive) or below (negative) the base value.
    impact : str
        'positive' if shap_value > 0, 'negative' otherwise, 'neutral' if ~0.
    abs_shap : float
        |shap_value| — used for ranking by importance.
    """

    feature: str
    raw_value: float
    shap_value: float
    impact: str
    abs_shap: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "raw_value": round(self.raw_value, 6),
            "shap_value": round(self.shap_value, 6),
            "impact": self.impact,
            "abs_shap": round(self.abs_shap, 6),
        }


@dataclass
class SHAPExplanation:
    """
    Complete SHAP explanation for a single prediction.

    Attributes
    ----------
    prediction : float
        The model's predicted water demand (m³/day).
    base_value : float
        SHAP expected value — average model output over background data.
    features : list of FeatureContribution
        All features sorted by |shap_value| descending.
    top_positive : list of FeatureContribution
        Top contributors that *increase* the prediction.
    top_negative : list of FeatureContribution
        Top contributors that *decrease* the prediction.
    model_name : str
        Which model generated this explanation.
    data_disclaimer : str
        Reminder that this is a synthetic dataset explanation.
    """

    prediction: float
    base_value: float
    features: List[FeatureContribution] = field(default_factory=list)
    top_positive: List[FeatureContribution] = field(default_factory=list)
    top_negative: List[FeatureContribution] = field(default_factory=list)
    model_name: str = "Unknown"
    data_disclaimer: str = (
        "Explanation based on synthetic agronomic data (FAO-56 ET₀×Kc×area). "
        "Not derived from real farmer records."
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "prediction": round(self.prediction, 4),
            "base_value": round(self.base_value, 4),
            "model_name": self.model_name,
            "features": [f.as_dict() for f in self.features],
            "top_positive": [f.as_dict() for f in self.top_positive],
            "top_negative": [f.as_dict() for f in self.top_negative],
            "data_disclaimer": self.data_disclaimer,
        }


@dataclass
class GlobalFeatureImportance:
    """
    Global feature importance across the full dataset (mean |SHAP|).

    Attributes
    ----------
    feature_importances : list of (feature_name, mean_abs_shap)
        Sorted descending by mean |SHAP|.
    model_name : str
    n_samples : int
        Number of samples used to compute global importance.
    """

    feature_importances: List[Tuple[str, float]] = field(default_factory=list)
    model_name: str = "Unknown"
    n_samples: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "n_samples": self.n_samples,
            "feature_importances": [
                {"feature": f, "mean_abs_shap": round(v, 6)}
                for f, v in self.feature_importances
            ],
        }


# ─── SHAP Explainer class ─────────────────────────────────────────────────────

class WaterDemandExplainer:
    """
    SHAP-based explainer for tree-based water-demand models.

    Parameters
    ----------
    model : fitted tree-based model (RandomForest or XGBoost)
        Must support ``shap.TreeExplainer``.
    background_data : np.ndarray, shape (n_background, n_features)
        Background dataset for SHAP baseline computation.
        Should be a sample from the TRAINING set only.
    feature_columns : list of str
        Ordered list of feature names (matches columns of background_data).
    model_name : str
        Human-readable model identifier for output.
    """

    def __init__(
        self,
        model: Any,
        background_data: np.ndarray,
        feature_columns: List[str],
        model_name: str = "Unknown",
    ) -> None:
        import shap  # deferred import — shap is slow to import

        self._model = model
        self._feature_columns = feature_columns
        self._model_name = model_name

        logger.info(
            "Initialising SHAP TreeExplainer (model=%s, background_samples=%d)…",
            model_name,
            len(background_data),
        )
        self._explainer = shap.TreeExplainer(
            model,
            data=background_data,
            feature_perturbation="interventional",
        )
        self._base_value: Optional[float] = None
        logger.info("SHAP TreeExplainer ready.")

    # ─── Factory ──────────────────────────────────────────────────────────────

    @classmethod
    def from_artifacts(
        cls,
        model_dir: Path,
        train_df: pd.DataFrame,
        model_name: str = "XGBoost",
        n_background: int = 200,
        seed: int = 42,
    ) -> "WaterDemandExplainer":
        """
        Build an explainer from persisted artefacts + a sample of training data.

        Parameters
        ----------
        model_dir : Path
            Directory with model .joblib artefacts.
        train_df : pd.DataFrame
            Training DataFrame (BEFORE feature engineering).
            A random subsample is used as SHAP background.
        model_name : str
            'XGBoost' or 'RandomForest'.
        n_background : int
            Number of background samples (200 is SHAP's recommendation).
        seed : int
            For reproducible background sampling.

        Returns
        -------
        WaterDemandExplainer
        """
        from app.ml.trainer import load_encoders, load_model
        from app.ml.feature_engineering import engineer_features, get_feature_matrix

        model = load_model(model_dir, model_name=model_name)
        encoders = load_encoders(model_dir)

        # Sample background from training data
        bg_df = train_df.sample(
            n=min(n_background, len(train_df)),
            random_state=seed,
        )
        bg_eng = engineer_features(bg_df, encoders)
        X_bg, _ = get_feature_matrix(bg_eng)

        from app.ml.feature_engineering import ENGINEERED_FEATURE_COLS
        return cls(
            model=model,
            background_data=X_bg,
            feature_columns=ENGINEERED_FEATURE_COLS,
            model_name=model_name,
        )

    # ─── Per-prediction explanation ────────────────────────────────────────────

    def explain_single(
        self,
        X_row: np.ndarray,
        prediction: Optional[float] = None,
        top_n: int = 5,
    ) -> SHAPExplanation:
        """
        Generate a SHAP explanation for a single feature vector.

        Parameters
        ----------
        X_row : np.ndarray, shape (1, n_features) or (n_features,)
            Engineered feature vector.
        prediction : float, optional
            Model prediction to attach. If None, model.predict(X_row) is called.
        top_n : int
            Number of top positive/negative contributors to return.

        Returns
        -------
        SHAPExplanation
        """
        X = np.atleast_2d(X_row)
        if prediction is None:
            prediction = float(self._model.predict(X)[0])

        # Compute SHAP values
        shap_values = self._explainer.shap_values(X)
        if isinstance(shap_values, list):
            # Multi-output: take first output
            shap_vals = shap_values[0][0]
        else:
            shap_vals = shap_values[0]

        base_value = float(self._explainer.expected_value)
        if isinstance(base_value, (list, np.ndarray)):
            base_value = float(base_value[0])

        # Build feature contribution objects
        contributions: List[FeatureContribution] = []
        for i, (feat, sv) in enumerate(zip(self._feature_columns, shap_vals)):
            raw_val = float(X[0, i])
            sv_float = float(sv)
            if sv_float > 1e-9:
                impact = "positive"
            elif sv_float < -1e-9:
                impact = "negative"
            else:
                impact = "neutral"
            contributions.append(FeatureContribution(
                feature=feat,
                raw_value=raw_val,
                shap_value=sv_float,
                impact=impact,
                abs_shap=abs(sv_float),
            ))

        # Sort by |SHAP| descending
        contributions.sort(key=lambda c: c.abs_shap, reverse=True)

        top_pos = [c for c in contributions if c.impact == "positive"][:top_n]
        top_neg = [c for c in contributions if c.impact == "negative"][:top_n]

        return SHAPExplanation(
            prediction=prediction,
            base_value=base_value,
            features=contributions,
            top_positive=top_pos,
            top_negative=top_neg,
            model_name=self._model_name,
        )

    def explain_from_dataframe(
        self,
        df: pd.DataFrame,
        encoders: Any,
        top_n: int = 5,
    ) -> List[SHAPExplanation]:
        """
        Explain predictions for every row in a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Raw (not yet engineered) DataFrame.
        encoders : FittedEncoders
            Same encoders used during training.
        top_n : int
            Top N contributors per explanation.

        Returns
        -------
        list of SHAPExplanation, one per row.
        """
        from app.ml.feature_engineering import engineer_features, get_feature_matrix

        eng_df = engineer_features(df, encoders)
        X, _ = get_feature_matrix(eng_df, require_target=False)
        predictions = self._model.predict(X).astype(float)

        explanations = []
        for i in range(len(X)):
            expl = self.explain_single(X[i : i + 1], prediction=float(predictions[i]), top_n=top_n)
            explanations.append(expl)
        return explanations

    # ─── Global feature importance ─────────────────────────────────────────────

    def global_feature_importance(
        self,
        X: np.ndarray,
        n_samples: Optional[int] = None,
    ) -> GlobalFeatureImportance:
        """
        Compute mean |SHAP| feature importance over a dataset.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            Feature matrix (engineered).
        n_samples : int, optional
            Subsample X to at most this many rows for speed.

        Returns
        -------
        GlobalFeatureImportance
        """
        if n_samples and n_samples < len(X):
            rng = np.random.default_rng(42)
            idx = rng.choice(len(X), size=n_samples, replace=False)
            X_sub = X[idx]
        else:
            X_sub = X

        logger.info(
            "Computing global SHAP importance over %d samples…", len(X_sub)
        )
        shap_values = self._explainer.shap_values(X_sub)
        if isinstance(shap_values, list):
            shap_mat = shap_values[0]
        else:
            shap_mat = shap_values

        mean_abs = np.mean(np.abs(shap_mat), axis=0)
        importance_pairs = sorted(
            zip(self._feature_columns, mean_abs.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )

        return GlobalFeatureImportance(
            feature_importances=importance_pairs,
            model_name=self._model_name,
            n_samples=len(X_sub),
        )
