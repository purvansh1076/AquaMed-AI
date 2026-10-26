"""
AquaMediAI — Automated Offline Unit Tests for Phase 3 ML Design & Utilities
============================================================================

All tests run completely OFFLINE using small local fixtures and synthetic data.
Zero network access.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.ml.agronomic_baseline import DeterministicAgronomicBaseline
from app.ml.chronological_split import (
    RollingOriginTimeSeriesSplit,
    chronological_train_val_test_split,
)
from app.ml.evaluation_reporter import (
    compute_benchmark_metrics,
    generate_comparative_report,
)
from app.ml.leakage_audit import audit_feature_leakage
from app.ml.time_series_features import compute_causal_weather_features

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "nasa_power_ahmednagar_sample.json"


# ─── 1. Approach A: Deterministic Baseline Tests ───────────────────────────────

def test_deterministic_baseline_calculation():
    """Verify exact physical calculation on known agronomic numbers."""
    calc = DeterministicAgronomicBaseline(default_application_efficiency=0.70)
    res = calc.calculate_daily_demand(
        farm_area_hectares=2.0,
        et0_mm_per_day=4.0,
        kc_value=1.15,
        rainfall_mm=0.0,
    )
    # ETc = 4.0 * 1.15 = 4.60 mm/day
    assert res.etc_mm_per_day == 4.60
    assert res.effective_precipitation_mm == 0.0
    assert res.net_irrigation_depth_mm == 4.60

    # Gross depth = 4.60 / 0.70 = 6.5714 mm/day
    assert pytest.approx(res.gross_irrigation_depth_mm, 0.001) == 4.60 / 0.70

    # Volume = 6.5714 mm * 2.0 ha * 10 = 131.4286 m3/day
    expected_vol = (4.60 / 0.70) * 2.0 * 10.0
    assert pytest.approx(res.volumetric_demand_m3_per_day, 0.01) == expected_vol


def test_deterministic_baseline_with_heavy_rainfall():
    """When rainfall exceeds ETc, volumetric demand must be zero."""
    calc = DeterministicAgronomicBaseline()
    res = calc.calculate_daily_demand(
        farm_area_hectares=3.0,
        et0_mm_per_day=3.0,
        kc_value=0.70,
        rainfall_mm=60.0,
    )
    assert res.net_irrigation_depth_mm == 0.0
    assert res.gross_irrigation_depth_mm == 0.0
    assert res.volumetric_demand_m3_per_day == 0.0


def test_deterministic_baseline_input_validation():
    """Invalid negative or zero values must be rejected."""
    calc = DeterministicAgronomicBaseline()
    with pytest.raises(ValueError, match="farm_area_hectares must be > 0"):
        calc.calculate_daily_demand(farm_area_hectares=0.0, et0_mm_per_day=4.0, kc_value=1.0)
    with pytest.raises(ValueError, match="et0_mm_per_day must be >= 0"):
        calc.calculate_daily_demand(farm_area_hectares=1.0, et0_mm_per_day=-1.0, kc_value=1.0)
    with pytest.raises(ValueError, match="kc_value must be > 0"):
        calc.calculate_daily_demand(farm_area_hectares=1.0, et0_mm_per_day=4.0, kc_value=0.0)


# ─── 2. Causal Time-Series Feature Engineering Tests ──────────────────────────

def test_causal_time_series_features():
    """Verify that lag and rolling features are strictly causal with zero lookahead."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "temperature_celsius": [20.0 + i for i in range(10)],
        "T2M_MAX": [28.0 + i for i in range(10)],
        "T2M_MIN": [12.0 + i for i in range(10)],
        "humidity_percent": [50.0] * 10,
        "wind_speed_m_per_s": [2.0] * 10,
        "rainfall_mm": [0.0, 5.0, 10.0, 15.0, 0.0, 0.0, 20.0, 0.0, 0.0, 0.0],
        "solar_radiation_mj_per_m2": [18.0] * 10,
        "day_of_year": list(range(1, 11)),
    })

    enriched = compute_causal_weather_features(df)

    # 1. Day 1 (index 0): lag 1 should be 0.0 (no prior day)
    assert enriched.loc[0, "rainfall_lag1_mm"] == 0.0

    # 2. Day 2 (index 1): lag 1 should be Day 1 rainfall (0.0)
    assert enriched.loc[1, "rainfall_lag1_mm"] == 0.0

    # 3. Day 3 (index 2): lag 1 should be Day 2 rainfall (5.0)
    assert enriched.loc[2, "rainfall_lag1_mm"] == 5.0

    # 4. Day 4 (index 3): antecedent 3-day rainfall should be Day 1 + Day 2 + Day 3 (0 + 5 + 10 = 15.0)
    # Today's rainfall (15.0 on Day 4) must NOT be included!
    assert enriched.loc[3, "rainfall_antecedent_3d_mm"] == 15.0

    # 5. Trigonometric identity: sin^2 + cos^2 == 1
    sin_sq = enriched["doy_sin"] ** 2
    cos_sq = enriched["doy_cos"] ** 2
    assert np.allclose(sin_sq + cos_sq, 1.0)


