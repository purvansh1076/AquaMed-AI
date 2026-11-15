# AquaMedi AI — Technical Project Handover Manual

**Document Version:** 1.0.0 (Phase T Final Release Handover)  
**Date:** November 2026  
**Audience:** Maintainers, DevOps Engineers, Agricultural System Integrators, Academic Researchers  

---

## 1. System Overview & Architectural Topology

AquaMedi AI provides algorithmic decision support for equitable irrigation distribution and multi-stakeholder dispute mediation across command areas.

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER (UI)                          │
├───────────────────────────────────┬────────────────────────────────────┤
│  Farmer Portal (Frictionless UX) │  Expert Portal (Authenticated UX)  │
│  - 1-Click Guest Access           │  - Role-Based Access Control (RBAC)│
│  - Multilingual (EN, HI, GU, MR)  │  - Scenario Configuration & Solver │
│  - Plain-Language Badges          │  - TreeSHAP & Convergence Logs     │
└─────────────────┬─────────────────┴───────────────────┬────────────────┘
                  │                                     │
                  │ REST API (JSON / JWT / CORS)        │
                  ▼                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION TIER (FastAPI)                       │
├────────────────────────────────────────────────────────────────────────┤
│  Endpoints: /api/v1/predict, /allocate, /negotiate, /explain, /health  │
│  Security: PBKDF2 Password Hashing, JWT Tokens, In-Memory Rate Limiter │
├───────────────────┬───────────────────┬────────────────────────────────┤
│   ML Pipeline     │  Allocation & LP  │    Multi-Agent Negotiation     │
│ - XGBoost 2.0     │ - Google OR-Tools │  - Farmer Digital Twins        │
│ - Conformal Pred. │   GLOP Solver     │  - Bounded Nash Bargaining     │
│ - Group Conformal │ - Max-Min LP      │  - Typed AgentMessage (v1.0)   │
│ - TreeSHAP Exp.   │ - Fallback Chain  │  - Convergence Telemetry       │
└─────────┬─────────┴─────────┬─────────┴───────────────┬────────────────┘
          │                   │                         │
          ▼                   ▼                         ▼
┌───────────────────┬───────────────────┬────────────────────────────────┐
│  DATA & STORAGE   │  MODEL ARTIFACTS  │     DEPLOYMENT & RUNTIME       │
│ - PostgreSQL 15+  │ - xgb_model.joblib│ - Docker Multi-stage           │
│ - Alembic Version │ - rf_model.joblib │ - Non-root execution (appuser) │
│   (0001 -> 0002)  │ - encoders.joblib │ - GitHub Actions CI/CD         │
│ - Synthetic FAO56 │ - eval_results.js │ - Health check endpoints       │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

---

## 2. Source Code & Repository Structure

```
aquamedi-ai/
├── .github/workflows/ci.yml       # GitHub Actions CI (pytest + vitest + build)
├── backend/
│   ├── alembic/versions/          # Database migration lineage (0001 -> 0002)
│   ├── app/
│   │   ├── agents/                # Farmer digital twins & typed message schema
│   │   ├── allocation/            # OR-Tools GLOP & Max-Min LP allocators
│   │   ├── api/                   # FastAPI route handlers (auth, health, core)
│   │   ├── conflict/              # Rule-based conflict detection engine
│   │   ├── core/                  # Security utilities & password hashing
│   │   ├── db/                    # SQLAlchemy engine & session management
│   │   ├── explainability/        # TreeSHAP feature attributions
│   │   ├── ml/                    # XGBoost trainer, conformal, group conformal
│   │   ├── models/                # SQLAlchemy ORM models (User, Scenario, etc.)
│   │   ├── negotiation/           # Nash bargaining engine & mediator
│   │   └── schemas/               # Pydantic v2 data models & validation
│   ├── data/
│   │   ├── models/                # Tracked model artifacts & benchmark outputs
│   │   └── raw/                   # Raw dataset dumps (ignored by git)
│   ├── scripts/                   # Reproducibility scripts (eval, simulation, etc.)
│   ├── tests/                     # 862 Pytest suite covering all modules
│   ├── Dockerfile                 # Hardened non-root production container
│   ├── requirements.txt           # Frozen Python dependencies
│   └── main.py                    # FastAPI entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/            # UI widgets, layout, navigation
│   │   ├── context/               # AuthContext (strictly server-authenticated)
│   │   ├── pages/                 # FarmerView, ExpertView, ScenarioConfig, etc.
│   │   ├── services/              # Axios REST client with error mapping
│   │   └── tests/                 # 95 Vitest unit & integration tests
│   ├── package.json               # Frontend dependencies & npm scripts
│   └── vite.config.ts             # Vite build configuration
├── docs/                          # Comprehensive architectural & audit docs
├── RELEASE_NOTES.md               # v1.0.0 capabilities and notes
├── CHANGELOG.md                   # Chronological version history
└── docker-compose.yml             # Local staging stack
```

