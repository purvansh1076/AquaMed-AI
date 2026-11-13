# AquaMedi AI — Prioritized Implementation Roadmap

**Document:** `AQUAMEDI_AI_PRIORITIZED_IMPLEMENTATION_ROADMAP.md`
**Type:** Recommendation-only

---

## 1. Scoring formula

For each recommendation compute:

`PriorityScore = 0.30·TechnicalImpact + 0.25·AcademicValue + 0.20·PracticalUsefulness + 0.15·ImplementationFeasibility + 0.10·ResearchPotential`

All sub-scores are 1–10. Higher is better. (Weights chosen to favor correctness/academic value for a B.Tech project; adjustable.)

Grouping:

- **Priority A — Essential:** correctness, validation, reliability, security.
- **Priority B — High-Value:** substantial technical/academic improvement.
- **Priority C — Advanced Research:** sophisticated ML/optimization/multi-agent.
- **Priority D — Product/UX:** interface/usability.
- **Priority E — Long-Term Future:** valuable but not needed now.

---

## 2. Ranked recommendations (top 20)

| Rank | ID | Name | Status | Tech | Acad | Pract | Feas | Res | Score | Group |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | R-ARCH-01 | Fix LP fallback control flow | Implemented but buggy | 10 | 8 | 9 | 9 | 6 | 8.95 | A |
| 2 | R-ML-01 | Normalize conformal calibration | Partial | 9 | 9 | 7 | 8 | 8 | 8.50 | A/B |
| 3 | R-SEC-01/02 | Remove default secrets + dev auth fallback | Implemented but unsafe defaults | 9 | 6 | 8 | 9 | 4 | 7.80 | A |
| 4 | R-ARCH-02 | Data-driven XGBoost base-score calibration | Implemented (hardcoded) | 8 | 7 | 8 | 9 | 5 | 7.75 | A |
| 5 | R-MA-01 | Fix negotiation response staleness | Implemented but fragile | 8 | 7 | 7 | 8 | 6 | 7.55 | A/B |
| 6 | R-ML-03/04 | Stratified evaluation + repeated CV | Partial | 7 | 9 | 6 | 8 | 7 | 7.50 | B |
| 7 | R-PERF-01 | CI/CD + dependency scanning | Absent | 7 | 6 | 8 | 7 | 4 | 6.95 | B |
| 8 | R-AGRO-01 | Regional ET₀ from NASA POWER | Scaffolded | 7 | 8 | 7 | 6 | 7 | 7.10 | B/C |
| 9 | R-ML-05 | Feature ablation | Partial (candidate v3) | 6 | 8 | 5 | 8 | 7 | 6.90 | B |
| 10 | R-UX-05 | Export PDF/CSV/Excel | Absent | 5 | 5 | 8 | 7 | 3 | 6.05 | D |
| 11 | R-OPT-02 | Fairness term / Pareto frontier | Absent | 7 | 8 | 6 | 6 | 8 | 7.00 | C |
| 12 | R-OPT-03 | Shadow prices | Absent | 6 | 7 | 5 | 7 | 7 | 6.35 | C |
| 13 | R-MA-02 | Convergence metrics | Absent | 6 | 7 | 6 | 8 | 7 | 6.70 | B/C |
| 14 | R-MA-03 | Pareto-efficiency verification | Absent | 6 | 8 | 5 | 7 | 8 | 6.75 | C |
| 15 | R-XAI-01 | Counterfactual explanations | Absent | 6 | 8 | 6 | 6 | 8 | 6.60 | C |
| 16 | R-UX-02/03 | Scenario comparison + before/after | Absent | 5 | 6 | 8 | 6 | 4 | 6.00 | D |
| 17 | R-ARCH-04 | Scenario history persistence | Absent | 6 | 6 | 7 | 6 | 4 | 6.05 | B/D |
| 18 | R-AGRO-02 | Growth-stage-varying Kc | Absent | 7 | 7 | 6 | 6 | 6 | 6.50 | B/C |
| 19 | R-ML-07 | Model versioning + manifest | Absent | 6 | 7 | 5 | 7 | 6 | 6.30 | B |
| 20 | R-ML-11 | Drift monitoring | Absent | 6 | 6 | 5 | 6 | 7 | 6.00 | C/E |

---

## 3. Grouped recommendations

### Priority A — Essential

- R-ARCH-01 Fix LP fallback control flow.
- R-ML-01 Normalize conformal calibration (coverage correctness).
- R-SEC-01/02 Remove default secrets + dev auth fallback.
- R-ARCH-02 Data-driven base-score calibration.

### Priority B — High-Value

- R-MA-01 Fix negotiation response staleness.
- R-ML-03/04 Stratified evaluation + repeated CV.
- R-PERF-01 CI/CD + dependency scanning.
- R-ML-05 Feature ablation.
- R-MA-02 Convergence metrics.
- R-MA-07 Negotiation history visualization.
- R-MA-08 Fairness before/after comparison.
- R-AGRO-01 Regional ET₀ (NASA POWER).
- R-ARCH-04 Scenario history persistence.
- R-ML-07 Model versioning.
- R-UX-05 Export PDF/CSV/Excel.

### Priority C — Advanced Research

