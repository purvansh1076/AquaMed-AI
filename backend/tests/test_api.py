"""
AquaMediAI — Phase 8: FastAPI Integration Tests
=================================================

Tests all Phase 8 API endpoints and the ScenarioService.

Coverage:
  1.  GET /api/v1/health
  2.  GET / root endpoint
  3.  POST /api/v1/scenarios/run (valid scenario)
  4.  POST /api/v1/scenarios/run (invalid scenario type)
  5.  POST /api/v1/scenarios/run (deterministic repeated request)
  6.  POST /api/v1/predictions (single prediction)
  7.  POST /api/v1/predictions/batch
  8.  POST /api/v1/conflicts
  9.  POST /api/v1/allocations
  10. POST /api/v1/negotiations
  11. POST /api/v1/scenarios/run (validation error)
  12. POST /api/v1/scenarios/run (JSON serialisation)
  13. POST /api/v1/scenarios/run (explanations present)
  14. POST /api/v1/scenarios/run (final_decision present)
  15. POST /api/v1/scenarios/run (no mutation of existing objects)
  16. OpenAPI schema registration
  17. ScenarioService standalone tests
  18. Farmer data validation
  19. Schema validation
  20. Error handling

Run with:
    pytest tests/test_api.py -v --tb=short

IMPORTANT: All 632 existing tests MUST continue passing.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app."""
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def service():
    """Create a ScenarioService instance."""
    from app.services.scenario_service import ScenarioService
    return ScenarioService()


@pytest.fixture(scope="module")
def minimal_scenario_args():
    """Minimal valid arguments for a scenario run."""
    return {
        "scenario_type": "normal_water",
        "n_farmers": 3,
        "seed": 42,
        "model_name": "XGBoost",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_structure(self, client):
        data = client.get("/api/v1/health").json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "pipeline" in data
        assert "disclaimer" in data

    def test_health_status_healthy(self, client):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "healthy"

    def test_health_service_name(self, client):
        data = client.get("/api/v1/health").json()
        assert data["service"] == "AquaMediAI"

    def test_health_pipeline_available(self, client):
        data = client.get("/api/v1/health").json()
        assert data["pipeline"] in ("available", "degraded")

    def test_health_no_secrets_exposed(self, client):
        data = client.get("/api/v1/health").json()
        raw = json.dumps(data)
        assert "SECRET_KEY" not in raw
        assert "password" not in raw.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 2. ROOT ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestRootEndpoint:
    """Tests for GET /."""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_structure(self, client):
        data = client.get("/").json()
        assert data["project"] == "AquaMediAI"
        assert "docs" in data
        assert "health" in data

    def test_root_health_points_to_v1(self, client):
        data = client.get("/").json()
        assert "/api/v1" in data["health"]


# ══════════════════════════════════════════════════════════════════════════════
# 3. SCENARIO RUN ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestScenarioRun:
    """Tests for POST /api/v1/scenarios/run."""

    def test_scenario_run_returns_200(self, client):
        resp = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        })
        assert resp.status_code == 200

    def test_scenario_run_structure(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        assert "scenario_id" in data
        assert "status" in data
        assert "predictions" in data
        assert "farmers" in data
        assert "conflicts" in data
        assert "initial_allocation" in data
        assert "negotiation" in data
        assert "final_allocation" in data
        assert "explanations" in data
        assert "final_decision" in data

    def test_scenario_run_has_correct_farmers(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        assert data["n_farmers"] == 3
        assert len(data["farmers"]) == 3
        assert len(data["predictions"]) == 3

    def test_scenario_run_valid_allocation(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        alloc = data["initial_allocation"]
        assert alloc["total_allocated_m3"] <= alloc["available_water_m3"] + 1e-6

    def test_scenario_run_no_negative_allocation(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "moderate_shortage",
            "n_farmers": 4,
            "seed": 42,
        }).json()
        for fa in data["initial_allocation"]["allocations"]:
            assert fa["allocated_water_m3"] >= -1e-9

    def test_scenario_run_fairness_in_range(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        assert 0.0 <= data["initial_allocation"]["fairness_score"] <= 1.0

    def test_scenario_run_with_water_override(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
            "available_water_override_m3": 1000.0,
        }).json()
        assert data["available_water_m3"] == 1000.0


# ══════════════════════════════════════════════════════════════════════════════
# 4. INVALID SCENARIO TYPE
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidScenario:
    """Tests for invalid scenario requests."""

    def test_invalid_scenario_type_returns_422(self, client):
        resp = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "nonexistent_type",
            "n_farmers": 3,
            "seed": 42,
        })
        assert resp.status_code == 422

    def test_invalid_n_farmers_returns_422(self, client):
        resp = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 1,
            "seed": 42,
        })
        assert resp.status_code == 422

    def test_negative_seed_returns_422(self, client):
        resp = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": -1,
        })
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# 5. DETERMINISM
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterminism:
    """Tests for deterministic API responses."""

    def test_same_input_same_allocation(self, client):
        args = {"scenario_type": "moderate_shortage", "n_farmers": 3, "seed": 42}
        r1 = client.post("/api/v1/scenarios/run", json=args).json()
        r2 = client.post("/api/v1/scenarios/run", json=args).json()
        a1 = r1["initial_allocation"]["total_allocated_m3"]
        a2 = r2["initial_allocation"]["total_allocated_m3"]
        assert abs(a1 - a2) < 0.01

    def test_same_input_same_fairness(self, client):
        args = {"scenario_type": "normal_water", "n_farmers": 3, "seed": 42}
        r1 = client.post("/api/v1/scenarios/run", json=args).json()
        r2 = client.post("/api/v1/scenarios/run", json=args).json()
        assert r1["initial_allocation"]["fairness_score"] == pytest.approx(
            r2["initial_allocation"]["fairness_score"], abs=1e-6
        )


