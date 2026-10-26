"""
AquaMediAI — Candidate v3 Two-Stage Model Shadow Adapter
========================================================

Integrates Candidate v3 as an optional, non-blocking shadow evaluator
alongside the live AquaMediAI prediction engine.

Mandatory Safety Rules:
-----------------------
1. NON-BLOCKING & FAIL-SAFE:
   Never throws uncaught exceptions that could interrupt live production predictions.
2. NO DISPATCH IMPACT:
   Shadow outputs are purely diagnostic and NEVER determine canal water allocation,
   irrigation dispatch, or farmer negotiation outcomes.
3. FEATURE-AVAILABILITY CONTRACT:
   - Historical analysis uses observed rainfall for completed days.
   - Forward morning scheduling MUST use forecasted rainfall, or documented antecedent fallback.
   - Never silently substitutes future observed rainfall for a forecast.
4. CONFIGURABLE:
   Disabled by default (ENABLE_CANDIDATE_V3_SHADOW=False).
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from app.config import get_settings
from app.ml.agronomic_baseline import DeterministicAgronomicBaseline
from app.ml.crop_registry import CropRegistry

logger = logging.getLogger(__name__)


class RainfallInputMode(str, Enum):
    """Operational mode defining how rainfall inputs are sourced."""

    OBSERVED_HISTORICAL = "observed_historical"
    FORECAST_FORWARD = "forecast_forward"
    FALLBACK_ANTECEDENT = "fallback_antecedent"


@dataclass(frozen=True)
class CandidateV3ShadowResult:
    """Detailed result of Candidate v3 shadow evaluation."""

    status: str  # "available" or "unavailable"
    candidate_version: str
    candidate_estimate_m3: Optional[float]
    deterministic_reference_m3: Optional[float]
    absolute_disagreement_m3: Optional[float]
    signed_disagreement_m3: Optional[float]
    input_mode: str
    rainfall_source: str
    rainfall_mm_used: Optional[float]
    is_valid: bool
    reasons: List[str]
    disclaimer: str

    @property
    def error_reason(self) -> Optional[str]:
        return "; ".join(self.reasons) if self.reasons else None

    @property
    def reference_estimate_m3(self) -> Optional[float]:
        return self.deterministic_reference_m3

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["reference_estimate_m3"] = self.deterministic_reference_m3
        d["error_reason"] = self.error_reason
        return d

    def as_dict(self) -> Dict[str, Any]:
        return self.to_dict()


class CandidateV3ShadowAdapter:
    """
    Adapter for loading and evaluating Candidate v3 in shadow mode.
    """

    def __init__(self, candidate_dir: Optional[Path | str] = None) -> None:
        settings = get_settings()
        self.candidate_dir = Path(candidate_dir) if candidate_dir else settings.candidate_v3_dir_path
        self.classifier: Optional[Any] = None
        self.regressor: Optional[Any] = None
        self.preprocessor: Optional[Any] = None
        self.decision_threshold: float = 0.20
        self.zero_threshold_val: float = 0.001
        self.feature_schema: Optional[Dict[str, Any]] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None

        self._load_artifacts()

    @classmethod
    def load(cls, candidate_dir: Optional[Path | str] = None) -> "CandidateV3ShadowAdapter":
        """Factory constructor for candidate v3 adapter."""
        return cls(candidate_dir=candidate_dir)

    @property
    def is_ready(self) -> bool:
        """Check if adapter is loaded and ready."""
        return self.is_loaded and self.classifier is not None and self.regressor is not None and self.preprocessor is not None

    @property
    def version(self) -> str:
        """Model version identifier."""
        return "candidate_v3_twostage_xgb"

    @property
    def zero_threshold(self) -> float:
        """Stage 1 decision threshold."""
        return self.decision_threshold

    @property
    def feature_cols(self) -> List[str]:
        """Engineered input feature list."""
        if self.feature_schema:
            if "features" in self.feature_schema:
                return list(self.feature_schema["features"])
            num = self.feature_schema.get("numeric_features", [])
            cat = self.feature_schema.get("categorical_features", [])
            return list(num) + list(cat)
        return []

    def _load_artifacts(self) -> None:
        """Validate and load Candidate v3 artifacts."""
        try:
            if not self.candidate_dir.exists():
                self.load_error = f"Candidate v3 directory not found at: {self.candidate_dir}"
                logger.warning("CandidateV3ShadowAdapter: %s", self.load_error)
                return

            meta_file = self.candidate_dir / "candidate_metadata.json"
            cfg_file = self.candidate_dir / "two_stage_config.json"
            schema_file = self.candidate_dir / "feature_schema.json"
            clf_file = self.candidate_dir / "candidate_v3_classifier.joblib"
            reg_file = self.candidate_dir / "candidate_v3_regressor.joblib"
            prep_file = self.candidate_dir / "candidate_v3_preprocessor.joblib"

            required_files = [meta_file, cfg_file, schema_file, clf_file, reg_file, prep_file]
            missing = [f.name for f in required_files if not f.exists()]
            if missing:
                self.load_error = f"Missing candidate v3 artifact files: {missing}"
                logger.warning("CandidateV3ShadowAdapter: %s", self.load_error)
                return

            # Validate metadata version
            with open(meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            if self.metadata.get("version") != "candidate_v3":
                self.load_error = f"Unexpected model version: {self.metadata.get('version')}"
                logger.warning("CandidateV3ShadowAdapter: %s", self.load_error)
                return

            # Load config and threshold
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.decision_threshold = float(cfg.get("decision_threshold", 0.20))
            self.zero_threshold_val = float(cfg.get("zero_threshold", 0.001))

            # Load feature schema
            with open(schema_file, "r", encoding="utf-8") as f:
                self.feature_schema = json.load(f)

            # Load fitted models
            self.classifier = joblib.load(clf_file)
            self.regressor = joblib.load(reg_file)
            self.preprocessor = joblib.load(prep_file)

            self.is_loaded = True
            logger.info(
                "CandidateV3ShadowAdapter loaded successfully from %s (threshold tau=%.2f)",
                self.candidate_dir,
                self.decision_threshold,
            )
        except Exception as exc:
            self.load_error = f"Failed to load candidate v3 artifacts: {str(exc)}"
            self.is_loaded = False
            logger.warning("CandidateV3ShadowAdapter load failure: %s", exc)

    def evaluate(
        self,
        farmer_data: Dict[str, Any],
        application_efficiency: float = 0.70,
        input_mode_override: Optional[str] = None,
        allow_antecedent_fallback: bool = True,
    ) -> CandidateV3ShadowResult:
        """Alias for evaluate_shadow returning CandidateV3ShadowResult object."""
        return self.evaluate_shadow(
            farmer_data=farmer_data,
            application_efficiency=application_efficiency,
            input_mode_override=input_mode_override,
            allow_antecedent_fallback=allow_antecedent_fallback,
        )

    def evaluate_shadow(
        self,
        farmer_data: Dict[str, Any],
        application_efficiency: float = 0.70,
        input_mode_override: Optional[str] = None,
        allow_antecedent_fallback: bool = True,
    ) -> CandidateV3ShadowResult:
        """
        Evaluate candidate v3 in shadow mode against farmer inputs and deterministic reference.
        Never raises an uncaught exception.
        """
        disclaimer = (
            "Candidate v3 shadow output is an offline research surrogate approximating theoretical "
            "FAO-56 calculations. It does NOT represent measured field deliveries and does NOT control dispatch."
        )

        if not self.is_ready:
            return CandidateV3ShadowResult(
                status="unavailable",
                candidate_version=self.version,
                candidate_estimate_m3=None,
                deterministic_reference_m3=None,
                absolute_disagreement_m3=None,
                signed_disagreement_m3=None,
                input_mode="unresolved",
                rainfall_source="none",
                rainfall_mm_used=None,
                is_valid=False,
                reasons=[f"Candidate v3 artifacts not loaded: {self.load_error}"],
                disclaimer=disclaimer,
            )

        reasons: List[str] = []

        # ── 1. Resolve Rainfall Availability Contract ──────────────────────────
        raw_mode = str(input_mode_override or farmer_data.get("rainfall_input_mode") or "").strip().lower()
        rain_forecast = farmer_data.get("rainfall_forecast_mm")
        rain_observed = farmer_data.get("rainfall_observed_mm")
        rain_generic = farmer_data.get("rainfall_mm")

        # Map mode synonyms
        if raw_mode in ("historical", "observed", "observed_historical"):
            input_mode = RainfallInputMode.OBSERVED_HISTORICAL.value
        elif raw_mode in ("forward", "forward_morning", "forecast_forward"):
            input_mode = RainfallInputMode.FORECAST_FORWARD.value
        elif raw_mode in ("fallback", "antecedent", "fallback_antecedent"):
            input_mode = RainfallInputMode.FALLBACK_ANTECEDENT.value
        elif raw_mode:
            input_mode = raw_mode
        else:
            if rain_forecast is not None:
                input_mode = RainfallInputMode.FORECAST_FORWARD.value
            elif rain_observed is not None:
                input_mode = RainfallInputMode.OBSERVED_HISTORICAL.value
            elif rain_generic is not None and farmer_data.get("is_historical_analysis", False):
                input_mode = RainfallInputMode.OBSERVED_HISTORICAL.value
            else:
                input_mode = RainfallInputMode.FALLBACK_ANTECEDENT.value

        rainfall_used: Optional[float] = None
        rainfall_source: str = "none"

        if input_mode == RainfallInputMode.OBSERVED_HISTORICAL.value:
            if rain_observed is not None:
                rainfall_used = float(rain_observed)
                rainfall_source = "rainfall_observed_mm"
            elif rain_generic is not None:
                rainfall_used = float(rain_generic)
                rainfall_source = "rainfall_mm"
            else:
                reasons.append("Historical mode requires observed rainfall (rainfall_observed_mm or rainfall_mm).")

        elif input_mode == RainfallInputMode.FORECAST_FORWARD.value:
            if rain_forecast is not None:
                rainfall_used = float(rain_forecast)
                rainfall_source = "rainfall_forecast_mm"
            elif allow_antecedent_fallback:
                lag1 = farmer_data.get("rainfall_lag1_mm")
                rainfall_used = float(lag1) if lag1 is not None else 0.0
                rainfall_source = "rainfall_lag1_mm (antecedent fallback)"
                reasons.append("Forward mode running without forecast; using documented antecedent fallback.")
            else:
                reasons.append(
                    "Forward scheduling mode requires a weather forecast (rainfall_forecast_mm). "
                    "Missing rainfall forecast. Future observed rainfall cannot be assumed."
                )

        elif input_mode == RainfallInputMode.FALLBACK_ANTECEDENT.value:
            lag1 = farmer_data.get("rainfall_lag1_mm")
            rainfall_used = float(lag1) if lag1 is not None else 0.0
            rainfall_source = "rainfall_lag1_mm (antecedent fallback)"
            reasons.append("Forward mode running without forecast; using documented antecedent fallback.")

        else:
            reasons.append(f"Unrecognized rainfall_input_mode: '{input_mode}'.")

        # ── 2. Validate Core Agronomic Inputs ──────────────────────────────────
        crop_type = str(farmer_data.get("crop_type", "")).strip().lower()
        farm_area = farmer_data.get("farm_area_hectares")
        growth_stage = str(farmer_data.get("growth_stage", "vegetative")).strip().lower()
        season = str(farmer_data.get("season", "kharif")).strip().lower()

        # Check registered crops
        registered_crops = [c.crop_id for c in CropRegistry.list_crops(include_paddy=False)]
        if crop_type not in registered_crops:
            reasons.append(f"Crop '{crop_type}' is not supported by Candidate v3 registry (valid: {registered_crops}).")

        if farm_area is None or float(farm_area) <= 0.0:
            reasons.append(f"farm_area_hectares must be > 0, got {farm_area}")

        # Check temperature & humidity
        temp = farmer_data.get("temperature_celsius", 28.0)
        humidity = farmer_data.get("humidity_percent", 60.0)
        try:
            temp = float(temp)
            if not (-5.0 <= temp <= 55.0):
                reasons.append(f"temperature_celsius out of physical range: {temp}")
        except (ValueError, TypeError):
            reasons.append(f"Invalid temperature_celsius: {temp}")

        try:
            humidity = float(humidity)
            if not (0.0 <= humidity <= 100.0):
                reasons.append(f"humidity_percent out of physical range: {humidity}")
        except (ValueError, TypeError):
            reasons.append(f"Invalid humidity_percent: {humidity}")

        # Return unavailable if mandatory inputs are invalid
        if any("requires" in r or "not supported" in r or "must be > 0" in r or "out of physical range" in r for r in reasons):
            return CandidateV3ShadowResult(
                status="unavailable",
                candidate_version=self.version,
                candidate_estimate_m3=None,
                deterministic_reference_m3=None,
                absolute_disagreement_m3=None,
                signed_disagreement_m3=None,
                input_mode=str(input_mode),
                rainfall_source=rainfall_source,
                rainfall_mm_used=rainfall_used,
                is_valid=False,
                reasons=reasons,
                disclaimer=disclaimer,
            )

        # ── 3. Run Inference & Comparison ──────────────────────────────────────
        try:
            # A. Authoritative Deterministic Reference
            et0 = float(farmer_data.get("et0_mm_per_day", 4.0))
            kc = float(farmer_data.get("kc_value", 1.0))
            rain_val = rainfall_used if rainfall_used is not None else 0.0

            baseline_engine = DeterministicAgronomicBaseline(default_application_efficiency=application_efficiency)
            det_res = baseline_engine.calculate_daily_demand(
                farm_area_hectares=float(farm_area),
                et0_mm_per_day=et0,
                kc_value=kc,
                rainfall_mm=rain_val,
                application_efficiency=application_efficiency,
            )
            det_m3 = round(det_res.volumetric_demand_m3_per_day, 2)

            # B. Candidate v3 Two-Stage Model Inference
            # Synthesize 21 input features matching Candidate v3 schema
            # Compute VPD proxy from temperature & relative humidity
            es = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
            ea = es * (humidity / 100.0)
            vpd = max(0.01, es - ea)
            temp_vpd = temp * vpd

            rain_lag1 = float(farmer_data.get("rainfall_lag1_mm", 0.0))
            rain_3d = float(farmer_data.get("rainfall_antecedent_3d_mm", rain_lag1))
            rain_7d = float(farmer_data.get("rainfall_antecedent_7d_mm", rain_3d))
            rain_ratio = rain_3d / (rain_7d + 1.0)

            doy = int(farmer_data.get("day_of_year", 180))
            doy_sin = math.sin(2.0 * math.pi * doy / 365.25)
            doy_cos = math.cos(2.0 * math.pi * doy / 365.25)

            feature_dict = {
                "temperature_celsius": temp,
                "diurnal_temp_range_celsius": float(farmer_data.get("diurnal_temp_range_celsius", 10.0)),
                "humidity_percent": humidity,
                "wind_speed_m_per_s": float(farmer_data.get("wind_speed_m_per_s", 2.0)),
                "solar_radiation_mj_per_m2": float(farmer_data.get("solar_radiation_mj_per_m2", 18.0)),
                "vpd_proxy_kpa": vpd,
                "rainfall_lag1_mm": rain_lag1,
                "rainfall_antecedent_3d_mm": rain_3d,
                "rainfall_antecedent_7d_mm": rain_7d,
                "temp_rolling_mean_3d_celsius": float(farmer_data.get("temp_rolling_mean_3d_celsius", temp)),
                "temp_rolling_mean_7d_celsius": float(farmer_data.get("temp_rolling_mean_7d_celsius", temp)),
                "solar_rad_rolling_mean_3d": float(farmer_data.get("solar_rad_rolling_mean_3d", 18.0)),
                "doy_sin": doy_sin,
                "doy_cos": doy_cos,
                "farm_area_hectares": float(farm_area),
                "rainfall_mm": rain_val,
                "temp_vpd_interaction": temp_vpd,
                "antecedent_rain_ratio": rain_ratio,
                "crop_type": crop_type,
                "growth_stage": growth_stage,
                "season": season,
            }

            df_input = pd.DataFrame([feature_dict])
            X_trans = self.preprocessor.transform(df_input)

            # Two-stage decision logic
            # Stage 1: Zero-demand probability
            prob_zero = self.classifier.predict_proba(X_trans)[0, 1]
            if prob_zero >= self.decision_threshold:
                cand_net_m3 = 0.0
            else:
                raw_pred = self.regressor.predict(X_trans)[0]
                cand_net_m3 = float(np.clip(raw_pred, a_min=0.0, a_max=None))

            # Scale net demand to gross volumetric demand using application efficiency
            cand_gross_m3 = round(cand_net_m3 / application_efficiency, 2)
            abs_disagreement = round(abs(cand_gross_m3 - det_m3), 2)
            signed_disagreement = round(cand_gross_m3 - det_m3, 2)

            # Structured logging for model disagreement > 10 m3/day
            if abs_disagreement > 10.0:
                logger.info(
                    "Candidate v3 Shadow Disagreement: crop=%s, stage=%s, area=%.1f, cand=%.2f, det=%.2f, diff=%.2f m3/day, rain=%.2f mm",
                    crop_type,
                    growth_stage,
                    float(farm_area),
                    cand_gross_m3,
                    det_m3,
                    abs_disagreement,
                    rain_val,
                )

            return CandidateV3ShadowResult(
                status="available",
                candidate_version=self.version,
                candidate_estimate_m3=cand_gross_m3,
                deterministic_reference_m3=det_m3,
                absolute_disagreement_m3=abs_disagreement,
                signed_disagreement_m3=signed_disagreement,
                input_mode=str(input_mode),
                rainfall_source=rainfall_source,
                rainfall_mm_used=rain_val,
                is_valid=True,
                reasons=reasons,
                disclaimer=disclaimer,
            )

        except Exception as exc:
            logger.warning("Candidate v3 shadow evaluation unexpected error: %s", exc)
            return CandidateV3ShadowResult(
                status="unavailable",
                candidate_version=self.version,
                candidate_estimate_m3=None,
                deterministic_reference_m3=None,
                absolute_disagreement_m3=None,
                signed_disagreement_m3=None,
                input_mode=str(input_mode),
                rainfall_source=rainfall_source,
                rainfall_mm_used=rainfall_used,
                is_valid=False,
                reasons=[f"Evaluation failure: {str(exc)}"],
                disclaimer=disclaimer,
            )