- R-OPT-02 Fairness term / Pareto frontier.
- R-OPT-03 Shadow prices.
- R-OPT-04 Robust optimization.
- R-MA-03 Pareto-efficiency verification.
- R-MA-05 Counterfactual negotiation.
- R-XAI-01 Counterfactual explanations.
- R-AGRO-02 Growth-stage-varying Kc.
- R-ML-11 Drift monitoring.
- R-XAI-02 What-if analysis UI.

### Priority D — Product/UX

- R-UX-02/03 Scenario comparison + before/after.
- R-UX-04 Scenario history UI.
- R-UX-06 What-if simulation.
- R-UX-07 Mobile usability.
- R-UX-08 Accessibility.
- R-UX-09 Bundle size.
- R-UX-10 Preserve branding.

### Priority E — Long-Term Future

- R-BE-04 Async migration.
- R-OPT-06 Stochastic optimization.
- R-AGRO-04 Vegetable crop expansion (with credible Kc sources).
- R-DATA-02 Backtesting against public records.
- R-DEP-05 Monitoring.
- Saint-Venant hydraulic routing.

---

## 4. Roadmap 1 — Quick improvements (1–2 weeks)

Sequence:
1. Fix LP fallback control flow (R-ARCH-01) — 1 day.
2. Remove dev auth fallback + default secrets (R-SEC-01/02) — 1–2 days.
3. Data-driven base-score calibration (R-ARCH-02) — 1 day.
4. Fix negotiation response staleness (R-MA-01) — 1 day.
5. Conformal normalization (R-ML-01) — 2–3 days.
6. CI/CD skeleton (R-PERF-01) — 2 days.
7. Docs: align feature count (10 → 22) and API routes — 1 day.

Files: `lp_allocator.py`, `config.py`, `AuthContext.tsx`, `trainer.py`, `conformal_predictor.py`, `.github/workflows/ci.yml`, docs.
Tests: `test_lp_allocator.py`, `test_ml_pipeline.py`, `test_phase10_independent_validation.py`, frontend `WelcomeAndAuth.test.tsx`.
Expected outcome: correct optimal allocations reported; 90% conformal coverage with narrower intervals; no fabricated auth sessions; CI green.

## 5. Roadmap 2 — Strong academic upgrade (3–6 weeks)

Sequence:
1. Stratified/grouped ML evaluation + repeated CV (R-ML-03/04) — 1 week.
2. Feature ablation (R-ML-05) — 3–4 days.
3. Scenario history persistence (R-ARCH-04) + export (R-UX-05) — 1 week.
4. Negotiation convergence metrics + history viz (R-MA-02, R-MA-07, R-MA-08) — 1 week.
5. Regional ET₀ from NASA POWER (R-AGRO-01) — 1–2 weeks.
6. Model versioning manifest (R-ML-07) — 3 days.
7. Pareto-efficiency verification (R-MA-03) + shadow prices (R-OPT-03) — 1 week.

Files: `evaluation_reporter.py`, `trainer.py`, `feature_engineering.py`, `scenario_service.py`, `negotiation_engine.py`, `negotiation_explainer.py`, `nasa_power_client.py`, `region_config.py`, `lp_allocator.py`.
Tests: extend `test_phase10/11/12`, add convergence tests.
Expected outcome: defensible evaluation report, scenario history, negotiation convergence evidence, region-aware ET₀, model manifest.

## 6. Roadmap 3 — Advanced research prototype (2–3 months)

Sequence:
1. Fairness term / Pareto frontier in LP (R-OPT-02) — 2 weeks.
2. Robust optimization over supply (R-OPT-04) — 2 weeks.
3. Counterfactual explanations (R-XAI-01) + what-if UI (R-XAI-02) — 2 weeks.
4. Counterfactual negotiation (R-MA-05) — 1 week.
5. Growth-stage-varying Kc + soil water balance (R-AGRO-02) — 2 weeks.
6. Drift monitoring (R-ML-11) — 1 week.
7. Vegetable crop expansion with credible Kc sources (R-AGRO-04) — 2 weeks.
8. Backtesting against public records (R-DATA-02) — 2 weeks.

Files: `lp_allocator.py`, `WaterAllocator`, `prediction_explainer.py`, `allocation_explainer.py`, `agronomic_baseline.py`, `data_generator.py`, new modules.
Tests: new experiment scripts under `scripts/`.
Expected outcome: research-grade prototype with fairness-aware allocation, robustness, counterfactuals, and a reproducible evaluation protocol suitable for a paper.

---

## 7. Testing requirements summary

- Backend: pytest; add tests for LP fallback correctness, conformal coverage, negotiation convergence, scenario persistence.
- Frontend: Vitest; add tests for export, scenario comparison, what-if.
- CI: run both suites + TypeScript build + Docker build.

## 8. Risks

- Conformal normalization may reduce interval width; verify coverage on held-out test set before claiming 90%.
- Base-score calibration change must preserve the disk artifact hash (non-destructive).
- Security changes may break dev workflows; gate behind `app_env`.
- Synthetic-data limitations remain; never present as field-validated.

---

## 9. Final note

Implement fewer, high-impact changes rather than many superficial features. Priority A items (especially R-ARCH-01) are correctness defects and should be addressed first. Do not implement any recommendation until reviewed and approved.