# ══════════════════════════════════════════════════════════════════════════════
# 6. PREDICTION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestPredictionEndpoint:
    """Tests for POST /api/v1/predictions."""

    def test_prediction_returns_200(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "F001",
                "crop_type": "wheat",
                "farm_area_hectares": 2.5,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
            "model_name": "XGBoost",
        })
        assert resp.status_code == 200

    def test_prediction_structure(self, client):
        data = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "F001",
                "crop_type": "wheat",
                "farm_area_hectares": 2.5,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
        }).json()
        assert "predicted_water_demand_m3" in data
        assert "model_name" in data
        assert data["farmer_id"] == "F001"
        assert data["predicted_water_demand_m3"] > 0

    def test_prediction_missing_required_field(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "F001",
                # Missing crop_type, etc
            },
        })
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# 7. BATCH PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

class TestBatchPrediction:
    """Tests for POST /api/v1/predictions/batch."""

    def test_batch_prediction_returns_200(self, client):
        resp = client.post("/api/v1/predictions/batch", json={
            "farmers": [
                {
                    "farmer_id": "F001",
                    "crop_type": "wheat",
                    "farm_area_hectares": 2.0,
                    "et0_mm_per_day": 5.0,
                    "kc_value": 1.15,
                    "etc_mm_per_day": 5.75,
                },
                {
                    "farmer_id": "F002",
                    "crop_type": "rice",
                    "farm_area_hectares": 3.0,
                    "et0_mm_per_day": 6.0,
                    "kc_value": 1.2,
                    "etc_mm_per_day": 7.2,
                },
            ],
        })
        assert resp.status_code == 200

    def test_batch_prediction_count(self, client):
        data = client.post("/api/v1/predictions/batch", json={
            "farmers": [
                {
                    "farmer_id": f"F{i:03d}",
                    "crop_type": "wheat",
                    "farm_area_hectares": 2.0,
                    "et0_mm_per_day": 5.0,
                    "kc_value": 1.15,
                    "etc_mm_per_day": 5.75,
                }
                for i in range(3)
            ],
        }).json()
        assert data["count"] == 3
        assert len(data["predictions"]) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 8. CONFLICT ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestConflictEndpoint:
    """Tests for POST /api/v1/conflicts."""

    def test_conflict_returns_200(self, client):
        resp = client.post("/api/v1/conflicts", json={
            "scenario_type": "severe_shortage",
            "n_farmers": 4,
            "seed": 42,
        })
        assert resp.status_code == 200

    def test_conflict_structure(self, client):
        data = client.post("/api/v1/conflicts", json={
            "scenario_type": "severe_shortage",
            "n_farmers": 4,
            "seed": 42,
        }).json()
        assert "scenario_id" in data
        assert "total_conflicts" in data
        assert "conflicts" in data
        assert isinstance(data["conflicts"], list)


