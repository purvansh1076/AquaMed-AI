# AquaMediAI — Government-Grade Transformation & Architecture Report

## 1. Overview & System Purpose
AquaMediAI is an agricultural intelligence and explainable multi-agent water-sharing dispute mediation platform. This transformation consolidates the system into a trustworthy, government-grade digital platform designed for state and national agricultural departments.

### Key Architectural Transformations:
1. **New Entry Experience & Role Selection**:
   - Primary landing screen (`/` and `/welcome`) inspired by NSW Government design principles (`nsw.gov.au`).
   - Distinct, unambiguous entry pathways for **Farmers** and **Agricultural Experts**.
2. **Frictionless Farmer Access**:
   - Instant guest entry requiring **no passwords or credentials**.
   - Server-side issuance of restricted guest sessions (`farmer_guest` role) with 24-hour expiration.
   - Plain-language dashboard with all ML/data-science jargon replaced by intuitive agricultural concepts.
3. **Government-Grade Expert Authentication**:
   - Dedicated authentication portal (`/login`) for extension officers, agronomists, and dispute mediators.
   - NIST SP 800-132 compliant PBKDF2-HMAC-SHA256 password hashing (100,000 iterations, 16-byte random salt).
   - Cryptographically signed HS256 JWT tokens with server-side validation.
   - Brute-force protection: in-memory `LoginRateLimiter` with automatic lockout after 5 consecutive failed attempts.
   - Strict server-side RBAC: Guest farmers attempting to call expert-only endpoints (`/scenarios/run`, `/conflicts`, `/allocations`, `/negotiations`) receive HTTP 403 Forbidden.
4. **XGBoost-Only Production Consolidation**:
   - Extreme Gradient Boosting (XGBoost 2.0) is the **exclusive active production model**.
   - Random Forest removed from all production dropdowns, UI selectors, and inference defaults.
   - Historical Random Forest artifacts (`rf_model.joblib`), evaluation metrics, and research baselines safely preserved on disk for academic reproducibility without destructive deletion.
5. **Centralized Multilingual Readiness**:
   - Added native **Marathi (`mr`)** localization alongside **Gujarati (`gu`)**, **Hindi (`hi`)**, and **English (`en`)**.
   - Real-time language switching in the government authority header.

---

## 2. Security & RBAC Specification

### Role-Based Access Matrix

| Endpoint | Method | Permitted Roles | Failure Response |
|----------|--------|-----------------|------------------|
| `/api/v1/auth/guest-session` | POST | Anonymous (Public) | 200 OK |
| `/api/v1/auth/expert/login` | POST | Anonymous (Public) | 401 / 429 Too Many Requests |
| `/api/v1/auth/me` | GET | `farmer_guest`, `expert`, `admin` | 401 Unauthorized |
| `/api/v1/predictions` | POST | `farmer_guest`, `expert`, `admin` | 401 / 403 Forbidden |
| `/api/v1/predictions/batch` | POST | `farmer_guest`, `expert`, `admin` | 401 / 403 Forbidden |
| `/api/v1/scenarios/run` | POST | `expert`, `admin` | 403 Forbidden (if `farmer_guest`) |
| `/api/v1/conflicts` | POST | `expert`, `admin` | 403 Forbidden (if `farmer_guest`) |
| `/api/v1/allocations` | POST | `expert`, `admin` | 403 Forbidden (if `farmer_guest`) |
| `/api/v1/negotiations` | POST | `expert`, `admin` | 403 Forbidden (if `farmer_guest`) |
| `/api/v1/health` | GET | Anonymous (Public) | 200 OK / 503 Degraded |

### Initial Expert Account Provisioning
For administrative and extension officer access:
- **Default Official Email**: `expert@aquamedi.gov.in`
- **Expert Account Provisioning**: Configured securely via `EXPERT_DEFAULT_EMAIL` and `EXPERT_DEFAULT_PASSWORD` in `backend/.env` (no hardcoded credentials exposed in client application).
- **Configurable via**: `EXPERT_DEFAULT_EMAIL` and `EXPERT_DEFAULT_PASSWORD` in `.env`.

---

## 3. Production Machine Learning Model Specification

### Active Regressor: XGBoost 2.0
- **Model File**: `backend/data/models/xgb_model.joblib` (576 KB)
- **Encoder File**: `backend/data/models/encoders.joblib` (2.4 KB)
- **Features**: 22 FAO-56 engineered features (soil water holding capacity, crop coefficient $K_c$, crop evapotranspiration $ET_c$, temperature, humidity, rainfall deficit, flexibility score, urgency score).

### Verified Evaluation Metrics on Holdout Test Set:
- **Test Samples**: 451
- **Mean Absolute Error (MAE)**: 18.6313 m³/day
- **Root Mean Squared Error (RMSE)**: 29.2661 m³/day
- **Coefficient of Determination ($R^2$)**: 0.9699 (96.99% variance explained)
- **Training Time**: 0.4161 seconds

### Random Forest Baseline (Preserved for Historical Research):
- **Model File**: `backend/data/models/rf_model.joblib` (16.3 MB)
- **Test MAE**: 17.4865 m³/day
- **Test RMSE**: 27.3761 m³/day
- **Test $R^2$**: 0.9737
- **Status**: Preserved on disk, removed from production UI.

---

## 4. UI/UX Transformation & Terminology Mapping

| Developer / Technical Term | Farmer-Facing Term | Purpose |
|-----------------------------|--------------------|---------|
| Random Forest Regression Model Prediction | Your Farm's Crop Health Prediction | Clear outcome without ML complexity |
| Feature Importance Analysis | What Affects Your Crop Health? | Explains environmental drivers in plain English |
| Model Evaluation Metrics | How Accurate Is the Prediction? | Transparent confidence disclosure |
| Data Preprocessing | Preparing Farm Data | Removes ETL jargon |
| Anomaly Detection | Unusual Farm Conditions Detected | Immediate operational alert |
| ETo / ETc (Evapotranspiration) | Crop Water Need (m³/day) | Practical metric for daily irrigation |
| LP Solver (GLOP) | Automated Water Sharing Plan | Actionable dispute resolution |

---

## 5. Local Execution Instructions

### Backend Startup:
```powershell
cd backend
# With virtual environment activated:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/api/v1/health`

### Frontend Startup:
```powershell
cd frontend
npm run dev
```
- Portal URL: `http://localhost:5173/` (Lands directly on Welcome & Role Selection Page)

### Test Execution:
- **Frontend Test Suite**:
  ```powershell
  cd frontend
  npm test
  # 78 tests passing across 10 test files
  ```
- **Frontend Production Build**:
  ```powershell
  cd frontend
  npm run build
  # tsc -b && vite build succeeds in ~1.5s
  ```
- **Backend Test Suite**:
  ```powershell
  cd backend
  pytest tests/test_security_rbac.py -v
  pytest tests/ -v
  ```

---

## 6. Deployment Readiness & Free/Low-Cost Strategy
- **Frontend**: Deploy static SPA (`frontend/dist/`) to **Vercel** or **Netlify** (Free tier, edge CDN).
- **Backend**: Containerize using existing `Dockerfile` and deploy on **Render** (Free web service) or **Railway** (low-cost starter tier).
- **Model Storage**: Model files total ~17 MB (XGBoost 576 KB, RF 16 MB), well within free git LFS and container limits.
- **Database**: Optional PostgreSQL on **Supabase** or **Neon** (Serverless PostgreSQL free tier) or local SQLite fallback.

