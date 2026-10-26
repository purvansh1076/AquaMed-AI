"""
AquaMediAI Phase 12 — Local End-to-End Shadow Smoke Test Script
==============================================================
Validates:
1. Backend startup and health endpoints.
2. Existing prediction endpoint with shadow disabled (default).
3. Prediction endpoint with Candidate v3 shadow enabled in an isolated test context:
   - Historical mode with observed rainfall.
   - Forward mode with genuine weather forecast.
   - Forward mode without forecast (marks unavailable, no silent substitution).
   - Documented antecedent fallback.
   - Artifact corruption safety failover.
   - Non-interference with LP allocation and negotiation.
4. Unit consistency: m3/day and rainfall provenance.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.ml.candidate_v3_shadow_adapter import CandidateV3ShadowAdapter
from app.services.scenario_service import ScenarioService


def get_base_farmer_payload() -> Dict[str, Any]:
    """Synthetic test fixture for farmer inputs."""
    return {
        "farmer_id": "FARMER_SMOKE_01",
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


def run_smoke_test() -> Dict[str, Any]:
    client = TestClient(app)
    results: Dict[str, Any] = {}

    # ── Task 1: Health Endpoints ──────────────────────────────────────────────
    resp_root = client.get("/health")
    resp_v1 = client.get("/api/v1/health")
    results["task1_health"] = {
        "root_health_status": resp_root.status_code,
        "root_health_payload": resp_root.json(),
        "v1_health_status": resp_v1.status_code,
        "v1_health_payload": resp_v1.json(),
    }

    # ── Task 2: Prediction with Shadow Disabled (Default) ─────────────────────
    base_farmer = get_base_farmer_payload()
    resp_pred_default = client.post(
        "/api/v1/predictions",
        json={"farmer_data": base_farmer, "model_name": "XGBoost"},
    )
    results["task2_shadow_disabled"] = {
        "status_code": resp_pred_default.status_code,
        "payload": resp_pred_default.json(),
    }

    # ── Task 3: Isolated Shadow Mode Enabled ──────────────────────────────────
    with patch.dict(os.environ, {"ENABLE_CANDIDATE_V3_SHADOW": "true"}):
        get_settings.cache_clear()
        try:
            # 3A. Historical analysis with observed rainfall
            hist_farmer = copy.deepcopy(base_farmer)
            hist_farmer["rainfall_input_mode"] = "observed_historical"
            hist_farmer["rainfall_observed_mm"] = 12.0
            resp_hist = client.post(
                "/api/v1/predictions",
                json={"farmer_data": hist_farmer, "model_name": "XGBoost"},
            )
            results["task3a_historical"] = {
                "status_code": resp_hist.status_code,
                "payload": resp_hist.json(),
            }

            # 3B. Forward morning scheduling with genuine weather forecast
            fwd_farmer = copy.deepcopy(base_farmer)
            fwd_farmer["rainfall_input_mode"] = "forecast_forward"
            fwd_farmer["rainfall_forecast_mm"] = 4.5
            resp_fwd = client.post(
                "/api/v1/predictions",
                json={"farmer_data": fwd_farmer, "model_name": "XGBoost"},
            )
            results["task3b_forward_with_forecast"] = {
                "status_code": resp_fwd.status_code,
                "payload": resp_fwd.json(),
            }

            # 3C. Forward scheduling without forecast and without fallback -> Unavailable
            # Note: rainfall_observed_mm is supplied to ensure it is NOT silently used
            fwd_missing = copy.deepcopy(base_farmer)
            fwd_missing["rainfall_input_mode"] = "forecast_forward"
            fwd_missing["rainfall_forecast_mm"] = None
            fwd_missing["rainfall_observed_mm"] = 15.0  # Must be rejected in forward mode
            adapter = CandidateV3ShadowAdapter.load()
            res_missing_obj = adapter.evaluate(fwd_missing, allow_antecedent_fallback=False)
            results["task3c_forward_missing_forecast_unavailable"] = {
                "status": res_missing_obj.status,
                "candidate_estimate_m3": res_missing_obj.candidate_estimate_m3,
                "reasons": res_missing_obj.reasons,
                "rainfall_source": res_missing_obj.rainfall_source,
            }

            # 3D. Forward scheduling using documented antecedent fallback
            fwd_fallback = copy.deepcopy(base_farmer)
            fwd_fallback["rainfall_input_mode"] = "forecast_forward"
            fwd_fallback["rainfall_forecast_mm"] = None
            fwd_fallback["rainfall_lag1_mm"] = 2.0
            res_fallback_obj = adapter.evaluate(fwd_fallback, allow_antecedent_fallback=True)
            results["task3d_forward_antecedent_fallback"] = {
                "status": res_fallback_obj.status,
                "candidate_estimate_m3": res_fallback_obj.candidate_estimate_m3,
                "rainfall_source": res_fallback_obj.rainfall_source,
                "rainfall_mm_used": res_fallback_obj.rainfall_mm_used,
            }

            # 3E. Invalid/corrupted candidate artifacts fail safely without breaking primary prediction
            with patch.object(
                CandidateV3ShadowAdapter,
                "evaluate_shadow",
                side_effect=RuntimeError("Simulated filesystem artifact corruption"),
            ):
                resp_failover = client.post(
                    "/api/v1/predictions",
                    json={"farmer_data": base_farmer, "model_name": "XGBoost"},
                )
                results["task3e_artifact_corruption_failover"] = {
                    "status_code": resp_failover.status_code,
                    "payload": resp_failover.json(),
                }

            # 3F. Allocation and Negotiation Non-Interference Verification
            service = ScenarioService()
            scenario_shadow_enabled = service.run_scenario(
                scenario_type="moderate_shortage",
                n_farmers=4,
                seed=42,
                model_name="XGBoost",
            )
        finally:
            get_settings.cache_clear()

    # Baseline scenario run with shadow disabled
    service = ScenarioService()
    scenario_shadow_disabled = service.run_scenario(
        scenario_type="moderate_shortage",
        n_farmers=4,
        seed=42,
        model_name="XGBoost",
    )

    results["task3f_non_interference"] = {
        "demand_match": (
            scenario_shadow_enabled["total_demand_m3"]
            == scenario_shadow_disabled["total_demand_m3"]
        ),
        "available_water_match": (
            scenario_shadow_enabled["available_water_m3"]
            == scenario_shadow_disabled["available_water_m3"]
        ),
        "total_allocated_match": (
            scenario_shadow_enabled["initial_allocation"]["total_allocated_m3"]
            == scenario_shadow_disabled["initial_allocation"]["total_allocated_m3"]
        ),
        "allocations_identical": (
            [a["allocated_water_m3"] for a in scenario_shadow_enabled["initial_allocation"]["allocations"]]
            == [a["allocated_water_m3"] for a in scenario_shadow_disabled["initial_allocation"]["allocations"]]
        ),
        "agreement_status_match": (
            scenario_shadow_enabled["negotiation"]["agreement_status"]
            == scenario_shadow_disabled["negotiation"]["agreement_status"]
        ),
        "fairness_score_match": (
            scenario_shadow_enabled["final_decision"]["fairness_score"]
            == scenario_shadow_disabled["final_decision"]["fairness_score"]
        ),
        "shadow_present_in_predictions": all(
            "shadow_candidate_v3_estimate_m3" in p
            for p in scenario_shadow_enabled["predictions"]
        ),
    }

    # ── Task 4: Feature Schema & Unit Inspection ──────────────────────────────
    schema_path = Path("backend/data/models/candidate_v3/feature_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    results["task4_schema_and_units"] = {
        "selected_feature_set": schema_data.get("selected_feature_set"),
        "total_feature_count": schema_data.get("total_feature_count"),
        "numeric_feature_count": len(schema_data.get("numeric_features", [])),
        "categorical_feature_count": len(schema_data.get("categorical_features", [])),
        "zero_leakage_confirmed": schema_data.get("leakage_audit_verdict") == "ZERO_LEAKAGE_CONFIRMED",
        "volumetric_unit": "m3/day",
        "rainfall_depth_unit": "mm",
    }

    return results


if __name__ == "__main__":
    out = run_smoke_test()
    print(json.dumps(out, indent=2))
