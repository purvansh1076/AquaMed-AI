"""
AquaMediAI — Candidate Feature Definitions & Leakage Audit for Phase 7
======================================================================

Defines the feature schema, scikit-learn preprocessing pipelines, and
automated leakage verification for the Phase 7 candidate models.

Design Rules:
-------------
1. NO TARGET LEAKAGE:
   Excluded:
     - net_irrigation_m3_per_day (target)
     - net_irrigation_depth_mm (depth equivalent of target)
     - etc_mm_per_day (direct component of target)
     - effective_precipitation_mm (direct component of target)
     - area_x_etc (tautological duplicate)
     - Agent game-state variables (flexibility_score, urgency_score, etc.)

2. DEFENSIBLE FEATURES:
   Uses observed meteorological features (temperature, humidity, wind, radiation,
   VPD, antecedent rainfall lags), seasonal harmonics (doy_sin, doy_cos),
   crop identity (crop_type), and phenological stage (growth_stage), plus farm area.

3. REPRODUCIBLE PREPROCESSOR:
   Fits encoders strictly on training data; transforms validation and test sets.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.leakage_audit import LeakageAuditReport, audit_feature_leakage

# ── Primary Defensible Feature Set ─────────────────────────────────────────────

NUMERIC_FEATURES: List[str] = [
    # Atmospheric state
    "temperature_celsius",
    "diurnal_temp_range_celsius",
    "humidity_percent",
    "wind_speed_m_per_s",
    "solar_radiation_mj_per_m2",
    "vpd_proxy_kpa",
    # Antecedent hydrology (strictly causal)
    "rainfall_lag1_mm",
    "rainfall_antecedent_3d_mm",
    "rainfall_antecedent_7d_mm",
    # Thermal & radiation persistence
    "temp_rolling_mean_3d_celsius",
    "temp_rolling_mean_7d_celsius",
    "solar_rad_rolling_mean_3d",
    # Cyclical calendar harmonics
    "doy_sin",
    "doy_cos",
    # Farm plot scale
    "farm_area_hectares",
]

CATEGORICAL_FEATURES: List[str] = [
    "crop_type",
    "growth_stage",
]

ALL_CANDIDATE_FEATURES: List[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Forbidden features that MUST NOT be used in candidate training
FORBIDDEN_LEAKAGE_FEATURES: List[str] = [
    "net_irrigation_m3_per_day",
    "net_irrigation_depth_mm",
    "etc_mm_per_day",
    "effective_precipitation_mm",
    "area_x_etc",
    "etc_x_area",
    "sample_key",
    "date",
    "date_str",
    "data_quality_status",
]


@dataclass(frozen=True)
class FeatureSchemaManifest:
    """Documented schema of all input features for candidate models."""

    target_column: str
    target_units: str
    numeric_features: List[str]
    categorical_features: List[str]
    forbidden_features_verified_absent: bool
    leakage_audit_verdict: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_candidate_preprocessor() -> ColumnTransformer:
    """
    Build a scikit-learn ColumnTransformer for candidate feature preprocessing.
    Numeric features: StandardScaler.
    Categorical features: OneHotEncoder(sparse_output=False, handle_unknown='ignore').
    """
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(sparse_output=False, handle_unknown="ignore")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def verify_feature_safety(
    df: pd.DataFrame,
    features: List[str] = ALL_CANDIDATE_FEATURES,
    target_col: str = "net_irrigation_m3_per_day",
) -> LeakageAuditReport:
    """
    Run automated leakage audit and verify that no forbidden columns are present in features.
    """
    for forbidden in FORBIDDEN_LEAKAGE_FEATURES:
        if forbidden in features:
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: Feature set includes forbidden column '{forbidden}'!")

    report = audit_feature_leakage(
        df=df,
        feature_columns=features,
        target_column=target_col,
        correlation_threshold=0.98,
    )
    return report
