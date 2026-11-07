# AquaMedi AI — System Architecture Specification

**Document ID:** `AQUAMEDI-ARCH-SPEC-2026-V1`  
**Classification:** Technical Architecture & System Design Document  
**Author:** Principal Full-Stack Software Architect  
**Project:** AquaMedi AI — Agricultural Intelligence & Canal Water Management  
**Branch:** `feature/aquamedi-ai-product-transformation`  
**Date:** November 7, 2026  
**Status:** **ACADEMIC DEMONSTRATION VERIFIED (RELEASE V1.0)**

---

## 1. Architectural Principles & System Goals

AquaMedi AI is engineered under four foundational software architecture principles:

1. **Decoupled Multi-Tier Topology:** Clean separation of concerns between presentation (React 19), business logic/service layer (FastAPI), compute engines (XGBoost, OR-Tools), and persistence (SQLAlchemy).
2. **Defensive Asynchronous Execution:** High-throughput, non-blocking I/O using Python AsyncIO/AnyIO, keeping compute-heavy inference and optimization operations isolated.
3. **Open Science & Transparent Physics:** Every machine learning output is paired with a classical physical baseline (FAO-56 Penman-Monteith) and distribution-free conformal confidence intervals.
4. **Government-Grade Usability & Security:** Compliance with Indian Government Web Guidelines (GIGW/NIC), strict server-side role-based access control, and zero user barriers for public farmer advisories.

---

## 2. High-Level Component Topology

```
+-----------------------------------------------------------------------------------+
|                            CLIENT PRESENTATION TIER                               |
|                                                                                   |
|  [ Public Farmer Portal ]       [ Expert Command Center ]      [ Canal Dashboard ]|
|  - Crop Water Calculator        - Discharge Monitoring         - Reach Balancing  |
|  - Crop Health Advisory         - Google OR-Tools Optimizer    - What-If Simulator|
|  - Conformal Range Display      - Dispute Mediation Desk       - Audit Reports    |
|                                                                                   |
|  Technology: React 19, TypeScript, Vite 6, Recharts, Lucide Icons, Modern CSS    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | HTTPS / REST / JSON
                                          v
+-----------------------------------------------------------------------------------+
|                            API GATEWAY & SECURITY LAYER                           |
|                                                                                   |
|  - HTTP Router & Middleware Pipeline                                              |
|  - CORS Whitelisting & Header Sanitization                                        |
|  - Sliding-Window Rate Limiter (10 req / 60s on auth)                             |
|  - JWT Authentication & RBAC Filter (Public Farmer vs Authenticated Expert)       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            APPLICATION BUSINESS LOGIC                             |
|                                                                                   |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  |  Agronomy Service  |  |   ML Inference     |  |   Operations Research       |  |
|  |  - FAO-56 Physics  |  |   - XGBoost 2.x    |  |   - Google OR-Tools GLOP    |  |
|  |  - Soil Depletion  |  |   - Split Conformal|  |   - Multi-Agent Negotiator  |  |
|  |  - Stress (Ks)     |  |   - TreeSHAP XAI   |  |   - Scenario Engine         |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            PERSISTENCE & MODEL STORAGE                            |
|                                                                                   |
|  - SQLAlchemy 2.0 ORM Repository Layer                                            |
|  - SQLite (Local Zero-Config Demo) / PostgreSQL 16 (Production Staging)           |
|  - Model Artifact Store (xgb_model.joblib, scaler.joblib, test_data.joblib)       |
+-----------------------------------------------------------------------------------+
```

---

## 3. Presentation Tier (Frontend Architecture)

### 3.1 Technology Stack
* **UI Framework:** React 19.0.0
* **Language:** TypeScript 5.6+ with strict typing (`strict: true`, `noImplicitAny: true`)
* **Build System:** Vite 6.2.0 (ESM-native dev server, Rollup production bundler)
* **Visualizations:** Recharts (responsive SVG chart components)
* **Icons:** Lucide React
* **Styling:** Modular CSS implementing the Government Design System

### 3.2 Page Component Hierarchy
```text
src/
├── App.tsx                   # Master router & layout container
├── components/
│   ├── Header.tsx            # Tricolor ribbon, bilingual national header, nav
│   ├── Footer.tsx            # NIC/GIGW standard footer & academic disclaimers
│   ├── ProtectedRoute.tsx    # Role-based route guard
│   └── MetricCard.tsx        # Government-style KPI metric container
├── pages/
│   ├── WelcomePage.tsx       # Landing page & quick role selector
│   ├── LoginPage.tsx         # Expert authentication portal
│   ├── FarmerPortalPage.tsx  # Unauthenticated crop water calculator
│   ├── DashboardPage.tsx     # Canal reach distribution telemetry
│   ├── MLPredictionsPage.tsx # XGBoost prediction, conformal intervals, SHAP
│   ├── AllocationPage.tsx    # Google OR-Tools GLOP optimization desk
│   ├── DisputeMediationPage.tsx # Multi-agent negotiation desk
│   ├── CropHealthPage.tsx    # Soil moisture & crop health alerts
│   ├── IrrigationAdvisoryPage.tsx # Scheduling calendar & water tips
│   ├── ScenarioPage.tsx      # What-If climate crisis simulator
│   └── ReportsPage.tsx       # Audit log export (CSV/PDF)
├── context/
│   └── AuthContext.tsx       # JWT state, user role, and logout hooks
└── services/
    └── api.ts                # Axios client with interceptors and error handling
```

