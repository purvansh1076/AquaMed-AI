# AquaMedi AI — Comprehensive Improvement Audit

**Document:** `AQUAMEDI_AI_COMPREHENSIVE_IMPROVEMENT_AUDIT.md`
**Type:** Recommendation-only engineering and research audit (no code changes)
**Repository:** `purvansh1076/AquaMed-AI`, branch `main`
**Audit date:** 2026-11-13
**Auditor stance:** Principal Software Architect, Senior ML Engineer, Applied AI Research Scientist, Agricultural Water Management Specialist, Mathematical Optimization Engineer, Multi-Agent Systems Researcher, Senior Full-Stack Engineer, DevSecOps Engineer, Academic Project Evaluator, Technical Product Designer

---

## 0. Scope and method

This audit is based on direct inspection of the repository source tree, not on README claims or prior audit reports alone. Evidence was drawn from:

- Backend: `backend/app/main.py`, `config.py`, `core/security.py`, `ml/*`, `allocation/*`, `negotiation/*`, `conflict/*`, `agents/*`, `explainability/*`, `data/*`, `services/*`, `api/*`, `models/*`, `schemas/*`.
- Frontend: `frontend/src/App.tsx`, pages, components, contexts, services, tests.
- Tests: `backend/tests/*`, `frontend/src/tests/*`.
- Configuration: `docker-compose.yml`, `backend/Dockerfile`, `render.yaml`, `backend/requirements.txt`, `frontend/package.json`.
- Prior audits in `docs/` were used only to cross-check claims, not as primary evidence.

Every recommendation below states whether the capability is already implemented, partially implemented, or absent, and names affected files/functions. Where evidence was insufficient, the item is marked **UNVERIFIED**.

---

## 1. Project maturity assessment

**Overall maturity: Academic demonstration ready (strong third-year B.Tech CSE prototype), not pilot/production ready.**

Verified strengths:

- A complete, runnable FastAPI + React 19 pipeline with deterministic synthetic-data grounding.
- 22 engineered ML features, XGBoost + Random Forest baseline, train/val/test split, encoders persisted separately.
- A non-destructive runtime calibration of the XGBoost `base_score` deserialization defect (`trainer.py:load_model`, `base_score` 0.5 → 214.17618).
- OR-Tools GLOP LP allocator with hard constraints, soft minimum relaxation, proportional fallback, and independent post-solve constraint verification.
- Multi-agent negotiation with BATNA utilities, Nash-bargaining-inspired log-surplus objective, mediator, and Merkle audit certificate.
- SHAP TreeExplainer, conformal prediction intervals, FAO-56 Penman-Monteith, conflict detection, RBAC, PBKDF2, JWT, rate limiting.
- 840 backend pytest + 82 frontend vitest passing (per prior verified run; not re-executed in this audit to avoid modifying state).

Primary maturity limiters:

- All data is synthetic; no real-world validation.
- LP optimizer contains a control-flow defect that can replace an optimal solution with a relaxed one (see Finding F-09).
- Conformal intervals are over-conservative because area scaling is applied post-hoc without normalized calibration (Finding F-03, already documented).
- Security defaults include a hardcoded JWT secret and expert password in `config.py` defaults, plus an in-memory rate limiter and a frontend dev-only auth fallback.
- No CI/CD, monitoring, model versioning, drift detection, or scenario persistence in the default (non-PostgreSQL) path.

---

## 2. Verified strengths (do not re-implement)

