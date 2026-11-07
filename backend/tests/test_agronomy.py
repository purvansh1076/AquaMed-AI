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
