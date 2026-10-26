"""
AquaMediAI — Chronological Holdout & Rolling-Origin Validation
==============================================================

Implements time-aware data splitting for meteorological and agricultural time series.

Crucial Rule:
NEVER use random train/test splitting (e.g. sklearn train_test_split(shuffle=True))
for time-series data! Random splitting allows future weather to leak into the past,
producing artificially deflated error metrics and invalidating real-world predictive validity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Generator, List, Tuple

import pandas as pd


@dataclass(frozen=True)
class SplitMetadata:
    """
    Metadata recording exact chronological split dates and sample counts.
    """

    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    train_date_start: str
    train_date_end: str
    val_date_start: str
    val_date_end: str
    test_date_start: str
    test_date_end: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def chronological_train_val_test_split(
    df: pd.DataFrame,
    date_col: str = "date",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, SplitMetadata]:
    """
    Perform a strict chronological split into Train, Validation, and Test sets.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing chronological time series.
    date_col : str
        Column name holding datetime or date string.
    train_ratio : float
        Fraction of early observations allocated to training (default 0.70).
    val_ratio : float
        Fraction of intermediate observations allocated to validation (default 0.15).
        Remaining fraction (1.0 - train_ratio - val_ratio) is allocated to test.

    Returns
    -------
    (train_df, val_df, test_df, metadata)
    """
    if train_ratio <= 0.0 or val_ratio <= 0.0 or (train_ratio + val_ratio >= 1.0):
        raise ValueError("Ratios must be positive and train_ratio + val_ratio < 1.0")

    # Sort strictly by date
    df_sorted = df.sort_values(date_col).copy().reset_index(drop=True)
    n = len(df_sorted)

    if n < 10:
        raise ValueError(f"Time series too short for 3-way split (n={n})")

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    n_test = n - n_train - n_val

    train_df = df_sorted.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df_sorted.iloc[n_train : n_train + n_val].copy().reset_index(drop=True)
    test_df = df_sorted.iloc[n_train + n_val :].copy().reset_index(drop=True)

    # Invariant assertion: no temporal overlap
    train_end = pd.to_datetime(train_df[date_col].iloc[-1])
    val_start = pd.to_datetime(val_df[date_col].iloc[0])
    val_end = pd.to_datetime(val_df[date_col].iloc[-1])
    test_start = pd.to_datetime(test_df[date_col].iloc[0])

    assert train_end < val_start, f"Temporal leakage: train_end ({train_end}) >= val_start ({val_start})"
    assert val_end < test_start, f"Temporal leakage: val_end ({val_end}) >= test_start ({test_start})"

    metadata = SplitMetadata(
        total_samples=n,
        train_samples=len(train_df),
        val_samples=len(val_df),
        test_samples=len(test_df),
        train_date_start=str(train_df[date_col].iloc[0]),
        train_date_end=str(train_df[date_col].iloc[-1]),
        val_date_start=str(val_df[date_col].iloc[0]),
        val_date_end=str(val_df[date_col].iloc[-1]),
        test_date_start=str(test_df[date_col].iloc[0]),
        test_date_end=str(test_df[date_col].iloc[-1]),
    )

    return train_df, val_df, test_df, metadata


class RollingOriginTimeSeriesSplit:
    """
    Walk-forward expanding window cross-validator for time series.

    Parameters
    ----------
    initial_window : int
        Minimum number of initial samples in training set (e.g. 180 days).
    forecast_horizon : int
        Number of samples evaluated in each forward step (e.g. 30 days).
    step_size : int, optional
        Step increment between successive folds. Default equals forecast_horizon.
    """

    def __init__(
        self,
        initial_window: int = 180,
        forecast_horizon: int = 30,
        step_size: int | None = None,
    ) -> None:
        if initial_window <= 0 or forecast_horizon <= 0:
            raise ValueError("initial_window and forecast_horizon must be > 0.")
        self.initial_window = initial_window
        self.forecast_horizon = forecast_horizon
        self.step_size = step_size or forecast_horizon

    def split(
        self, df: pd.DataFrame
    ) -> Generator[Tuple[List[int], List[int]], None, None]:
        """Yield train_indices and test_indices for each forward roll."""
        n = len(df)
        train_end = self.initial_window

        while train_end + self.forecast_horizon <= n:
            train_idx = list(range(0, train_end))
            test_idx = list(range(train_end, train_end + self.forecast_horizon))
            yield train_idx, test_idx
            train_end += self.step_size
