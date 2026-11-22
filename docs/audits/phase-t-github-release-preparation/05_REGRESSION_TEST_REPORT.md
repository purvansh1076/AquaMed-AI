# Phase T — Final Regression Test and Build Report

**Execution Date:** 2026-11-15  
**Platform:** Windows 11 (Python 3.12.10, Node.js 24.21.0, npm 11.19.0)  
**Branch:** `feature/aquamedi-ai-product-transformation`  
**Commit Inspected:** `75e60a0` (Phase S Project Closure Audit)  

---

## 1. Test Execution Matrix and Baseline Comparison

| Test Suite / Build Target | Phase S Baseline | Phase T Verified Result | Delta / Regressions | Status |
|---|---|---|---|---|
| **Backend Test Suite (Pytest)** | 862 passed | **862 passed, 0 failed, 5 warnings** | None (0 regressions) | **MATCH / PASS** |
| **Frontend Test Suite (Vitest)** | 95 passed | **95 passed, 0 failed** (12 files) | None (0 regressions) | **MATCH / PASS** |
| **Frontend Production Build** | Success | **Success** (`tsc -b && vite build`) | None (0 errors) | **MATCH / PASS** |
| **Model Checksums (SHA-256)** | Verified | **Identical across 4 artifacts** | None (0 drift) | **MATCH / PASS** |
| **Database Migrations** | Linear | **Linear (0001 -> 0002)** | None (0 conflicts) | **MATCH / PASS** |

---

## 2. Backend Regression Suite Breakdown

- **Framework:** Pytest 8.4.2 (asyncio 0.24.0, anyio 4.15.1)
- **Invocation:** `python -m pytest -q`
- **Duration:** 79.62 seconds
- **Collected Test Items:** 862
- **Results:** 862 passed, 5 non-fatal library warnings, 0 failures.

### Module Coverage Breakdown
1. `test_agent_messages.py`: 3 tests (Pydantic schema validation, message types).
2. `test_agronomy.py`: 5 tests (Crop coefficients, water limits, XGBoost unpickling calibration).
3. `test_api.py`: 74 tests (FastAPI route contracts, query parsing, payload validation).
4. `test_conflict_detector.py`: 88 tests (5 conflict classifications, boundary conditions).
5. `test_data_generator.py`: 60 tests (FAO-56 parameter ranges, distribution shapes).
6. `test_data_ingestion.py`: 14 tests (CSV loaders, schema checks).
7. `test_et0_bounds.py`: 2 tests (Physical upper/lower bounds of ET0).
8. `test_et0_independent.py`: 2 tests (Independent analytical cross-check of Penman-Monteith).
9. `test_explainability.py`: 113 tests (TreeSHAP force values, reason code translations).
10. `test_fairness_metrics.py`: 5 tests (Jain's index, disparity, deficit).
11. `test_fao56_reference.py`: 3 tests (Standard FAO-56 table replication).
12. `test_farmer_agents.py`: 96 tests (Utility curves, urgency, stress multipliers).
13. `test_group_conformal.py` & `test_group_conformal_remediation.py`: 5 tests (Finite-sample correction, subgroup fallbacks).
14. `test_iot.py`: 3 tests (Synthetic sensor ingestion mock).
15. `test_lp_allocator.py`: 87 tests (OR-Tools GLOP solver, capacity limits, relaxed and proportional fallbacks).
16. `test_maxmin_fairness.py`: 1 test (Max-Min LP formulation).
17. `test_ml_pipeline.py`: 42 tests (Inference pipelines, feature order, preprocessor transforms).
18. `test_model_path_resolution.py`: 9 tests (Filesystem path resolution across environments).
19. `test_negotiation.py`: 121 tests (Nash bargaining solver, concession dynamics, BATNA constraints).
20. `test_phase10_independent_validation.py` to `test_phase12_smoke_test.py`: 34 tests (System smoke tests, component integration).
21. `test_phase3_ml_design.py` & `test_phase4_shadow_validation.py`: 27 tests (Historical shadow tests).
22. `test_phase7_candidate_pipeline.py` to `test_phase9_error_analysis.py`: 31 tests (Candidate model architectures).
23. `test_security_rbac.py`: 10 tests (Role gating, guest token restriction, brute force limiter).
24. `test_shadow_mode.py`: 1 test (Model evaluation routing).

### Warnings Audit
The 5 recorded warnings are external library deprecations and serialization notifications that do not impact runtime correctness:
- 1 Starlette deprecation warning (`anyio.abc.BlockingPortal`).
- 3 Python internal Swig object module namespace warnings (`builtin type SwigPyPacked`).
- 1 XGBoost model serialization advisory noting historical pickle format versus JSON booster format.

---

## 3. Frontend Regression Suite Breakdown

- **Framework:** Vitest 5.0.1 (jsdom environment)
- **Invocation:** `npm test -- --run`
- **Duration:** 25.64 seconds
- **Test Files:** 12 passed (100%)
- **Tests:** 95 passed (100%), 0 failed.

### Component & Flow Coverage
- `api.test.ts`: 5 tests (Axios mock clients, error mapping).
- `AgronomicComparisonCard.test.tsx`: 4 tests (Rendering ML vs theoretical baselines).
- `Components.test.tsx`: 9 tests (UI cards, badges, language toggles).
- `SidebarAndLanguageUX.test.tsx`: 10 tests (Collapsible rail mode, keyboard accessibility).
- `ViewMode.test.tsx`: 12 tests (Farmer View vs Expert View presentation separation).
- `ScenarioPages.test.tsx`: 8 tests (Route rendering and parameter form initialization).
- `OverviewAuthenticity.test.tsx`: 3 tests (Clean empty state enforcement when scenario is unloaded).
- `CustomFarmPredictor.test.tsx`: 10 tests (Single-farmer form submission and result cards).
- `FarmerPortal.test.tsx`: 6 tests (Guest flow, input validation, advisory cards).
- `App.test.tsx`: 5 tests (Main layout routing, top navigation).
- `WelcomeAndAuth.test.tsx`: 9 tests (Government branding, role selection, expert authentication, rejection of invalid credentials, zero offline session fabrication).

---

## 4. Production Build Verification

- **Command:** `npm run build` (`tsc -b && vite build`)
- **Compilation:** TypeScript compiler completed with 0 diagnostic errors.
- **Bundling Output:**
  - `dist/index.html`: 0.76 kB (gzip: 0.46 kB)
  - `dist/assets/index-Co93dcIi.css`: 50.78 kB (gzip: 9.27 kB)
  - `dist/assets/index-C-0od2A1.js`: 1,020.92 kB (gzip: 272.45 kB)
- **Build Duration:** 1.58 seconds.

---

## 5. Regression Verdict

**Verdict: VERIFIED PASS**  
100% test pass rate across backend (862/862) and frontend (95/95). Production build verified. Complete equivalence with Phase S baseline.
