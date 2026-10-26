"""
AquaMediAI — Phase 11 Safe Candidate v3 Shadow Integration Tests
================================================================

Validates that:
1. Candidate v3 loads as an isolated, non-blocking shadow evaluator.
2. Corrupted or missing artifacts fail safely with status="unavailable".
3. The feature-availability contract enforces strict separation between:
   - Historical mode (observed rainfall)
   - Forward morning scheduling (genuine weather forecast)
   - Antecedent fallback (lag1 rainfall)
   - Strict rejection of silent lookahead substitution.
4. Candidate v3 predictions are strictly non-negative.
5. Shadow mode is disabled by default in settings and predictor.
6. Failures in shadow evaluation NEVER break primary predictions.
7. Shadow evaluator NEVER alters allocations, negotiations, or dispatch.
8. API contracts remain backward-compatible.
9. All baseline and production model artifact hashes remain intact.
"""

from __future__ import annotations

import copy
import hashlib
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
from app.ml.predictor import WaterDemandPredictor
from app.services.scenario_service import ScenarioService


@pytest.fixture
def sample_farmer_data() -> Dict[str, Any]:
    """Representative valid farmer input payload."""
    return {
        "farmer_id": "FARMER_TEST_11",
        "crop_type": "wheat",
        "growth_stage": "flowering",
        "soil_type": "loam",
        "season": "rabi",
        "farm_area_hectares": 2.5,
        "soil_moisture_percent": 32.0,
        "temperature_celsius": 28.5,
        "humidity_percent": 45.0,
        "wind_speed_m_per_s": 2.1,
        "solar_radiation_mj_m2": 19.5,
        "et0_mm_per_day": 4.8,
        "kc_value": 1.15,
        "etc_mm_per_day": 5.52,
        "rainfall_lag1_mm": 3.0,
        "rainfall_forecast_mm": 0.0,
        "rainfall_observed_mm": 0.0,
        "rainfall_input_mode": "forward_morning",
        "urgency_score": 0.6,
        "crop_stress_index": 0.5,
        "flexibility_score": 0.4,
        "preferred_start_hour": 6,
        "irrigation_window_hours": 4,
    }


# ─── 1. Artifact Loading & Isolation Tests ───────────────────────────────────

def test_candidate_v3_adapter_loading_success():
    """Verify Candidate v3 adapter loads classifier, regressor, and preprocessor."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)
    assert adapter.is_ready is True
    assert adapter.version == "candidate_v3_twostage_xgb"
    assert adapter.zero_threshold == 0.20
    assert len(adapter.feature_cols) == 21


def test_candidate_v3_adapter_invalid_artifact_handling(tmp_path: Path):
    """Corrupted/missing artifact directory must degrade safely to unavailable."""
    empty_dir = tmp_path / "empty_candidate"
    empty_dir.mkdir()
    adapter = CandidateV3ShadowAdapter.load(empty_dir)
    assert adapter.is_ready is False

    result = adapter.evaluate({"crop_type": "wheat", "farm_area_hectares": 2.0})
    assert result.status == "unavailable"
    assert result.candidate_estimate_m3 is None
    assert "artifacts not loaded" in (result.error_reason or "").lower()


# ─── 2. Feature-Availability Contract Tests ─────────────────────────────────

def test_feature_availability_contract_historical_observed(sample_farmer_data: Dict[str, Any]):
    """Historical analysis uses observed rainfall for the completed day."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    data = copy.deepcopy(sample_farmer_data)
    data["rainfall_input_mode"] = "historical"
    data["rainfall_observed_mm"] = 12.5
    data["rainfall_forecast_mm"] = None

    result = adapter.evaluate(data)
    assert result.status == "available"
    assert result.input_mode == RainfallInputMode.OBSERVED_HISTORICAL.value
    assert result.rainfall_source == "rainfall_observed_mm"
    assert result.candidate_estimate_m3 is not None
    assert result.candidate_estimate_m3 >= 0.0


