# AquaMediAI — API Documentation

**Base URL**: `http://localhost:8000` (development, from .env APP_PORT=8000)  
**Framework**: FastAPI (openapi auto-generated)  
**Authentication**: None (academic prototype; CORS configured for local dev)  
**Timeout**: Default httpx timeout 30s  

## 1. Authentication & CORS

- **CORS Origins** (from `.env`): `http://localhost:5173,http://localhost:3000`
- All endpoints allow `GET`, `POST`, `PUT`, `DELETE` methods where appropriate
- No API keys or auth tokens; the system is an academic prototype

## 2. Endpoint Reference

### 2.1 Root

**GET `/`**

| Field | Type | Description |
|-------|------|-------------|
| `message` | `str` | "AquaMediAI API is running" |
| `status` | `str` | "ok" |

**Example response**:
```json
{
  "message": "AquaMediAI API is running",
  "status": "ok"
}
```

---

### 2.2 Health Check

**GET `/health`**

Checks that the FastAPI app and (optionally) the database are operational.

| Field | Type | Description |
|-------|------|-------------|
| `api` | `str` | Always `"online"` when endpoint is reachable |
| `database` | `str` | `"connected"` if PostgreSQL reachable and psycopg2 installed, otherwise `"unreachable"` |

**Example response (with PostgreSQL)**:
```json
{
  "api": "online",
  "database": "connected"
}
```

**Example response (without PostgreSQL / psycopg2 missing)**:
```json
{
  "api": "online",
  "database": "unreachable"
}
```

---

### 2.3 Scenario Types

**GET `/scenarios`**

Returns the 8 supported scenario types with brief descriptions.

| Field | Type | Description |
|-------|------|-------------|
| `scenario_types` | `list[str]` | `["normal_water", "moderate_shortage", "severe_shortage", "sudden_rainfall", "canal_reduction", "simultaneous_demand", "high_urgency_farmer", "flexible_farmer"]` |

**Example response**:
```json
{
  "scenario_types": ["normal_water", "moderate_shortage", "severe_shortage", "sudden_rainfall", "canal_reduction", "simultaneous_demand", "high_urgency_farmer", "flexible_farmer"]
}
```

---

### 2.4 Water Demand Prediction

**POST `/predict`**

Predict water demand for a farmer profile.

**Request Body (JSON)**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `farm_area_hectares` | `float` | Yes | Cultivated area |
| `et0_mm_per_day` | `float` | Yes | Reference ET₀ |
| `kc_value` | `float` | Yes | Crop coefficient K_c |
| `etc_mm_per_day` | `float` | Yes | ET_c = ET_0 × K_c |
| `soil_whc_mm_per_m` | `float` | No | Soil water-holding capacity |
| `preferred_start_hour` | `int` | No | Desired irrigation start (0-23) |
| `irrigation_window_hours` | `int` | No | Irrigation window duration |
| `flexibility_score` | `float` | No | Schedule flexibility [0,1] |
| `urgency_score` | `float` | No | Urgency level [0,1] |
| `crop_stress_index` | `float` | No | Crop stress indicator [0,1] |
| `temperature_celsius` | `float` | No | Daily max temperature |
| `humidity_percent` | `float` | No | Relative humidity (%) |
| `rainfall_mm` | `float` | No | Daily rainfall (mm) |
| `crop_type_encoded` | `int` | No | Crop type encoding |
| `soil_type_encoded` | `int` | No | Soil type encoding |
| `growth_stage_encoded` | `int` | No | Growth stage encoding |
| `season_encoded` | `int` | No | Season encoding |
| `area_x_etc` | `float` | No | Engineered: farm_area_hectares × etc_mm_per_day |
| `urgency_x_stress` | `float` | No | Engineered: urgency_score × crop_stress_index |
| `et0_x_kc` | `float` | No | Engineered: ET_0 × K_c |
| `rain_deficit` | `float` | No | Engineered: potential demand - rainfall |
| `flexibility_window` | `float` | No | Engineered: flexibility_score × irrigation_window_hours |

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `predicted_demand_m3` | `float` | Water demand prediction (m³/day) |
| `model_name` | `str` | "RandomForest" or "XGBoost" (whichever was loaded) |
| `model_version` | `str` | "1.0.0" |
| `features_used` | `int` | Number of non-null features provided |
| `disclaimer` | `str` | "Based on synthetic data generated via FAO-56 single-crop-coefficient method" |

