"""
AquaMediAI — Phase 12 Local End-to-End Shadow Smoke Test Suite
==============================================================
Validates:
1. Backend health endpoints (/health, /api/v1/health).
2. Existing prediction endpoint with shadow disabled (default unchanged).
3. Shadow evaluation in isolated configuration:
   - Valid historical prediction with observed rainfall.
   - Forward scheduling with genuine forecast.
   - Forward scheduling without forecast rejected (unavailable).
   - Documented antecedent fallback.
   - Artifact corruption safety failover.
   - Non-interference with allocations and negotiation outcomes.
4. Schema consistency and unit definitions (m3/day, mm).
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.ml.candidate_v3_shadow_adapter import (
    CandidateV3ShadowAdapter,
    RainfallInputMode,
)
from app.services.scenario_service import ScenarioService


@pytest.fixture
def smoke_farmer_payload() -> Dict[str, Any]:
    """Synthetic test fixture for farmer inputs."""
    return {
        "farmer_id": "FARMER_SMOKE_12",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "flowering",
        "season": "rabi",
        "farm_area_hectares": 3.0,
        "et0_mm_per_day": 4.5,
        "kc_value": 1.15,
        "etc_mm_per_day": 5.175,
        "soil_whc_mm_per_m": 125.0,
        "preferred_start_hour": 6,
        "irrigation_window_hours": 4,
        "flexibility_score": 0.5,
        "urgency_score": 0.6,
        "crop_stress_index": 0.45,
        "temperature_celsius": 27.5,
        "humidity_percent": 48.0,
        "rainfall_mm": 0.0,
        "soil_moisture_percent": 30.0,
        "wind_speed_m_per_s": 2.2,
        "solar_radiation_mj_m2": 19.0,
    }


def test_task1_health_endpoints():
    """Verify backend startup and health endpoints."""
    client = TestClient(app)
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/api/v1/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "healthy"
    assert "version" in r2.json()


def test_task2_prediction_endpoint_shadow_disabled_default(smoke_farmer_payload: Dict[str, Any]):
    """Verify existing prediction endpoint with shadow mode disabled; normal behavior unchanged."""
    client = TestClient(app)
    payload = {
        "farmer_data": smoke_farmer_payload,
        "model_name": "XGBoost",
    }
    resp = client.post("/api/v1/predictions", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["farmer_id"] == "FARMER_SMOKE_12"
    assert data["predicted_water_demand_m3"] > 0
    assert data["model_name"] == "XGBoost"
    assert data["shadow_candidate_v3_estimate_m3"] is None
    assert data["shadow_candidate_v3_comparison"] is None


def test_task3a_historical_prediction_with_shadow_enabled(smoke_farmer_payload: Dict[str, Any]):
    """Historical analysis with observed rainfall returns valid shadow comparison."""
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            client = TestClient(app)
            data = copy.deepcopy(smoke_farmer_payload)
            data["rainfall_input_mode"] = "observed_historical"
            data["rainfall_observed_mm"] = 12.0

            resp = client.post(
                "/api/v1/predictions",
                json={"farmer_data": data, "model_name": "XGBoost"},
            )
            assert resp.status_code == 200
            res = resp.json()

            assert res["predicted_water_demand_m3"] > 0
            assert res["shadow_candidate_v3_estimate_m3"] is not None
            assert res["shadow_candidate_v3_comparison"] is not None

            comp = res["shadow_candidate_v3_comparison"]
            assert comp["status"] == "available"
            assert comp["input_mode"] == RainfallInputMode.OBSERVED_HISTORICAL.value
            assert comp["rainfall_source"] == "rainfall_observed_mm"
            assert comp["rainfall_mm_used"] == 12.0
            assert comp["candidate_estimate_m3"] >= 0.0
            assert comp["reference_estimate_m3"] is not None
        finally:
            get_settings.cache_clear()


def test_task3b_forward_prediction_with_weather_forecast(smoke_farmer_payload: Dict[str, Any]):
    """Forward morning scheduling with genuine weather forecast returns available comparison."""
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            client = TestClient(app)
            data = copy.deepcopy(smoke_farmer_payload)
            data["rainfall_input_mode"] = "forecast_forward"
            data["rainfall_forecast_mm"] = 4.5

            resp = client.post(
                "/api/v1/predictions",
                json={"farmer_data": data, "model_name": "XGBoost"},
            )
            assert resp.status_code == 200
            res = resp.json()

            comp = res["shadow_candidate_v3_comparison"]
            assert comp["status"] == "available"
            assert comp["input_mode"] == RainfallInputMode.FORECAST_FORWARD.value
            assert comp["rainfall_source"] == "rainfall_forecast_mm"
            assert comp["rainfall_mm_used"] == 4.5
            assert comp["candidate_estimate_m3"] >= 0.0
        finally:
            get_settings.cache_clear()


def test_task3c_forward_scheduling_missing_forecast_unavailable(smoke_farmer_payload: Dict[str, Any]):
    """Forward scheduling without forecast returns unavailable and rejects future observed rainfall."""
    adapter = CandidateV3ShadowAdapter.load()
    data = copy.deepcopy(smoke_farmer_payload)
    data["rainfall_input_mode"] = "forecast_forward"
    data["rainfall_forecast_mm"] = None
    data["rainfall_observed_mm"] = 15.0  # Must NOT be silently used in forward mode

    result = adapter.evaluate(data, allow_antecedent_fallback=False)
    assert result.status == "unavailable"
    assert result.candidate_estimate_m3 is None
    assert any("missing rainfall forecast" in r.lower() for r in result.reasons)


def test_task3d_forward_scheduling_antecedent_fallback(smoke_farmer_payload: Dict[str, Any]):
    """Forward scheduling allows documented antecedent fallback using lag1 rainfall."""
    adapter = CandidateV3ShadowAdapter.load()
    data = copy.deepcopy(smoke_farmer_payload)
    data["rainfall_input_mode"] = "forecast_forward"
    data["rainfall_forecast_mm"] = None
    data["rainfall_lag1_mm"] = 2.0

    result = adapter.evaluate(data, allow_antecedent_fallback=True)
    assert result.status == "available"
    assert result.rainfall_source == "rainfall_lag1_mm (antecedent fallback)"
    assert result.rainfall_mm_used == 2.0
    assert result.candidate_estimate_m3 is not None


def test_task3e_shadow_failure_never_breaks_primary_prediction(smoke_farmer_payload: Dict[str, Any]):
    """Corrupted/failing shadow evaluator leaves primary prediction 100% intact."""
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            client = TestClient(app)
            with patch.object(
                CandidateV3ShadowAdapter,
                "evaluate_shadow",
                side_effect=RuntimeError("Corrupted shadow memory"),
            ):
                resp = client.post(
                    "/api/v1/predictions",
                    json={"farmer_data": smoke_farmer_payload, "model_name": "XGBoost"},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert data["predicted_water_demand_m3"] > 0
                assert data["shadow_candidate_v3_estimate_m3"] is None
                assert data["shadow_candidate_v3_comparison"]["status"] == "failed"
                assert "Corrupted shadow memory" in data["shadow_candidate_v3_comparison"]["error_reason"]
        finally:
            get_settings.cache_clear()


def test_task3f_non_interference_with_allocations_and_negotiation():
    """Shadow mode does not alter LP allocation, conflict detection, or negotiation outcomes."""
    service = ScenarioService()

    # Disabled
    res_disabled = service.run_scenario(
        scenario_type="moderate_shortage",
        n_farmers=4,
        seed=42,
        model_name="XGBoost",
    )

    # Enabled
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            res_enabled = service.run_scenario(
                scenario_type="moderate_shortage",
                n_farmers=4,
                seed=42,
                model_name="XGBoost",
            )
        finally:
            get_settings.cache_clear()

    assert res_enabled["available_water_m3"] == res_disabled["available_water_m3"]
    assert res_enabled["total_demand_m3"] == res_disabled["total_demand_m3"]
    assert res_enabled["initial_allocation"]["total_allocated_m3"] == res_disabled["initial_allocation"]["total_allocated_m3"]
    assert res_enabled["final_allocation"]["total_allocated_m3"] == res_disabled["final_allocation"]["total_allocated_m3"]

    allocs_enabled = [a["allocated_water_m3"] for a in res_enabled["initial_allocation"]["allocations"]]
    allocs_disabled = [a["allocated_water_m3"] for a in res_disabled["initial_allocation"]["allocations"]]
    assert allocs_enabled == allocs_disabled

    assert res_enabled["negotiation"]["agreement_status"] == res_disabled["negotiation"]["agreement_status"]
    assert res_enabled["negotiation"]["best_allocation"] == res_disabled["negotiation"]["best_allocation"]
    assert res_enabled["final_decision"]["fairness_score"] == res_disabled["final_decision"]["fairness_score"]


def test_task4_schema_features_and_units():
    """Verify required 21 feature schema and unit definitions."""
    schema_path = Path("backend/data/models/candidate_v3/feature_schema.json")
    assert schema_path.exists()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["selected_feature_set"] == "set_c_enriched"
    assert schema["total_feature_count"] == 21
    assert len(schema["numeric_features"]) == 18
    assert len(schema["categorical_features"]) == 3
    assert schema["forbidden_features_verified_absent"] is True
    assert schema["leakage_audit_verdict"] == "ZERO_LEAKAGE_CONFIRMED"
