"""
AquaMediAI — Prediction Service
=================================

Provides a typed, production-safe inference API for water-demand prediction.

IMPORTANT
---------
The predictor uses **identical** preprocessing to training:
  - The same FittedEncoders object (loaded from encoders.joblib)
  - The same engineer_features() function
  - The same ENGINEERED_FEATURE_COLS ordering

Deviation from this contract would silently corrupt predictions.

Usage
-----
    from pathlib import Path
    from app.ml.predictor import WaterDemandPredictor

    predictor = WaterDemandPredictor.from_artifacts(Path("data/models"))
    result = predictor.predict_single(farmer_row_dict)
    print(result.predicted_water_demand_m3)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.ml.feature_engineering import (
    ENGINEERED_FEATURE_COLS,
    TARGET_COL,
    FittedEncoders,
    engineer_features,
    get_feature_matrix,
)
from app.ml.trainer import (
    MODEL_VERSION,
    load_encoders,
    load_evaluation_results,
    load_model,
    validate_and_load_artifacts,
)

logger = logging.getLogger(__name__)

# Required raw input columns (before feature engineering)
REQUIRED_INPUT_COLS: List[str] = [
    "crop_type",
    "soil_type",
    "growth_stage",
    "season",
    "farm_area_hectares",
    "et0_mm_per_day",
    "kc_value",
    "etc_mm_per_day",
    "soil_whc_mm_per_m",
    "preferred_start_hour",
    "irrigation_window_hours",
    "flexibility_score",
    "urgency_score",
    "crop_stress_index",
    "temperature_celsius",
    "humidity_percent",
    "rainfall_mm",
]


@dataclass
class PredictionResult:
    """
    Typed result from the water-demand predictor.

    Attributes
    ----------
    predicted_water_demand_m3 : float
        Predicted daily water requirement in cubic metres.
    model_name : str
        Name of the model used for prediction.
    model_version : str
        Version string of the model.
    feature_values : dict
        Engineered feature values used for the prediction.
    input_summary : dict
        Summary of the raw input provided by the caller.
    warning : str or None
        Any warnings about input quality or clipping.
    """

    predicted_water_demand_m3: float
    model_name: str
    model_version: str = MODEL_VERSION
    feature_values: Dict[str, float] = field(default_factory=dict)
    input_summary: Dict[str, Any] = field(default_factory=dict)
    warning: Optional[str] = None
    shadow_agronomic_estimate_m3: Optional[float] = None
    shadow_comparison: Optional[Dict[str, Any]] = None
    shadow_candidate_v3_estimate_m3: Optional[float] = None
    shadow_candidate_v3_comparison: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "predicted_water_demand_m3": self.predicted_water_demand_m3,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_summary": self.input_summary,
            "warning": self.warning,
            "shadow_agronomic_estimate_m3": self.shadow_agronomic_estimate_m3,
            "shadow_comparison": self.shadow_comparison,
            "shadow_candidate_v3_estimate_m3": self.shadow_candidate_v3_estimate_m3,
            "shadow_candidate_v3_comparison": self.shadow_candidate_v3_comparison,
        }


class WaterDemandPredictor:
    """
    Stateful prediction service that wraps a trained model and its encoders.

    Use ``WaterDemandPredictor.from_artifacts()`` for normal usage.
    Use ``WaterDemandPredictor(model, encoders, model_name)`` for testing.

    Parameters
    ----------
    model : fitted sklearn/XGBoost model
        Any model with a .predict(X) method.
    encoders : FittedEncoders
        The exact same encoder object used during training.
    model_name : str
        Human-readable model identifier.
    """

    def __init__(
        self,
        model: Any,
        encoders: FittedEncoders,
        model_name: str = "Unknown",
    ) -> None:
        self._model = model
        self._encoders = encoders
        self._model_name = model_name
        self._candidate_v3_adapter = None
        logger.info("WaterDemandPredictor initialised (model=%s)", model_name)

    def _get_candidate_v3_adapter(self):
        if self._candidate_v3_adapter is None:
            try:
                from app.ml.candidate_v3_shadow_adapter import CandidateV3ShadowAdapter
                self._candidate_v3_adapter = CandidateV3ShadowAdapter()
            except Exception as exc:
                logger.warning("Could not initialize CandidateV3ShadowAdapter: %s", exc)
                self._candidate_v3_adapter = None
        return self._candidate_v3_adapter

    # ─── Factory constructor ───────────────────────────────────────────────────

    @classmethod
    def from_artifacts(
        cls,
        model_dir: Path,
        model_name: str = "XGBoost",
    ) -> "WaterDemandPredictor":
        """
        Load a predictor from persisted artefacts.

        Parameters
        ----------
        model_dir : Path
            Directory containing model .joblib and encoders.joblib.
        model_name : str
            'XGBoost' (default, primary) or 'RandomForest' (baseline).

        Returns
        -------
        WaterDemandPredictor
        """
        model, encoders, eval_results = validate_and_load_artifacts(
            model_dir, model_name=model_name
        )
        # Log which artifact was loaded for debugging
        logger.info(
            "WaterDemandPredictor loaded: model_name=%s from %s",
            model_name,
            model_dir,
        )
        return cls(model=model, encoders=encoders, model_name=model_name)

    # ─── Single-row prediction ─────────────────────────────────────────────────

    def predict_single(
        self,
        farmer_data: Dict[str, Any],
        enable_shadow_mode: Optional[bool] = None,
        enable_candidate_v3_shadow: Optional[bool] = None,
    ) -> PredictionResult:
        """
        Predict water demand for a single farmer/farm row.

        Parameters
        ----------
        farmer_data : dict
            Dictionary with raw input fields (see REQUIRED_INPUT_COLS).
            Missing optional fields are filled with sensible defaults.
        enable_shadow_mode : bool, optional
            Whether to calculate deterministic agronomic baseline in shadow mode.
            Defaults to app config `enable_shadow_mode`.
        enable_candidate_v3_shadow : bool, optional
            Whether to evaluate Candidate v3 in shadow mode.
            Defaults to app config `enable_candidate_v3_shadow`.

        Returns
        -------
        PredictionResult
        """
        validated, warning = self._validate_and_fill(farmer_data)
        row_df = pd.DataFrame([validated])
        prediction, feat_values = self._run_inference(row_df)

        pred_val = float(prediction[0])
        if pred_val < 5.0:
            clamp_msg = (
                f"Predicted water demand ({pred_val:.2f} m3/day) is below minimum physical threshold; "
                f"clamped to 5.00 m3/day."
            )
            warning = f"{warning}; {clamp_msg}" if warning else clamp_msg
            pred_val = 5.0

        # Determine shadow mode execution
        if enable_shadow_mode is None:
            try:
                from app.config import get_settings
                enable_shadow_mode = get_settings().enable_shadow_mode
            except Exception:
                enable_shadow_mode = True

        shadow_val: Optional[float] = None
        shadow_comp: Optional[Dict[str, Any]] = None
        if enable_shadow_mode:
            shadow_val, shadow_comp = self._compute_shadow_baseline(
                raw_data=farmer_data,
                legacy_prediction=pred_val,
            )

        # Determine Candidate v3 shadow mode execution
        if enable_candidate_v3_shadow is None:
            try:
                from app.config import get_settings
                enable_candidate_v3_shadow = get_settings().enable_candidate_v3_shadow
            except Exception:
                enable_candidate_v3_shadow = False

        cand_v3_val: Optional[float] = None
        cand_v3_comp: Optional[Dict[str, Any]] = None
        if enable_candidate_v3_shadow:
            try:
                adapter = self._get_candidate_v3_adapter()
                if adapter is not None:
                    raw_res = adapter.evaluate_shadow(
                        farmer_data=farmer_data,
                    )
                    cand_v3_comp = raw_res.as_dict() if hasattr(raw_res, "as_dict") else raw_res
                    cand_v3_val = cand_v3_comp.get("candidate_estimate_m3")
            except Exception as exc:
                logger.warning("Non-blocking Candidate v3 shadow error: %s", exc)
                cand_v3_comp = {
                    "status": "failed",
                    "candidate_version": "candidate_v3",
                    "error_reason": f"Shadow execution failed: {str(exc)}",
                    "reasons": [f"Shadow execution failed: {str(exc)}"],
                }

        return PredictionResult(
            predicted_water_demand_m3=pred_val,
            model_name=self._model_name,
            feature_values=feat_values,
            input_summary=self._build_input_summary(validated),
            warning=warning,
            shadow_agronomic_estimate_m3=shadow_val,
            shadow_comparison=shadow_comp,
            shadow_candidate_v3_estimate_m3=cand_v3_val,
            shadow_candidate_v3_comparison=cand_v3_comp,
        )

    def predict_batch(
        self,
        farmers: List[Dict[str, Any]],
        enable_shadow_mode: Optional[bool] = None,
        enable_candidate_v3_shadow: Optional[bool] = None,
    ) -> List[PredictionResult]:
        """
        Predict water demand for a batch of farmers.

        Parameters
        ----------
        farmers : list of dict
            Each dict is a raw farmer input (same schema as predict_single).
        enable_shadow_mode : bool, optional
            Whether to calculate deterministic agronomic baseline in shadow mode.
        enable_candidate_v3_shadow : bool, optional
            Whether to calculate Candidate v3 in shadow mode.

        Returns
        -------
        list of PredictionResult
        """
        results = []
        for farmer in farmers:
            results.append(
                self.predict_single(
                    farmer,
                    enable_shadow_mode=enable_shadow_mode,
                    enable_candidate_v3_shadow=enable_candidate_v3_shadow,
                )
            )
        return results

    def predict_from_dataframe(
        self,
        df: pd.DataFrame,
    ) -> np.ndarray:
        """
        Predict from a DataFrame directly (used internally and in tests).

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with required raw columns (before feature engineering).

        Returns
        -------
        np.ndarray
            Predicted water demand values (m³/day), shape (n_samples,).
        """
        eng_df = engineer_features(df, self._encoders)
        X, _ = get_feature_matrix(eng_df, require_target=False)
        preds = self._model.predict(X).astype(float)
        return np.maximum(5.0, preds)

    # ─── Internal helpers ──────────────────────────────────────────────────────

    def _run_inference(
        self, row_df: pd.DataFrame
    ) -> tuple[np.ndarray, Dict[str, float]]:
        """Apply feature engineering and run model inference."""
        eng_df = engineer_features(row_df, self._encoders)

        # Extract feature matrix (same column order as training)
        X, _ = get_feature_matrix(eng_df, require_target=False)

        # Predict
        y_pred = self._model.predict(X).astype(float)

        # Collect feature values for explainability / audit
        feat_values: Dict[str, float] = {}
        for i, col in enumerate(ENGINEERED_FEATURE_COLS):
            feat_values[col] = float(X[0, i])

        return y_pred, feat_values

    def _validate_and_fill(
        self, farmer_data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Validate input dict and fill missing optional fields with defaults.

        Returns
        -------
        (filled_dict, warning_message_or_None)
        """
        warnings: List[str] = []
        data = dict(farmer_data)

        # ── Defaults for optional / missing fields ─────────────────────────
        defaults: Dict[str, Any] = {
            "soil_type": "loam",
            "growth_stage": "vegetative",
            "season": "kharif",
            "soil_whc_mm_per_m": 125.0,
            "preferred_start_hour": 6,
            "irrigation_window_hours": 8,
            "flexibility_score": 0.5,
            "urgency_score": 0.5,
            "crop_stress_index": 0.5,
            "humidity_percent": 60.0,
            "rainfall_mm": 0.0,
            "temperature_celsius": 28.0,
            # is_synthetic is required by engineer_features indirectly via
            # validate_dataframe; add a safe default
            "is_synthetic": True,
            "farmer_id": "INFER_ROW",
            "scenario_type": "normal_water",
        }
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
                if k not in ("is_synthetic", "farmer_id", "scenario_type"):
                    warnings.append(f"Missing '{k}' — using default: {v}")

        # ── Critical fields: must be provided ─────────────────────────────
        critical = ["crop_type", "farm_area_hectares", "et0_mm_per_day",
                    "kc_value", "etc_mm_per_day"]
        missing_critical = [c for c in critical if c not in data or data[c] is None]
        if missing_critical:
            raise ValueError(
                f"Missing required input fields: {missing_critical}. "
                "These cannot be inferred automatically."
            )

        # ── Range clipping with warnings ──────────────────────────────────
        if data.get("farm_area_hectares", 1) <= 0:
            data["farm_area_hectares"] = 0.1
            warnings.append("farm_area_hectares was ≤0; clipped to 0.1 ha.")
        if data.get("flexibility_score", 0.5) > 1.0:
            data["flexibility_score"] = 1.0
            warnings.append("flexibility_score clamped to 1.0.")
        if data.get("flexibility_score", 0.5) < 0.0:
            data["flexibility_score"] = 0.0
            warnings.append("flexibility_score clamped to 0.0.")

        warning_str = " | ".join(warnings) if warnings else None
        return data, warning_str

    @staticmethod
    def _build_input_summary(data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a clean summary dict for audit / response."""
        return {
            "crop_type": data.get("crop_type"),
            "soil_type": data.get("soil_type"),
            "growth_stage": data.get("growth_stage"),
            "season": data.get("season"),
            "farm_area_hectares": data.get("farm_area_hectares"),
            "et0_mm_per_day": data.get("et0_mm_per_day"),
            "kc_value": data.get("kc_value"),
            "temperature_celsius": data.get("temperature_celsius"),
            "rainfall_mm": data.get("rainfall_mm"),
        }

    def _compute_shadow_baseline(
        self,
        raw_data: Dict[str, Any],
        legacy_prediction: float,
        application_efficiency: float = 0.70,
    ) -> tuple[Optional[float], Dict[str, Any]]:
        """
        Compute deterministic agronomic baseline (FAO-56 + USDA-SCS) in shadow mode.

        Validates all required physical inputs strictly without fabricating missing data.
        Returns:
            (shadow_agronomic_estimate_m3_or_None, shadow_comparison_dict)
        """
        errors: List[str] = []

        # Validate required physical variables from caller input
        farm_area = raw_data.get("farm_area_hectares")
        et0 = raw_data.get("et0_mm_per_day")
        kc = raw_data.get("kc_value")
        rain = raw_data.get("rainfall_mm")

        if farm_area is None:
            errors.append("farm_area_hectares is required and missing.")
        elif not isinstance(farm_area, (int, float)) or farm_area <= 0:
            errors.append(f"farm_area_hectares must be > 0, got {farm_area}")

        if et0 is None:
            errors.append("et0_mm_per_day is required and missing.")
        elif not isinstance(et0, (int, float)) or et0 < 0:
            errors.append(f"et0_mm_per_day must be >= 0, got {et0}")

        if kc is None:
            errors.append("kc_value is required and missing.")
        elif not isinstance(kc, (int, float)) or kc <= 0:
            errors.append(f"kc_value must be > 0, got {kc}")

        if rain is None:
            errors.append("rainfall_mm is required and missing.")
        elif not isinstance(rain, (int, float)) or rain < 0:
            errors.append(f"rainfall_mm must be >= 0, got {rain}")

        if errors:
            return None, {
                "status": "unavailable",
                "agronomic_demand_m3": None,
                "legacy_prediction_m3": round(legacy_prediction, 2),
                "difference_m3": None,
                "difference_percent": None,
                "method": "FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall",
                "application_efficiency": application_efficiency,
                "is_empirical_error": False,
                "input_validation": {
                    "is_valid": False,
                    "errors": errors,
                },
                "provenance_note": (
                    "Legacy ML models (RandomForest, XGBoost) were trained on synthetic data. "
                    "The agronomic estimate is a deterministic physical calculation, NOT measured delivery."
                ),
                "disclaimer": (
                    "Differences between legacy predictions and deterministic baseline are comparison metrics, "
                    "NOT empirical model error, because no measured real-world delivery ground truth is available."
                ),
            }

        try:
            from app.ml.agronomic_baseline import DeterministicAgronomicBaseline

            baseline_engine = DeterministicAgronomicBaseline(
                default_application_efficiency=application_efficiency
            )
            res = baseline_engine.calculate_daily_demand(
                farm_area_hectares=float(farm_area),
                et0_mm_per_day=float(et0),
                kc_value=float(kc),
                rainfall_mm=float(rain),
                application_efficiency=application_efficiency,
            )
            agronomic_m3 = round(res.volumetric_demand_m3_per_day, 2)
            diff_m3 = round(legacy_prediction - agronomic_m3, 2)
            diff_pct = (
                round((diff_m3 / agronomic_m3) * 100.0, 2)
                if agronomic_m3 > 0
                else (0.0 if legacy_prediction == 0 else None)
            )

            return agronomic_m3, {
                "status": "available",
                "agronomic_demand_m3": agronomic_m3,
                "legacy_prediction_m3": round(legacy_prediction, 2),
                "difference_m3": diff_m3,
                "difference_percent": diff_pct,
                "method": res.method,
                "application_efficiency": application_efficiency,
                "is_empirical_error": False,
                "input_validation": {
                    "is_valid": True,
                    "errors": [],
                },
                "provenance_note": (
                    "Legacy ML models (RandomForest, XGBoost) were trained on synthetic data. "
                    "The agronomic estimate is a deterministic physical calculation, NOT measured delivery."
                ),
                "disclaimer": (
                    "Differences between legacy predictions and deterministic baseline are comparison metrics, "
                    "NOT empirical model error, because no measured real-world delivery ground truth is available."
                ),
            }
        except Exception as exc:
            return None, {
                "status": "unavailable",
                "agronomic_demand_m3": None,
                "legacy_prediction_m3": round(legacy_prediction, 2),
                "difference_m3": None,
                "difference_percent": None,
                "method": "FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall",
                "application_efficiency": application_efficiency,
                "is_empirical_error": False,
                "input_validation": {
                    "is_valid": False,
                    "errors": [f"Calculation error: {str(exc)}"],
                },
                "provenance_note": (
                    "Legacy ML models (RandomForest, XGBoost) were trained on synthetic data. "
                    "The agronomic estimate is a deterministic physical calculation, NOT measured delivery."
                ),
                "disclaimer": (
                    "Differences between legacy predictions and deterministic baseline are comparison metrics, "
                    "NOT empirical model error, because no measured real-world delivery ground truth is available."
                ),
            }

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def feature_columns(self) -> List[str]:
        return list(ENGINEERED_FEATURE_COLS)