# ══════════════════════════════════════════════════════════════════════════════
# 9. ALLOCATION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestAllocationEndpoint:
    """Tests for POST /api/v1/allocations."""

    def test_allocation_returns_200(self, client):
        resp = client.post("/api/v1/allocations", json={
            "scenario_type": "moderate_shortage",
            "n_farmers": 3,
            "seed": 42,
        })
        assert resp.status_code == 200

    def test_allocation_structure(self, client):
        data = client.post("/api/v1/allocations", json={
            "scenario_type": "moderate_shortage",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        assert "solver_status" in data
        assert "allocations" in data
        assert "fairness_score" in data
        assert "utilization" in data
        assert "verification" in data

    def test_allocation_water_constraint(self, client):
        data = client.post("/api/v1/allocations", json={
            "scenario_type": "severe_shortage",
            "n_farmers": 4,
            "seed": 42,
        }).json()
        assert data["total_allocated_m3"] <= data["available_water_m3"] + 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# 10. NEGOTIATION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

class TestNegotiationEndpoint:
    """Tests for POST /api/v1/negotiations."""

    def test_negotiation_returns_200(self, client):
        resp = client.post("/api/v1/negotiations", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
            "max_rounds": 3,
        })
        assert resp.status_code == 200

    def test_negotiation_structure(self, client):
        data = client.post("/api/v1/negotiations", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
            "max_rounds": 3,
        }).json()
        assert "session_id" in data
        assert "agreement_status" in data
        assert "agreement" in data
        assert data["agreement"]["agreement_status"] in (
            "AGREED", "MAX_ROUNDS_REACHED", "NO_FEASIBLE_IMPROVEMENT", "FAILED"
        )

    def test_negotiation_agreement_valid_allocation(self, client):
        data = client.post("/api/v1/negotiations", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
            "max_rounds": 3,
        }).json()
        agr = data["agreement"]
        assert agr["is_physically_valid"] is True


# ══════════════════════════════════════════════════════════════════════════════
# 11. VALIDATION ERRORS
# ══════════════════════════════════════════════════════════════════════════════

class TestValidationErrors:
    """Tests for input validation."""

    def test_missing_body_returns_422(self, client):
        resp = client.post("/api/v1/scenarios/run")
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/api/v1/scenarios/run", json={})
        assert resp.status_code == 422

    def test_farmer_id_too_long(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "x" * 200,
                "crop_type": "wheat",
                "farm_area_hectares": 2.0,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
        })
        # Should succeed (no length limit in schema)
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 12. JSON SERIALIZATION
# ══════════════════════════════════════════════════════════════════════════════

