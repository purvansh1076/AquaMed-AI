"""
Tests for IoT Telemetry Ingestion and Simulation Endpoints
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_iot_telemetry_ingest(client):
    payload = {
        "device_id": "LORA_NODE_AHMEDNAGAR_01",
        "farmer_id": "F001",
        "soil_moisture_pct": 52.4,
        "soil_temp_c": 26.8,
        "battery_mv": 3450,
    }
    res = client.post("/api/v1/iot/telemetry", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ingested"
    assert data["packet"]["soil_moisture_pct"] == 52.4
    assert data["packet"]["battery_status"] == "Healthy"


def test_iot_get_latest_telemetry(client):
    res = client.get("/api/v1/iot/telemetry/LORA_NODE_AHMEDNAGAR_01")
    assert res.status_code == 200
    data = res.json()
    assert data["device_id"] == "LORA_NODE_AHMEDNAGAR_01"


def test_iot_diurnal_curve_simulation(client):
    res = client.get("/api/v1/iot/simulate?farmer_id=F001&base_moisture=46.0")
    assert res.status_code == 200
    data = res.json()
    assert "diurnal_readings" in data
    assert len(data["diurnal_readings"]) == 24
    assert data["diurnal_readings"][0]["hour"] == "00:00"