# ─── 3. Chronological Splitting Tests ─────────────────────────────────────────

def test_chronological_holdout_split():
    """Verify that train, val, and test partitions have zero temporal overlap."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date": dates, "value": range(100)})

    train, val, test, meta = chronological_train_val_test_split(
        df, date_col="date", train_ratio=0.70, val_ratio=0.15
    )

    assert len(train) == 70
    assert len(val) == 15
    assert len(test) == 15

    # Strict temporal ordering assertion
    assert train["date"].max() < val["date"].min()
    assert val["date"].max() < test["date"].min()

    assert meta.train_samples == 70
    assert meta.val_samples == 15
    assert meta.test_samples == 15


def test_rolling_origin_split():
    """Verify walk-forward time-series CV expanding window."""
    df = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=120, freq="D")})
    cv = RollingOriginTimeSeriesSplit(initial_window=60, forecast_horizon=20, step_size=20)

    folds = list(cv.split(df))
    assert len(folds) == 3  # (60->80, 80->100, 100->120)

    for train_idx, test_idx in folds:
        assert max(train_idx) < min(test_idx)
        assert len(test_idx) == 20


# ─── 4. Leakage Audit Tool Tests ──────────────────────────────────────────────

def test_leakage_audit_detects_tautological_and_operational_features():
    """Leakage audit tool must flag area_x_etc as CRITICAL and agent vars as operational."""
    n = 200
    rng = np.random.default_rng(42)
    area = rng.uniform(1.0, 5.0, size=n)
    etc = rng.uniform(2.0, 6.0, size=n)
    demand = area * etc * 10.0 + rng.normal(0, 1.0, size=n)

    df = pd.DataFrame({
        "farm_area_hectares": area,
        "etc_mm_per_day": etc,
        "area_x_etc": area * etc,                 # Tautological duplicate of demand/10
        "urgency_score": rng.uniform(0, 1, size=n), # Agent game state variable
        "temperature_celsius": rng.uniform(20, 35, size=n), # Legitimate weather
        "water_demand_m3": demand,
    })

    candidate_features = [
        "farm_area_hectares",
        "etc_mm_per_day",
        "area_x_etc",
        "urgency_score",
        "temperature_celsius",
    ]

    report = audit_feature_leakage(df, candidate_features, target_column="water_demand_m3")

    assert report.has_critical_leakage is True
    assert report.verdict == "FAIL"

    # Verify area_x_etc is flagged as tautological
    tautological_findings = [f for f in report.findings if f.feature_name == "area_x_etc"]
    assert len(tautological_findings) == 1
    assert tautological_findings[0].finding_type == "tautological"
    assert tautological_findings[0].severity == "CRITICAL"

    # Verify urgency_score is flagged as operational leakage
    op_findings = [f for f in report.findings if f.feature_name == "urgency_score"]
    assert len(op_findings) == 1
    assert op_findings[0].finding_type == "operational_leakage"


# ─── 5. Evaluation Reporter Tests ─────────────────────────────────────────────

def test_comparative_evaluation_reporter():
    """Verify benchmark metrics and comparative report generation."""
    y_train = np.array([100.0, 110.0, 120.0, 130.0, 140.0])  # mean = 120.0
    y_test = np.array([115.0, 125.0, 135.0])
    y_pred_model = np.array([116.0, 124.0, 134.0])  # good model: MAE = 1.0

    report = generate_comparative_report(
        y_test=y_test,
        y_pred_model=y_pred_model,
        y_train=y_train,
        candidate_model_name="Test Regressor",
    )

    assert report.n_evaluation_samples == 3
    assert report.candidate_model.mae == 1.0
    # Naive baseline predicts 120.0 for all test items -> errors: |115-120|=5, |125-120|=5, |135-120|=15 -> MAE = 25/3 = 8.3333
    assert pytest.approx(report.naive_mean_baseline.mae, 0.01) == 8.3333
    assert report.improvement_over_naive_pct > 80.0