class TestJsonSerialization:
    """Tests for JSON serialisation of responses."""

    def test_scenario_response_is_json_serialisable(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        json_str = json.dumps(data)
        assert len(json_str) > 0
        # Round-trip
        parsed = json.loads(json_str)
        assert parsed["scenario_id"] == data["scenario_id"]

    def test_health_response_is_json(self, client):
        data = client.get("/api/v1/health").json()
        json_str = json.dumps(data)
        assert len(json_str) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 13. EXPLANATIONS PRESENT
# ══════════════════════════════════════════════════════════════════════════════

class TestExplanationsPresent:
    """Tests for explainability data in responses."""

    def test_explanations_structure(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        exp = data["explanations"]
        assert "scenario_id" in exp
        assert "summary" in exp
        assert "allocation_explanations" in exp
        assert "fairness_explanation" in exp
        assert "constraint_explanations" in exp
        assert "data_disclaimer" in exp

    def test_final_decision_structure(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        fd = data["final_decision"]
        assert "scenario_id" in fd
        assert "summary" in fd
        assert "agreement_status" in fd
        assert "fairness_score" in fd
        assert "water_utilization" in fd

    def test_allocation_explanations_per_farmer(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        alloc_exps = data["explanations"]["allocation_explanations"]
        assert len(alloc_exps) == 3
        for ae in alloc_exps:
            assert "farmer_id" in ae
            assert "allocated_m3" in ae
            assert "reason_codes" in ae


# ══════════════════════════════════════════════════════════════════════════════
# 14. SCENARIOS ALL VALID
# ══════════════════════════════════════════════════════════════════════════════

class TestAllScenarioTypes:
    """Tests that all 8 scenario types work through the API."""

    SCENARIO_TYPES = [
        "normal_water", "moderate_shortage", "severe_shortage",
        "sudden_rainfall", "canal_reduction", "simultaneous_demand",
        "high_urgency_farmer", "flexible_farmer",
    ]

    @pytest.mark.parametrize("scenario_type", SCENARIO_TYPES)
    def test_scenario_type_runs(self, client, scenario_type):
        resp = client.post("/api/v1/scenarios/run", json={
            "scenario_type": scenario_type,
            "n_farmers": 3,
            "seed": 42,
        })
        assert resp.status_code == 200, f"Failed for {scenario_type}"
        data = resp.json()
        assert data["scenario_type"] == scenario_type
        assert len(data["farmers"]) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 15. CONSERVATION CHECKS
# ══════════════════════════════════════════════════════════════════════════════

class TestConservationChecks:
    """Tests that conservation laws hold through the API."""

    def test_water_conservation(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "severe_shortage",
            "n_farmers": 4,
            "seed": 42,
        }).json()
        alloc = data["initial_allocation"]
        assert alloc["total_allocated_m3"] <= alloc["available_water_m3"] + 1e-6
        assert alloc["remaining_water_m3"] >= -1e-6

    def test_no_nan_in_allocation(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "moderate_shortage",
            "n_farmers": 3,
            "seed": 42,
        }).json()
        for fa in data["initial_allocation"]["allocations"]:
            assert not math.isnan(fa["allocated_water_m3"])
            assert not math.isnan(fa["satisfaction_ratio"])

    def test_fairness_in_range(self, client):
        data = client.post("/api/v1/scenarios/run", json={
            "scenario_type": "normal_water",
            "n_farmers": 4,
            "seed": 42,
        }).json()
        assert 0.0 <= data["initial_allocation"]["fairness_score"] <= 1.0
        assert 0.0 <= data["initial_allocation"]["utilization"] <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 16. OpenAPI SCHEMA
# ══════════════════════════════════════════════════════════════════════════════

class TestOpenAPISchema:
    """Tests for OpenAPI schema registration."""

    def test_openapi_accessible(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_openapi_has_scenarios_endpoint(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/scenarios/run" in paths

    def test_openapi_has_health_endpoint(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/health" in paths

    def test_openapi_has_predictions_endpoint(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/predictions" in paths

    def test_openapi_has_conflicts_endpoint(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/conflicts" in paths

    def test_openapi_has_allocations_endpoint(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/allocations" in paths

    def test_openapi_has_negotiations_endpoint(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/negotiations" in paths


# ══════════════════════════════════════════════════════════════════════════════
# 17. SCENARIO SERVICE STANDALONE
# ══════════════════════════════════════════════════════════════════════════════

class TestScenarioServiceStandalone:
    """Tests for ScenarioService used directly (without HTTP)."""

    def test_service_predict_single(self, service):
        result = service.predict_single(
            farmer_data={
                "farmer_id": "F001",
                "crop_type": "wheat",
                "farm_area_hectares": 2.5,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
            model_name="XGBoost",
        )
        assert result.predicted_water_demand_m3 > 0

    def test_service_detect_conflicts(self, service):
        result = service.detect_conflicts(
            scenario_type="severe_shortage",
            n_farmers=4,
            seed=42,
        )
        assert "total_conflicts" in result
        assert isinstance(result["conflicts"], list)

    def test_service_run_allocation(self, service):
        result = service.run_allocation(
            scenario_type="moderate_shortage",
            n_farmers=3,
            seed=42,
        )
        assert "solver_status" in result
        assert result["total_allocated_m3"] <= result["available_water_m3"] + 1e-6

    def test_service_run_negotiation(self, service):
        result = service.run_negotiation(
            scenario_type="normal_water",
            n_farmers=3,
            seed=42,
            max_rounds=3,
        )
        assert "agreement" in result
        assert result["agreement"]["agreement_status"] in (
            "AGREED", "MAX_ROUNDS_REACHED", "NO_FEASIBLE_IMPROVEMENT", "FAILED"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 18. NO MUTATION
# ══════════════════════════════════════════════════════════════════════════════

class TestNoMutation:
    """Tests that API does not mutate internal objects."""

    def test_repeated_calls_same_result(self, client):
        args = {"scenario_type": "normal_water", "n_farmers": 3, "seed": 42}
        r1 = client.post("/api/v1/scenarios/run", json=args).json()
        r2 = client.post("/api/v1/scenarios/run", json=args).json()
        # Identical allocations
        assert r1["initial_allocation"]["total_allocated_m3"] == pytest.approx(
            r2["initial_allocation"]["total_allocated_m3"], abs=0.01
        )


# ══════════════════════════════════════════════════════════════════════════════
# 19. FARMER DATA VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestFarmerDataValidation:
    """Tests for Pydantic schema validation on farmer data."""

    def test_negative_area_rejected(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "F001",
                "crop_type": "wheat",
                "farm_area_hectares": -1.0,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
        })
        assert resp.status_code == 422

    def test_negative_et0_rejected(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "F001",
                "crop_type": "wheat",
                "farm_area_hectares": 2.0,
                "et0_mm_per_day": -1.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
        })
        assert resp.status_code == 422

    def test_urgency_out_of_range_rejected(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "F001",
                "crop_type": "wheat",
                "farm_area_hectares": 2.0,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
                "urgency_score": 1.5,
            },
        })
        assert resp.status_code == 422

    def test_empty_farmer_id_rejected(self, client):
        resp = client.post("/api/v1/predictions", json={
            "farmer_data": {
                "farmer_id": "",
                "crop_type": "wheat",
                "farm_area_hectares": 2.0,
                "et0_mm_per_day": 5.0,
                "kc_value": 1.15,
                "etc_mm_per_day": 5.75,
            },
        })
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# 20. ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Tests for structured error responses."""

    def test_get_on_post_endpoint_returns_405(self, client):
        resp = client.get("/api/v1/scenarios/run")
        assert resp.status_code == 405

    def test_put_on_health_returns_405(self, client):
        resp = client.put("/api/v1/health")
        assert resp.status_code == 405

    def test_delete_on_health_returns_405(self, client):
        resp = client.delete("/api/v1/health")
        assert resp.status_code == 405