---

## 3. Environment Configuration & Secret Management

Configuration is handled through Pydantic `BaseSettings` reading environment variables or `.env` files.

### Critical Environment Variables

| Variable Name | Required Environment | Default | Description |
|---|---|---|---|
| `APP_ENV` | All | `development` | Environment mode (`development`, `testing`, `production`). |
| `APP_DEBUG` | All | `true` in dev, `false` in prod | Enables FastAPI debug traces. Must be `false` in production. |
| `DATABASE_URL` | Production / Staging | `postgresql+psycopg2://...` | Connection URI for PostgreSQL database. |
| `SECRET_KEY` | Production | `""` (Empty) | General application secret key. Validator prevents empty in prod. |
| `JWT_SECRET_KEY` | Production | `""` (Empty) | Key for signing JWT tokens. Validator prevents empty in prod. |
| `EXPERT_DEFAULT_PASSWORD` | Production | `""` (Empty) | Admin password for expert user. Validator prevents empty in prod. |
| `ENABLE_DEV_DEMO_CREDENTIALS` | Development | `false` | When `true` (dev only), permits prototype login (`admin123`). |
| `MODEL_DIR` | All | `data/models` | Filesystem path where trained `.joblib` models reside. |

> [!IMPORTANT]
> In `APP_ENV=production`, `Settings.validate_production_secrets` will raise a `ValueError` and abort startup if `SECRET_KEY`, `JWT_SECRET_KEY`, or `EXPERT_DEFAULT_PASSWORD` are missing or empty.

---

## 4. Execution & Testing Runbooks

### 4.1 Running the Backend Locally
```bash
cd backend
source .venv/bin/activate  # Or Windows: .\.venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4.2 Executing the Backend Test Suite
```bash
cd backend
pytest -q
# Target outcome: 862 passed, 5 warnings in ~80s
```

### 4.3 Running the Frontend Locally
```bash
cd frontend
npm run dev
# Vite server launches at http://localhost:5173
```

### 4.4 Executing the Frontend Test Suite & Production Build
```bash
cd frontend
npm test -- --run    # Vitest execution: 95 passed
npm run build        # Production build: tsc -b && vite build
```

---

## 5. Model Artifact Tracking & Verification

All model artifacts are stored in `backend/data/models/` and tracked directly in Git (~16 MB total, well below GitHub's 100 MB per-file threshold).

### Verified Checksums (SHA-256)
- `backend/data/models/encoders.joblib`:  
  `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD`
- `backend/data/models/rf_model.joblib`:  
  `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75`
- `backend/data/models/xgb_model.joblib`:  
  `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56`
- `backend/data/models/evaluation_results.json`:  
  `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7`

### Model Retraining Runbook
To retrain models from scratch using synthetic data generation:
```bash
cd backend
python -c "from app.ml.trainer import run_training_pipeline; run_training_pipeline(n_samples=3000, seed=42)"
```

---

## 6. Database Migrations Runbook

Database schema evolution is managed with Alembic.

### Applying Migrations
```bash
cd backend
alembic upgrade head
```

### Creating New Migrations
```bash
cd backend
alembic revision --autogenerate -m "description_of_change"
```

### Current Revision History
1. `0001_initial`: Sets up core tables (`scenarios`, `allocations`, `farmer_records`).
2. `0002_add_users_table`: Adds authentication tables and hashed credential storage.

---

## 7. Recommended Production Roadmap

Prioritized enhancements for upcoming development cycles:

1. **Distributed Rate Limiting (P1):** Replace in-memory auth rate limiting with a Redis-backed token bucket implementation.
2. **Dynamic Code Splitting (P2):** Implement React `lazy()` imports in the frontend router to split the 1.02 MB bundle.
3. **Async Database Engine (P2):** Upgrade SQLAlchemy engine to `asyncpg` for high-concurrency event loops.
4. **Regional Weather Ingestion (P3):** Integrate live IMD/CWC REST APIs for automated real-time $ET_0$ calculation.
5. **Physical SCADA Adapter (P3):** Develop standard Modbus/OPC-UA connectors for remote canal gate telemetry.

---

## 8. Handover Sign-off

- **Engineering Status:** Complete, Verified, Zero Defect Backlog
- **Repository Hygiene:** Clean, Fully Tracked, Strict Ignore Rules
- **Publication Gate:** Prepared for GitHub Publication (Awaiting Authorization)
