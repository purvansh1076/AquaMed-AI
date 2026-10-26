"""
AquaMediAI — Comprehensive Local End-to-End System Verification Script
======================================================================
Tests all primary API workflows, scenarios, predictions, SHAP, and disclaimers.
"""

from __future__ import annotations

import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_full_verification():
    results = {}

    # 1. Health Endpoints
    r1 = client.get("/health")
    r2 = client.get("/api/v1/health")
    results["health_root"] = {"status": r1.status_code, "data": r1.json()}
    results["health_api"] = {"status": r2.status_code, "data": r2.json()}

    # 2. OpenAPI Specs
    r_docs = client.get("/openapi.json")
    results["openapi"] = {"status": r_docs.status_code, "title": r_docs.json().get("info", {}).get("title")}

    # 3. Single Prediction & Shadow Mode
    sample_farmer = {
        "farmer_id": "FARMER_TEST_01",
        "crop_type": "wheat",
        "soil_type": "loam",
        "growth_stage": "mid_season",
        "season": "rabi",
        "farm_area_hectares": 3.5,
        "et0_mm_per_day": 5.5,
        "kc_value": 1.15,
        "etc_mm_per_day": 6.325,
        "soil_whc_mm_per_m": 130.0,
        "preferred_start_hour": 6,
        "irrigation_window_hours": 4,
        "flexibility_score": 0.6,
        "urgency_score": 0.5,
        "crop_stress_index": 0.4,
        "temperature_celsius": 26.0,
        "humidity_percent": 50.0,
        "rainfall_mm": 1.5,
    }
    r_pred = client.post("/api/v1/predictions", json={"farmer_data": sample_farmer, "model_name": "XGBoost"})
    pred_data = r_pred.json()
    results["single_prediction"] = {
        "status": r_pred.status_code,
        "predicted_water_demand_m3": pred_data.get("predicted_water_demand_m3"),
        "shadow_agronomic_estimate_m3": pred_data.get("shadow_agronomic_estimate_m3"),
        "difference_m3": pred_data.get("shadow_comparison", {}).get("difference_m3"),
        "difference_percent": pred_data.get("shadow_comparison", {}).get("difference_percent"),
        "provenance_note": bool(pred_data.get("shadow_comparison", {}).get("provenance_note")),
    }

    # 4. Batch Prediction
    r_batch = client.post(
        "/api/v1/predictions/batch",
        json={
            "farmers": [
                sample_farmer,
                {**sample_farmer, "farmer_id": "FARMER_TEST_02", "farm_area_hectares": 5.0},
            ],
            "model_name": "XGBoost",
        },
    )
    results["batch_prediction"] = {"status": r_batch.status_code, "count": r_batch.json().get("count")}

    # 5. Scenarios (Normal, Moderate, Severe, Sudden Rain)
    scenario_runs = {}
    for sc in ["normal_water", "moderate_shortage", "severe_shortage", "sudden_rainfall"]:
        r_sc = client.post(
            "/api/v1/scenarios/run",
            json={"scenario_type": sc, "n_farmers": 4, "seed": 42, "model_name": "XGBoost"},
        )
        sc_data = r_sc.json()
        scenario_runs[sc] = {
            "status_code": r_sc.status_code,
            "agreement_status": sc_data.get("status"),
            "available_water_m3": sc_data.get("available_water_m3"),
            "total_demand_m3": sc_data.get("total_demand_m3"),
            "n_predictions": len(sc_data.get("predictions", [])),
            "has_shadow_in_predictions": all("shadow_agronomic_estimate_m3" in p for p in sc_data.get("predictions", [])),
            "has_explanations": bool(sc_data.get("explanations")),
            "final_allocation_valid": sc_data.get("final_decision", {}).get("is_physically_valid"),
        }
    results["scenarios"] = scenario_runs

    # 6. Conflicts, Allocation, Negotiation Endpoints
    r_conf = client.post("/api/v1/conflicts", json={"scenario_type": "moderate_shortage", "n_farmers": 4, "seed": 42})
    r_alloc = client.post("/api/v1/allocations", json={"scenario_type": "moderate_shortage", "n_farmers": 4, "seed": 42})
    r_nego = client.post("/api/v1/negotiations", json={"scenario_type": "moderate_shortage", "n_farmers": 4, "seed": 42})

    results["conflict_endpoint"] = {"status": r_conf.status_code, "conflicts_found": len(r_conf.json().get("conflicts", []))}
    results["allocation_endpoint"] = {"status": r_alloc.status_code, "status_str": r_alloc.json().get("status")}
    results["negotiation_endpoint"] = {"status": r_nego.status_code, "agreement_status": r_nego.json().get("agreement_status")}

    # 7. Error Handling (Validation Errors)
    r_err_scenario = client.post("/api/v1/scenarios/run", json={"scenario_type": "invalid_type", "n_farmers": 4})
    results["invalid_scenario_error"] = {"status": r_err_scenario.status_code}

    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    run_full_verification()