---

## 4. Application Tier (Backend Architecture)

### 4.1 Technology Stack
* **Web Framework:** FastAPI 0.115+ (ASGI framework running on Starlette)
* **Server:** Uvicorn with asynchronous event loop
* **Validation:** Pydantic v2 schemas for all request/response models
* **Python Runtime:** Python 3.12.9

### 4.2 Module Organization
```text
backend/app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py          # Login, token refresh, logout
│   │   │   ├── farmer.py        # Farmer crop demand & advisories (Public)
│   │   │   ├── expert.py        # Canal telemetry & expert controls (Protected)
│   │   │   ├── ml.py            # Inference, conformal intervals, SHAP
│   │   │   ├── allocation.py    # OR-Tools GLOP water quota optimization
│   │   │   ├── negotiation.py   # Multi-agent dispute mediation
│   │   │   ├── scenarios.py     # What-If crisis simulation
│   │   │   └── reports.py       # Audit logs & data export
│   │   └── router.py            # API v1 unified route aggregator
├── core/
│   ├── config.py                # Environment settings via Pydantic
│   ├── security.py              # JWT encoding/decoding, Bcrypt hashing
│   └── rate_limiter.py          # Sliding-window IP rate limiter
├── db/
│   ├── database.py              # SQLAlchemy engine & session factory
│   └── models.py                # Database ORM models
├── ml/
│   ├── artifacts/               # Serialized model, scaler, and test datasets
│   ├── trainer.py               # XGBoost model loader & base_score calibrator
│   ├── conformal_predictor.py   # Split conformal prediction engine
│   └── explainer.py             # SHAP feature attribution generator
└── services/
    ├── agronomic_baseline.py    # FAO-56 Penman-Monteith physics calculator
    ├── allocator.py             # Google OR-Tools GLOP solver integration
    └── negotiator.py            # Multi-agent game-theoretic dispute mediator
```

---

## 5. Security & Authentication Architecture

### 5.1 RBAC Enforcement Model
AquaMedi AI enforces a strict two-tier access architecture:

| Endpoint Pattern | Authentication | Required Role | Failure Response |
|:---|:---:|:---:|:---:|
| `/api/v1/farmer/*` | None (Public) | None (Anonymous) | N/A |
| `/api/v1/ml/predict` | None (Public) | None (Anonymous) | N/A |
| `/api/v1/auth/login` | None (Public) | None | HTTP 401 / 429 |
| `/api/v1/expert/*` | JWT Bearer | `expert` or `admin` | HTTP 401 / 403 |
| `/api/v1/allocation/*`| JWT Bearer | `expert` or `admin` | HTTP 401 / 403 |
| `/api/v1/negotiation/*`| JWT Bearer | `expert` or `admin` | HTTP 401 / 403 |
| `/api/v1/reports/*` | JWT Bearer | `expert` or `admin` | HTTP 401 / 403 |

### 5.2 Cryptographic Pipeline
* **JWT Token Specification:** Algorithm: HMAC-SHA256 (`HS256`), Payload: `{"sub": username, "role": role, "exp": timestamp}`, Expiry: 60 minutes.
* **Password Hashing:** Passlib with Bcrypt algorithm (`rounds = 12`).
* **Rate Limiting:** In-memory sliding window tracking client IP addresses. Maximum 10 failed login attempts per 60-second window.

---

## 6. Machine Learning & Optimization Pipeline

### 6.1 XGBoost 2.x In-Memory Booster Calibration
To resolve the XGBoost 2.x deserialization defect where `base_score` was lost upon unpickling, `trainer.py` executes in-memory calibration upon startup:

```python
def load_model():
    model = joblib.load(MODEL_PATH)
    try:
        booster = model.get_booster()
        # Restore serialized training mean prior without altering disk artifact
        booster.set_param('base_score', 214.17618)
    except Exception as e:
        logger.warning(f"Failed to set base_score: {e}")
    return model
```

### 6.2 Google OR-Tools GLOP Integration
The Linear Programming allocator is wrapped inside `services/allocator.py`:
1. Instantiates `pywraplp.Solver.CreateSolver('GLOP')`.
2. Adds continuous decision variables $x_i \in [0, C_{\text{max}, i}]$ for each canal distributary.
3. Adds capacity, total inflow, minimum subsistence, and reach equity constraints.
4. Solves the system using primal/dual simplex in $<15\text{ ms}$.

---

## 7. Scalability & Deployment Configurations

* **Development & Academic Demonstration:**
  * SQLite database (zero-configuration file-based DB).
  * In-memory rate limiting and session storage.
  * Single-process Uvicorn worker + Vite dev server.
* **Production Staging Environment:**
  * Containerized deployment using Docker Compose.
  * PostgreSQL 16 with connection pooling (`QueuePool`, pool size = 20, max overflow = 10).
  * Multi-worker Uvicorn deployment (`uvicorn --workers 4`).
  * Nginx reverse proxy with SSL termination and Gzip/Brotli compression.
