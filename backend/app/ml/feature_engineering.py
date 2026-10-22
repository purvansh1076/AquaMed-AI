"""
AquaMediAI — Feature Engineering Pipeline
==========================================

Transforms raw synthetic data columns into ML-ready features.

Responsibilities
----------------
1. Ordinal encoding of growth stages (agronomically ordered).
2. Label encoding of crop types, soil types, seasons.
3. Computation of derived interaction features.
4. Data validation (range checks, missing-value detection).
5. Train/validation/test split with stratification by scenario type.
6. Reproducible random state via seed parameter.

Design Notes
------------
- Encoders are fitted only on training data and applied to val/test splits
  to prevent data leakage.
- The OrdinalEncoder for growth_stage preserves the biological order:
  germination < vegetative < flowering < maturity < harvest
- All encoders are returned from ``fit_encoders()`` so they can be
  persisted alongside the model artefacts (Phase 2).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

logger = logging.getLogger(__name__)

# ─── Ordered growth stages ────────────────────────────────────────────────────
GROWTH_STAGE_ORDER: List[str] = [
    "germination",
    "vegetative",
    "flowering",
    "maturity",
    "harvest",
]

# ─── Categorical columns that need encoding ───────────────────────────────────
CATEGORICAL_LABEL_COLS: List[str] = ["crop_type", "soil_type", "season"]
ORDINAL_COL: str = "growth_stage"

# ─── Feature columns produced by this module ─────────────────────────────────
ENGINEERED_FEATURE_COLS: List[str] = [
    # Raw numeric
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
    # Encoded categoricals
    "crop_type_encoded",
    "soil_type_encoded",
    "growth_stage_encoded",
    "season_encoded",
    # Derived interaction features
    "area_x_etc",            # farm_area_hectares × etc_mm_per_day
    "urgency_x_stress",      # urgency_score × crop_stress_index
    "et0_x_kc",              # et0_mm_per_day × kc_value (= etc, cross-check)
    "rain_deficit",          # max(0, etc_mm_per_day - rainfall_mm)
    "flexibility_window",    # flexibility_score × irrigation_window_hours
]

TARGET_COL: str = "water_demand_m3"


@dataclass
class FittedEncoders:
    """
    Container for fitted encoders.
    Should be persisted alongside model artefacts to ensure inference
    uses the same encoding as training.
    """
    label_encoders: Dict[str, LabelEncoder] = field(default_factory=dict)
    growth_stage_encoder: Optional[OrdinalEncoder] = None
    feature_columns: List[str] = field(default_factory=list)


def fit_encoders(df: pd.DataFrame) -> FittedEncoders:
    """
    Fit label/ordinal encoders on the provided DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Training data (should be TRAIN split only to prevent leakage).

    Returns
    -------
    FittedEncoders
        Container of fitted encoder objects.
    """
    encoders = FittedEncoders()

    # ── Label encoders for unordered categoricals ──────────────────────────────
    for col in CATEGORICAL_LABEL_COLS:
        if col not in df.columns:
            logger.warning("Column '%s' not found in DataFrame — skipping encoder.", col)
            continue
        le = LabelEncoder()
        le.fit(df[col].astype(str))
        encoders.label_encoders[col] = le
        logger.debug("Fitted LabelEncoder for '%s': classes=%s", col, list(le.classes_))

    # ── Ordinal encoder for growth stage ──────────────────────────────────────
    if ORDINAL_COL in df.columns:
        oe = OrdinalEncoder(
            categories=[GROWTH_STAGE_ORDER],
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
        oe.fit(df[[ORDINAL_COL]])
        encoders.growth_stage_encoder = oe
        logger.debug("Fitted OrdinalEncoder for '%s'.", ORDINAL_COL)

    encoders.feature_columns = ENGINEERED_FEATURE_COLS
    return encoders


def apply_encoders(df: pd.DataFrame, encoders: FittedEncoders) -> pd.DataFrame:
    """
    Apply pre-fitted encoders to a DataFrame (train, val, or test split).

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame (as produced by data_generator).
    encoders : FittedEncoders
        Fitted encoder container from ``fit_encoders()``.

    Returns
    -------
    pd.DataFrame
        New DataFrame with ``_encoded`` columns appended.
    """
    df = df.copy()

    # ── Label encode unordered categoricals ────────────────────────────────────
    for col, le in encoders.label_encoders.items():
        if col not in df.columns:
            logger.warning("Column '%s' missing at inference — filling with 0.", col)
            df[f"{col}_encoded"] = 0
            continue
        # Handle unseen labels gracefully
        known = set(le.classes_)
        df[col] = df[col].astype(str).apply(
            lambda x: x if x in known else le.classes_[0]
        )
        df[f"{col}_encoded"] = le.transform(df[col])

    # ── Ordinal encode growth stage ────────────────────────────────────────────
    if encoders.growth_stage_encoder is not None and ORDINAL_COL in df.columns:
        df["growth_stage_encoded"] = (
            encoders.growth_stage_encoder.transform(df[[ORDINAL_COL]])
            .astype(float)
            .ravel()
        )
    elif "growth_stage_encoded" not in df.columns:
        df["growth_stage_encoded"] = 0.0

    return df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived interaction features.

    These features help ML models capture non-linear relationships that
    are agronomically meaningful.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with base numeric columns already present.

    Returns
    -------
    pd.DataFrame
        DataFrame with interaction columns appended.
    """
    df = df.copy()

    # area × ETc → stronger predictor than each alone
    df["area_x_etc"] = df["farm_area_hectares"] * df["etc_mm_per_day"]

    # urgency × stress → combined pressure signal
    df["urgency_x_stress"] = df["urgency_score"] * df["crop_stress_index"]

    # ET₀ × Kc = ETc cross-check feature
    df["et0_x_kc"] = df["et0_mm_per_day"] * df["kc_value"]

    # Rainfall deficit: net water needed after rain
    df["rain_deficit"] = (df["etc_mm_per_day"] - df["rainfall_mm"]).clip(lower=0.0)

    # Flexibility × window → scheduling latitude
    df["flexibility_window"] = df["flexibility_score"] * df["irrigation_window_hours"]

    return df


