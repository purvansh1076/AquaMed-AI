"""
AquaMediAI — Date-Grouped Chronological Train/Val/Test Splitter
==============================================================

Guarantees that all rows associated with the same meteorological date
(across all crops, growth stages, or plots) remain strictly in the same
partition (Train, Validation, or Test).

Crucial Invariants:
-------------------
1. Zero temporal leakage: Future weather is never available during training.
2. Grouped consistency: No date can appear in more than one partition.
3. Strict chronological sorting: max(Train_dates) < min(Val_dates) < min(Test_dates).
4. No random shuffling of calendar dates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class DateGroupedSplitMetadata:
    """Metadata recording date-grouped partition boundaries and record counts."""

    total_records: int
    total_unique_dates: int
    train_records: int
    train_unique_dates: int
    train_date_start: str
    train_date_end: str
    val_records: int
    val_unique_dates: int
    val_date_start: str
    val_date_end: str
    test_records: int
    test_unique_dates: int
    test_date_start: str
    test_date_end: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def date_grouped_chronological_split(
    df: pd.DataFrame,
    date_col: str = "date",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, DateGroupedSplitMetadata]:
    """
    Split DataFrame chronologically by unique dates.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset containing a date column.
    date_col : str
        Column containing dates (datetime or YYYY-MM-DD string).
    train_ratio : float
        Fraction of earlier unique dates allocated to Train (default 0.70).
    val_ratio : float
        Fraction of intermediate unique dates allocated to Validation (default 0.15).
        Remaining unique dates (1 - train_ratio - val_ratio) allocated to Test.

    Returns
    -------
    (train_df, val_df, test_df, metadata)
    """
    if train_ratio <= 0.0 or val_ratio <= 0.0 or (train_ratio + val_ratio >= 1.0):
        raise ValueError("train_ratio and val_ratio must be positive and their sum < 1.0.")

    if date_col not in df.columns:
        raise KeyError(f"Date column '{date_col}' not found in DataFrame.")

    # Normalize dates to standard string format YYYY-MM-DD
    df_work = df.copy()
    df_work["_norm_date"] = pd.to_datetime(df_work[date_col]).dt.strftime("%Y-%m-%d")

    # Extract sorted unique dates
    unique_dates: List[str] = sorted(df_work["_norm_date"].unique())
    n_dates = len(unique_dates)

    if n_dates < 10:
        raise ValueError(f"Too few unique dates ({n_dates}) for a 3-way chronological split.")

    n_train_dates = int(n_dates * train_ratio)
    n_val_dates = int(n_dates * val_ratio)
    n_test_dates = n_dates - n_train_dates - n_val_dates

    train_dates = set(unique_dates[:n_train_dates])
    val_dates = set(unique_dates[n_train_dates : n_train_dates + n_val_dates])
    test_dates = set(unique_dates[n_train_dates + n_val_dates :])

    # Assert mutual exclusivity of date sets
    assert not (train_dates & val_dates), "Train and Val date sets overlap!"
    assert not (train_dates & test_dates), "Train and Test date sets overlap!"
    assert not (val_dates & test_dates), "Val and Test date sets overlap!"

    # Partition the DataFrame
    train_mask = df_work["_norm_date"].isin(train_dates)
    val_mask = df_work["_norm_date"].isin(val_dates)
    test_mask = df_work["_norm_date"].isin(test_dates)

    train_df = df_work[train_mask].drop(columns=["_norm_date"]).reset_index(drop=True)
    val_df = df_work[val_mask].drop(columns=["_norm_date"]).reset_index(drop=True)
    test_df = df_work[test_mask].drop(columns=["_norm_date"]).reset_index(drop=True)

    # Invariant checks on temporal ordering
    max_train_date = max(train_dates)
    min_val_date = min(val_dates)
    max_val_date = max(val_dates)
    min_test_date = min(test_dates)

    assert max_train_date < min_val_date, (
        f"Temporal ordering violation: max(train)={max_train_date} >= min(val)={min_val_date}"
    )
    assert max_val_date < min_test_date, (
        f"Temporal ordering violation: max(val)={max_val_date} >= min(test)={min_test_date}"
    )

    metadata = DateGroupedSplitMetadata(
        total_records=len(df),
        total_unique_dates=n_dates,
        train_records=len(train_df),
        train_unique_dates=len(train_dates),
        train_date_start=min(train_dates),
        train_date_end=max_train_date,
        val_records=len(val_df),
        val_unique_dates=len(val_dates),
        val_date_start=min_val_date,
        val_date_end=max_val_date,
        test_records=len(test_df),
        test_unique_dates=len(test_dates),
        test_date_start=min_test_date,
        test_date_end=max(test_dates),
    )

    return train_df, val_df, test_df, metadata