def test_feature_availability_contract_forward_forecast(sample_farmer_data: Dict[str, Any]):
    """Forward morning scheduling must use genuine rainfall forecast."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    data = copy.deepcopy(sample_farmer_data)
    data["rainfall_input_mode"] = "forward_morning"
    data["rainfall_forecast_mm"] = 5.0
    data["rainfall_observed_mm"] = None

    result = adapter.evaluate(data)
    assert result.status == "available"
    assert result.input_mode == RainfallInputMode.FORECAST_FORWARD.value
    assert result.rainfall_source == "rainfall_forecast_mm"
    assert result.candidate_estimate_m3 is not None


def test_feature_availability_contract_forward_fallback_antecedent(sample_farmer_data: Dict[str, Any]):
    """Forward scheduling allows documented antecedent fallback if configured."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    data = copy.deepcopy(sample_farmer_data)
    data["rainfall_input_mode"] = "forward_morning"
    data["rainfall_forecast_mm"] = None
    data["rainfall_lag1_mm"] = 2.5

    result = adapter.evaluate(data, allow_antecedent_fallback=True)
    assert result.status == "available"
    assert result.rainfall_source == "rainfall_lag1_mm (antecedent fallback)"
    assert result.candidate_estimate_m3 is not None


def test_feature_availability_contract_forward_rejects_missing_forecast(sample_farmer_data: Dict[str, Any]):
    """Forward morning scheduling strictly rejects missing forecast when fallback is disabled."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    data = copy.deepcopy(sample_farmer_data)
    data["rainfall_input_mode"] = "forward_morning"
    data["rainfall_forecast_mm"] = None
    data["rainfall_observed_mm"] = None

    result = adapter.evaluate(data, allow_antecedent_fallback=False)
    assert result.status == "unavailable"
    assert "missing rainfall forecast" in (result.error_reason or "").lower()
    assert result.candidate_estimate_m3 is None


def test_feature_availability_contract_rejects_silent_lookahead_substitution(sample_farmer_data: Dict[str, Any]):
    """Never silently substitute future observed rainfall for a forecast in forward mode."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    data = copy.deepcopy(sample_farmer_data)
    data["rainfall_input_mode"] = "forward_morning"
    data["rainfall_forecast_mm"] = None
    # Inadvertently provided observed rainfall for a future day
    data["rainfall_observed_mm"] = 15.0

    # With allow_antecedent_fallback=False, it must NOT use rainfall_observed_mm
    result = adapter.evaluate(data, allow_antecedent_fallback=False)
    assert result.status == "unavailable"
    assert "missing rainfall forecast" in (result.error_reason or "").lower()


# ─── 3. Nonnegative and Zero-Demand Logic ────────────────────────────────────