**Example response**:
```json
{
  "predicted_demand_m3": 245.3,
  "model_name": "XGBoost",
  "model_version": "1.0.0",
  "features_used": 22,
  "disclaimer": "Based on synthetic data generated via FAO-56 single-crop-coefficient method"
}
```

**Error responses**:
- `422 Unprocessable Entity` — missing or out-of-range feature values
- `500 Internal Server Error` — model artifacts not found (run training pipeline)

---

### 2.5 Water Allocation

**POST `/allocate`**

Allocate available water among farmer agents using the GLOP LP optimizer.

**Request Body (JSON)**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_profiles` | `list` | Yes | List of farmer profiles (see below) |
| `available_water_m3` | `float` | Yes | Total available water for this scenario |

**Agent Profile Object**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `farmer_id` | `str` | Yes | Unique farmer identifier |
| `predicted_water_demand` | `float` | Yes | Farmer's predicted demand (m³/day) |
| `minimum_water_requirement` | `float` | Yes | Minimum m³/day for crop survival |
| `maximum_water_requirement` | `float` | Yes | Maximum m³/day physical limit |
| `urgency` | `float` | No | Urgency level [0,1]; default 0.5 |
| `crop_sensitivity` | `float` | No | Crop sensitivity [0,1]; default 0.5 |
| `growth_stage` | `str` | No | Growth stage name |
| `crop` | `str` | No | Crop name |

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `allocations` | `list[FarmerAllocation]` | Per-farmer allocation details |
| `total_allocated_m3` | `float` | Sum of all allocations |
| `remaining_water_m3` | `float` | available_water - total_allocated |
| `utilization` | `float` | total_allocated / available_water (clamped [0,1]) |
| `fairness_score` | `float` | Jain's Fairness Index on satisfaction ratios |
| `allocation_method` | `str` | "lp_optimal" | "lp_relaxed" | "proportional_fallback" | "empty" |
| `solver_status` | `str` | WaterAllocator solver status |
| `verification` | `ConstraintVerificationResult` | Independent constraint check result |
| `total_demand_m3` | `float` | Sum of all farmers' predicted demands |
| `total_minimum_requirement_m3` | `float` | Sum of all farmers' minimum requirements |

**FarmerAllocation Object**:
| Field | Type | Description |
|-------|------|-------------|
| `farmer_id` | `str` | Farmer identifier |
| `allocated_water_m3` | `float` | Water allocated (m³) |
| `predicted_demand_m3` | `float` | Predicted demand (m³) |
| `minimum_requirement_m3` | `float` | Minimum requirement (m³) |
| `maximum_requirement_m3` | `float` | Maximum requirement (m³) |
| `urgency` | `float` | Urgency level [0,1] |
| `crop_sensitivity` | `float` | Crop sensitivity [0,1] |
| `growth_stage` | `str` | Growth stage name |
| `crop` | `str` | Crop name |
| `constraint_status` | `str` | "satisfied" | "at_maximum" | "minimum_relaxed" |
| `unmet_demand_m3` | `float` | max(0, predicted_demand - allocated) |
| `minimum_shortfall_m3` | `float` | max(0, minimum_requirement - allocated) |

**ConstraintVerificationResult**:
| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | `bool` | All hard constraints satisfied |
| `total_water_ok` | `bool` | total_allocated <= available_water + tolerance |
| `non_negative_ok` | `bool` | All allocations >= 0 |
| `maximum_ok` | `bool` | All allocations <= maximum_requirement |
| `no_nan_ok` | `bool` | No NaN/Inf values |
| `all_farmers_present` | `bool` | All expected farmers present |
| `violations` | `list[str]` | List of violation strings (empty if valid) |

**Error responses**:
- `400 Bad Request` — invalid agent profile (missing fields, negative water, etc.)
- `422 Unprocessable Entity` — validation error (structured Pydantic errors)

---

### 2.6 Negotiation

**POST `/negotiate`**

Run the full multi-agent negotiation pipeline.

**Request Body (JSON)**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agents` | `list` | Yes | List of agent profiles (same structure as `/allocate` `agent_profiles`) |
| `available_water_m3` | `float` | Yes | Total available water |
| `config` | `object` | No | NegotiationConfig override (optional); see NegotiationConfig fields |

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `agreement` | `Agreement` | Full agreement object (see Agreement schema below) |
| `status` | `str` | "completed" or "failed" |

