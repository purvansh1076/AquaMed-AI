# AQUAMEDI AI — PHASE 9: REMAINING WORK & PRODUCTION HARDENING ROADMAP

> **Document Type:** Production Hardening Roadmap, Technical Debt Analysis & Remaining Work  
> **Date:** November 6, 2026  
> **Auditors:** Principal Software Architect, Senior Infrastructure Engineer, AI/ML Research Engineer, Application Security Engineer  
> **Repository:** AquaMedi AI (`aquamedi-ai`)  
> **Branch:** `feature/aquamedi-ai-product-transformation`  
> **Context:** Post-Phase 9 Independent Audit

---

## 1. EXECUTIVE ASSESSMENT: THE PATH TO COMMERCIAL PRODUCTION

While AquaMedi AI is **100% Academic Demonstration Ready** and **Conditionally Approved for Monitored Field Pilots**, it is **not yet approved for unbounded commercial production deployment**.

The platform's computational and mathematical pipelines (FAO-56, XGBoost, SHAP, OR-Tools GLOP, multi-agent game-theoretic bargaining) are fully implemented and verified with 920 passing automated tests. However, several physical-world prerequisites, empirical data requirements, and cloud infrastructure hardenings remain before it can be deployed at scale across national canal command areas.

This document outlines the exact, unvarnished roadmap categorized by priority (P0 to P3).

---

## 2. P0: BLOCKERS FOR COMMERCIAL PRODUCTION RELEASE

These items represent fundamental requirements that must be resolved before commercial production release.

```
+---------------------------------------------------------------------------------------+
|                                P0 BLOCKERS ROADMAP                                     |
+---------------------------------------------------------------------------------------+
|  1. Empirical Field Telemetry & Model Retraining (Replace synthetic FAO-56 data)     |
|  2. Physical IoT Gateway Deployment (LoRaWAN / Cellular telemetry integration)       |
|  3. Live Copernicus Open Access Hub Sentinel-2 API Integration                        |
|  4. Enterprise Secrets Management (HashiCorp Vault / Cloud Secret Ingestion)          |
+---------------------------------------------------------------------------------------+
```

### P0.1 Real Empirical Field Dataset Collection & Model Retraining
- **Current State:** The XGBoost model was trained on 200 synthetic scenarios generated via `SyntheticDataGenerator`. While mathematically grounded in FAO-56 physics, synthetic data cannot reflect micro-climate anomalies, canal sediment seepage, or unpredictable farmer soil compaction.
- **Requirement:**
  1. Partner with state agricultural universities (e.g. TNAU, PAU, UAS Dharwad) to collect empirical soil moisture and lysimeter data across 3 distinct crop seasons (Kharif, Rabi, Zaid).
  2. Ingest real canal discharge telemetry from state irrigation department flumes.
  3. Retrain XGBoost and conduct multi-year backtesting against actual farmer water withdrawals.
- **Estimated Effort:** 3 to 6 months (aligned with crop seasons).

### P0.2 Physical IoT Hardware Gateway Integration
- **Current State:** The IoT telemetry endpoints (`/api/v1/iot/telemetry`) and simulated dynamics are functional in software via an in-memory diurnal physics simulator. No physical sensors are connected.
- **Requirement:**
  1. Deploy LoRaWAN-enabled capacitance soil moisture probes (e.g. Decagon/Meter Group 5TM) and solar-powered ultrasonic canal level sensors.
  2. Implement an MQTT broker (e.g. EMQX / Eclipse Mosquitto) or AWS IoT Core connector to ingest sensor telemetry directly into the FastAPI backend.
  3. Implement hardware device authentication using X.509 client certificates.
- **Estimated Effort:** 4 weeks.

### P0.3 Live Copernicus Open Access Hub Sentinel-2 API Integration
- **Current State:** The GIS service (`app.services.remote_sensing`) implements band-math equations (NDVI, NDWI) and processes mock raster data.
- **Requirement:**
  1. Provision cloud credentials for Copernicus Data Space Ecosystem (CDSE) or AWS Earth Sentinel-2 COG (Cloud Optimized GeoTIFF) repository.
  2. Implement asynchronous Celery / Redis background worker tasks to fetch Sentinel-2 MSI 10-meter band tiles on a 5-day revisit cycle.
  3. Implement automated cloud-masking using the Scene Classification Layer (SCL).
- **Estimated Effort:** 3 weeks.

### P0.4 Enterprise Secrets Management & Production Configuration
- **Current State:** Secrets and default credentials are read via `pydantic-settings` from local environment variables.
- **Requirement:**
  1. Integrate HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault to dynamically inject database passwords and JWT signing keys.
  2. Rotate JWT signing keys with automated JWKS endpoint provisioning.
  3. Disable all development demo credential pathways permanently in production builds.
- **Estimated Effort:** 1 week.

---

