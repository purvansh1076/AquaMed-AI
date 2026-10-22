"""
AquaMediAI — Tests for the ML Training Pipeline (Phase 2)
==========================================================

Test coverage:
  1. Dataset loading & shape
  2. Feature matrix shape & dtype
  3. RandomForest training & prediction
  4. XGBoost training & prediction
  5. Metrics: finite, plausible ranges (sanity only — no fabricated thresholds)
  6. Model save / load round-trip
  7. Loaded model produces identical predictions
  8. SHAP explanation structure & values
  9. Preprocessing consistency (same X from same raw input)
  10. No train/test leakage (via _row_id check from Phase 1)
  11. Predictor API (single & batch)

Academic Note
-------------
Metric thresholds are sanity checks only (e.g., R² > 0, MAE finite).
We do NOT hard-code unrealistically tight bounds because:
  a) Metrics vary with random seed and dataset size.
  b) Fabricating metric thresholds would be academically dishonest.
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import pytest

from app.ml.data_generator import SyntheticDataGenerator
from app.ml.feature_engineering import (
    ENGINEERED_FEATURE_COLS,
    TARGET_COL,
    engineer_features,
    fit_encoders,
    get_feature_matrix,
    train_val_test_split,
)
from app.ml.trainer import (
    MODEL_VERSION,
    ModelMetrics,
    ModelResult,
    TrainingArtifacts,
    compute_metrics,
    load_encoders,
    load_model,
    run_training_pipeline,
    train_random_forest,
    train_xgboost,
)


# ─── Shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def small_raw_df():
    """Small raw dataset for fast unit tests (400 samples)."""
    gen = SyntheticDataGenerator(seed=42)
    return gen.generate_dataset(n_samples=400)


@pytest.fixture(scope="module")
def splits(small_raw_df):
    """Train/val/test split of the small dataset."""
    return train_val_test_split(small_raw_df, seed=42)


@pytest.fixture(scope="module")
def encoders(splits):
    train_df, _, _ = splits
    return fit_encoders(train_df)


@pytest.fixture(scope="module")
def engineered_splits(splits, encoders):
    """Feature-engineered arrays for train, val, test."""
    train_df, val_df, test_df = splits
    train_eng = engineer_features(train_df, encoders)
    val_eng = engineer_features(val_df, encoders)
    test_eng = engineer_features(test_df, encoders)
    X_train, y_train = get_feature_matrix(train_eng)
    X_val, y_val = get_feature_matrix(val_eng)
    X_test, y_test = get_feature_matrix(test_eng)
    return X_train, y_train, X_val, y_val, X_test, y_test


@pytest.fixture(scope="module")
def trained_rf(engineered_splits):
    """Trained RandomForest model."""
    X_train, y_train, _, _, _, _ = engineered_splits
    model, _ = train_random_forest(X_train, y_train, params={"n_estimators": 30, "random_state": 42})
    return model


@pytest.fixture(scope="module")
def trained_xgb(engineered_splits):
    """Trained XGBoost model."""
    X_train, y_train, X_val, y_val, _, _ = engineered_splits
    model, _ = train_xgboost(
        X_train, y_train, X_val, y_val,
        params={"n_estimators": 50, "learning_rate": 0.1, "random_state": 42,
                "verbosity": 0, "early_stopping_rounds": 5, "eval_metric": "rmse"}
    )
    return model


@pytest.fixture(scope="module")
def full_artifacts(tmp_path_factory):
    """Run the full training pipeline once with a small dataset, save artefacts."""
    model_dir = tmp_path_factory.mktemp("models")
    artifacts = run_training_pipeline(
        n_samples=600,
        seed=42,
        model_dir=model_dir,
        save_artifacts=True,
        rf_params={"n_estimators": 30},
        xgb_params={
            "n_estimators": 50, "learning_rate": 0.1, "verbosity": 0,
            "early_stopping_rounds": 5, "eval_metric": "rmse"
        },
    )
    return artifacts, model_dir


# ─── 1. Dataset & feature shape ───────────────────────────────────────────────

class TestDatasetShape:
    """Verify dataset generation and feature engineering shapes."""

    def test_raw_df_is_dataframe(self, small_raw_df):
        assert isinstance(small_raw_df, pd.DataFrame)

    def test_raw_df_has_target_column(self, small_raw_df):
        assert TARGET_COL in small_raw_df.columns

    def test_feature_matrix_shape(self, engineered_splits):
        X_train, y_train, X_val, y_val, X_test, y_test = engineered_splits
        n_feats = len(ENGINEERED_FEATURE_COLS)
        assert X_train.shape[1] == n_feats
        assert X_val.shape[1] == n_feats
        assert X_test.shape[1] == n_feats

    def test_y_vector_positive(self, engineered_splits):
        _, y_train, _, y_val, _, y_test = engineered_splits
        assert (y_train > 0).all()
        assert (y_val > 0).all()
        assert (y_test > 0).all()

    def test_no_nans_in_X(self, engineered_splits):
        X_train, _, X_val, _, X_test, _ = engineered_splits
        for X, name in [(X_train, "train"), (X_val, "val"), (X_test, "test")]:
            assert not np.any(np.isnan(X)), f"NaN in {name} feature matrix"

    def test_feature_matrix_dtype_float64(self, engineered_splits):
        X_train, _, _, _, _, _ = engineered_splits
        assert X_train.dtype == np.float64

    def test_correct_number_of_features(self, engineered_splits):
        X_train, _, _, _, _, _ = engineered_splits
        assert X_train.shape[1] == len(ENGINEERED_FEATURE_COLS)


# ─── 2. RandomForest training ─────────────────────────────────────────────────

class TestRandomForestTraining:
    """Tests that RandomForest trains, predicts, and produces finite metrics."""

    def test_rf_trains_without_error(self, trained_rf):
        assert trained_rf is not None

    def test_rf_has_estimators(self, trained_rf):
        assert len(trained_rf.estimators_) > 0

    def test_rf_predictions_finite(self, trained_rf, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        preds = trained_rf.predict(X_test)
        assert np.all(np.isfinite(preds)), "RF predictions contain inf/nan"

    def test_rf_predictions_positive(self, trained_rf, engineered_splits):
        """Water demand should never be predicted as negative (tree ensemble)."""
        _, _, _, _, X_test, _ = engineered_splits
        preds = trained_rf.predict(X_test)
        # RF cannot extrapolate below training minimum — predictions should be > 0
        assert (preds > 0).all(), "Some RF predictions are non-positive"

    def test_rf_prediction_shape(self, trained_rf, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_rf.predict(X_test)
        assert preds.shape == y_test.shape

    def test_rf_metrics_finite(self, trained_rf, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_rf.predict(X_test)
        m = compute_metrics(y_test, preds)
        assert math.isfinite(m.mae), "RF MAE is not finite"
        assert math.isfinite(m.rmse), "RF RMSE is not finite"
        assert math.isfinite(m.r2), "RF R² is not finite"

    def test_rf_mae_positive(self, trained_rf, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_rf.predict(X_test)
        m = compute_metrics(y_test, preds)
        assert m.mae >= 0.0, "MAE must be non-negative"

    def test_rf_rmse_positive(self, trained_rf, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_rf.predict(X_test)
        m = compute_metrics(y_test, preds)
        assert m.rmse >= 0.0, "RMSE must be non-negative"

    def test_rf_r2_less_than_1(self, trained_rf, engineered_splits):
        """R² can be negative (worse than mean baseline) but must be ≤ 1."""
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_rf.predict(X_test)
        m = compute_metrics(y_test, preds)
        assert m.r2 <= 1.0, "R² cannot exceed 1.0"


# ─── 3. XGBoost training ──────────────────────────────────────────────────────

class TestXGBoostTraining:
    """Tests that XGBoost trains, predicts, and produces finite metrics."""

    def test_xgb_trains_without_error(self, trained_xgb):
        assert trained_xgb is not None

    def test_xgb_predictions_finite(self, trained_xgb, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        preds = trained_xgb.predict(X_test)
        assert np.all(np.isfinite(preds)), "XGB predictions contain inf/nan"

    def test_xgb_prediction_shape(self, trained_xgb, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_xgb.predict(X_test)
        assert preds.shape == y_test.shape

    def test_xgb_metrics_finite(self, trained_xgb, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_xgb.predict(X_test)
        m = compute_metrics(y_test, preds)
        assert math.isfinite(m.mae)
        assert math.isfinite(m.rmse)
        assert math.isfinite(m.r2)

    def test_xgb_r2_less_than_1(self, trained_xgb, engineered_splits):
        _, _, _, _, X_test, y_test = engineered_splits
        preds = trained_xgb.predict(X_test)
        m = compute_metrics(y_test, preds)
        assert m.r2 <= 1.0


# ─── 4. Metrics dataclass ─────────────────────────────────────────────────────

class TestModelMetrics:
    """Tests for the ModelMetrics dataclass."""

    def test_compute_metrics_returns_model_metrics(self, engineered_splits, trained_rf):
        _, _, _, _, X_test, y_test = engineered_splits
        m = compute_metrics(y_test, trained_rf.predict(X_test))
        assert isinstance(m, ModelMetrics)

    def test_metrics_as_dict_has_required_keys(self, engineered_splits, trained_rf):
        _, _, _, _, X_test, y_test = engineered_splits
        m = compute_metrics(y_test, trained_rf.predict(X_test))
        d = m.as_dict()
        for key in ("mae", "rmse", "r2", "n_samples", "split"):
            assert key in d

    def test_metrics_n_samples_correct(self, engineered_splits, trained_rf):
        _, _, _, _, X_test, y_test = engineered_splits
        m = compute_metrics(y_test, trained_rf.predict(X_test))
        assert m.n_samples == len(y_test)


# ─── 5. Model save / load round-trip ─────────────────────────────────────────

class TestModelPersistence:
    """Verify joblib save/load round-trip produces identical predictions."""

    def test_full_pipeline_runs(self, full_artifacts):
        artifacts, _ = full_artifacts
        assert isinstance(artifacts, TrainingArtifacts)

    def test_rf_model_file_exists(self, full_artifacts):
        _, model_dir = full_artifacts
        assert (model_dir / "rf_model.joblib").exists()

    def test_xgb_model_file_exists(self, full_artifacts):
        _, model_dir = full_artifacts
        assert (model_dir / "xgb_model.joblib").exists()

    def test_encoders_file_exists(self, full_artifacts):
        _, model_dir = full_artifacts
        assert (model_dir / "encoders.joblib").exists()

    def test_eval_results_file_exists(self, full_artifacts):
        _, model_dir = full_artifacts
        assert (model_dir / "evaluation_results.json").exists()

    def test_eval_results_json_valid(self, full_artifacts):
        _, model_dir = full_artifacts
        with open(model_dir / "evaluation_results.json") as f:
            data = json.load(f)
        assert "best_model" in data
        assert "RandomForest" in data
        assert "XGBoost" in data

    def test_load_xgb_model(self, full_artifacts, engineered_splits):
        _, model_dir = full_artifacts
        model = load_model(model_dir, "XGBoost")
        _, _, _, _, X_test, _ = engineered_splits
        preds = model.predict(X_test)
        assert np.all(np.isfinite(preds))

    def test_load_rf_model(self, full_artifacts, engineered_splits):
        _, model_dir = full_artifacts
        model = load_model(model_dir, "RandomForest")
        _, _, _, _, X_test, _ = engineered_splits
        preds = model.predict(X_test)
        assert np.all(np.isfinite(preds))

    def test_loaded_model_identical_predictions(self, full_artifacts, engineered_splits, trained_xgb):
        """Loaded model must produce the exact same predictions as the in-memory model.
        
        We do this by saving the in-memory trained_xgb to a temp dir, reloading it,
        and comparing predictions.
        """
        _, _, _, _, X_test, _ = engineered_splits
        preds_original = trained_xgb.predict(X_test)

        # Save + reload
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "xgb_test.joblib"
            joblib.dump(trained_xgb, path)
            reloaded = joblib.load(path)

        preds_reloaded = reloaded.predict(X_test)
        np.testing.assert_array_almost_equal(preds_original, preds_reloaded, decimal=5)

    def test_load_encoders(self, full_artifacts):
        _, model_dir = full_artifacts
        enc = load_encoders(model_dir)
        assert enc is not None
        assert "crop_type" in enc.label_encoders

    def test_best_model_field_is_valid(self, full_artifacts):
        artifacts, _ = full_artifacts
        assert artifacts.best_model_name in ("XGBoost", "RandomForest")

    def test_eval_results_metrics_finite(self, full_artifacts):
        _, model_dir = full_artifacts
        with open(model_dir / "evaluation_results.json") as f:
            data = json.load(f)
        for model_key in ("RandomForest", "XGBoost"):
            test_m = data[model_key]["test_metrics"]
            assert math.isfinite(test_m["mae"])
            assert math.isfinite(test_m["rmse"])
            assert math.isfinite(test_m["r2"])
            assert test_m["mae"] >= 0
            assert test_m["rmse"] >= 0


# ─── 6. SHAP Explainability ───────────────────────────────────────────────────

class TestSHAPExplainability:
    """Tests for the WaterDemandExplainer."""

    @pytest.fixture(scope="class")
    def explainer(self, full_artifacts, splits, encoders):
        """Build a SHAP explainer from the full pipeline artefacts."""
        from app.ml.explainer import WaterDemandExplainer
        from app.ml.feature_engineering import engineer_features, get_feature_matrix

        artifacts, model_dir = full_artifacts
        model = load_model(model_dir, "XGBoost")
        enc = load_encoders(model_dir)

        train_df, _, _ = splits
        bg_eng = engineer_features(train_df, enc)
        X_bg, _ = get_feature_matrix(bg_eng)

        # Use small background for speed in tests
        X_bg_small = X_bg[:50]
        from app.ml.feature_engineering import ENGINEERED_FEATURE_COLS
        return WaterDemandExplainer(
            model=model,
            background_data=X_bg_small,
            feature_columns=ENGINEERED_FEATURE_COLS,
            model_name="XGBoost",
        )

    def test_explainer_initialises(self, explainer):
        assert explainer is not None

    def test_explain_single_returns_shap_explanation(self, explainer, engineered_splits):
        from app.ml.explainer import SHAPExplanation
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        assert isinstance(expl, SHAPExplanation)

    def test_explanation_has_correct_n_features(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        assert len(expl.features) == len(ENGINEERED_FEATURE_COLS)

    def test_explanation_base_value_finite(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        assert math.isfinite(expl.base_value)

    def test_explanation_prediction_finite(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        assert math.isfinite(expl.prediction)
        assert expl.prediction > 0

    def test_shap_values_finite(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        for fc in expl.features:
            assert math.isfinite(fc.shap_value), f"SHAP for {fc.feature} is inf/nan"

    def test_impact_labels_valid(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        valid_impacts = {"positive", "negative", "neutral"}
        for fc in expl.features:
            assert fc.impact in valid_impacts

    def test_top_positive_all_positive(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        for fc in expl.top_positive:
            assert fc.shap_value > 0 or fc.impact == "neutral"

    def test_top_negative_all_negative(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        for fc in expl.top_negative:
            assert fc.shap_value < 0 or fc.impact == "neutral"

    def test_as_dict_has_required_keys(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        d = expl.as_dict()
        for key in ("prediction", "base_value", "model_name", "features",
                    "top_positive", "top_negative", "data_disclaimer"):
            assert key in d

    def test_features_sorted_by_abs_shap(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        abs_shaps = [fc.abs_shap for fc in expl.features]
        assert abs_shaps == sorted(abs_shaps, reverse=True), \
            "Features not sorted by |SHAP| descending"

    def test_data_disclaimer_present(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        expl = explainer.explain_single(X_test[0:1])
        assert "synthetic" in expl.data_disclaimer.lower()

    def test_global_importance_runs(self, explainer, engineered_splits):
        from app.ml.explainer import GlobalFeatureImportance
        _, _, _, _, X_test, _ = engineered_splits
        gi = explainer.global_feature_importance(X_test, n_samples=30)
        assert isinstance(gi, GlobalFeatureImportance)
        assert len(gi.feature_importances) == len(ENGINEERED_FEATURE_COLS)

    def test_global_importance_sorted(self, explainer, engineered_splits):
        _, _, _, _, X_test, _ = engineered_splits
        gi = explainer.global_feature_importance(X_test, n_samples=30)
        vals = [v for _, v in gi.feature_importances]
        assert vals == sorted(vals, reverse=True)


# ─── 7. Predictor API ─────────────────────────────────────────────────────────

class TestPredictorAPI:
    """Tests for the WaterDemandPredictor typed inference API."""

    @pytest.fixture(scope="class")
    def predictor(self, full_artifacts):
        from app.ml.predictor import WaterDemandPredictor
        artifacts, model_dir = full_artifacts
        return WaterDemandPredictor.from_artifacts(model_dir, model_name="XGBoost")

    def test_predictor_loads(self, predictor):
        assert predictor is not None

    def test_predictor_model_name(self, predictor):
        assert predictor.model_name == "XGBoost"

    def test_predict_single_returns_result(self, predictor):
        from app.ml.predictor import PredictionResult
        inp = {
            "crop_type": "wheat",
            "farm_area_hectares": 2.5,
            "et0_mm_per_day": 5.0,
            "kc_value": 1.15,
            "etc_mm_per_day": 5.75,
            "soil_type": "loam",
            "growth_stage": "flowering",
            "season": "kharif",
            "temperature_celsius": 32.0,
            "rainfall_mm": 0.0,
        }
        result = predictor.predict_single(inp)
        assert isinstance(result, PredictionResult)

    def test_predict_single_positive_demand(self, predictor):
        inp = {
            "crop_type": "rice",
            "farm_area_hectares": 3.0,
            "et0_mm_per_day": 6.0,
            "kc_value": 1.10,
            "etc_mm_per_day": 6.6,
        }
        result = predictor.predict_single(inp)
        assert result.predicted_water_demand_m3 > 0

    def test_predict_single_finite(self, predictor):
        inp = {
            "crop_type": "maize",
            "farm_area_hectares": 1.5,
            "et0_mm_per_day": 4.5,
            "kc_value": 0.80,
            "etc_mm_per_day": 3.6,
        }
        result = predictor.predict_single(inp)
        assert math.isfinite(result.predicted_water_demand_m3)

    def test_predict_single_has_input_summary(self, predictor):
        inp = {
            "crop_type": "cotton",
            "farm_area_hectares": 5.0,
            "et0_mm_per_day": 7.0,
            "kc_value": 1.15,
            "etc_mm_per_day": 8.05,
        }
        result = predictor.predict_single(inp)
        assert "crop_type" in result.input_summary
        assert result.input_summary["crop_type"] == "cotton"

    def test_predict_batch_returns_list(self, predictor):
        batch = [
            {"crop_type": "wheat", "farm_area_hectares": 2.0,
             "et0_mm_per_day": 5.0, "kc_value": 1.15, "etc_mm_per_day": 5.75},
            {"crop_type": "rice", "farm_area_hectares": 3.0,
             "et0_mm_per_day": 6.0, "kc_value": 1.10, "etc_mm_per_day": 6.6},
        ]
        results = predictor.predict_batch(batch)
        assert len(results) == 2
        assert all(r.predicted_water_demand_m3 > 0 for r in results)

    def test_predict_from_dataframe(self, predictor, small_raw_df):
        sample = small_raw_df.head(5).copy()
        preds = predictor.predict_from_dataframe(sample)
        assert len(preds) == 5
        assert np.all(np.isfinite(preds))

    def test_missing_critical_field_raises(self, predictor):
        """Omitting farm_area_hectares must raise ValueError."""
        inp = {
            "crop_type": "wheat",
            # Missing: farm_area_hectares (critical)
            "et0_mm_per_day": 5.0,
            "kc_value": 1.15,
            "etc_mm_per_day": 5.75,
        }
        with pytest.raises(ValueError, match="Missing required input fields"):
            predictor.predict_single(inp)

    def test_predictor_feature_columns_match(self, predictor):
        assert predictor.feature_columns == ENGINEERED_FEATURE_COLS


# ─── 8. Preprocessing consistency ────────────────────────────────────────────

class TestPreprocessingConsistency:
    """Verify that repeated feature engineering of the same input gives same result."""

    def test_same_input_same_features(self, small_raw_df, encoders):
        """Same raw row → same engineered features (no randomness in transform)."""
        row = small_raw_df.head(1).copy()
        eng1 = engineer_features(row, encoders)
        eng2 = engineer_features(row, encoders)
        X1, _ = get_feature_matrix(eng1)
        X2, _ = get_feature_matrix(eng2)
        np.testing.assert_array_equal(X1, X2)

    def test_feature_order_is_deterministic(self, small_raw_df, encoders):
        """Feature column order must be stable."""
        eng = engineer_features(small_raw_df.head(1), encoders)
        cols = [c for c in ENGINEERED_FEATURE_COLS if c in eng.columns]
        assert cols == ENGINEERED_FEATURE_COLS

    def test_no_leakage_between_splits(self, splits):
        """Train and test must share no rows (by _row_id)."""
        train_df, val_df, test_df = splits
        train_ids = set(train_df["_row_id"])
        test_ids = set(test_df["_row_id"])
        assert train_ids.isdisjoint(test_ids), "Train/test row leakage detected!"

    def test_encoder_fitted_only_on_train(self, splits):
        """
        Encoder classes should be a subset of what appeared in training data.
        If test data has classes unseen in train, they should be handled gracefully
        (mapped to first class) rather than raising.
        """
        train_df, val_df, test_df = splits
        enc = fit_encoders(train_df)
        # Apply to test — must not raise
        test_eng = engineer_features(test_df, enc)
        assert "crop_type_encoded" in test_eng.columns