def engineer_features(
    df: pd.DataFrame,
    encoders: FittedEncoders,
) -> pd.DataFrame:
    """
    Apply the full feature engineering pipeline to a DataFrame.

    Combines encoding + interaction features. Use this for both
    training and inference.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from the data generator.
    encoders : FittedEncoders
        Pre-fitted encoders (from ``fit_encoders()`` on training data).

    Returns
    -------
    pd.DataFrame
        Feature-engineered DataFrame.
    """
    df = apply_encoders(df, encoders)
    df = add_interaction_features(df)
    return df


def get_feature_matrix(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    require_target: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract X (feature matrix) and y (target vector) from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Feature-engineered DataFrame (output of ``engineer_features()``).
    feature_cols : list of str, optional
        Override list of feature column names. Defaults to ENGINEERED_FEATURE_COLS.
    require_target : bool
        If True (default), raises KeyError when TARGET_COL is absent.
        Set to False at inference time when no ground-truth target is available;
        a zero-filled array is returned for y.

    Returns
    -------
    X : np.ndarray, shape (n_samples, n_features)
    y : np.ndarray, shape (n_samples,)  — zeros when require_target=False and col absent
    """
    cols = feature_cols or ENGINEERED_FEATURE_COLS
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Feature columns missing from DataFrame: {missing}. "
            "Did you run engineer_features() first?"
        )
    X = df[cols].to_numpy(dtype=np.float64)
    if TARGET_COL in df.columns:
        y = df[TARGET_COL].to_numpy(dtype=np.float64)
    elif require_target:
        raise KeyError(
            f"Target column '{TARGET_COL}' not found in DataFrame. "
            "Pass require_target=False for inference-only use."
        )
    else:
        y = np.zeros(len(df), dtype=np.float64)
    return X, y


def train_val_test_split(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    seed: int = 42,
    stratify_col: str = "scenario_type",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into train / validation / test subsets.

    Stratifies by ``stratify_col`` to ensure all scenario types are
    represented proportionally in each split.

    Each returned DataFrame includes a ``_row_id`` column preserving the
    original row position from the input DataFrame. This allows downstream
    tests to verify that no row appears in more than one split.

    Parameters
    ----------
    df : pd.DataFrame
        Full dataset (before feature engineering to avoid leakage).
    train_frac : float
        Fraction for training set. Default 0.70.
    val_frac : float
        Fraction for validation set. Default 0.15.
    test_frac : float
        Fraction for test set. Default 0.15.
    seed : int
        Random seed. Default 42.
    stratify_col : str
        Column to stratify on. Default 'scenario_type'.

    Returns
    -------
    train_df, val_df, test_df : tuple of DataFrames
        Each has a ``_row_id`` column preserving the original row index.
    """
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-6, (
        "Fractions must sum to 1.0"
    )

    # Stamp each row with its original position so we can detect leakage
    df = df.copy()
    df["_row_id"] = range(len(df))

    stratify = df[stratify_col] if stratify_col in df.columns else None

    # First split: train | (val + test)
    train_df, temp_df = train_test_split(
        df,
        test_size=(1.0 - train_frac),
        random_state=seed,
        stratify=stratify,
    )

    # Second split: val | test from the remaining pool
    val_relative = val_frac / (val_frac + test_frac)
    stratify_temp = temp_df[stratify_col] if stratify_col in temp_df.columns else None
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1.0 - val_relative),
        random_state=seed,
        stratify=stratify_temp,
    )

    logger.info(
        "Dataset split -> train=%d, val=%d, test=%d",
        len(train_df),
        len(val_df),
        len(test_df),
    )
    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def validate_dataframe(df: pd.DataFrame) -> List[str]:
    """
    Validate the raw generated DataFrame for integrity.

    Checks:
    - Required columns present
    - No NaN values in critical columns
    - Numeric ranges are agronomically plausible
    - scenario_type is one of the 8 valid types

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from data_generator.

    Returns
    -------
    list of str
        List of validation error messages. Empty list = valid.
    """
    from app.ml.data_generator import SCENARIO_TYPES

    errors: List[str] = []

    required_cols = [
        "farmer_id", "scenario_type", "is_synthetic",
        "crop_type", "soil_type", "growth_stage", "season",
        "farm_area_hectares", "et0_mm_per_day", "kc_value",
        "etc_mm_per_day", "soil_whc_mm_per_m", "water_demand_m3",
        "minimum_requirement_m3", "preferred_start_hour",
        "irrigation_window_hours", "flexibility_score",
        "urgency_score", "crop_stress_index",
        "temperature_celsius", "humidity_percent", "rainfall_mm",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    if not errors:
        # NaN checks
        null_counts = df[required_cols].isnull().sum()
        null_cols = null_counts[null_counts > 0].index.tolist()
        if null_cols:
            errors.append(f"NaN values found in columns: {null_cols}")

        # Range checks
        if (df["farm_area_hectares"] <= 0).any():
            errors.append("farm_area_hectares contains non-positive values.")
        if (df["et0_mm_per_day"] < 1.0).any() or (df["et0_mm_per_day"] > 15.0).any():
            errors.append("et0_mm_per_day out of plausible range [1, 15] mm/day.")
        if (df["kc_value"] < 0.1).any() or (df["kc_value"] > 1.5).any():
            errors.append("kc_value out of FAO-56 range [0.1, 1.5].")
        if (df["water_demand_m3"] <= 0).any():
            errors.append("water_demand_m3 contains non-positive values.")
        if (df["flexibility_score"] < 0).any() or (df["flexibility_score"] > 1).any():
            errors.append("flexibility_score must be in [0, 1].")
        if (df["urgency_score"] < 0).any() or (df["urgency_score"] > 1).any():
            errors.append("urgency_score must be in [0, 1].")

        # Scenario type validation
        invalid_types = set(df["scenario_type"].unique()) - set(SCENARIO_TYPES)
        if invalid_types:
            errors.append(f"Unknown scenario_type values: {invalid_types}")

        # Synthetic flag
        if "is_synthetic" in df.columns:
            if not df["is_synthetic"].all():
                errors.append(
                    "is_synthetic is False for some rows — all data must be synthetic."
                )

    return errors
