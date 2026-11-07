# AquaMedi AI — Comprehensive REST API Reference

**Document ID:** `AQUAMEDI-API-REF-2026-V1`  
**Classification:** API Reference & Developer Integration Manual  
**Author:** Senior Backend Engineer & API Designer  
**Project:** AquaMedi AI — Agricultural Intelligence & Canal Water Management  
**Branch:** `feature/aquamedi-ai-product-transformation`  
**Date:** November 7, 2026  
**Status:** **ACADEMIC DEMONSTRATION VERIFIED (RELEASE V1.0)**

---

## 1. Overview & Protocol Standards

The AquaMedi AI REST API exposes endpoints for agronomic demand prediction, conformal uncertainty bounds, canal reach telemetry, linear programming water quota optimization, and multi-agent dispute mediation.

* **Base URL:** `http://127.0.0.1:8000/api/v1`
* **Transport:** HTTP/1.1 (Development) / HTTPS (Production)
* **Data Format:** `application/json` (UTF-8)
* **Authentication Scheme:** HTTP Authorization Header with Bearer JWT:  
  `Authorization: Bearer <access_token>`

---

## 2. Standard HTTP Status & Error Codes

| Status Code | Description | Semantic Application in AquaMedi AI |
|:---:|:---|:---|
| `200 OK` | Request Successful | Standard successful GET / POST operation |
| `201 Created` | Resource Created | New farm record or mediation session established |
| `400 Bad Request` | Validation Failure | Pydantic validation error (e.g., negative parcel area) |
| `401 Unauthorized` | Authentication Missing | Missing, expired, or invalid JWT Bearer token |
| `403 Forbidden` | Access Denied | Authenticated user lacks `expert` or `admin` role |
| `404 Not Found` | Resource Absent | Canal reach or farm identifier not found |
| `429 Too Many Requests` | Rate Limit Exceeded | More than 10 login attempts per 60 seconds |
| `500 Internal Error` | Server Exception | Uncaught runtime exception or solver failure |

### Standard Error Response Envelope
```json
{
  "detail": [
    {
      "loc": ["body", "area_hectares"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ],
  "status_code": 400,
  "timestamp": "2026-11-07T12:00:00Z"
}
```

---

## 3. Authentication & Security Endpoints (`/auth`)

