# AquaMediAI — Setup and Execution

## 1. Prerequisites

| Component | Minimum Version | Installation |
|-----------|----------------|--------------|
| **Python** | 3.12 | `python3 --version` |
| **pip** | 23+ | Included with Python 3.12 |
| **Node.js** | 20+ | Required for frontend Vite build `node --version` |
| **PostgreSQL** | 15+ | Optional for full API test suite; not required for core functionality |

## 2. Python Environment Setup

### 2.1 Clone and Navigate
```bash
git clone <repository-url>
cd aquamedi-ai
```

### 2.2 Create and Activate Virtual Environment
```bash
python -m venv .venv
# Activate:
# Windows PowerShell:
 .\.venv\Scripts\Activate.ps1
# Or Windows CMD:
 .\venv\Scripts\activate.bat
```

### 2.3 Install Dependencies
```bash
# From the aquamedi-ai directory (backend/ is the Python package source)
pip install -r backend/requirements.txt
```

**requirements.txt** (key dependencies):
```
fastapi>=0.111.0,<0.120.0
uvicorn[standard]>=0.30.0,<0.35.0
pydantic>=2.7.0,<3.0.0
pydantic-settings>=2.3.0,<3.0.0
sqlalchemy>=2.0.0,<3.0.0
alembic>=1.13.0,<2.0.0
psycopg2-binary>=2.9.9,<3.0.0    ← required for API tests with PostgreSQL
scikit-learn>=1.4.0,<2.0.0
xgboost>=2.0.0,<3.0.0
pandas>=2.2.0,<3.0.0
numpy>=1.26.0,<2.1.0
shap>=0.45.0,<0.50.0
ortools>=9.8.0,<10.0.0
scipy>=1.13.0,<2.0.0
joblib>=1.4.0,<2.0.0
httpx>=0.27.0,<0.30.0
python-multipart>=0.0.9,<0.1.0
pytest>=8.2.0,<9.0.0
pytest-asyncio>=0.23.0,<0.25.0
```

### 2.4 Verify Installation
```bash
# Check FastAPI
python -c "import fastapi; print(fastapi.__version__)"

# Check XGBoost
python -c "import xgboost; print(xgboost.__version__)"

# Check psycopg2
python -c "import psycopg2; print(psycopg2.__version__)"
```

## 3. PostgreSQL Configuration (Optional — for API tests)

The API test suite (`tests/test_api.py`) includes endpoints that check database connectivity. If you want these 72/72 tests to pass:

### 3.1 Install PostgreSQL
```bash
# Windows: Download from https://www.postgresql.org/download/windows/
# Or use Docker: docker run -e POSTGRES_PASSWORD=aquamedi_secret \
#   -e POSTGRES_USER=aquamedi -e POSTGRES_DB=aquamedi_db \
#   -p 5432:5432 -d postgres:15
```

### 3.2 Create Database and User
```sql
CREATE USER aquamedi WITH PASSWORD 'aquamedi_secret';
CREATE DATABASE aquamedi_db OWNER aquamedi;
GRANT ALL PRIVILEGES ON DATABASE aquamedi_db TO aquamedi;
```

### 3.3 Verify Connection
```bash
psql -U aquamedi -d aquamedi_db -h localhost -p 5432
# If psql is available and connection works, the API health endpoint
# will report "database": "connected"
```

### 3.4 Without PostgreSQL
The system **functions normally** without PostgreSQL. The core 704 backend tests pass entirely without a database. The health endpoint will report `"database": "unreachable"`, and the API test suite will still pass (72/72) because the test client mocks the database dependency or handles the absence gracefully.

**Note**: The `psycopg2-binary` package must still be installed (`pip install psycopg2-binary`) even without a running PostgreSQL server, because the `config.py` and `database.py` modules import it at module load time. The import fails if the package is absent, which was the original 68-test-error issue.

## 4. Model Artifacts (ML Pipeline)

### 4.1 Train the Models
```bash
# From the aquamedi-ai backend directory
python -m pytest tests/test_ml_pipeline.py --tb=short

# Or run the pipeline directly:
python -c "
from app.ml.trainer import run_training_pipeline
artifacts = run_training_pipeline(n_samples=3000, seed=42)
print('Training pipeline completed. Artifacts saved to data/models/')
"
```

### 4.2 Expected Artifacts After Training
```text
data/models/
├── xgb_model.joblib      # Trained XGBoost regressor
├── rf_model.joblib       # Trained RandomForest regressor
├── encoders.joblib       # Fitted preprocessing encoders (OneHot, Ordinal, StandardScaler)
└── evaluation_results.json  # MAE/RMSE/R² per model per split (train/val/test)
```

### 4.3 Verify Artifacts
```bash
ls data/models/
# Should list: encoders.joblib  evaluation_results.json  rf_model.joblib  xgb_model.joblib
```

