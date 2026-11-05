# AquaMediAI

> **Government-Grade Explainable AI Agricultural Water-Sharing Dispute Mediation & Decision Platform**  
> *Production-Ready Intelligent Irrigation Allocation, Regional Conflict Mediation, and Farmer Advisory System*

---

## 1. Problem Statement & Overview

Agricultural water scarcity and rotational canal distribution frequently precipitate acute disputes among regional farming communities. Traditional administrative water rationing often lacks transparency, struggles to accommodate asymmetric crop sensitivities and irrigation timing constraints, and offers farmers little insight into why specific allocation decisions were made.

**AquaMediAI** is a production-grade, government-grade agricultural intelligence and dispute mediation platform designed to:
1. Predict crop water demand with high precision from agronomic and environmental parameters using a production-hardened **XGBoost Regressor** ($R^2 = 0.9699$, $\text{MAE} = 18.63\text{ m}^3$).
2. Deliver **Frictionless Farmer Access**: 1-click guest access without login credentials, presenting plain-language recommendations across 4 regional languages (**English**, **Hindi**, **Gujarati**, and **Marathi**).
3. Provide **Secure Agricultural Expert Access**: Role-based access control (RBAC), cryptographically salted PBKDF2 password hashing, brute-force rate-limiting, and deep analytical dashboards.
4. Represent individual farmers via autonomous **Digital Twin Agents** that model utility, urgency, crop stress, and scheduling flexibility.
5. Automatically identify resource shortages and canal capacity conflicts via an algorithmic rule engine.
6. Solve multi-farmer constrained water allocation via **Linear Programming (LP)** using Google OR-Tools.
7. Mediate regional disputes through an iterative **Nash Bargaining Negotiation** protocol.
8. Provide transparent, human-auditable explanations using **SHAP (SHapley Additive exPlanations)**.

---

## 2. Important Disclaimers & Model Integrity

> [!IMPORTANT]
> **Production Model Lock**: The production inference engine is locked exclusively to **XGBoost 2.0** ($R^2 = 0.9699$, $\text{MAE} = 18.6313\text{ m}^3$, $\text{RMSE} = 29.2661\text{ m}^3$). All operational runtime selectors and user flows execute using XGBoost. The Random Forest model artifact (`rf_model.joblib`) is preserved on disk purely as a historical benchmark and is disabled from production selection.
> 
> **Synthetic Agronomic Grounding**: Operational scenarios and training data are generated algorithmically using the standard **FAO-56 Irrigation and Drainage methodology** (Penman-Monteith reference evapotranspiration $ET_0$, crop coefficients $K_c$, and soil water-holding capacities). No private farmer telemetry or confidential state water authority data is stored or exposed.

---

## 3. Key System Features & Portal Roles

### A. Frictionless Farmer Access (1-Click Guest Access)
- **Zero Credentials Needed**: Farmers click **"Continue as Farmer"** on the Welcome Portal to immediately access the Farmer Dashboard.
- **Plain-Language Advisory**: Replaces technical ML/LP jargon with intuitive badges (e.g. *"Sufficient Water Available"*, *"Recommended Water: 120 m³"*).
- **Multilingual Support**: Fully localized in **English** (`en`), **Hindi** (`hi`), **Gujarati** (`gu`), and native **Marathi** (`mr`).
- **Strict Role-Based Sandboxing**: Guest farmer sessions cannot access administrative, scenario-execution, or conflict-resolution endpoints (server-side HTTP 403 Forbidden).

### B. Authenticated Agricultural Expert Access
- **Government-Grade Login**: Extension officers, canal engineers, and agronomists authenticate via `/expert-login`.
- **Environment-Provisioned Account**: Configured securely via `EXPERT_DEFAULT_EMAIL` and `EXPERT_DEFAULT_PASSWORD` in `backend/.env` (no hardcoded credentials embedded in frontend).
- **Security & Rate Limiting**: Passwords hashed with **PBKDF2-HMAC-SHA256** (100,000 iterations); progressive brute-force lockout after 5 consecutive failed attempts (15-minute lock).
- **Advanced Engineering Controls**: Full access to OR-Tools GLOP solver logs, Nash bargaining rounds, TreeSHAP force plots, and manual scenario execution.

