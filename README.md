# AquaMediAI

> **An Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System for Agricultural Communities**  
> *Third-Year B.Tech Computer Science and Engineering Project — Academic Demonstration*

---

## 1. Problem Statement & Overview

Agricultural water scarcity and canal rotational distribution frequently result in localized disputes among farming communities. Traditional administrative water rationing often lacks transparency, struggles to accommodate asymmetric crop sensitivities and irrigation timing constraints, and offers farmers little insight into why specific allocation decisions were made.

**AquaMediAI** is an academic proof-of-concept demonstrating an end-to-end multi-agent artificial intelligence pipeline designed to:
1. Predict crop water demand accurately from agronomic and environmental parameters.
2. Represent individual farmers via autonomous **Digital Twin Agents** that model utility, urgency, crop stress, and scheduling flexibility.
3. Automatically identify resource shortages and canal capacity conflicts.
4. Solve multi-farmer constrained water allocation via **Linear Programming (LP)** using Google OR-Tools.
5. Mediate disputes through an iterative **Nash Bargaining Negotiation** mechanism.
6. Provide transparent, human-auditable explanations using **SHAP (SHapley Additive exPlanations)** presented in multiple regional languages (English, Hindi, and Gujarati).

---

## 2. Important Disclaimers & Academic Integrity

> [!IMPORTANT]
> **Synthetic Data Disclaimer**: This project uses a **fully synthetic, agronomically grounded dataset** generated algorithmically using the **FAO-56 Irrigation and Drainage methodology** (Penman-Monteith reference evapotranspiration $ET_0$, crop coefficients $K_c$, and soil water-holding capacities).  
> **No real farmer records, telemetry sensors, or confidential water authority data are included or used.** All simulation scenarios and evaluation metrics reflect synthetic distributions and serve solely to demonstrate algorithmic behavior for academic research.

---

## 3. Key System Features

- **FAO-56 Synthetic Data Engine**: Generates realistic crop, soil, weather, and scheduling parameters across 8 distinct simulation scenario types (`normal_water`, `moderate_shortage`, `severe_shortage`, `sudden_rainfall`, `canal_reduction`, `simultaneous_demand`, `high_urgency_farmer`, `flexible_farmer`).
- **Machine Learning Demand Prediction**: Dual-model architecture featuring an **XGBoost Regressor** (primary) and a **Random Forest Regressor** (baseline) trained on 22 engineered agronomic features.
- **Farmer Digital Twin Agents**: Models individual farmer utility using multi-attribute valuation (water deficit penalty, timing satisfaction, crop stress vulnerability, and concession flexibility).
- **Conflict Detection Engine**: Algorithmic rule engine that classifies structural deficits and operational clashes into 5 distinct conflict types across severity tiers.
- **Constraint-Based LP Optimization**: Formulates and solves fair water allocation via **Google OR-Tools GLOP**, maximizing total utility and Jain's Fairness Index subject to canal flow rate bounds and minimum survival requirements, backed by graceful relaxed and proportional fallback chains.
- **Multi-Agent Mediated Negotiation**: Automated mediator coordinating bilateral and multilateral concessions towards Pareto-efficient Nash Bargaining equilibria.
- **Explainability Layer**: Local explanation engine generating feature attribution scores via **TreeSHAP**, translated into clear natural-language rationale.
- **Dual-Mode Interactive Web Interface**: Modern React 19/TypeScript dashboard with **Farmer Presentation Mode** (simplified, non-technical, multilingual) and **Expert Analytical Mode** (deep agronomic metrics, SHAP charts, solver logs).

---

## 4. System Architecture

```
                                  ┌───────────────────────────────────────────────┐
                                  │       FAO-56 Synthetic Data Generator         │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │    Feature Engineering & ML Demand Models     │
                                  │          (XGBoost / Random Forest)            │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │          Farmer Digital Twin Agents           │
                                  │     (Utility, Urgency, Flexibility Score)     │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │           Conflict Detection Engine           │
                                  │    (Resource Shortage, Window Clashes, etc.)  │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │      OR-Tools GLOP Linear Programming         │
                                  │       (Optimal Initial Water Allocation)      │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │     Multi-Agent Nash Bargaining Mediator      │
                                  │         (Iterative Consensus Search)          │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │            SHAP Explainability Layer          │
                                  │      (Multilingual: English, Hindi, Gujarati) │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │     FastAPI REST API & React/Vite Frontend    │
                                  └───────────────────────────────────────────────┘
```