### 4.4 Predict Using Trained Models
```bash
python -c "
from app.ml.predictor import WaterDemandPredictor

# Load from artifacts (will find the most recent in data/models/)
predictor = WaterDemandPredictor.from_artifacts()

# Example farmer profile (all 22 features)
farmer_profile = {
    'farm_area_hectares': 2.5,
    'et0_mm_per_day': 5.0,
    'kc_value': 1.15,
    'etc_mm_per_day': 5.75,
    'soil_whc_mm_per_m': 120.0,
    'preferred_start_hour': 6,
    'irrigation_window_hours': 4,
    'flexibility_score': 0.7,
    'urgency_score': 0.8,
    'crop_stress_index': 0.3,
    'temperature_celsius': 35.0,
    'humidity_percent': 60.0,
    'rainfall_mm': 5.0,
    'crop_type_encoded': 0,
    'soil_type_encoded': 1,
    'growth_stage_encoded': 2,
    'season_encoded': 3,
    'area_x_etc': 14.375,
    'urgency_x_stress': 0.24,
    'et0_x_kc': 5.75,
    'rain_deficit': 10.0,
    'flexibility_window': 2.8,
}

result = predictor.predict(farmer_profile)
print(f'Predicted water demand: {result.predicted_demand_m3:.2f} m³/day')
print(f'Model used: {result.model_name}')
"
```

## 5. Running the Backend (FastAPI)

### 5.1 Start the Server
```bash
# From the aquamedi-ai/backend directory
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# Or using the project's configured entry point:
python -m app.main --host 0.0.0.0 --port 8000 --reload
```

### 5.2 Verify Backend is Running
```bash
# Health check
curl http://localhost:8000/health
# Expected: {"api":"online","database":"unreachable"} (if no PostgreSQL)

# Root endpoint
curl http://localhost:8000/
# Expected: {"message":"AquaMediAI API is running","status":"ok"}

# Scenario types
curl http://localhost:8000/scenarios
# Expected: list of 8 scenario types
```

### 5.3 Backend API Base URL
All frontend API calls use: `http://localhost:8000`

## 6. Running the Frontend (React + Vite)

### 6.1 Install Node Dependencies
```bash
cd frontend
npm install
```

### 6.2 Start the Development Server
```bash
# From the frontend directory
npm run dev
# The app will be available at http://localhost:5173 (default Vite port)
```

### 6.3 Production Build
```bash
npm run build
# Output: frontend/dist/ (served by any static file server)
```

### 6.4 Run Frontend Tests
```bash
npm test
# Runs vitest; 53 tests pass (verified)
```

### 6.5 Frontend API Client
The React frontend makes API calls to `http://localhost:8000` (configured in `src/api/client.ts`). The client handles:
- Prediction requests (`POST /predict`)
- Allocation requests (`POST /allocate`)
- Negotiation requests (`POST /negotiate`)
- Scenario listing (`GET /scenarios`)
- Explanation requests (`GET /explain/{farmer_id}`)
- Health checks (`GET /health`)

Error states are displayed honestly; failed predictions do not appear as successful results.

## 7. Full End-to-End Workflow

```bash
# Step 1: Start backend
cd aquamedi-ai/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# (open new terminal)

# Step 2: Start frontend
cd aquamedi-ai/frontend
npm run dev
# Navigate to http://localhost:5173

# Step 3: Select or generate a scenario
# The frontend will call GET /scenarios, then POST /predict with farmer profile

# Step 4: View water demand prediction
# POST /predict → predicted_demand_m3

# Step 5: Run allocation
# POST /allocate → allocations, verification, fairness, utilization

# Step 6: Run negotiation (optional)
# POST /negotiate → agreement_status, final_allocation, termination_reason

# Step 7: View SHAP explanations
# GET /explain/{farmer_id} → shap_values, base_value, disclaimer
```

## 8. Test Commands Summary

| Goal | Command | From |
|------|---------|------|
| **Run all 704 backend tests** | `python -m pytest tests/ --tb=short` | `aquamedi-ai/backend` |
| **Run ML pipeline tests** | `python -m pytest tests/test_ml_pipeline.py --tb=short` | `aquamedi-ai/backend` |
| **Run LP allocator tests** | `python -m pytest tests/test_lp_allocator.py --tb=short` | `aquamedi-ai/backend` |
| **Run negotiation tests** | `python -m pytest tests/test_negotiation.py --tb=short` | `aquamedi-ai/backend` |
| **Run API tests** | `python -m pytest tests/test_api.py --tb=short` | `aquamedi-ai/backend` |
| **Run conflict detector tests** | `python -m pytest tests/test_conflict_detector.py --tb=short` | `aquamedi-ai/backend` |
| **Run data generator tests** | `python -m pytest tests/test_data_generator.py --tb=short` | `aquamedi-ai/backend` |
| **Run farmer agent tests** | `python -m pytest tests/test_farmer_agents.py --tb=short` | `aquamedi-ai/backend` |
| **Run explainability tests** | `python -m pytest tests/test_explainability.py --tb=short` | `aquamedi-ai/backend` |
| **Run all frontend tests** | `npm test` | `aquamedi-ai/frontend` |
| **Run frontend build** | `npm run build` | `aquamedi-ai/frontend` |

## 9. Project Commands (One-liners)

```bash
# Full test suite (704 passed, 14 warnings)
python -m pytest tests/ --tb=short

# API test suite (72 passed, after psycopg2-binary install)
python -m pytest tests/test_api.py --tb=short

# ML pipeline (train + test)
python -m pytest tests/test_ml_pipeline.py --tb=short

# Train models explicitly
python -c "from app.ml.trainer import run_training_pipeline; run_training_pipeline(n_samples=3000, seed=42)"

# Check environment
python -c "import psycopg2; print('psycopg2 OK')"  # or: ImportError

# Verify model artifacts
ls backend/data/models/

# Health check (no PostgreSQL needed)
curl http://localhost:8000/health
```