### C. Core Intelligence & Optimization Engines
- **Machine Learning Demand Prediction**: Production **XGBoost Regressor** trained on 22 engineered agronomic features.
- **Farmer Digital Twin Agents**: Multi-attribute utility functions (water deficit penalty, timing satisfaction, crop stress vulnerability, and concession flexibility).
- **Conflict Detection Engine**: Algorithmic rule engine classifying structural deficits and operational clashes into 5 distinct conflict types.
- **Constraint-Based LP Optimization**: Google OR-Tools GLOP solver maximizing total utility and Jain's Fairness Index subject to canal flow constraints, with graceful relaxed and proportional fallback chains.
- **Multi-Agent Mediated Negotiation**: Automated mediator coordinating bilateral and multilateral concessions towards Pareto-efficient Nash Bargaining equilibria.
- **Explainability Layer**: Local explanation engine generating feature attribution scores via **TreeSHAP**, translated into regional language explanations.

---

## 4. System Architecture

```
                                  ┌───────────────────────────────────────────────┐
                                  │       FAO-56 Synthetic Data Generator         │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │       Production XGBoost Demand Model         │
                                  │       (Locked: R²=0.9699, MAE=18.63 m³)       │
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
                                  │    (Multilingual: English, Hindi, Guj, Mar)   │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │        Role-Based FastAPI REST API (RBAC)     │
                                  │     [Farmer Guest / Authenticated Expert]     │
                                  └──────────────────────┬────────────────────────┘
                                                         │
                                                         ▼
                                  ┌───────────────────────────────────────────────┐
                                  │    Government-Grade React 19 Frontend (nsw)   │
                                  │       [Welcome Portal | Farmer | Expert]      │
                                  └───────────────────────────────────────────────┘
```

---

## 5. Technology Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (0.119+), Uvicorn | High-performance ASGI REST API |
| **Security & Auth** | PBKDF2-HMAC-SHA256, RFC 7519 HS256, RateLimiter | Cryptographic auth, JWT sessions, brute-force defense |
| **Validation & Settings** | Pydantic v2, Pydantic-Settings | Typed configuration and request/response validation |
| **Database & ORM** | SQLAlchemy 2, Alembic, PostgreSQL | Relational storage for users, agreements & scenario runs |
| **Machine Learning** | XGBoost (2.1+ / 3.4+), scikit-learn, joblib | Production water demand regression and encoders |
| **Explainability** | SHAP (TreeExplainer) | Shapley additive feature attribution |
| **Mathematical Optimization** | Google OR-Tools (GLOP Linear Solver), SciPy | Constrained water-allocation optimization |
| **Data Processing** | NumPy, Pandas | Agronomic data manipulation and feature matrices |
| **Frontend Framework** | React 19, TypeScript, Vite 8 | Reactive component architecture and production build |
| **Frontend Routing & UI** | React Router 7, Lucide React, Recharts | Navigation, government iconography, and interactive data charts |
| **Internationalization** | Custom Context Engine | Multi-language translation (EN, HI, GU, MR) |
| **Testing** | pytest, pytest-asyncio, Vitest | Backend unit/RBAC tests and frontend test suites |
| **Containerization** | Docker, Docker Compose | Containerized database and backend deployment |

---

## 6. Repository Structure