---

## 5. Technology Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (0.119+), Uvicorn | High-performance ASGI REST API |
| **Validation & Settings** | Pydantic v2, Pydantic-Settings | Typed configuration and request/response validation |
| **Database & ORM** | SQLAlchemy 2, Alembic, PostgreSQL | Relational storage for agreements & scenario runs |
| **Machine Learning** | XGBoost (2.1+ / 3.4+), scikit-learn, joblib | Water demand regression models and encoders |
| **Explainability** | SHAP (TreeExplainer) | Shapley additive feature attribution |
| **Mathematical Optimization** | Google OR-Tools (GLOP Linear Solver), SciPy | Constrained water-allocation optimization |
| **Data Processing** | NumPy, Pandas | Agronomic data manipulation and feature matrices |
| **Frontend Framework** | React 19, TypeScript, Vite 8 | Reactive component architecture and dev build |
| **Frontend Routing & UI** | React Router 7, Lucide React, Recharts | Navigation, iconography, and interactive data charts |
| **Testing** | pytest, pytest-asyncio, Vitest | Backend unit/integration tests and frontend testing |
| **Containerization** | Docker, Docker Compose | Containerized database and backend deployment |

---

## 6. Repository Structure

```
aquamedi-ai/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py                 # FastAPI application instance & routing
│   │   ├── config.py               # Application configuration (Pydantic settings)
│   │   ├── database.py             # SQLAlchemy synchronous engine & sessionmaker
│   │   ├── agents/                 # FarmerAgent, DigitalTwin, and factory
│   │   ├── allocation/             # OR-Tools GLOP Linear Programming allocator
│   │   ├── api/                    # REST routers (/health, /scenarios, /predictions)
│   │   ├── conflict/               # Conflict detector and severity evaluator
│   │   ├── explainability/         # SHAP explainer and natural language templates
│   │   ├── ml/                     # Data generator, feature engineering, predictor
│   │   ├── models/                 # SQLAlchemy ORM database models
│   │   ├── negotiation/            # Mediator and Nash bargaining protocol
│   │   ├── schemas/                # Pydantic API request/response schemas
│   │   ├── services/               # ScenarioService pipeline orchestration
│   │   └── utils/                  # Helper utilities and math functions
│   ├── data/
│   │   ├── models/                 # Trained model artifacts (.joblib, evaluation.json)
│   │   └── raw/                    # Raw synthetic dataset storage (.gitkeep)
│   ├── alembic/                    # Database migration scripts
│   ├── scripts/                    # CLI scripts (train_models.py)
│   ├── tests/                      # pytest test suite (704 backend tests)
│   ├── main.py                     # Root ASGI entrypoint shim
│   ├── requirements.txt            # Python dependencies manifest
│   ├── .env.example                # Safe environment configuration template
│   └── Dockerfile                  # Backend container build specification
├── frontend/                       # React + TypeScript + Vite Application
│   ├── src/
│   │   ├── components/             # Reusable UI cards, tables, charts, forms
│   │   ├── context/                # Scenario state and view mode management
│   │   ├── i18n/                   # English, Hindi, and Gujarati translations
│   │   ├── layouts/                # Header, navigation, and page layouts
│   │   ├── pages/                  # Scenario, Allocation, Negotiation, Docs pages
│   │   ├── services/               # Frontend API client connecting to backend
│   │   ├── tests/                  # Vitest frontend test suite
│   │   └── types/                  # TypeScript interface definitions
│   ├── package.json                # Node dependencies and scripts
│   ├── package-lock.json           # Frozen lockfile
│   ├── vite.config.ts              # Vite server & proxy configuration
│   └── .env.example                # Safe frontend environment template
├── docs/                           # Comprehensive Architectural & Audit Documentation
│   ├── ARCHITECTURE.md             # Detailed multi-tier system architecture
│   ├── API_DOCUMENTATION.md        # API route contracts and request/response examples
│   ├── DATA_DICTIONARY.md          # 22 engineered features and parameter definitions
│   ├── ML_EVALUATION.md            # XGBoost vs Random Forest performance analysis
│   ├── SETUP_AND_EXECUTION.md      # Detailed step-by-step developer setup
│   ├── KNOWN_LIMITATIONS.md        # Explicit boundary conditions and future work
│   └── FINAL_PROJECT_REPORT.md     # Complete academic seminar and technical report
├── scripts/                        # Repository maintenance and migration scripts
├── docker-compose.yml              # Multi-container orchestration (DB + API)
├── .gitignore                      # Git exclusion rules for clean publication
└── README.md                       # Main project documentation entrypoint
```

