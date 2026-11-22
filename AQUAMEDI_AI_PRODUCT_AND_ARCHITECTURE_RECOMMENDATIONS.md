# AquaMedi AI — Product and Architecture Recommendations

**Document:** `AQUAMEDI_AI_PRODUCT_AND_ARCHITECTURE_RECOMMENDATIONS.md`
**Type:** Recommendation-only

---

## 1. Current product/architecture state (verified)

- Backend: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic (2 migrations), PostgreSQL default URL.
- Frontend: React 19, TypeScript, Vite, React Router, Recharts, Lucide; pages listed in `frontend/src/pages`; contexts Auth/Scenario/ViewMode; i18n en/hi/gu/mr.
- Security: PBKDF2 (100k), HS256 JWT, in-memory rate limiter (5 attempts / 900 s), RBAC deps.
- Dev fallback: frontend `AuthContext.tsx` fabricates an expert session for `admin123 / 12345678` in dev/test mode (F-16).
- Bundle: ~1.0 MB JS (per build output).
- No CI/CD (`.github/` absent).
- Synchronous SQLAlchemy (no async).

## 2. Backend/architecture recommendations

- **R-BE-01 (Priority B):** Fix dev auth fallback removal (cross-ref security).
- **R-BE-02 (Priority B):** Remove default secrets; require `jwt_secret_key` and `expert_default_password` in production. Affected: `config.py`.
- **R-BE-03 (Priority B):** Add scenario persistence (SQLite/PostgreSQL) for history and re-run. Affected: `services/scenario_service.py`, `models/scenario.py`, alembic.
- **R-BE-04 (Priority C):** Async migration only after load testing. Affected: `database.py`, services.
- **R-BE-05 (Priority B):** Service boundary cleanup — split `scenario_service.py` into prediction/conflict/allocation/negotiation services. Affected: `services/*`.
- **R-BE-06 (Priority C):** Archive candidate v1/v2/v3 experiment code under `experiments/` to reduce main-path complexity; keep gated by config.
- **R-BE-07 (Priority B):** Structured JSON logging + request timing; correlation ID already present. Affected: `main.py`.
- **R-BE-08 (Priority B):** Readiness health checks for model artifacts and DB. Affected: `api/health.py`, `main.py`.
- **R-BE-09 (Priority C):** N+1/query audit via SQLAlchemy echo in dev (UNVERIFIED whether any exist).

## 3. Security recommendations

- **R-SEC-01 (Priority A):** Remove default secrets (F-14).
- **R-SEC-02 (Priority A):** Remove frontend dev auth fallback (F-16).
- **R-SEC-03 (Priority B):** Distributed rate limiting (Redis/DB) or document single-worker constraint.
- **R-SEC-04 (Priority B):** Secret scanning in CI (gitleaks).
- **R-SEC-05 (Priority B):** Dependency vulnerability scanning (pip-audit, npm audit).
- **R-SEC-06 (Priority B):** No stack traces in production (`app_debug=False`).
- **R-SEC-07 (Priority C):** Audit upload endpoints in `iot_routes.py` / `spatial_routes.py` (UNVERIFIED).

## 4. Frontend/product recommendations

- **R-UX-01 (Priority A):** Remove dev auth fallback.
- **R-UX-02 (Priority B):** Interactive scenario comparison (side-by-side).
- **R-UX-03 (Priority B):** Before/after allocation comparison (LP vs. negotiated vs. proportional).
- **R-UX-04 (Priority B):** Scenario history + re-run with one parameter changed.
- **R-UX-05 (Priority B):** Export PDF/CSV/Excel from reports page.
- **R-UX-06 (Priority B):** What-if simulation (sliders → re-predict/re-allocate).
- **R-UX-07 (Priority C):** Mobile usability audit (breakpoints, touch targets, empty/loading/error states).
- **R-UX-08 (Priority C):** Accessibility (keyboard nav, ARIA, focus, contrast).
- **R-UX-09 (Priority C):** Bundle size reduction via code-splitting and lazy loading (target < 500 kB initial).
- **R-UX-10 (Priority D):** Preserve AquaMedi AI branding and design system (no redesign).

## 5. Deployment recommendations

- **R-DEP-01 (Priority B):** GitHub Actions CI (lint, typecheck, pytest, vitest, build, docker build).
- **R-DEP-02 (Priority B):** Docker hardening (multi-stage, non-root, healthcheck, pinned base).
- **R-DEP-03 (Priority C):** Performance benchmarking script (API latency, inference, LP time, negotiation time).
- **R-DEP-04 (Priority C):** Concurrency/load tests on scenario endpoint.
- **R-DEP-05 (Priority D):** Monitoring (structured logs + basic metrics) — optional.

## 6. API/contract recommendations

- **R-API-01 (Priority B):** Align documentation with actual routes (`/predictions`, `/allocations`, `/negotiations`, not `/ml/predict` etc.) — already flagged F-01.
- **R-API-02 (Priority C):** Uniform error envelope and deprecation policy for `/api/v1`.
- **R-API-03 (Priority C):** Pagination for scenario history.

## 7. References

- FastAPI documentation; SQLAlchemy 2 documentation; Vite documentation; React Router documentation.
- GIGW/NIC government web guidelines (for branding/accessibility).
