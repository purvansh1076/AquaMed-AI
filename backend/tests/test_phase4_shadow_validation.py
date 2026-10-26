"""
AquaMediAI — Phase 4: Safe Agronomic Baseline Integration and Shadow Validation Tests
=====================================================================================

Offline unit, regression, and integration tests verifying:
1. FAO-56 and USDA-SCS agronomic equation correctness and unit conversions.
2. Missing and invalid input handling (no fabrication of weather/crop data).
3. Zero and small farm areas behavior.
4. Rainfall edge cases (zero rain vs heavy rain).
5. Shadow mode configuration (enabled vs disabled).
6. Backward compatibility of prediction API endpoints and response schemas.
7. Allocation and multi-agent negotiation regression stability under shadow mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.ml.agronomic_baseline import DeterministicAgronomicBaseline
from app.ml.predictor import PredictionResult, WaterDemandPredictor
from app.services.scenario_service import ScenarioService


@pytest.fixture(scope="module")
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def valid_farmer_payload() -> Dict[str, Any]:
    return {
        "farmer_id": "FARMER_PHASE4_01",
        "crop_type": "sugarcane",
        "soil_type": "clay_loam",
        "growth_stage": "mid_season",
        "season": "annual",
        "farm_area_hectares": 2.5,
        "et0_mm_per_day": 5.2,
        "kc_value": 1.25,
        "etc_mm_per_day": 6.5,
        "soil_whc_mm_per_m": 140.0,
        "preferred_start_hour": 6,
        "irrigation_window_hours": 6,
        "flexibility_score": 0.4,
        "urgency_score": 0.7,
        "crop_stress_index": 0.6,
        "temperature_celsius": 32.5,
        "humidity_percent": 45.0,
        "rainfall_mm": 2.0,
    }


# ─── 1. Agronomic Equations & Unit Conversions ───────────────────────────────

class TestAgronomicEquationsAndConversions:
    """Validate mathematical correctness of FAO-56 and USDA-SCS baseline calculations."""

    def test_volumetric_conversion_exactness(self):
        """
        Verify the physical conversion factor:
        1 mm of water depth over 1 hectare of surface area equals exactly 10.0 m³.
        Depth (1 mm = 0.001 m) * Area (1 ha = 10,000 m²) = 10 m³.
        """
        baseline = DeterministicAgronomicBaseline(default_application_efficiency=1.0)
        # 1 mm depth over 1 hectare at 100% efficiency should yield 10.0 m³
        res = baseline.calculate_daily_demand(
            farm_area_hectares=1.0,
            et0_mm_per_day=1.0,
            kc_value=1.0,
            rainfall_mm=0.0,
            application_efficiency=1.0,
        )
        assert res.volumetric_demand_m3_per_day == pytest.approx(10.0, rel=1e-4)

        # 5 mm depth over 3.5 hectares at 70% efficiency
        # Inet = 5 mm, Igross = 5 / 0.70 = 7.142857 mm
        # Volume = 7.142857 * 3.5 * 10 = 250.0 m³
        res2 = baseline.calculate_daily_demand(
            farm_area_hectares=3.5,
            et0_mm_per_day=5.0,
            kc_value=1.0,
            rainfall_mm=0.0,
            application_efficiency=0.70,
        )
        expected_vol = (5.0 / 0.70) * 3.5 * 10.0
        assert res2.volumetric_demand_m3_per_day == pytest.approx(round(expected_vol, 4), rel=1e-4)

    def test_growth_stage_kc_variations(self):
        """Verify demand changes appropriately across growth stages with varying Kc."""
        baseline = DeterministicAgronomicBaseline(default_application_efficiency=0.70)
        kc_initial = 0.40
        kc_mid = 1.20
        kc_late = 0.65

        res_init = baseline.calculate_daily_demand(2.0, 5.0, kc_initial, rainfall_mm=0.0)
        res_mid = baseline.calculate_daily_demand(2.0, 5.0, kc_mid, rainfall_mm=0.0)
        res_late = baseline.calculate_daily_demand(2.0, 5.0, kc_late, rainfall_mm=0.0)

        assert res_init.etc_mm_per_day == pytest.approx(2.0, rel=1e-3)
        assert res_mid.etc_mm_per_day == pytest.approx(6.0, rel=1e-3)
        assert res_late.etc_mm_per_day == pytest.approx(3.25, rel=1e-3)

        assert res_init.volumetric_demand_m3_per_day < res_late.volumetric_demand_m3_per_day < res_mid.volumetric_demand_m3_per_day

    def test_irrigation_efficiency_scaling(self):
        """Drip irrigation (85%) requires significantly less gross diversion than gravity flood (60%)."""
        baseline = DeterministicAgronomicBaseline()
        res_flood = baseline.calculate_daily_demand(2.0, 5.0, 1.0, rainfall_mm=0.0, application_efficiency=0.60)
        res_drip = baseline.calculate_daily_demand(2.0, 5.0, 1.0, rainfall_mm=0.0, application_efficiency=0.85)

        assert res_flood.gross_irrigation_depth_mm > res_drip.gross_irrigation_depth_mm
        assert res_flood.volumetric_demand_m3_per_day > res_drip.volumetric_demand_m3_per_day
        ratio = res_flood.volumetric_demand_m3_per_day / res_drip.volumetric_demand_m3_per_day
        assert ratio == pytest.approx(0.85 / 0.60, rel=1e-3)


# ─── 2. Missing & Invalid Input Validation (Never Fabricate) ────────────────

class TestMissingAndInvalidInputs:
    """Ensure missing or non-physical inputs are rejected in shadow mode without fabrication."""

    def test_missing_farm_area_returns_unavailable(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        # Directly test shadow baseline input validation when farm_area is missing
        est, comp = predictor._compute_shadow_baseline(
            raw_data={"rainfall_mm": 5.0, "et0_mm_per_day": 4.0, "kc_value": 1.0},
            legacy_prediction=50.0,
        )
        assert est is None
        assert comp["status"] == "unavailable"
        assert comp["input_validation"]["is_valid"] is False
        assert any("farm_area_hectares" in err for err in comp["input_validation"]["errors"])

    def test_missing_rainfall_not_fabricated(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        del payload["rainfall_mm"]

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 is None
        assert result.shadow_comparison["status"] == "unavailable"
        assert any("rainfall_mm" in err for err in result.shadow_comparison["input_validation"]["errors"])

    def test_negative_et0_rejected(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        payload["et0_mm_per_day"] = -3.5

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 is None
        assert result.shadow_comparison["status"] == "unavailable"
        assert any("et0_mm_per_day" in err for err in result.shadow_comparison["input_validation"]["errors"])

    def test_zero_or_negative_kc_rejected(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        payload["kc_value"] = 0.0

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 is None
        assert result.shadow_comparison["status"] == "unavailable"
        assert any("kc_value" in err for err in result.shadow_comparison["input_validation"]["errors"])


# ─── 3. Zero and Very Small Farm Areas ──────────────────────────────────────

class TestZeroAndSmallFarmAreas:
    """Verify handling of zero, negative, and micro farm sizes."""

    def test_zero_farm_area_marked_unavailable(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        payload["farm_area_hectares"] = 0.0

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 is None
        assert result.shadow_comparison["status"] == "unavailable"
        assert any("farm_area_hectares must be > 0" in err for err in result.shadow_comparison["input_validation"]["errors"])

    def test_negative_farm_area_marked_unavailable(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        payload["farm_area_hectares"] = -1.5

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 is None
        assert result.shadow_comparison["status"] == "unavailable"

    def test_very_small_farm_area_calculated_correctly(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        payload["farm_area_hectares"] = 0.05  # 500 m²

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 is not None
        assert result.shadow_comparison["status"] == "available"
        assert result.shadow_agronomic_estimate_m3 > 0.0


# ─── 4. Rainfall Edge Cases ──────────────────────────────────────────────────

class TestRainfallEdgeCases:
    """Verify effective rainfall behavior with zero rain, normal rain, and heavy storm events."""

    def test_zero_rainfall(self):
        baseline = DeterministicAgronomicBaseline(default_application_efficiency=0.70)
        res = baseline.calculate_daily_demand(1.0, 5.0, 1.0, rainfall_mm=0.0)
        assert res.effective_precipitation_mm == 0.0
        assert res.net_irrigation_depth_mm == res.etc_mm_per_day

    def test_heavy_rainfall_exceeding_etc_zeros_irrigation_requirement(self):
        """When effective precipitation exceeds ETc, net irrigation requirement drops to 0."""
        baseline = DeterministicAgronomicBaseline(default_application_efficiency=0.70)
        res = baseline.calculate_daily_demand(2.0, 4.0, 1.0, rainfall_mm=50.0)
        assert res.effective_precipitation_mm >= res.etc_mm_per_day
        assert res.net_irrigation_depth_mm == 0.0
        assert res.gross_irrigation_depth_mm == 0.0
        assert res.volumetric_demand_m3_per_day == 0.0

    def test_safe_handling_of_zero_agronomic_demand_in_shadow_comparison(self, valid_farmer_payload):
        """Safe difference percentage calculation when deterministic demand is 0."""
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        payload = dict(valid_farmer_payload)
        payload["rainfall_mm"] = 100.0  # Massive rain event

        result = predictor.predict_single(payload, enable_shadow_mode=True)
        assert result.shadow_agronomic_estimate_m3 == 0.0
        assert result.shadow_comparison["agronomic_demand_m3"] == 0.0
        # Percentage must not raise ZeroDivisionError and should safely be None
        assert result.shadow_comparison["difference_percent"] is None


# ─── 5. Shadow Mode Configuration ────────────────────────────────────────────

class TestShadowModeConfiguration:
    """Verify feature flag toggling between enabled and disabled."""

    def test_shadow_mode_disabled_yields_none(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        result = predictor.predict_single(valid_farmer_payload, enable_shadow_mode=False)

        assert result.predicted_water_demand_m3 >= 5.0
        assert result.shadow_agronomic_estimate_m3 is None
        assert result.shadow_comparison is None

    def test_shadow_mode_enabled_yields_complete_audit(self, valid_farmer_payload):
        predictor = WaterDemandPredictor.from_artifacts(get_settings().model_dir_path)
        result = predictor.predict_single(valid_farmer_payload, enable_shadow_mode=True)

        assert result.shadow_agronomic_estimate_m3 is not None
        assert result.shadow_comparison is not None
        assert result.shadow_comparison["status"] == "available"
        assert result.shadow_comparison["difference_m3"] is not None
        assert "provenance_note" in result.shadow_comparison
        assert "disclaimer" in result.shadow_comparison
        assert result.shadow_comparison["is_empirical_error"] is False


# ─── 6. Backward Compatibility of API Responses ──────────────────────────────

class TestAPIBackwardCompatibility:
    """Verify existing endpoint contracts continue to operate without breaking changes."""

    def test_single_prediction_endpoint_has_legacy_keys_and_optional_shadow(
        self, api_client: TestClient, valid_farmer_payload
    ):
        resp = api_client.post("/api/v1/predictions", json={"farmer_data": valid_farmer_payload, "model_name": "XGBoost"})
        assert resp.status_code == 200
        data = resp.json()

        # Legacy fields MUST exist
        assert "farmer_id" in data
        assert "predicted_water_demand_m3" in data
        assert "model_name" in data
        assert "model_version" in data
        assert "warning" in data
        assert "input_summary" in data

        # Shadow mode fields exist as optional enhancements
        assert "shadow_agronomic_estimate_m3" in data
        assert "shadow_comparison" in data
        assert data["farmer_id"] == valid_farmer_payload["farmer_id"]
        assert data["predicted_water_demand_m3"] > 0

    def test_batch_prediction_endpoint(self, api_client: TestClient, valid_farmer_payload):
        batch_payload = {
            "farmers": [
                valid_farmer_payload,
                {**valid_farmer_payload, "farmer_id": "FARMER_PHASE4_02", "farm_area_hectares": 3.0},
            ],
            "model_name": "RandomForest",
        }
        resp = api_client.post("/api/v1/predictions/batch", json=batch_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        for pred in data["predictions"]:
            assert "predicted_water_demand_m3" in pred
            assert "shadow_agronomic_estimate_m3" in pred
            assert "shadow_comparison" in pred


# ─── 7. Allocation & Negotiation Regression Behavior ─────────────────────────

class TestAllocationAndNegotiationRegression:
    """Verify that full pipeline run_scenario() runs deterministically with shadow mode enabled."""

    def test_run_scenario_succeeds_with_shadow_data(self):
        service = ScenarioService()
        result = service.run_scenario(
            scenario_type="normal_water",
            n_farmers=4,
            seed=42,
            model_name="XGBoost",
        )

        assert result["status"].upper() in ("AGREED", "PARTIAL", "IMPASSE")
        assert len(result["predictions"]) == 4
        assert len(result["farmers"]) == 4
        assert "final_allocation" in result

        # Verify shadow fields are included in scenario predictions
        for p in result["predictions"]:
            assert "predicted_water_demand_m3" in p
            assert "shadow_agronomic_estimate_m3" in p
            assert "shadow_comparison" in p
            assert p["shadow_comparison"]["provenance_note"] is not None
            assert p["shadow_comparison"]["is_empirical_error"] is False

    def test_water_allocation_conservation_preserved(self):
        """Allocation total must not exceed available water."""
        service = ScenarioService()
        result = service.run_scenario(
            scenario_type="moderate_shortage",
            n_farmers=4,
            seed=42,
            model_name="XGBoost",
        )
        available = result["available_water_m3"]
        allocations = result["initial_allocation"]["allocations"]
        total_allocated = sum(a["allocated_water_m3"] for a in allocations)

        assert total_allocated <= available + 1e-3