1. **FAO-56 Penman-Monteith** in `backend/app/data/fao56_penman_monteith.py:calculate_fao56_et0` with standard equations (pressure, psychrometric constant, saturation vapor pressure, slope, extraterrestrial radiation, net radiation, soil heat flux).
2. **Deterministic agronomic baseline** in `backend/app/ml/agronomic_baseline.py:DeterministicAgronomicBaseline.calculate_daily_demand` (ETc, USDA SCS effective rainfall, net/gross irrigation, volumetric conversion 1 mm × 1 ha = 10 m³).
3. **Feature engineering with train-only encoder fitting** in `backend/app/ml/feature_engineering.py:fit_encoders`, `apply_encoders`, `engineer_features`, `train_val_test_split`.
4. **XGBoost base-score calibration** in `backend/app/ml/trainer.py:load_model` (non-destructive, disk artifact unchanged).
5. **Conformal prediction** in `backend/app/ml/conformal_predictor.py:ConformalPredictor.predict_interval` (split conformal, 90% target).
6. **LP allocation** in `backend/app/allocation/lp_allocator.py:WaterAllocator.solve` with independent `verify_constraints`.
7. **Conflict detection** in `backend/app/conflict/detector.py:ConflictDetector.detect_all` (5 conflict types, Jain's fairness measured post-hoc).
8. **Multi-agent negotiation** in `backend/app/negotiation/negotiation_engine.py:NegotiationEngine.run` and `bargaining.py`.
9. **SHAP explainability** in `backend/app/ml/explainer.py` and `backend/app/explainability/*`.
10. **RBAC** in `backend/app/api/deps.py` (`require_expert`, `require_farmer_or_expert`) and `backend/app/api/auth.py`.
11. **PBKDF2 password hashing** in `backend/app/core/security.py:hash_password` / `verify_password` with `hmac.compare_digest`.
12. **Merkle audit certificate** in `backend/app/core/audit_crypto.py:MerkleAuditTree` (used in `negotiation_engine.py:_build_agreement`).

---

## 3. Verified findings (evidence-based)

| ID | Severity | Title | Evidence (file:function) | Status |
|---|---|---|---|---|
| F-09 | HIGH | LP `solve()` replaces an optimal solution with the relaxed fallback on every successful solve | `backend/app/allocation/lp_allocator.py:WaterAllocator.solve`, lines ~255–274 | **NEW (this audit)** |
| F-10 | MEDIUM | Conformal area scaling applied post-hoc without normalized calibration → 97.3% coverage, wider intervals | `backend/app/ml/conformal_predictor.py:ConformalPredictor.predict_interval`, line 62 | Confirms F-03 |
| F-11 | MEDIUM | XGBoost base-score calibration hardcodes the training target mean 214.17618 | `backend/app/ml/trainer.py:load_model`, lines 551–560 | **NEW** |
| F-12 | MEDIUM | Negotiation loop uses `initial_responses if round_num == 2 else current_responses`; `current_responses` is only defined after the first mediator call; relies on reassignment `initial_responses = current_responses` at end of iteration | `backend/app/negotiation/negotiation_engine.py:NegotiationEngine.run`, lines ~323–378 | **NEW** |
| F-13 | LOW | `_check_concession_progress` measures total water reduction, not farmer concession; may suppress or delay stagnation detection | `backend/app/negotiation/negotiation_engine.py:_check_concession_progress` | **NEW** |
| F-14 | MEDIUM | Default config ships a real-looking expert password and JWT secret in source defaults | `backend/app/config.py:Settings`, lines 44–49 | Confirms security audit |
| F-15 | MEDIUM | Rate limiter is process-local in-memory; not shared across workers/instances | `backend/app/core/security.py:LoginRateLimiter` | Confirms known limitations |
| F-16 | HIGH | Frontend dev/test-only auth fallback can fabricate an expert session when backend rejects credentials | `frontend/src/context/AuthContext.tsx` (per independent audit F-04) | Confirms F-04 |
| F-17 | LOW | Documentation claims 10 features / 3,601 samples; code has 22 features / 3,000 samples | `backend/app/ml/feature_engineering.py:ENGINEERED_FEATURE_COLS`; `data_generator.py:generate_dataset` | Confirms F-02 |
| F-18 | LOW | No model versioning, drift monitoring, or retraining trigger | `backend/app/ml/*` (absent) | **NEW** |
| F-19 | LOW | Synchronous SQLAlchemy engine; no async support | `backend/app/database.py` (per known limitations) | Confirms |
| F-20 | LOW | Frontend production bundle ~1.0 MB JS | `docs/...` build output | Confirms |
| F-21 | MEDIUM | No CI/CD pipeline in repository | `.github/` absent (verified via git ls-files) | **NEW** |
| F-22 | LOW | No scenario history persistence in the default (no-PostgreSQL) path | `backend/app/services/scenario_service.py` (UNVERIFIED in depth) | **NEW** |
| F-23 | LOW | Conformal predictor accepts `growth_stage` but only uses it for a critical-stage flag; it does not scale intervals by stage | `backend/app/ml/conformal_predictor.py:predict_interval` | **NEW** |

---

## 4. Architecture review

**Verified.** Decoupled FastAPI (Python 3.11/3.12) + React 19/Vite. SQLAlchemy 2 with PostgreSQL default URL but SQLite-compatible local path. Routers registered in `backend/app/main.py:app` (health, auth, scenario, agronomy, spatial, iot). CORS uses `settings.cors_origins_list` plus regex for Vercel.

Recommended (high value, low risk):

- **R-ARCH-01 — Fix LP fallback control flow (Priority A).** In `WaterAllocator.solve`, after `_solve_lp()` returns `lp_optimal`, the code unconditionally calls `_lp_relaxed_fallback()` because `allocation_method != "lp_relaxed"`. This discards the optimal allocation and reports a relaxed one. Fix: only invoke relaxed fallback when `solver_status` is not OPTIMAL/FEASIBLE, or when an explicit degraded mode is requested. Affected: `backend/app/allocation/lp_allocator.py:solve` (lines ~255–274). Test: `tests/test_lp_allocator.py`.
- **R-ARCH-02 — Make base-score calibration data-driven.** Replace hardcoded 214.17618 with the training target mean persisted in `evaluation_results.json` (or read from `dataset_summary`), and guard with a range check rather than `< 1.0`. Affected: `trainer.py:load_model`. Risk: if a future retrain changes the target mean, the hardcoded value silently re-introduces the defect.
- **R-ARCH-03 — Add API versioning and response envelope consistency.** Currently `/api/v1` only. Add a documented deprecation policy and a uniform error envelope. Affected: `main.py`, `schemas/api_models.py`.
- **R-ARCH-04 — Add a lightweight scenario-history store** (SQLite/PostgreSQL) so scenario runs are reproducible and comparable. Affected: `services/scenario_service.py`, `models/scenario.py`, alembic.

---

## 5. Machine learning audit

**Verified implementation:** `data_generator.py` (8 scenario types, 9 crops, 5 soils, FAO-56 Kc table), `feature_engineering.py` (22 features), `trainer.py` (RF 200 trees, XGBoost 300, early stopping 20), conformal predictor, SHAP explainer, candidate v1/v2/v3 shadow experiments.

Recommendations:

- **R-ML-01 — Normalize conformal calibration.** Implement locally weighted conformal prediction: compute non-conformity scores `R_i = |y_i - ŷ_i| / s(A_i)` on the validation set, take the 90% quantile `q_norm`, and at test time use margin `q_norm × s(A)`. This should restore ~90% coverage with ~40 m³ half-width instead of ~72 m³. Affected: `conformal_predictor.py`, `trainer.py` (calibration script). References: Lei et al. (2018); Angelopoulos & Bates (2021).
- **R-ML-02 — Scale conformal intervals by growth stage** in addition to area, since flowering-stage variance is larger. Affected: `conformal_predictor.py:predict_interval`.
- **R-ML-03 — Add group/stratified evaluation.** Report MAE/RMSE/R² by crop, season, and scenario type (already partially in `candidate_v3/error_breakdown_by_crop_season.json`). Add to the main evaluation report. Affected: `evaluation_reporter.py`, `trainer.py`.
- **R-ML-04 — Repeated cross-validation for stability.** Run the existing split with multiple seeds (e.g., 5) and report mean ± std of metrics. Affected: `trainer.py:run_training_pipeline`, `chronological_split.py`, `date_grouped_split.py`.
- **R-ML-05 — Feature ablation.** Use the existing `candidate_v3/test_ablations.json` pattern for the production model to justify the 22-feature set; drop redundant interaction features (`et0_x_kc` duplicates `etc_mm_per_day`) if ablation shows no loss. Affected: `feature_engineering.py`, `candidate_v3_experiments.py`.
- **R-ML-06 — Hyperparameter optimization (Optuna) — optional.** Only after R-ML-03/R-ML-04 establish a defensible baseline; do not add models (LightGBM/CatBoost) unless they beat XGBoost on stratified metrics. Affected: `trainer.py`.
- **R-ML-07 — Model versioning and drift monitoring.** Persist a model manifest (version, training seed, dataset hash, metrics, git commit) and a simple prediction-log sampler for drift (PSI on features). Affected: new module `ml/model_registry.py`; `predictor.py`.
- **R-ML-08 — Do not claim 10 features.** Update docs and any UI labels to state 10 raw agronomic inputs → 22 engineered features. Affected: docs, `frontend`.

---

## 6. Agronomic validity audit

**Verified.** FAO-56 PM implementation is mathematically standard. Kc table covers 9 crops × 5 stages. Soil WHC ranges follow Doorenbos & Pruitt. Effective rainfall uses USDA SCS. Application efficiency default 0.70 (gravity surface). Minimum requirement = 35–45% of demand.

Recommendations:

- **R-AGRO-01 — Regional calibration for Indian conditions.** Replace the synthetic ET₀ range (4–8 mm/day kharif) with NASA POWER / IMD-derived ET₀ for a chosen region (e.g., Ahmednagar, Maharashtra) using the existing `nasa_power_client.py` and `ingest_weather_data.py`. Affected: `data/nasa_power_client.py`, `data/region_config.py`, `data_generator.py`.
- **R-AGRO-02 — Growth-stage-varying Kc within a farmer record.** Currently one `kc_value` per farmer; FAO-56 practice updates Kc across phenology. Add a `growth_stage` → Kc lookup at inference (already in `KC_TABLE`) and a multi-stage schedule for advisory. Affected: `data_generator.py`, `predictor.py`, `agronomy_routes.py`.
- **R-AGRO-03 — Add soil moisture / irrigation scheduling.** Current model has no soil water balance or depletion; add a simple root-zone water balance (initial soil moisture, allowable depletion) to `agronomic_baseline.py`. Affected: `agronomic_baseline.py`, `crop_health_service.py`.
- **R-AGRO-04 — Crop coverage gap.** Current crops: wheat, rice, cotton, sugarcane, maize, soybean, groundnut, sunflower (8 crops). Requested crops include vegetables (tomato, onion, chilli) and potato. Add only with credible Kc sources (FAO-56 Table 12 or ICAR/IIHR). Affected: `data_generator.py:KC_TABLE`.
- **R-AGRO-05 — Distinguish net vs. gross in UI.** Document and display the 4-level hierarchy (ETc → NIR → GIR → canal-gate delivery) already clarified in the independent audit. Affected: frontend predictions page, docs.
- **R-AGRO-06 — Validate against public datasets.** Use ICAR/IMD/CoA crop statistics for plausibility checks; never present synthetic metrics as field-validated.

---

## 7. Optimization audit

**Verified.** Linear LP, GLOP, hard constraints H1–H3, soft S1, Jain's index post-hoc, proportional fallback, independent verification, conveyance efficiency (eta) support.

Recommendations:

- **R-OPT-01 — Fix fallback control flow (same as R-ARCH-01).** Highest priority.
- **R-OPT-02 — Multi-objective optimization via weighted scalarization before NSGA-II.** Expose `ObjectiveWeights` (urgency, crop_sensitivity, unmet_demand, minimum_shortfall) as user-tunable and add a fairness weight term; compute Pareto frontier over fairness vs. efficiency by sweeping weights. Affected: `lp_allocator.py:ObjectiveWeights`, `constraints.py:compute_jains_fairness_index`. Do not replace GLOP with NSGA-II unless evidence shows benefit.
- **R-OPT-03 — Sensitivity / shadow-price reporting.** GLOP dual values (shadow prices) for the supply constraint give the marginal value of additional water; expose in `AllocationResult`. Affected: `lp_allocator.py` (read `solver.dual_value`), `allocation_types.py`.
- **R-OPT-04 — Robust optimization for supply uncertainty.** Add a scenario-based variant: solve for a set of supply realizations and report worst-case allocation. Affected: `WaterAllocator`, `scenario_service.py`.
- **R-OPT-05 — Stochastic optimization — future scope.** Only after real weather distributions exist.
- **R-OPT-06 — Canal capacity as a hard constraint.** Currently canal capacity is in conflict detection but not in the LP (only total supply). Add per-window canal capacity constraints when irrigation windows are scheduled. Affected: `lp_allocator.py`, `constraints.py`.
- **R-OPT-07 — Relaxation transparency.** When `minimum_relaxed` occurs, the UI should show which farmers are below minimum and by how much (already in `minimum_shortfall_m3`). Affected: frontend allocation page.

---

## 8. Multi-agent / negotiation audit

**Verified.** Utility function (water satisfaction, timing, urgency protection, min-req satisfaction, stress penalty), BATNA, mediator, Nash-bargaining-inspired log-surplus, termination conditions, Merkle certificate.

Recommendations:

- **R-MA-01 — Fix response staleness in negotiation loop.** Make `current_responses` initialization explicit (e.g., `current_responses = initial_responses` before the loop) and pass the correct previous responses to `mediator.mediate`. Affected: `negotiation_engine.py:run`, lines ~299–328.
- **R-MA-02 — Convergence metrics.** Record per-round Nash objective, fairness, number of acceptances, and concession amount; expose a convergence flag (e.g., objective change < 1e-4 for 2 rounds). Affected: `negotiation_types.py:NegotiationRound`, `negotiation_engine.py`.
- **R-MA-03 — Pareto-efficiency verification.** After termination, check whether any farmer can be made better off without making another worse off given the final allocation and constraints; report a boolean + witness. Affected: new helper in `bargaining.py`.
- **R-MA-04 — Agent-level explanations.** For each farmer, explain why they accepted/rejected (utility vs. BATNA, shortfall) in plain language. Affected: `negotiation_explainer.py`, frontend negotiation page.
- **R-MA-05 — Counterfactual negotiation analysis.** Re-run with one farmer removed or with altered BATNA to show sensitivity. Affected: `NegotiationEngine` (new method).
- **R-MA-06 — Fix concession-progress metric.** Base it on actual farmer utility concessions or allocation changes relative to each farmer's request, not aggregate water reduction. Affected: `_check_concession_progress`.
- **R-MA-07 — Keep the "Nash-bargaining-inspired" framing.** Do not claim axiomatic NBS/Pareto proofs; the code already disclaims this. Keep docs aligned (already fixed in independent audit).

---

## 9. Explainable AI and trust

**Verified.** SHAP TreeExplainer, local + global importance, allocation explainer, negotiation explainer, prediction explainer, explanation service and types.

Recommendations:

- **R-XAI-01 — Counterfactual explanations.** "What single feature change would flip this allocation/prediction?" Use SHAP or a simple grid search over top features. Affected: `prediction_explainer.py`, `allocation_explainer.py`.
- **R-XAI-02 — What-if analysis UI.** Interactive sliders for ET₀, Kc, area, rainfall → re-predict and re-allocate; show delta. Affected: frontend `CustomFarmPredictor.tsx`, predictions page.
- **R-XAI-03 — Decision provenance and audit trail.** Persist scenario inputs, model version, allocation result, negotiation rounds, and Merkle certificate in a tamper-evident log. Affected: `core/audit_crypto.py`, `models/*`, `services/scenario_service.py`.
- **R-XAI-04 — Farmer-friendly vs. expert-level explanations.** Already partially via i18n; add a toggle and ensure SHAP feature names are translated. Affected: `explainability/explanation_service.py`, frontend.
- **R-XAI-05 — Explain rejected allocations.** When a farmer is below minimum, explain which constraint bound (supply, canal, max). Affected: `allocation_explainer.py`.

---

## 10. Real-world data and integration

**Verified.** `nasa_power_client.py`, `ingest_weather_data.py`, `region_config.py`, `remote_sensing.py`, `weather_service.py`, `crop_health_service.py`, `iot_service.py`, `iot_routes.py`, `spatial_routes.py`. These appear to exist; depth of implementation is **UNVERIFIED** in this audit (not line-inspected). Treat as candidate integration points.

Recommendations:

- **R-DATA-01 — Weather-aware demand prediction.** Feed NASA POWER / IMD-derived ET₀ and rainfall into the ML features instead of synthetic ranges. Affected: `nasa_power_client.py`, `data_generator.py`, `feature_engineering.py`.
- **R-DATA-02 — Backtesting.** Compare allocator decisions against historical (public) water distribution records where available. Affected: new evaluation script.
- **R-DATA-03 — Label data provenance clearly.** Keep the synthetic/public/simulated/field-measured distinction explicit in every output (already done in several places). Do not present synthetic metrics as validated.

---

## 11. Product and frontend audit

**Verified (structure).** React 19, TypeScript, Vite, React Router, Recharts, Lucide. Pages: overview, predictions, allocation, conflicts, negotiation, explainability, reports, scenario, crop health, irrigation advisory, farmer portal, farmer view, welcome, expert login, agreement, debug. Contexts: Auth, Scenario, ViewMode. i18n: en/hi/gu/mr.

Recommendations:

- **R-UX-01 — Fix dev auth fallback** (same as F-16). Remove client-side mock session fabrication.
- **R-UX-02 — Interactive scenario comparison.** Side-by-side comparison of two scenario runs (allocation + fairness + negotiation outcome). Affected: frontend pages + ScenarioContext.
- **R-UX-03 — Before/after allocation comparison.** Show LP allocation vs. negotiated allocation vs. proportional baseline. Affected: allocation page.
- **R-UX-04 — Scenario history and re-run.** List prior runs with inputs; allow re-run with one parameter changed. Affected: backend scenario persistence (R-ARCH-04) + frontend.
- **R-UX-05 — Export PDF/CSV/Excel.** Reports page currently renders; add downloadable exports. Affected: `ReportsPage.tsx`, backend report endpoint (UNVERIFIED if exists).
- **R-UX-06 — What-if simulation.** Affected: `CustomFarmPredictor.tsx`.
- **R-UX-07 — Mobile usability.** Verify responsive breakpoints and touch targets; add empty/loading/error states audit. Affected: `layouts/*`, pages.
- **R-UX-08 — Accessibility.** Add keyboard navigation, ARIA labels, focus management, contrast checks. Affected: all components.
- **R-UX-09 — Bundle size.** Code-split routes and lazy-load Recharts/SHAP views; target < 500 kB initial. Affected: `App.tsx`, vite config.
- **R-UX-10 — Preserve branding.** Keep AquaMedi AI design system; do not redesign.

---

## 12. Backend, database, and software architecture

Recommendations:

- **R-BE-01 — Async migration (optional, later).** Move SQLAlchemy to asyncpg for concurrent scenario execution. Affected: `database.py`, all services. Complexity high; justify by load testing first.
- **R-BE-02 — Dependency injection and service boundaries.** `scenario_service.py` likely orchestrates everything; split into prediction, conflict, allocation, negotiation services with interfaces. Affected: `services/scenario_service.py`.
- **R-BE-03 — Remove dead code and duplicate logic.** Candidate v1/v2/v3 shadow adapters add complexity; gate behind config (already `enable_candidate_v3_shadow=False`). Consider archiving experiment code under `experiments/`.
- **R-BE-04 — Structured logging + correlation ID.** Already has correlation ID middleware; add request/response timing and JSON logs for production. Affected: `main.py`.
- **R-BE-05 — Health checks.** `/health` and `/api/v1/health` exist; add readiness for model artifacts and DB. Affected: `api/health.py`, `main.py`.
- **R-BE-06 — N+1 / query audit.** UNVERIFIED; run SQLAlchemy echo in dev and inspect. Affected: `models/*`, services.

---

## 13. Security and reliability

Recommendations:

- **R-SEC-01 — Remove default secrets.** Make `jwt_secret_key` and `expert_default_password` required (no defaults) in production mode; fail startup if unset. Affected: `config.py`.
- **R-SEC-02 — Remove dev auth fallback** (F-16).
- **R-SEC-03 — Distributed rate limiting.** Move `LoginRateLimiter` to Redis or DB-backed for multi-worker deployments; or document single-worker constraint. Affected: `core/security.py`.
- **R-SEC-04 — Secret scanning in CI.** Add gitleaks/trufflehog to CI; ensure `.env` not committed (already gitignored, but verify). Affected: new `.github/workflows`.
- **R-SEC-05 — Dependency vulnerability scanning.** pip-audit / npm audit in CI. Affected: CI.
- **R-SEC-06 — Error information disclosure.** Ensure 500 responses do not leak stack traces in production (`app_debug=False`). Affected: `main.py`, `config.py`.
- **R-SEC-07 — File upload security.** UNVERIFIED if any upload endpoints exist; inspect `iot_routes.py` / `spatial_routes.py` (not line-inspected).

---

## 14. Performance and deployment

Recommendations:

- **R-PERF-01 — Add CI/CD (GitHub Actions).** Lint, typecheck, pytest, vitest, build, docker build. Affected: new `.github/workflows/ci.yml`.
- **R-PERF-02 — Docker hardening.** Multi-stage build, non-root user, healthcheck, pinned base image. Affected: `backend/Dockerfile`, `docker-compose.yml`.
- **R-PERF-03 — Performance benchmarking.** Measure API latency, ML inference, LP solve time (already logged in ms), negotiation time; add a benchmark script. Affected: `scripts/*`.
- **R-PERF-04 — Concurrency tests.** Run scenario endpoint under concurrent load. Affected: tests.
- **R-PERF-05 — Monitoring.** Structured logs + basic metrics (Prometheus/OpenTelemetry) — optional, later.

---

## 15. Research novelty and academic value

**What is genuinely original in this project:**

- The end-to-end integration of FAO-56 → XGBoost → conformal intervals → Farmer Digital Twin agents → conflict detection → OR-Tools LP → Nash-bargaining-inspired negotiation → SHAP → multilingual government UI is an unusually complete academic prototype.
- The non-destructive XGBoost `base_score` diagnosis and runtime calibration is a real, defensible engineering contribution (F-01 in prior audit).
- The conformal prediction module with area scaling is a reasonable (if over-conservative) uncertainty quantification layer.
- The Merkle audit certificate on negotiated agreements is a nice trust feature.

**What is implementation of existing research:** FAO-56 PM, USDA SCS effective rainfall, Jain's fairness index, split conformal prediction, SHAP, Nash bargaining (inspired).

**What is integration of existing tools:** XGBoost, scikit-learn, OR-Tools, FastAPI, React.

**Strongest research potential:** Fairness-aware water allocation with explainable multi-agent negotiation and uncertainty-aware optimization. The current LP optimizes utility; fairness is measured post-hoc. A defensible contribution would be to (a) add a fairness term or constraint to the LP, (b) verify Pareto efficiency, and (c) show experimentally that the negotiated outcome improves fairness and farmer acceptance vs. the initial LP.

**Suggested experiments (realistic for B.Tech):**

1. Compare initial LP vs. negotiated allocation on Jain's fairness index and number of accepting farmers across the 8 scenario types (N=8 scenarios × 5 seeds).
2. Ablation of the 22 features; report top-10 by SHAP and by permutation importance.
3. Conformal coverage before/after normalized calibration (should move 97.3% → ~90% with narrower intervals).
4. Sensitivity of LP outcome to `ObjectiveWeights` (Pareto frontier fairness vs. efficiency).

---

## 16. Benchmark against professional systems (conceptual)

Compared conceptually with agricultural decision-support systems, smart irrigation platforms, explainable AI decision-support systems, multi-agent negotiation research, and water allocation optimization research:

Gaps vs. professional systems:

- No real telemetry / IoT ingestion (only simulated routes).
- No hydraulic routing (Saint-Venant) for canal delivery lag.
- No multi-crop / rotation support.
- No operational SCADA integration.
- No regulatory/audit compliance (e.g., water rights, entitlements).

Opportunities (realistic):

- Integrate NASA POWER ET₀ (already scaffolded).
- Add a simple canal conveyance model (distance-based loss) — already partially in `conveyance_efficiencies`.
- Publish the synthetic dataset and evaluation protocol as a reproducible artifact.

Credible references (do not fabricate):

- Allen, R.G. et al. (1998). FAO Irrigation and Drainage Paper No. 56.
- Nash, J.F. (1950). The Bargaining Problem. Econometrica 18(2): 155–162.
- Jain, R. et al. (1984). A Quantitative Measure of Fairness. (Jain's fairness index.)
- Vovk, V. et al. (2005). Algorithmic Learning in a Random World (conformal prediction).
- Angelopoulos, A.N. & Bates, S. (2021). A Gentle Introduction to Conformal Prediction.
- Lei, J. et al. (2018). Distribution-Free Predictive Inference for Regression (normalized conformal).
- OR-Tools documentation (Google).

---

## 17. Top 10 recommended improvements (ranked)

1. **Fix LP fallback control flow** (R-ARCH-01 / R-OPT-01) — correctness.
2. **Normalize conformal calibration** (R-ML-01) — scientific accuracy.
3. **Remove frontend dev auth fallback + default secrets** (F-16, R-SEC-01/02) — security.
4. **Make XGBoost base-score calibration data-driven** (R-ARCH-02) — reliability.
5. **Add CI/CD + dependency scanning** (R-PERF-01, R-SEC-04/05) — engineering.
6. **Fix negotiation response staleness** (R-MA-01) — correctness.
7. **Stratified/grouped ML evaluation + repeated CV** (R-ML-03/04) — scientific credibility.
8. **Regional ET₀ from NASA POWER** (R-AGRO-01, R-DATA-01) — realism for Indian agriculture.
9. **Feature ablation + drop redundant interaction** (R-ML-05) — model quality.
10. **Scenario history + PDF/CSV export** (R-ARCH-04, R-UX-05) — product value.

---

## 18. Five improvements that should NOT be implemented

1. **Replacing GLOP with NSGA-II or MILP** — no evidence of benefit; LP solves in <15 ms and constraints are linear. Keep GLOP.
2. **Adding LightGBM/CatBoost "for model count"** — only if they beat XGBoost on stratified metrics; complexity without demonstrated value.
3. **Adding an LLM agent** — the project's contribution is mathematical multi-agent negotiation; an LLM would add cost/opacity without technical value.
4. **Complex cloud infrastructure (Kubernetes, microservices)** — unjustified for an academic prototype; Docker Compose is sufficient.
5. **Full async migration before load testing** — high risk/effort; measure first.

---

## 19. Final assessment

AquaMedi AI is a strong, unusually complete third-year B.Tech CSE academic prototype with defensible engineering (XGBoost calibration, OR-Tools LP, conformal prediction, SHAP, RBAC). Its main weaknesses are (a) a real LP control-flow defect, (b) over-conservative conformal intervals, (c) security defaults, and (d) synthetic-data limitations that must be stated honestly. Fixing items 1–4 in section 17 would materially raise both technical and academic quality without changing the project's scope.