**Agreement Summary Object**:
| Field | Type | Description |
|-------|------|-------------|
| `agreement_status` | `str` | "AGREED" | "MAX_ROUNDS_REACHED" | "NO_FEASIBLE_IMPROVEMENT" | "FAILED" |
| `final_allocation` | `dict` | farmer_id → m³ |
| `negotiation_rounds` | `int` | Number of rounds that ran |
| `fairness_score` | `float` | Jain's Index on final allocation |
| `water_utilization` | `float` | total_allocated / available_water |
| `termination_reason` | `str` | Human-readable cause |
| `round_nash_history` | `list[float]` | Nash objective per round |
| `round_fairness_history` | `list[float]` | Fairness per round |
| `concessions` | `list` | Concession trail |
| `is_physically_valid` | `bool` | Final constraint verification |

**Error responses**:
- `400 Bad Request` — no agents, negative water, invalid config
- `422 Unprocessable Entity` — validation error

---

### 2.7 Determinism Check

**GET `/determinism-check`**

Verifies that the system produces identical outputs given identical inputs.

**Response**:
| Field | Type | Description |
|-------|------|-------------|
| `same_input_same_output` | `bool` | True if RF + XGB give same rankings with seed=42 |
| `seed_used` | `int` | The random seed value (42) |

**Example response**:
```json
{
  "same_input_same_output": true,
  "seed_used": 42
}
```

---

### 2.8 Explanations

**GET `/explain/{farmer_id}`**

SHAP explanation for a single farmer prediction.

**Path Parameter**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `farmer_id` | `str` | Farmer identifier (must match an agent in the current model context) |

**Response**:
| Field | Type | Description |
|-------|------|-------------|
| `base_value` | `float` | SHAP base value (model expectation) |
| `feature_names` | `list[str]` | 22 feature column names |
| `shap_values` | `list[float]` | SHAP impact per feature (positive = increases demand prediction, negative = decreases) |
| `explanation_type` | `str` | "global" or "local" |
| `disclaimer` | `str` | "Based on synthetic data generated via FAO-56 single-crop-coefficient method" |

**Example response**:
```json
{
  "base_value": 210.5,
  "feature_names": ["farm_area_hectares", "et0_mm_per_day", "kc_value", "etc_mm_per_day", "soil_whc_mm_per_m", "preferred_start_hour", "irrigation_window_hours", "flexibility_score", "urgency_score", "crop_stress_index", "temperature_celsius", "humidity_percent", "rainfall_mm", "crop_type_encoded", "soil_type_encoded", "growth_stage_encoded", "season_encoded", "area_x_etc", "urgency_x_stress", "et0_x_kc", "rain_deficit", "flexibility_window"],
  "shap_values": [8.2, -3.1, 5.7, ...],  // one per feature, sum + base = prediction
  "explanation_type": "local",
  "disclaimer": "Based on synthetic data generated via FAO-56 single-crop-coefficient method"
}
```

---

### 2.9 API Error Format

All error responses follow FastAPI's standard validation error format:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "validation error message",
      "type": "validation_error"
    }
  ]
}
```

## 3. Response Models (Defined in FastAPI)

All response models are defined using Pydantic in the backend. The full OpenAPI schema is available at `GET /openapi.json` or `GET /docs` (Swagger UI).

## 4. Production Considerations

- **CORS**: Configure `BACKEND_CORS_ORIGINS` in production deployment
- **Credentials**: `.env` must not be committed; `DATABASE_URL`, `SECRET_KEY` are runtime secrets
- **PostgreSQL**: Required for persistent storage; `psycopg2-binary` must be installed
- **Model Artifacts**: `data/models/` must contain `xgb_model.joblib`, `rf_model.joblib`, `encoders.joblib`, `evaluation_results.json` before inference
- **Rate Limiting**: Not implemented in this academic prototype
- **Request Size**: Limited by FastAPI default (10MB body limit)
- **Timeouts**: httpx client timeout 30s; increase if negotiation involves many rounds

---
*API documentation generated from source code inspection. Synthetic data disclaimer applies throughout.*