---

## 7. Prerequisites

Before setting up AquaMediAI, ensure your local environment meets these requirements:

- **Operating System**: Windows 10/11, macOS, or Linux (commands below assume Windows PowerShell).
- **Python**: Version `3.11` or `3.12` (Python 3.12 verified).
- **Node.js**: Version `20+` or `24+` (includes `npm`).
- **PostgreSQL** *(Optional)*: Version 15+ or Docker Desktop (see section 9 for details).
- **Git**: Version 2.40+.

---

## 8. Installation & Local Startup

Clone the repository and follow the steps below in **two separate PowerShell terminals**:

### Step 1: Clone the Repository
```powershell
git clone <repository-url>
cd aquamedi-ai
```

### Step 2: Backend Setup (Terminal 1)
```powershell
cd backend

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create local environment file from example template
Copy-Item .env.example .env

# Start the FastAPI ASGI server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
*(Alternatively, `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` works identically).*

### Step 3: Frontend Setup (Terminal 2)
```powershell
cd frontend

# Install Node dependencies
npm install

# Create frontend environment file
Copy-Item .env.example .env

# Start Vite development server
npm run dev
```

---

## 9. Database Configuration (PostgreSQL: Required vs. Optional)

| Workflow / Capability | PostgreSQL Required? | Explanation |
| :--- | :---: | :--- |
| **Interactive UI & Scenarios** | **NO** (Optional) | The full mediation pipeline (`POST /api/v1/scenarios/run`) executes dynamically in-memory with synthetic data. |
| **ML Inference & Explainability** | **NO** (Optional) | Models load directly from persisted `.joblib` files; SHAP explanations compute on demand. |
| **Linear Programming & Negotiation** | **NO** (Optional) | OR-Tools GLOP solver and Nash bargaining run entirely in CPU memory. |
| **Core Test Suite (704 tests)** | **NO** (Optional) | Full backend unit and mock test suites pass 100% without an active database server. |
| **Persistent Historical DB Audits** | **YES** | Saving finalized mediation settlement records to relational database tables requires PostgreSQL. |

### Running without PostgreSQL
When PostgreSQL is not active, the backend starts normally and outputs a non-fatal warning:
```text
Database connection: FAILED — run 'alembic upgrade head' and ensure PostgreSQL is running.
```
- `GET /api/v1/health` returns `200 OK` (`pipeline: available`).
- The frontend displays **"API Connected"** and all scenario simulations operate with zero degradation.

### Enabling PostgreSQL (Optional)
If database persistence is desired:
1. Start PostgreSQL on `localhost:5432` (or via Docker: `docker-compose up -d db`).
2. Create user `aquamedi` with password `aquamedi_secret` and database `aquamedi_db`.
3. Run migrations from `backend/`:
   ```powershell
   alembic upgrade head
   ```

---

## 10. Machine Learning Artifact Management

The repository includes pre-trained model artifacts inside [`backend/data/models/`](backend/data/models/) (~16MB total) so the application functions immediately upon initial checkout:
- `encoders.joblib` (Fitted OneHot, Ordinal, and StandardScaler transforms)
- `xgb_model.joblib` (Trained XGBoost Regressor)
- `rf_model.joblib` (Trained Random Forest Regressor)
- `evaluation_results.json` (Full test split validation metrics)

### Retraining the Models Reproducibly
To regenerate and evaluate model artifacts from scratch:
```powershell
cd backend
python scripts/train_models.py --n-samples 3000 --seed 42 --model-dir data/models
```
This script executes the complete pipeline:
1. Generates 3,000 synthetic farm profiles grounded in FAO-56.
2. Fits categorical and numerical encoders strictly on the training partition.
3. Fits XGBoost with early stopping on validation RMSE and Random Forest baseline.
4. Evaluates MAE, RMSE, and $R^2$ on the held-out test split ($n = 451$).
5. Atomically writes updated `.joblib` and metrics files to `data/models/`.

---

## 11. Application URLs

Once both servers are running:

| Service / Interface | Local URL | Description |
| :--- | :--- | :--- |
| **Frontend Application** | [http://127.0.0.1:5173](http://127.0.0.1:5173) | Interactive web interface with Farmer and Expert views |
| **Interactive API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI for exploring and testing API routes |
| **Alternative API Specs** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | ReDoc formatted API specifications |
| **Pipeline Health Endpoint** | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) | Pipeline readiness probe |
| **System Status Probe** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Infrastructure probe reporting database connectivity |

---

## 12. Verification & Testing

### Backend Test Suite (pytest)
```powershell
cd backend
python -m pytest tests/ --tb=short
```
- **Total backend tests**: 704 passed.
- **Coverage**: ML pipeline (64 tests), LP allocator & fallbacks (41 tests), Negotiation & Mediator (77 tests), Conflict detector (40 tests), Agent factory (52 tests), API integration routes (72 tests).

### Frontend Test Suite (Vitest)
```powershell
cd frontend
npm test
```
- **Total frontend tests**: 53 passed across 6 test suites.

### Frontend Production Build
```powershell
cd frontend
npm run build
```
- Runs `tsc -b && vite build` and generates verified static assets in `frontend/dist/`.

---

## 13. API Route Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API service metadata and version summary |
| `GET` | `/health` | System liveness probe and database connection status |
| `GET` | `/api/v1/health` | Pipeline status and model artifact readiness probe |
| `POST` | `/api/v1/scenarios/run` | **Primary pipeline endpoint**: runs synthetic generation → ML demand → conflict detection → LP allocation → negotiation → SHAP explanations |
| `POST` | `/api/v1/predictions` | Predicts daily water demand ($m^3$) for a single farmer profile |
| `POST` | `/api/v1/predictions/batch` | Batch demand prediction for multiple farmers |
| `POST` | `/api/v1/conflicts` | Detects resource shortages and scheduling overlaps |
| `POST` | `/api/v1/allocations` | Runs Google OR-Tools GLOP constrained water allocation |
| `POST` | `/api/v1/negotiations` | Executes multi-round Nash bargaining mediated negotiation |

---

## 14. Known Limitations

As an academic prototype, AquaMediAI is governed by defined boundary conditions (see [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) for full analysis):
1. **Synthetic Data Dependency**: Evaluation metrics ($R^2 > 0.96$) are derived from synthetic FAO-56 equations. Models have not been calibrated on empirical field sensor telemetry or telemetry-equipped canal infrastructure.
2. **Simplified Canal Hydraulics**: Canal transit delay and seepage losses are modeled as linear percentage constraints rather than hydrodynamic Saint-Venant partial differential equations.
3. **Synchronous Database Driver**: SQLAlchemy operates synchronously for academic MVP simplicity; high-concurrency production deployments would require `asyncpg`.
4. **Game-Theoretic Assumptions**: Farmer digital twins evaluate concessions using rational utility models; irrational, emotional, or non-cooperative behaviors are simplified.

---

## 15. Future Scope

- **Real-World Telemetry Ingestion**: Integration with IoT soil moisture probes, automated canal headgate telemetry, and remote-sensing satellite imagery (NDVI/NDWI).
- **Uncertainty Quantification**: Conformal prediction intervals for water demand forecasting under extreme meteorological volatility.
- **Hydrodynamic Simulation**: Coupling LP allocation with hydraulic simulators (such as EPANET or SWMM) to model transient pipe and open-channel water dynamics.
- **Mobile Voice Interface**: Regional speech-to-text input enabling conversational access for rural farmers.

---

## 16. Academic Attribution & Project Context

- **Institution**: Department of Computer Science and Engineering
- **Academic Degree**: Bachelor of Technology (B.Tech) in Computer Science and Engineering
- **Project Title**: AquaMediAI: An Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System
- **Year of Submission**: Final Year / Third Year Academic Seminar
- **Authors**: Project Team Members (Department of CSE)
- **Supervision**: Project Guide / Faculty Advisor, Department of CSE

---

## 17. License

This project is released under the **MIT License**. See `LICENSE` for details.
