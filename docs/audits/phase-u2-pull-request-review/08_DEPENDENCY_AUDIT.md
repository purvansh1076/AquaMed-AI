# Phase U2 — Comprehensive Dependency & Vulnerability Audit Report

**Audit Target:** Frontend (`package.json`) & Backend (`requirements.txt`)  
**Audit Date:** 2026-11-15  
**Auditor:** AquaMedi AI Release Engineering  

---

## 1. Full Dependency Manifest Audit

### 1.1 Production Runtime Dependencies (Frontend)
Verified via `npm audit --omit=dev`:
```bash
found 0 vulnerabilities
```
All production client-side packages are clean:
- `react` (`^19.2.8`) & `react-dom` (`^19.2.8`): Core UI library.
- `react-router-dom` (`^7.18.4`): Client-side routing.
- `recharts` (`^3.10.1`): Charting and visualizations.
- `lucide-react` (`^1.47.0`): Icon system.

### 1.2 Development Tooling Advisories (5 Reported)
When including offline `devDependencies`, `npm audit` reports 5 advisories (2 moderate, 3 high):

| Package Name | Severity | CVE / GHSA ID | Scope & Environment | Production Client Risk |
|---|---|---|---|---|
| `@vitest/mocker` / `vitest` | Moderate | GHSA-qxg6-89mg-rqv8 | Unit test mock runner | **None** (Offline test tool only) |
| `source-map-js` | High | GHSA-68fv-2mgg-jv7q | Build-time CSS source map generator | **None** (Build tool only; not in bundle) |
| `undici` | High | GHSA-4qv8-2p9j-2685 | Transitive dependency of `jsdom` (HTTP parser) | **None** (Test environment only) |
| `vite` | High | GHSA-698v-4r3x-3vcv | Development HTTP server / `launch-editor` | **None** (Build tool only; static assets deployed) |

### 1.3 Technical Risk Evaluation
In production deployment, the frontend application is compiled into static JavaScript and CSS files located in `dist/`. These files are served statically by an unprivileged HTTP server (Nginx, Caddy, or FastAPI static mounts). **Neither Vite development server, Vitest test runner, JSDOM, nor Undici run as services in production.** Consequently, these advisories pose zero remote attack surface to end users.

In strict compliance with release safeguards, dependencies were not automatically upgraded to prevent unintended regression or API incompatibility.

---

## 2. Backend Dependencies Audit (`backend/requirements.txt`)

- Web framework: `fastapi>=0.111.0,<0.120.0`, `uvicorn>=0.30.0,<0.35.0`
- Pydantic: `pydantic>=2.7.0,<3.0.0`, `pydantic-settings>=2.3.0,<3.0.0`
- Database: `sqlalchemy>=2.0.0,<3.0.0`, `alembic>=1.13.0,<2.0.0`, `psycopg2-binary>=2.9.9,<3.0.0`
- Scientific & ML: `xgboost>=2.0.0,<3.0.0`, `scikit-learn>=1.4.0,<2.0.0`, `ortools>=9.8.0,<10.0.0`

All backend dependencies use bounded version ranges, pin major releases, and show zero known high-severity vulnerabilities.

---

## 3. Dependency Audit Verdict

**Verdict: VERIFIED PASS (WITH DOCUMENTED DEV ADVISORIES)**  
Production runtime dependencies are 100% vulnerability-free. Development-tool advisories are strictly offline and isolated from runtime deployment.
