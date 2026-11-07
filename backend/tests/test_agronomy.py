"""
Tests for Agricultural Intelligence, Live Weather, and Diagnostic API
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def farmer_token(client):
    res = client.post("/api/v1/auth/guest-session")
    return res.json()["access_token"]


def test_weather_endpoint_returns_data(client):
    res = client.get("/api/v1/weather/current?lat=19.0948&lon=74.7480")
    assert res.status_code == 200
    data = res.json()
    assert "current" in data
    assert "forecast_7day" in data
    assert "temperature_c" in data["current"]
    assert len(data["forecast_7day"]) > 0


def test_conformal_prediction_intervals(client, farmer_token):
    headers = {"Authorization": f"Bearer {farmer_token}"}
    payload = {
        "predicted_demand_m3": 25.0,
        "farm_area_ha": 1.5,
        "growth_stage": "flowering",
    }
    res = client.post("/api/v1/predictions/conformal-interval", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["predicted_demand_m3"] == 25.0
    assert data["lower_bound_m3"] < 25.0
    assert data["upper_bound_m3"] > 25.0
    assert data["confidence_level"] == 0.90
    assert data["is_critical_stage"] is True


def test_crop_health_diagnostic_screening(client, farmer_token):
    headers = {"Authorization": f"Bearer {farmer_token}"}
    payload = {
        "crop_type": "sugarcane",
        "symptom_key": "curled_spindle_leaves",
        "soil_moisture_pct": 20.0,
        "growth_stage": "vegetative",
    }
    res = client.post("/api/v1/agronomy/diagnose", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["severity"] == "High"
    assert "Drought" in data["diagnosis"]
    assert "Critical Root-Zone Deficit" in data["soil_moisture_context"]
    assert "disclaimer" in data


def test_xgboost_unpickled_base_score_calibration():
    """Verify that unpickling XGBoost in Python 3.12 / XGBoost 2.x properly calibrates base_score."""
    from pathlib import Path
    from app.config import get_settings
    from app.ml.trainer import load_model, load_encoders
    from app.ml.feature_engineering import engineer_features, get_feature_matrix, train_val_test_split
    from app.ml.data_generator import SyntheticDataGenerator
    from sklearn.metrics import r2_score, mean_absolute_error

    settings = get_settings()
    model_dir = settings.model_dir_path
    xgb_model = load_model(model_dir, "XGBoost")
    encoders = load_encoders(model_dir)

    gen = SyntheticDataGenerator(seed=42)
    df = gen.generate_dataset(n_samples=600)
    _, _, test_df = train_val_test_split(df, seed=42)

    test_eng = engineer_features(test_df, encoders)
    X_test, y_test = get_feature_matrix(test_eng, require_target=True)

    preds = xgb_model.predict(X_test)
    assert preds.mean() > 150.0, f"Expected volumetric mean > 150 m3, got {preds.mean():.2f} (dropped base_score bug!)"
    assert r2_score(y_test, preds) > 0.95, f"Expected R2 > 0.95, got {r2_score(y_test, preds):.4f}"
    assert mean_absolute_error(y_test, preds) < 25.0


def test_conformal_interval_bounds_point_prediction(client, farmer_token):
    """Verify that conformal prediction intervals strictly contain the point prediction in m³."""
    headers = {"Authorization": f"Bearer {farmer_token}"}
    payload = {
        "predicted_demand_m3": 221.38,
        "farm_area_ha": 3.5,
        "growth_stage": "flowering",
    }
    res = client.post("/api/v1/predictions/conformal-interval", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["lower_bound_m3"] <= 221.38 <= data["upper_bound_m3"]
    assert data["lower_bound_m3"] > 100.0
    assert data["upper_bound_m3"] < 350.0

