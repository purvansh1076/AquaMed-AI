# AQUAMEDI AI — MASTER ARCHITECTURE SPECIFICATION
**Document Reference**: `AQUA-ARCH-2026-V2`  
**System Classification**: Dual-Portal Agricultural Intelligence & Multi-Agent Water Dispute Resolution Platform  
**Target Basin**: Godavari / Mula-Pravara Canal Irrigation District (Ahmednagar, Maharashtra, India)  
**Author**: Principal Software Architect & Core Engineering Team  

---

## 1. High-Level Architectural Vision

AquaMedi AI bridges the critical gap between agricultural physics (FAO-56 Penman-Monteith reference evapotranspiration), empirical machine learning (XGBoost water demand prediction), constrained resource optimization (Google OR-Tools GLOP), and multi-party game-theoretic bargaining.

The architecture strictly segregates into two isolated presentation and privilege tiers:
1. **Farmer Portal**: Frictionless, uncredentialed guest access designed for semi-literate and smallholder farmers, offering voice queries in Marathi, Hindi, and English, smart irrigation recommendations, and symptom-guided crop health diagnostics.
2. **Agricultural Expert Portal**: Authenticated RBAC access designed for water resources engineers, extension officers, and canal magistrates, featuring LP-based allocation optimization, multi-agent dispute mediation, SHAP explainability, and cryptographic Merkle audit certification.

---

## 2. End-to-End System Topology

```mermaid
flowchart TD
    subgraph ClientTier["Client Presentation Layer (React 19 + TypeScript + Tailwind v4)"]
        Landing["Welcome Portal Selector (/)"]
        FarmerUI["Farmer Portal (/farmer)\n- Voice Assistant (Marathi/Hindi/EN)\n- Quick Water Estimator\n- Smart Irrigation Advisories\n- Crop Health Screening"]
        ExpertUI["Expert Dashboard (/overview, /dispute, /reports)\n- Hydro-GIS Canal Network Map\n- GLOP LP Optimization Console\n- Multi-Agent Negotiation Replay\n- SHAP Feature Attribution Tree"]
        AuthContext["AuthContext & Session Store\n- JWT LocalStorage Management\n- Guest Token Auto-Acquisition"]
    end

    subgraph GatewayTier["API Gateway & Middleware Layer (FastAPI 0.115)"]
        Router["API Gateway (/api/v1)"]
        CorrMiddleware["Correlation ID Middleware\n(X-Correlation-ID Tracking)"]
        CorsMiddleware["Strict CORS Policy Enforcement"]
        RateLimiter["In-Memory Rate Limiting & Lockout"]
        RBAC["FastAPI Security Dependencies\n- require_expert\n- require_farmer_or_expert"]
    end

    subgraph ServiceTier["Core Domain & Computation Engines"]
        MLService["Machine Learning Engine\n- XGBoost Regressor (xgb_model.joblib)\n- Preprocessor Pipeline (MinMaxScaler)\n- Split Conformal Prediction (90% Interval)"]
        FAOService["Agronomic Physics Model\n- FAO-56 Penman-Monteith Equations\n- Crop Kc Reference Database"]
        WeatherService["Meteorological Service\n- Open-Meteo Agro API Client\n- 30-min TTL In-Memory Cache\n- Regional Historical Baseline Fallback"]
        SpatialService["Spatial & Remote Sensing Engine\n- Sentinel-2 MSI Spectral Indices (NDVI, NDWI)\n- Satellite Dynamic Kc Calibration\n- Canal GIS Topology Provider"]
        LPService["Water Allocation Solver\n- Google OR-Tools GLOP Linear Solver\n- Physical Conveyance Loss Constraints\n- Objective Urgency Rescaling"]
        AgentService["Multi-Agent Dispute Mediation\n- Farmer Agent Concession Protocol\n- Utility-Based Equilibrium Engine\n- Nash Product Convergence"]
        AuditService["Cryptographic Trust Engine\n- Binary Merkle Tree Construction\n- SHA-256 Agreement Verification Certificate"]
        IoTService["IoT & Field Telemetry Bridge\n- LoRaWAN/ESP32 Packet Ingestion\n- 24-Hour Diurnal Soil Physics Simulator"]
    end

    subgraph PersistenceTier["Storage & Persistence Layer"]
        PostgresDB[("PostgreSQL 16 / SQLite\n- SQLAlchemy 2.0 ORM\n- Alembic Migrations (0001, 0002)\n- Connection Pooling")]
        ModelStore[("Model Registry\n- Serialized Joblib Artifacts\n- Synthetic Training Ground Truth")]
    end

    Landing -->|Guest Entry| FarmerUI
    Landing -->|Expert Auth| ExpertUI
    FarmerUI --> AuthContext
    ExpertUI --> AuthContext
    AuthContext -->|Bearer JWT| GatewayTier

    Router --> CorrMiddleware --> CorsMiddleware --> RateLimiter --> RBAC
    RBAC --> ServiceTier

    ServiceTier --> PostgresDB
    MLService --> ModelStore
    LPService -.-> PostgresDB
```

---

## 3. Component Specifications & Boundaries

### 3.1 Authentication & RBAC Engine
- **Farmer Guest Access**: Uncredentialed issuance of JWTs containing `role: "farmer_guest"` and scoped permissions (`farmer:read`, `farmer:predict`, `farmer:irrigation_advice`).
- **Expert Access**: Authenticated via `/api/v1/auth/expert/login`. Validates credentials against database-backed `users` table with PBKDF2-HMAC-SHA256 password hashing. In development mode, `admin123`/`12345678` is permitted when `enable_dev_demo_credentials=True`.
- **RBAC Boundaries**: Endpoints under `/scenarios/run`, `/conflicts`, `/allocations`, and `/negotiations` strictly enforce `require_expert` (HTTP 403 Forbidden for guest farmers).

### 3.2 Physics & Machine Learning Coupling
- **Physics Layer (`calculate_fao56_et0`)**: Computes reference evapotranspiration $ET_0$ based on radiation balance, psychrometric constant, vapor pressure deficit, and aerodynamic resistance according to FAO Paper 56.
- **Machine Learning Layer (`xgb_model.joblib`)**: High-speed surrogate regressor producing predicted water requirements in $11\text{ ms}$.
- **Uncertainty Layer (`conformal_predictor.py`)**: Computes finite-sample distribution-free prediction intervals $[Q_{lower}, Q_{upper}]$ with 90% statistical confidence.

### 3.3 Hydro-Spatial Optimization Layer
- **Physical Loss Formulation**: Canal discharge loses volume via transit seepage:
  $$\sum_{i=1}^N \frac{x_i}{\eta_i} \le Q_{total}$$
  where $\eta_i = \exp(-k L_i)$ accounts for distance $L_i$ from canal head regulator.
- **Google OR-Tools GLOP**: Maximizes urgency-weighted satisfaction subject to survival lower bounds and conveyance limits.

### 3.4 Multi-Agent Agreement & Cryptographic Ledger
- **Concession Bargaining**: Simulates discrete negotiation rounds where agents with higher relative surplus concede marginal allocations to deficit agents.
- **Cryptographic Merkle Proof**: Computes binary SHA-256 Merkle root across final allocation vectors, generating an immutable verification certificate.