### 3.1 Authenticate User & Issue JWT Token
* **Route:** `POST /api/v1/auth/login`
* **Access Level:** Public (Rate-limited to 10 requests / 60 seconds)
* **Request Headers:** `Content-Type: application/json`
* **Request Body:**
```json
{
  "username": "admin",
  "password": "<secure_password>"
}
```
* **Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "role": "admin",
  "username": "admin"
}
```
* **Response `401 Unauthorized`:**
```json
{
  "detail": "Invalid username or password"
}
```
* **Response `429 Too Many Requests`:**
```json
{
  "detail": "Rate limit exceeded. Maximum 10 attempts per minute allowed."
}
```

---

## 4. Machine Learning & Agronomy Endpoints (`/ml`)

### 4.1 Predict Crop Water Demand & Conformal Bounds
* **Route:** `POST /api/v1/ml/predict`
* **Access Level:** Public (Unauthenticated Farmer Access)
* **Request Body:**
```json
{
  "crop_type": "Sugarcane",
  "growth_stage": "Mid-Season",
  "soil_type": "Loamy",
  "area_hectares": 3.5,
  "temperature_c": 32.5,
  "humidity_pct": 45.0,
  "rainfall_mm": 0.0,
  "soil_moisture_pct": 22.0,
  "et0_mm": 5.2,
  "crop_coefficient": 1.20
}
```
* **Response `200 OK`:**
```json
{
  "prediction_m3_day": 221.38,
  "target_definition": "Net Crop Evapotranspiration Volume (NIR, eta = 1.0)",
  "conformal_interval": {
    "lower_bound_m3": 152.86,
    "upper_bound_m3": 289.90,
    "confidence_level": 0.90,
    "q_hat_base": 45.68,
    "area_scaling_factor": 1.50
  },
  "fao56_shadow_baseline": {
    "net_irrigation_requirement_m3": 209.30,
    "gross_application_requirement_m3": 299.00,
    "application_efficiency": 0.70,
    "ratio_to_net": 1.35
  },
  "status": "success",
  "timestamp": "2026-11-07T12:00:00Z"
}
```

### 4.2 Fetch SHAP Feature Attribution
* **Route:** `POST /api/v1/ml/explain`
* **Access Level:** Public
* **Request Body:** (Identical to `/ml/predict`)
* **Response `200 OK`:**
```json
{
  "base_value": 214.18,
  "prediction": 221.38,
  "feature_attributions": [
    {"feature": "area_hectares", "value": 3.5, "shap_value": 68.42},
    {"feature": "et0_mm", "value": 5.2, "shap_value": 18.25},
    {"feature": "crop_coefficient", "value": 1.20, "shap_value": 14.10},
    {"feature": "soil_moisture_pct", "value": 22.0, "shap_value": -24.80},
    {"feature": "temperature_c", "value": 32.5, "shap_value": 5.12}
  ]
}
```

---

## 5. Farmer Advisory & Crop Health Endpoints (`/farmer`)

### 5.1 Fetch Localized Crop Health & Soil Stress Advisory
* **Route:** `GET /api/v1/farmer/crop-health?crop=Sugarcane&soil_moisture=22.0&soil_type=Loamy`
* **Access Level:** Public
* **Response `200 OK`:**
```json
{
  "crop": "Sugarcane",
  "soil_moisture_pct": 22.0,
  "soil_type": "Loamy",
  "field_capacity_pct": 28.0,
  "permanent_wilting_point_pct": 14.0,
  "moisture_status": "MILD_DEFICIT",
  "stress_coefficient_ks": 0.957,
  "advisory_notes": "Soil moisture is approaching the replenishment threshold. Irrigation recommended within the next 48 hours to prevent flowering stress."
}
```

---

## 6. Canal Telemetry & Water Distribution Endpoints (`/dashboard`)

### 6.1 Get Canal Reach Distribution Status
* **Route:** `GET /api/v1/dashboard/canal-status`
* **Access Level:** Protected (Requires `expert` or `admin` token)
* **Request Headers:** `Authorization: Bearer <token>`
* **Response `200 OK`:**
```json
{
  "network_name": "Godavari Left Bank Distributary System",
  "total_inflow_m3s": 27.1,
  "reaches": [
    {
      "reach_id": "REACH-HEAD-01",
      "reach_type": "HEAD",
      "distance_km": "0 - 15 km",
      "discharge_m3s": 14.2,
      "status": "NORMAL"
    },
    {
      "reach_id": "REACH-MID-02",
      "reach_type": "MIDDLE",
      "distance_km": "15 - 40 km",
      "discharge_m3s": 9.8,
      "status": "NORMAL"
    },
    {
      "reach_id": "REACH-TAIL-03",
      "reach_type": "TAIL",
      "distance_km": "> 40 km",
      "discharge_m3s": 3.1,
      "status": "DEFICIT_ALERT",
      "deficit_percentage": -24.5
    }
  ],
  "disclaimer": "Demonstration Canal Telemetry"
}
```

---

## 7. Water Allocation Optimization Endpoints (`/allocation`)

### 7.1 Run Google OR-Tools GLOP Linear Solver
* **Route:** `POST /api/v1/allocation/optimize`
* **Access Level:** Protected (Requires `expert` or `admin` token)
* **Request Body:**
```json
{
  "available_supply_m3": 15000.0,
  "enforce_fairness_constraint": true,
  "subsistence_floor_pct": 0.50
}
```
* **Response `200 OK`:**
```json
{
  "solver_status": "OPTIMAL",
  "execution_time_ms": 12.4,
  "total_allocated_m3": 14980.5,
  "unallocated_reserve_m3": 19.5,
  "gini_fairness_index": 0.168,
  "tail_reach_satisfaction_ratio": 0.812,
  "allocations": [
    {
      "distributary_id": "D-01 (Head)",
      "requested_demand_m3": 3200.0,
      "allocated_quota_m3": 2850.0,
      "satisfaction_pct": 89.06
    },
    {
      "distributary_id": "D-08 (Tail)",
      "requested_demand_m3": 1800.0,
      "allocated_quota_m3": 1450.0,
      "satisfaction_pct": 80.56
    }
  ]
}
```

---

## 8. Multi-Agent Dispute Mediation Endpoints (`/negotiation`)

### 8.1 Execute Tripartite Dispute Resolution Session
* **Route:** `POST /api/v1/negotiation/mediate`
* **Access Level:** Protected (Requires `expert` or `admin` token)
* **Request Body:**
```json
{
  "disputed_distributary_id": "D-08 (Tail)",
  "farmer_claimed_demand_m3": 2400.0,
  "officer_offered_quota_m3": 1100.0,
  "max_negotiation_rounds": 5
}
```
* **Response `200 OK`:**
```json
{
  "session_id": "MED-2026-X892",
  "convergence_status": "AGREEMENT_REACHED",
  "rounds_executed": 4,
  "settlement_quota_m3": 1650.0,
  "nash_product": 0.482,
  "negotiation_log": [
    {"round": 1, "farmer_bid_m3": 2400.0, "officer_bid_m3": 1100.0, "concession_gap": 1300.0},
    {"round": 2, "farmer_bid_m3": 2150.0, "officer_bid_m3": 1300.0, "concession_gap": 850.0},
    {"round": 3, "farmer_bid_m3": 1850.0, "officer_bid_m3": 1500.0, "concession_gap": 350.0},
    {"round": 4, "farmer_bid_m3": 1650.0, "officer_bid_m3": 1650.0, "concession_gap": 0.0}
  ]
}
```

---

## 9. Scenario Simulation & What-If Endpoints (`/scenarios`)

### 9.1 Simulate Crisis Scenario
* **Route:** `POST /api/v1/scenarios/simulate`
* **Access Level:** Protected (Requires `expert` or `admin` token)
* **Request Body:**
```json
{
  "scenario_type": "SEVERE_DROUGHT",
  "inflow_reduction_pct": 40.0,
  "duration_days": 30
}
```
* **Response `200 OK`:**
```json
{
  "scenario": "SEVERE_DROUGHT",
  "impact_summary": {
    "reservoir_head_drop_meters": 3.8,
    "storage_depletion_timeline_days": 42,
    "rationing_policy": "EMERGENCY_FOOD_CROP_PRIORITY",
    "cash_crop_curtailment_pct": 45.0,
    "projected_yield_loss_pct": 14.2
  }
}
```