```
aquamedi-ai/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py                 # FastAPI app instance, CORS & router registration
│   │   ├── config.py               # Security, auth, and pipeline settings
│   │   ├── database.py             # SQLAlchemy synchronous engine & sessionmaker
│   │   ├── core/
│   │   │   └── security.py         # PBKDF2 hashing, JWT creation/decoding, rate limiter
│   │   ├── agents/                 # FarmerAgent, DigitalTwin, and factory
│   │   ├── allocation/             # OR-Tools GLOP Linear Programming allocator
│   │   ├── api/                    # REST routers (/auth, /scenarios, /predictions, /health)
│   │   │   ├── auth.py             # Guest sessions, expert login, /me, /logout
│   │   │   ├── deps.py             # Server-side RBAC guards (require_expert, require_farmer_or_expert)
│   │   │   ├── scenario_routes.py  # Secured scenario and simulation routes
│   │   │   └── health.py           # Pipeline readiness probe
│   │   ├── conflict/               # Conflict detector and severity evaluator
│   │   ├── explainability/         # SHAP explainer and natural language templates
│   │   ├── ml/                     # Data generator, feature engineering, predictor
│   │   ├── models/                 # SQLAlchemy ORM models (User, Agreement, Scenario)
│   │   ├── negotiation/            # Mediator and Nash bargaining protocol
│   │   ├── schemas/                # Pydantic API schemas (Auth, Prediction, Scenario)
│   │   ├── services/               # ScenarioService pipeline orchestration
│   │   └── utils/                  # Helper utilities and math functions
│   ├── data/
│   │   ├── models/                 # Trained model artifacts (xgb_model.joblib, rf_model.joblib)
│   │   └── raw/                    # Raw synthetic dataset storage
│   ├── alembic/                    # Database migration scripts
│   ├── scripts/                    # CLI scripts (train_models.py)
│   ├── tests/                      # pytest test suite (including test_security_rbac.py)
│   ├── requirements.txt            # Python dependencies manifest
│   ├── .env.example                # Safe environment configuration template
│   └── Dockerfile                  # Backend container build specification
├── frontend/                       # React + TypeScript + Vite Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/             # GovernmentHeader, authority banners, badge cards
│   │   │   ├── pipeline/           # CustomFarmPredictor (XGBoost locked), scenario views
│   │   │   └── navigation/         # Accessible navigation menus
│   │   ├── context/
│   │   │   ├── AuthContext.tsx     # Role state (FARMER_GUEST vs AGRICULTURAL_EXPERT)
│   │   │   ├── ScenarioContext.tsx # Scenario pipeline execution state
│   │   │   └── ViewModeContext.tsx # View mode & i18n state (EN, HI, GU, MR)
│   │   ├── i18n/                   # English, Hindi, Gujarati, Marathi dictionaries
│   │   ├── layouts/                # Header with model indicator, navigation layouts
│   │   ├── pages/                  # WelcomePage, ExpertLoginPage, FarmerPortalPage, ScenarioPage
│   │   ├── services/               # API client with JWT bearer interceptors
│   │   ├── styles/                 # Government design tokens (nsw.gov.au palette)
│   │   ├── tests/                  # Vitest suite (78 tests across 10 files)
│   │   └── types/                  # TypeScript interface definitions
│   ├── package.json                # Node dependencies and scripts
│   ├── vite.config.ts              # Vite server & proxy configuration
│   └── .env.example                # Safe frontend environment template
├── docs/                           # Architecture, RBAC, and Transformation Reports
│   ├── GOVERNMENT_GRADE_TRANSFORMATION_REPORT.md # Full transformation technical report
│   ├── ARCHITECTURE.md             # Detailed multi-tier system architecture
│   ├── API_DOCUMENTATION.md        # API route contracts and request/response examples
│   ├── DATA_DICTIONARY.md          # 22 engineered features and parameter definitions
│   ├── ML_EVALUATION.md            # XGBoost vs Random Forest performance analysis
│   └── SETUP_AND_EXECUTION.md      # Detailed step-by-step developer setup
└── README.md                       # Main project documentation entrypoint
```

---

## 7. Prerequisites

Before setting up AquaMediAI, ensure your local environment meets these requirements:

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Version `3.11` or `3.12`.
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
*(The backend automatically initializes security configurations, JWT tokens, and seed expert credentials).*

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

## 9. Default Credentials & Role Access

| Role | Access URL | Credentials | Permitted Operations | Restricted Operations |
| :--- | :--- | :--- | :--- | :--- |
| **Farmer (Guest)** | `/` or `/welcome` | **No login required** (1-click *"Continue as Farmer"*) | View personalized farm demand, crop advisory, water quota, multilingual advice | Cannot run multi-farmer scenario simulations, edit canal capacities, or trigger optimization |
| **Agricultural Expert** | `/expert-login` | Configured via `backend/.env`<br>(e.g. `expert@aquamedi.gov.in`) | Full system access, OR-Tools LP allocations, Nash bargaining simulations, SHAP audits | Protected behind server-side RBAC token verification |

---

## 10. Database Configuration (PostgreSQL: Required vs. Optional)

| Workflow / Capability | PostgreSQL Required? | Explanation |
| :--- | :---: | :--- |
| **Interactive UI & Scenarios** | **NO** (Optional) | The full mediation pipeline (`POST /api/v1/scenarios/run`) executes dynamically in-memory with synthetic data. |
| **ML Inference & Explainability** | **NO** (Optional) | Models load directly from persisted `.joblib` files; SHAP explanations compute on demand. |
| **Linear Programming & Negotiation** | **NO** (Optional) | OR-Tools GLOP solver and Nash bargaining run entirely in CPU memory. |
| **Guest Sessions & Expert Auth** | **NO** (Optional) | Fallback in-memory secure tokens and credential validation run seamlessly out-of-the-box. |
| **Persistent Historical DB Audits** | **YES** | Saving finalized mediation settlement records to relational database tables requires PostgreSQL. |

