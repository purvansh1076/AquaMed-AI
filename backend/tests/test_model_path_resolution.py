"""
AquaMediAI — Regression Tests for Model Path Resolution
=========================================================

Verifies that model artifacts (encoders.joblib, rf_model.joblib, xgb_model.joblib)
resolve robustly regardless of whether commands or tests are executed from:
  1. The backend directory (backend/)
  2. The repository root directory (aquamedi-ai/)
  3. An arbitrary external working directory (e.g., CI runners, tmp directories)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import BACKEND_DIR, Settings, get_settings
from app.services.scenario_service import ScenarioService, clear_predictor_cache


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure clean predictor and settings cache for each test."""
    clear_predictor_cache()
    get_settings.cache_clear()
    yield
    clear_predictor_cache()
    get_settings.cache_clear()


def test_settings_resolves_when_cwd_is_backend(monkeypatch):
    """When CWD is backend/, model_dir_path resolves to existing artifacts."""
    monkeypatch.chdir(BACKEND_DIR)
    settings = Settings()
    path = settings.model_dir_path
    assert path.is_absolute()
    assert (path / "encoders.joblib").exists(), f"encoders.joblib missing in {path}"
    assert (path / "rf_model.joblib").exists(), f"rf_model.joblib missing in {path}"


def test_settings_resolves_when_cwd_is_repo_root(monkeypatch):
    """When CWD is repository root, model_dir_path resolves to backend artifacts."""
    repo_root = BACKEND_DIR.parent
    monkeypatch.chdir(repo_root)
    settings = Settings()
    path = settings.model_dir_path
    assert path.is_absolute()
    assert (path / "encoders.joblib").exists(), f"encoders.joblib missing in {path}"
    assert (path / "rf_model.joblib").exists(), f"rf_model.joblib missing in {path}"


def test_settings_resolves_from_arbitrary_temp_dir(tmp_path, monkeypatch):
    """When CWD is an isolated directory without data/models, fallback resolves to backend."""
    monkeypatch.chdir(tmp_path)
    settings = Settings()
    path = settings.model_dir_path
    assert path.is_absolute()
    assert (path / "encoders.joblib").exists(), f"encoders.joblib missing in {path}"


def test_settings_preserves_explicit_absolute_path(tmp_path):
    """Explicit absolute path is preserved and returned as-is."""
    custom_dir = tmp_path / "custom_models"
    custom_dir.mkdir()
    settings = Settings(model_dir=str(custom_dir))
    assert settings.model_dir_path == custom_dir.resolve()


def test_scenario_service_resolves_predictor_from_repo_root(monkeypatch):
    """ScenarioService can load predictor and run single prediction from repo root."""
    repo_root = BACKEND_DIR.parent
    monkeypatch.chdir(repo_root)

    service = ScenarioService()
    sample_farmer = {
        "farmer_id": "test_f1",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "vegetative",
        "season": "rabi",
        "farm_area_hectares": 2.5,
        "et0_mm_per_day": 4.0,
        "kc_value": 0.70,
        "etc_mm_per_day": 2.8,
    }
    result = service.predict_single(sample_farmer, model_name="XGBoost")
    assert result.predicted_water_demand_m3 > 0
    assert result.model_name == "XGBoost"


def test_health_check_reports_pipeline_available_from_any_cwd(tmp_path, monkeypatch):
    """GET /api/v1/health reports pipeline available even from an isolated CWD."""
    monkeypatch.chdir(tmp_path)
    from app.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["pipeline"] == "available"


def test_model_selection_loads_actual_rf_artifact():
    """Verify that model_name='RandomForest' loads actual RandomForestRegressor."""
    from sklearn.ensemble import RandomForestRegressor
    from app.services.scenario_service import _predictor_cache

    service = ScenarioService()
    sample_farmer = {
        "farmer_id": "test_rf_farmer",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "vegetative",
        "season": "rabi",
        "farm_area_hectares": 2.0,
        "et0_mm_per_day": 4.0,
        "kc_value": 0.70,
        "etc_mm_per_day": 2.8,
    }
    result = service.predict_single(sample_farmer, model_name="RandomForest")
    assert result.model_name == "RandomForest"
    rf_pred = _predictor_cache["RandomForest"]
    assert isinstance(rf_pred._model, RandomForestRegressor)


def test_model_selection_loads_actual_xgb_artifact():
    """Verify that model_name='XGBoost' loads actual XGBRegressor."""
    from xgboost import XGBRegressor
    from app.services.scenario_service import _predictor_cache

    service = ScenarioService()
    sample_farmer = {
        "farmer_id": "test_xgb_farmer",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "vegetative",
        "season": "rabi",
        "farm_area_hectares": 2.0,
        "et0_mm_per_day": 4.0,
        "kc_value": 0.70,
        "etc_mm_per_day": 2.8,
    }
    result = service.predict_single(sample_farmer, model_name="XGBoost")
    assert result.model_name == "XGBoost"
    xgb_pred = _predictor_cache["XGBoost"]
    assert isinstance(xgb_pred._model, XGBRegressor)


def test_api_predict_respects_model_selection():
    """Verify /api/v1/predict returns correct model_name for both RandomForest and XGBoost."""
    from app.main import app

    client = TestClient(app)
    sample_farmer = {
        "farmer_id": "test_api_farmer",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "vegetative",
        "season": "rabi",
        "farm_area_hectares": 2.0,
        "et0_mm_per_day": 4.0,
        "kc_value": 0.70,
        "etc_mm_per_day": 2.8,
    }
    # Test RandomForest
    resp_rf = client.post("/api/v1/predictions", json={"farmer_data": sample_farmer, "model_name": "RandomForest"})
    assert resp_rf.status_code == 200, resp_rf.text
    data_rf = resp_rf.json()
    assert data_rf["model_name"] == "RandomForest"

    # Test XGBoost
    resp_xgb = client.post("/api/v1/predictions", json={"farmer_data": sample_farmer, "model_name": "XGBoost"})
    assert resp_xgb.status_code == 200, resp_xgb.text
    data_xgb = resp_xgb.json()
    assert data_xgb["model_name"] == "XGBoost"
