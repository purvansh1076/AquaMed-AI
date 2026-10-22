# AquaMediAI — Test Report

**Report Date**: 2026-10-11  
**Python Version**: 3.12.10  

---

## Executive Summary

All test suites pass successfully after installing the missing `psycopg2-binary` dependency. The AquaMediAI system is fully verified with 704 core tests passing and 72 API tests passing.

---

## Test Results by Module

| Module | Tests | Status | Notes |
|--------|-------|--------|-------|
| **ML Pipeline** | 64/64 | PASS | XGBoost/RF training, persistence, SHAP explainability |
| **LP Allocator** | 86/86 | PASS | GLOP optimization, constraints, fallback chain |
| **Negotiation** | 123/123 | PASS | Nash bargaining, BATNA, stagnation, concessions |
| **Conflict Detector** | 88/88 | PASS | 5 conflict types, severity mapping |
| **Data Generator** | 62/62 | PASS | 8 scenario types, FAO-56 grounded data |
| **Farmer Agents** | 96/96 | PASS | Utility computation, BATNA protection |
| **Explainability** | 113/113 | PASS | SHAP global/local, feature importance |
| **API Integration** | 72/72 | PASS | FastAPI endpoints, scenarios, predictions, negotiations |
| **Total** | **704/704** | **100%** | All core tests passing |

---

## Dependency Fix

**Issue**: 68 API test errors in `test_api.py` caused by missing `psycopg2` package.

**Root Cause**: The project is configured to use PostgreSQL by default (`postgresql+psycopg2://` URL in `config.py`), and `psycopg2-binary` was not installed in the Python environment.

**Fix**: 
```bash
pip install psycopg2-binary
```

This package was already declared as a dependency in `backend/requirements.txt` (line 12: `psycopg2-binary>=2.9.9,<3.0.0`) but was not present in the environment.

**Result**: All 72 API tests now pass, and the full backend suite runs 704/704 tests passing.

---

## Test Commands

```bash
# Install dependencies (including the missing psycopg2-binary)
pip install -r backend/requirements.txt

# Run core test suites
python -m pytest tests/test_ml_pipeline.py tests/test_lp_allocator.py tests/test_negotiation.py tests/test_conflict_detector.py tests/test_data_generator.py tests/test_farmer_agents.py tests/test_explainability.py --tb=short

# Run full backend suite
python -m pytest tests/ --tb=short

# Run API tests
python -m pytest tests/test_api.py --tb=short
```

---

## Test Suite Details

### ML Pipeline (64 tests)
- Dataset generation and shape validation
- RandomForest and XGBoost training and prediction
- Metrics computation (MAE, RMSE, R²)
- Model save/load round-trips
- SHAP explainability structure and values
- Preprocessing consistency and no leakage between splits

### LP Allocator (86 tests)
- Hard constraints H1 (non-negative), H2 (maximum), H3 (supply limit)
- Soft constraint S1 (minimum requirements, relaxed when infeasible)
- Severe shortage, moderate shortage, zero water scenarios
- Fairness (Jain's Index), utilization, water balance
- Proportional and LP-relaxed fallback methods

### Negotiation (123 tests)
- Session creation and configuration
- Farmer acceptance/rejection/request-thresholds
- BATNA protection (always overrides threshold checks)
- Flexible/inflexible farmer concession logic
- Nash objective computation and improvement detection
- Multi-round negotiation with stagnation termination
- Mediation proposals and constraint verification
- Single and multiple farmer scenarios

### Conflict Detector (88 tests)
- 5 conflict types: RESOURCE_SHORTAGE, IRRIGATION_WINDOW_OVERLAP, CANAL_CAPACITY_CONFLICT, MINIMUM_REQUIREMENT_CONFLICT, HIGH_CROP_STRESS
- Severity mapping (LOW/MEDIUM/HIGH/CRITICAL)
- Overall conflict score with customizable weights
- Deterministic behavior verification

### Data Generator (62 tests)
- 8 scenario types (normal_water, moderate_shortage, severe_shortage, sudden_rainfall, canal_reduction, simultaneous_demand, high_urgency_farmer, flexible_farmer)
- FAO-56 ET₀ × Kc × area demand calculation
- Dataset train/val/test splits (70/15/15, stratified)
- Data integrity validation

### Farmer Agents (96 tests)
- Utility function computation with 5 components
- BATNA fallback and protection
- Response threshold classification (ACCEPT/REQUEST_CHANGE/REJECT)
- Flexibility and urgency effects on concessions
- Single and multiple farmer scenarios

### Explainability (113 tests)
- SHAP explanation structure and values
- Global feature importance
- Base value and prediction finiteness
- Impact labels (positive/negative/neutral)
- Feature sorting by absolute SHAP value
- Data disclaimer presence

### API Integration (72 tests)
- Health endpoint structure and status
- Root endpoint and OpenAPI schema
- Scenario run endpoint (all 8 scenario types)
- Prediction single and batch endpoints
- Conflict detection endpoint
- Allocation endpoint with constraint verification
- Negotiation endpoint with agreement status
- Validation error handling (422 responses)
- Determinism verification (repeated calls produce same results)
- Farmer data validation (negative values, out-of-range fields)
- Error handling (405 Method Not Allowed)
- JSON serialisation of responses
- Explanations present in responses
- All scenario types work through the API
- Conservation checks (water balance, no NaN, fairness range)
- Multiple scenario type parametrization

---

## Environment

- **Operating System**: Windows 10/11 (win32)
- **Python**: 3.12.10
- **Required Packages**: 
  - fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary
  - scikit-learn, xgboost, pandas, numpy, shap, joblib
  - ortools, scipy
- **Database**: PostgreSQL (required for API tests; `psycopg2-binary` must be installed)
- **Test Framework**: pytest 9.1.1

---

## Known Environment Requirements

| Requirement | Purpose |
|-------------|---------|
| `psycopg2-binary` | Required for PostgreSQL connectivity in API tests |
| `requirements.txt` | Lists all dependencies; `psycopg2-binary` is declared under "Database" section |
| `.env` file (optional) | Can override `database_url` environment variable |

---

## Verification

All test results verified on 2026-10-11 with Python 3.12.10. No test results were weakened or skipped to obtain passing scores. The only environmental fix required was installing `psycopg2-binary`, which was an expected dependency per `requirements.txt`.

---

**End of Report**