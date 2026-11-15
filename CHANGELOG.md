# Changelog

All notable changes to the **AquaMedi AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-15

### Added
- **Production CI Pipeline (`.github/workflows/ci.yml`):** GitHub Actions workflow executing backend pytest (Python 3.12) and frontend vitest/production build (Node 20) on push and pull requests.
- **Group-Conditional Conformal Prediction (`backend/app/ml/group_conformal.py`):** Stratified conformal prediction intervals per crop and growth stage with exact finite-sample quantile calibration.
- **Max-Min Fairness Linear Program (`backend/app/allocation/lp_allocator.py`):** Explicit mathematical optimization maximizing the minimum demand-satisfaction ratio across competing farmers.
- **Allocation Fairness Metrics Suite (`backend/app/allocation/fairness.py`):** Quantitative metrics including Jain's Fairness Index, allocation disparity, water deficit, minimum satisfaction, and mean satisfaction.
- **Typed Multi-Agent Messaging Schema (`backend/app/agents/messages.py`):** Pydantic-validated `AgentMessage` schema enforcing typed interactions and preventing invalid agent messages.
- **Negotiation Convergence Reporting (`backend/app/negotiation/negotiation_engine.py`):** Added `convergence_report()` method providing transparent telemetry on Nash objective trajectories and termination criteria.
- **Production Docker Hardening (`docker-compose.yml`, `backend/Dockerfile`):** Non-root user execution (`appuser`, UID 10001), container health checks via `/api/v1/health/ready`, and strict `.dockerignore`.
- **Comprehensive Audit & Documentation Archive (`docs/audits/`):** Traceability reports from Phase A through Phase T covering ML, agronomy, game theory, database, security, and repository hygiene.
- **Reproducibility Benchmark Artifacts (`backend/data/models/*.json`):** Tracked benchmark outputs for data leakage audits, repeated cross-validation, allocation comparisons, and multi-agent simulations.

### Changed
- **Production Secret Validation (`backend/app/config.py`):** Replaced hardcoded default secrets with empty strings and added a Pydantic model validator that aborts application startup in `production` environment if `JWT_SECRET_KEY`, `SECRET_KEY`, or `EXPERT_DEFAULT_PASSWORD` are missing.
- **Prototype Authentication Gating (`backend/app/api/auth.py`):** Development demo credentials (`admin123`) strictly disabled by default (`enable_dev_demo_credentials=False`) and blocked in production environments.
- **Client-Side Authentication (`frontend/src/context/AuthContext.tsx`):** Removed prototype demo-session fabrication; authentication is strictly performed by backend verification.
- **XGBoost Unpickling Calibration (`backend/app/ml/trainer.py`):** Dynamically calibrates unpickled XGBoost `base_score` using persisted evaluation target means, resolving library version serialization differences.
- **Linear Programming Control Flow (`backend/app/allocation/lp_allocator.py`):** Enforced strict fallback hierarchy where successful primary solves cannot be overwritten by relaxed or proportional fallbacks.
- **Independent FAO-56 Reference Verification (`backend/tests/test_et0_independent.py`):** Added independent analytical cross-checks for Penman-Monteith ET0 calculation against verified reference tables.

### Fixed
- **Negotiation Engine State Tracking (`backend/app/negotiation/negotiation_engine.py`):** Fixed uninitialized `current_responses` in multi-round mediator loop.
- **Conformal Interval Area Scaling (`backend/app/ml/conformal_predictor.py`):** Corrected non-conformity score normalization to prevent interval skew across heterogeneous farm sizes.
- **Docker Compose Environment Inconsistencies:** Aligned environment variables and removed insecure defaults in container service declarations.

### Security
- **Eliminated Hardcoded Credentials:** Removed default passwords and production JWT keys from source code.
- **Strict Role-Based Sandboxing:** Enforced backend authorization boundaries preventing guest farmer sessions from accessing administrative or optimization endpoints.
- **Brute-Force Rate Limiting:** PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and progressive 15-minute lockouts after 5 consecutive failures.