## 3. P1: HIGH-PRIORITY HARDENING FOR FIELD PILOT DEPLOYMENT

Required prior to running multi-village field pilots with real farmer participation.

### P1.1 Refresh Token Rotation & Session Revocation
- **Current State:** JWTs are stateless HS256 tokens valid for 8 hours (expert) or 24 hours (farmer guest).
- **Hardening:**
  - Implement short-lived access tokens (15 minutes) paired with cryptographic refresh tokens stored in HTTP-only, Secure, SameSite cookies.
  - Implement a Redis-backed token revocation list to allow immediate session termination upon administrative logout or compromise.

### P1.2 Database Connection Pooling & Multi-Pod Failover
- **Current State:** Standard SQLAlchemy engine configuration.
- **Hardening:**
  - Deploy PgBouncer between FastAPI instances and PostgreSQL to support concurrent connection spikes during simultaneous irrigation rounds.
  - Configure SQLAlchemy connection pool recycling (`pool_recycle=1800`, `pool_size=20`, `max_overflow=10`).

### P1.3 Distributed Rate Limiting via Redis
- **Current State:** In-memory sliding window rate limiter (`LoginRateLimiter`) inside the single Python process.
- **Hardening:**
  - Replace process-local dictionary with a Redis-backed token bucket algorithm (e.g. `redis-py` with Lua scripts) so rate limits are uniformly enforced across multiple horizontally scaled Uvicorn workers.

### P1.4 HTTP Security Headers & Content Security Policy (CSP)
- **Current State:** CORS headers configured; basic FastAPI middleware.
- **Hardening:**
  - Add `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
  - Add `Content-Security-Policy` restricting script execution, style sources, and iframe embedding.
  - Add `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.

---

## 4. P2: MEDIUM-PRIORITY REFINEMENTS & ENHANCEMENTS

Planned for iterative enhancement post-pilot launch.

### P2.1 Cloud-Backed Multilingual Voice Pipeline (Bhashini / Azure Speech)
- **Current State:** Browser Web Speech API (`webkitSpeechRecognition` / `SpeechSynthesisUtterance`). Works natively without API keys, but synthesis accents and recognition accuracy vary significantly across different mobile browsers and rural dialects.
- **Refinement:**
  - Integrate government AI platforms such as BHASHINI (National Language Translation Mission) for high-accuracy regional Indian dialect synthesis (Hindi, Marathi, Telugu, Tamil, Gujarati).

### P2.2 Interactive GIS Canal Vector Maps
- **Current State:** SVG/Canvas-based topology map (`CanalNetworkMap.tsx`).
- **Refinement:**
  - Integrate Mapbox GL JS or Leaflet.js with MapLibre to overlay real OpenStreetMap satellite layers, cadastral farm survey boundaries, and digital elevation models (DEM) for hydrological catchment slope analysis.

### P2.3 Automated Model Drift & Water Balance Monitoring
- **Current State:** Static XGBoost model evaluated via historical split.
- **Refinement:**
  - Deploy Evidently AI or MLflow to monitor feature drift (Kolmogorov-Smirnov tests on humidity and temperature shifts) and trigger automated alerts when climate patterns deviate significantly from training baselines.

---

## 5. P3: LONG-TERM RESEARCH & INNOVATION

Future technological expansions for large-scale state water resource departments.

### P3.1 Edge AI on Microcontrollers for Canal Gate Automation
- Deploy quantized TinyML models (TensorFlow Lite for Microcontrollers) directly onto ESP32 or Raspberry Pi boards installed at canal headworks to autonomously modulate motorized sluice gates based on local LP allocation decisions, even during cellular backhaul outages.

### P3.2 Cryptographic Ledger for Water Entitlements
- Connect the existing SHA-256 audit log chains (`app.core.audit_crypto`) to a state-authorized distributed ledger (Hyperledger Fabric) to provide tamper-proof, legally admissible proof-of-allocation records for interstate river dispute tribunals.

---

## 6. TIMELINE & IMPLEMENTATION MILESTONES

| Milestone | Target Horizon | Key Deliverables | Readiness Gate |
| :--- | :---: | :--- | :--- |
| **Phase 9 Complete** | **Current** | Independent verification, 920 passing tests, zero TS errors, audit reports. | Academic Demonstration Ready |
| **Milestone 10: Pilot Hardening** | 1 - 2 Months | Redis rate limiting, refresh tokens, PgBouncer, CSP headers. | Monitored Field Pilot Ready |
| **Milestone 11: Real Telemetry** | 3 - 6 Months | Physical LoRaWAN sensors, Copernicus live satellite data, empirical retraining. | Regional Production Ready |
| **Milestone 12: Enterprise Scale**| 6 - 12 Months | Multi-region Kubernetes, BHASHINI voice integration, Edge AI sluice gates. | Commercial Production Ready |