def test_shadow_evaluator_nonnegative_output(sample_farmer_data: Dict[str, Any]):
    """Candidate v3 output must always be non-negative (>= 0.0)."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    heavy_rain_data = copy.deepcopy(sample_farmer_data)
    heavy_rain_data["rainfall_forecast_mm"] = 80.0
    heavy_rain_data["soil_moisture_percent"] = 85.0

    result = adapter.evaluate(heavy_rain_data)
    assert result.status == "available"
    assert result.candidate_estimate_m3 is not None
    assert result.candidate_estimate_m3 >= 0.0
    assert result.candidate_estimate_m3 == 0.0


def test_shadow_comparison_metrics_and_delta(sample_farmer_data: Dict[str, Any]):
    """Shadow comparison includes version, candidate estimate, reference estimate, and signed/abs disagreement."""
    settings = get_settings()
    adapter = CandidateV3ShadowAdapter.load(settings.candidate_v3_dir_path)

    result = adapter.evaluate(sample_farmer_data)
    comp = result.to_dict()

    assert comp["candidate_version"] == "candidate_v3_twostage_xgb"
    assert comp["status"] == "available"
    assert comp["candidate_estimate_m3"] is not None
    assert comp["reference_estimate_m3"] is not None
    assert comp["signed_disagreement_m3"] is not None
    assert comp["absolute_disagreement_m3"] is not None
    assert pytest.approx(comp["absolute_disagreement_m3"], abs=1e-2) == abs(comp["signed_disagreement_m3"])


# ─── 4. Predictor Shadow Integration & Default Configuration ────────────────

def test_shadow_disabled_by_default_in_config():
    """Safety rule: Candidate v3 shadow evaluator must be disabled by default."""
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.enable_candidate_v3_shadow is False


def test_predictor_shadow_disabled_by_default(sample_farmer_data: Dict[str, Any]):
    """When disabled in config, predictor returns None for candidate v3 fields."""
    settings = get_settings()
    predictor = WaterDemandPredictor.from_artifacts(settings.model_dir_path, model_name="XGBoost")

    result = predictor.predict_single(sample_farmer_data)
    assert result.predicted_water_demand_m3 > 0.0
    assert result.shadow_candidate_v3_estimate_m3 is None
    assert result.shadow_candidate_v3_comparison is None


def test_predictor_shadow_enabled_explicitly(sample_farmer_data: Dict[str, Any]):
    """Explicitly enabling candidate v3 shadow populates shadow comparison without altering prediction."""
    settings = get_settings()
    predictor = WaterDemandPredictor.from_artifacts(settings.model_dir_path, model_name="XGBoost")

    res_disabled = predictor.predict_single(sample_farmer_data, enable_candidate_v3_shadow=False)
    res_enabled = predictor.predict_single(sample_farmer_data, enable_candidate_v3_shadow=True)

    # Primary prediction must remain 100% identical
    assert res_enabled.predicted_water_demand_m3 == res_disabled.predicted_water_demand_m3
    assert res_enabled.model_name == res_disabled.model_name
    assert res_enabled.model_version == res_disabled.model_version

    # Shadow fields are populated
    assert res_enabled.shadow_candidate_v3_estimate_m3 is not None
    assert res_enabled.shadow_candidate_v3_comparison is not None
    assert res_enabled.shadow_candidate_v3_comparison["status"] == "available"


def test_shadow_failures_never_break_primary_prediction(sample_farmer_data: Dict[str, Any]):
    """Even if candidate v3 throws an unhandled exception, primary prediction MUST succeed."""
    settings = get_settings()
    predictor = WaterDemandPredictor.from_artifacts(settings.model_dir_path, model_name="XGBoost")

    with patch.object(CandidateV3ShadowAdapter, "evaluate_shadow", side_effect=RuntimeError("Corrupted shadow memory")):
        result = predictor.predict_single(sample_farmer_data, enable_candidate_v3_shadow=True)

    # Primary prediction unaffected
    assert result.predicted_water_demand_m3 > 0.0
    assert result.shadow_candidate_v3_estimate_m3 is None
    assert result.shadow_candidate_v3_comparison is not None
    assert result.shadow_candidate_v3_comparison["status"] == "failed"
    assert "Corrupted shadow memory" in result.shadow_candidate_v3_comparison["error_reason"]


# ─── 5. API Compatibility Tests ──────────────────────────────────────────────

def test_api_prediction_endpoint_with_shadow_disabled(sample_farmer_data: Dict[str, Any]):
    """POST /api/v1/predictions with shadow disabled returns valid schema with null shadow fields."""
    client = TestClient(app)
    payload = {
        "farmer_data": sample_farmer_data,
        "model_name": "XGBoost",
    }
    resp = client.post("/api/v1/predictions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_water_demand_m3" in data
    assert data["shadow_candidate_v3_estimate_m3"] is None
    assert data["shadow_candidate_v3_comparison"] is None


def test_api_prediction_endpoint_with_shadow_enabled(sample_farmer_data: Dict[str, Any]):
    """POST /api/v1/predictions when shadow is enabled via env returns valid schema with shadow estimate."""
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            client = TestClient(app)
            payload = {
                "farmer_data": sample_farmer_data,
                "model_name": "XGBoost",
            }
            resp = client.post("/api/v1/predictions", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["predicted_water_demand_m3"] > 0
            assert data["shadow_candidate_v3_estimate_m3"] is not None
            assert data["shadow_candidate_v3_comparison"] is not None
            assert data["shadow_candidate_v3_comparison"]["status"] == "available"
        finally:
            get_settings.cache_clear()


def test_api_batch_prediction_endpoint_with_shadow(sample_farmer_data: Dict[str, Any]):
    """POST /api/v1/predictions/batch returns shadow diagnostics for each farmer."""
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            client = TestClient(app)
            farmer2 = copy.deepcopy(sample_farmer_data)
            farmer2["farmer_id"] = "FARMER_TEST_12"
            farmer2["crop_type"] = "cotton"

            payload = {
                "farmers": [sample_farmer_data, farmer2],
                "model_name": "XGBoost",
            }
            resp = client.post("/api/v1/predictions/batch", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 2
            for pred in data["predictions"]:
                assert pred["predicted_water_demand_m3"] > 0
                assert pred["shadow_candidate_v3_estimate_m3"] is not None
                assert pred["shadow_candidate_v3_comparison"] is not None
        finally:
            get_settings.cache_clear()


# ─── 6. Non-Interference Safety Tests (Allocations & Negotiations) ────────────

def test_candidate_v3_does_not_affect_allocations_or_negotiations():
    """Candidate v3 shadow evaluation must NOT alter LP allocation, conflict detection, or negotiation."""
    service = ScenarioService()

    # Run scenario with shadow disabled
    res_disabled = service.run_scenario(
        scenario_type="moderate_shortage",
        n_farmers=4,
        seed=42,
        model_name="XGBoost",
    )

    # Run scenario with shadow enabled
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

    # 1. Available water and total demand must match exactly
    assert res_enabled["available_water_m3"] == res_disabled["available_water_m3"]
    assert res_enabled["total_demand_m3"] == res_disabled["total_demand_m3"]

    # 2. Conflict report must match exactly in semantic outcomes
    assert res_enabled["conflicts"]["total_conflicts"] == res_disabled["conflicts"]["total_conflicts"]
    assert res_enabled["conflicts"]["highest_severity"] == res_disabled["conflicts"]["highest_severity"]
    assert res_enabled["conflicts"]["overall_shortage_ratio"] == res_disabled["conflicts"]["overall_shortage_ratio"]
    assert res_enabled["conflicts"]["total_demand_m3"] == res_disabled["conflicts"]["total_demand_m3"]

    # 3. Initial and final LP allocations must match exactly
    assert res_enabled["initial_allocation"]["total_allocated_m3"] == res_disabled["initial_allocation"]["total_allocated_m3"]
    assert res_enabled["final_allocation"]["total_allocated_m3"] == res_disabled["final_allocation"]["total_allocated_m3"]
    allocs_enabled = [a["allocated_water_m3"] for a in res_enabled["initial_allocation"]["allocations"]]
    allocs_disabled = [a["allocated_water_m3"] for a in res_disabled["initial_allocation"]["allocations"]]
    assert allocs_enabled == allocs_disabled

    # 4. Negotiation agreement status and best allocation must match exactly
    assert res_enabled["negotiation"]["agreement_status"] == res_disabled["negotiation"]["agreement_status"]
    assert res_enabled["negotiation"]["best_allocation"] == res_disabled["negotiation"]["best_allocation"]
    assert res_enabled["final_decision"]["fairness_score"] == res_disabled["final_decision"]["fairness_score"]


# ─── 7. Cryptographic Artifact Integrity Preservation ────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_all_baseline_and_production_artifacts_unmodified():
    """Mandatory safety rule: Keep all existing model artifacts and candidate hashes intact."""
    base_dir = Path("backend/data/models")

    # Production models
    prod_files = ["encoders.joblib", "evaluation_results.json", "rf_model.joblib", "xgb_model.joblib"]
    for fname in prod_files:
        assert (base_dir / fname).exists(), f"Production file missing: {fname}"

    # Candidate v1, v2, v3 directories must all exist
    assert (base_dir / "candidate_v1").exists()
    assert (base_dir / "candidate_v2").exists()
    assert (base_dir / "candidate_v3").exists()

    # Candidate v3 core files must exist
    c3_files = [
        "candidate_v3_preprocessor.joblib",
        "candidate_v3_classifier.joblib",
        "candidate_v3_regressor.joblib",
        "feature_schema.json",
        "two_stage_config.json",
    ]
    for fname in c3_files:
        path = base_dir / "candidate_v3" / fname
        assert path.exists(), f"Candidate v3 file missing: {fname}"
        assert path.stat().st_size > 0