---

## 11. Application URLs

Once both servers are running:

| Service / Interface | Local URL | Description |
| :--- | :--- | :--- |
| **Welcome Portal** | [http://127.0.0.1:5173/welcome](http://127.0.0.1:5173/welcome) | Government-grade portal landing & role selection |
| **Farmer Dashboard** | [http://127.0.0.1:5173/farmer-portal](http://127.0.0.1:5173/farmer-portal) | Plain-language farmer irrigation advisory |
| **Expert Login** | [http://127.0.0.1:5173/expert-login](http://127.0.0.1:5173/expert-login) | Secure official login for agricultural officers |
| **Expert Analytical Dashboard** | [http://127.0.0.1:5173/overview](http://127.0.0.1:5173/overview) | Multi-farmer mediation, conflict graphs, LP solver |
| **Farm Demand Predictor** | [http://127.0.0.1:5173/predictions](http://127.0.0.1:5173/predictions) | Interactive XGBoost farm prediction calculator |
| **Interactive API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI for exploring and testing API routes |
| **Pipeline Health Endpoint** | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) | Pipeline readiness and XGBoost model probe |

---

## 12. Verification & Testing

### Frontend Test Suite (Vitest)
```powershell
cd frontend
npm test
```
- **Test Status**: **78 passed across 10 test files (100% passing)**.
- **Test Suites**:
  - `WelcomeAndAuth.test.tsx`: Tests welcome role selection, 1-click farmer guest access, expert login validation, and error banner display.
  - `CustomFarmPredictor.test.tsx`: Verifies locked XGBoost model choice and accurate demand calculation.
  - `FarmerPortal.test.tsx`: Verifies plain-language advisory, multilingual rendering, and simplified view cards.
  - `ScenarioRunner.test.tsx`, `AllocationView.test.tsx`, `NegotiationView.test.tsx`, `Header.test.tsx`, etc.

### Frontend Production Build
```powershell
cd frontend
npm run build
```
- Runs `tsc -b && vite build` and generates verified static production bundles in `frontend/dist/` in under 1.6s with **0 TypeScript errors**.

### Backend Test Suite (pytest)
```powershell
cd backend
python -m pytest tests/ --tb=short
```
- **Backend Test Suite**: Includes `test_security_rbac.py` verifying PBKDF2 password hashing, HS256 token verification, rate limiter lockouts, and server-side HTTP 403 Forbidden enforcement on expert endpoints for guest farmer sessions.

---

## 13. API Route Specifications & RBAC Matrix

| Method | Endpoint | RBAC Role Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/guest-session` | **Public** | Issues a restricted guest session token for farmers |
| `POST` | `/api/v1/auth/expert/login` | **Public (Rate-limited)** | Validates credentials; issues authenticated expert JWT |
| `GET` | `/api/v1/auth/me` | **Bearer Token** | Returns identity and active role of caller |
| `POST` | `/api/v1/auth/logout` | **Bearer Token** | Terminates session and invalidates client token |
| `GET` | `/api/v1/health` | **Public** | Pipeline readiness and production XGBoost model status |
| `POST` | `/api/v1/predictions` | **Farmer or Expert** | Predicts daily water demand ($m^3$) using XGBoost |
| `POST` | `/api/v1/predictions/batch` | **Farmer or Expert** | Batch water demand predictions for multiple farms |
| `POST` | `/api/v1/scenarios/run` | **Expert Only (HTTP 403 for Farmer)** | Executes full mediation simulation pipeline |
| `POST` | `/api/v1/conflicts` | **Expert Only (HTTP 403 for Farmer)** | Detects structural deficits and canal capacity clashes |
| `POST` | `/api/v1/allocations` | **Expert Only (HTTP 403 for Farmer)** | Solves OR-Tools GLOP constrained water allocation |
| `POST` | `/api/v1/negotiations` | **Expert Only (HTTP 403 for Farmer)** | Runs multi-round Nash bargaining mediated negotiation |

---

## 14. Academic & Engineering Attribution

- **Project**: AquaMediAI — Government-Grade Explainable AI Water-Sharing Dispute Mediation System
- **Engineering Stack**: FastAPI, React 19, TypeScript, XGBoost 2.0, Google OR-Tools GLOP, TreeSHAP
- **License**: MIT License
