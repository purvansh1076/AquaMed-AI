# AquaMediAI — Project Overview

## Abstract

AquaMediAI is an Explainable AI-Based Multi-Agent Water-Sharing Dispute Mediation System for Farmers. The system combines predictive modeling, constrained optimization, and multi-agent negotiation to support fair and efficient water allocation in agricultural irrigation scenarios. All data and computations are synthetically generated using agronomically grounded formulas (FAO-56 single-crop-coefficient method), and the system is designed as a academic prototype for third-year B.Tech Computer Science and Engineering evaluation.

## Problem Statement

Agricultural water sharing is a persistent conflict domain. Farmers competing for limited water resources often face irreducible shortages, especially during droughts or canal reductions. Traditional allocation methods (pro-rata, priority-based) lack transparency and do not account for individual farmer utilities, crop sensitivities, or urgency levels. There is no automated mechanism for negotiation or conflict resolution, leading to prolonged disputes and inefficient water use.

## Project Objectives

1. **Predict water demand** using ML models (RandomForest, XGBoost) grounded in FAO-56 agronomy.
2. **Detect irrigation conflicts** between farmers sharing a water source.
3. **Allocate available water** using a constrained linear programming (GLOP) optimizer with hard and soft constraints.
4. **Mediate negotiated settlements** between farmers using a Nash-bargaining-inspired objective with BATNA protection.
5. **Provide explainability** via SHAP feature-importance diagrams.
6. **Expose results through a FastAPI backend and a React frontend** with multilingual support (English, Hindi, Gujarati).

## Scope

### Included Features

- **ML Pipeline**: Synthetic data generation (3000 samples, 8 scenario types), training/evaluation/persistence of RandomForest and XGBoost models, SHAP explainability, preprocessing without leakage.
- **Conflict Detection**: 5 conflict types (RESOURCE_SHORTAGE, IRRIGATION_WINDOW_OVERLAP, CANAL_CAPACITY_CONFLICT, MINIMUM_REQUIREMENT_CONFLICT, HIGH_CROP_STRESS) with severity mapping.
- **GLOP Allocation**: Hard constraints H1 (x_i >= 0), H2 (x_i <= max_water_i), H3 (sum x_i <= available_water); soft constraint S1 (minimum requirements with penalty); fallback chain (lp_optimal -> lp_relaxed -> proportional -> empty).
- **Negotiation Engine**: Log Nash objective Σlog(max(surplus_i, 1e-6)); BATNA protection (utility < batna_utility -> REJECT); response thresholds (ACCEPT >= 0.65, REQUEST_CHANGE in [0.35, 0.65), REJECT < 0.35); stagnation detection (2 consecutive rounds without improvement -> NO_FEASIBLE_IMPROVEMENT); concession logic with flexibility_factor and urgency_factor; min_nash_improvement (1e-4) and concession_progress_threshold (0.1) config parameters.
- **Farmer Agents**: Utility function U_i = norm(w1*S_w + w2*S_t + w3*S_u + w4*S_m - w5*S_p·cs_i); BATNA fallback; flexibility/urgency scores.
- **Multilingual Interface**: English, Hindi, Gujarati translation keys.
- **API**: 15 endpoint groups (health, root, scenarios, predictions, conflicts, allocations, negotiations, validation, determinism, farmer data, error handling, JSON serialization, explanations, scenario types).

### Explicitly Excluded

- Real farmer records or real-world water usage data
- LLM or AI generative features
- Blockchain, IoT sensor integration, or voice interfaces
- Real-time weather service integration (weather parameters are synthetically generated)
- Public deployment or paid services

## Existing System Architecture

### Technology Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.x, OR-Tools GLOP | pydantic-settings for configuration; psycopg2-binary for PostgreSQL |
| **ML** | scikit-learn 1.5, XGBoost 2.0, joblib, SHAP 0.45 | RandomForestRegressor, XGBRegressor; SHAP explainability |
| **Frontend** | React, TypeScript, Vite | 53 vitest tests; English/Hindi/Gujarati i18n |
| **Database** | PostgreSQL (declared dependency) | SQLAlchemy engine; psycopg2-binary driver |
| **ML Data Generator** | Custom synthetic generator | FAO-56 formula; 8 scenario types; ±15% noise; seed=42 |

### Directory Structure (High-Level)

```
aquamedi-ai/
├── backend/          # FastAPI application
│   ├── app/          # Source code
│   │   ├── ml/       # ML pipeline (trainer, predictor, feature_engineering, data_generator)
│   │   ├── allocation/ # GLOP allocator, constraints, types
│   │   ├── negotiation/ # Negotiation engine, mediator, bargaining, types
│   │   ├── agents/   # FarmerAgent, DigitalTwin
│   │   ├── conflict/ # ConflictDetector
│   │   ├── config.py # pydantic-settings configuration
│   │   └── database.py # SQLAlchemy engine
│   ├── tests/        # 704 unit/integration tests
│   ├── requirements.txt # Python dependencies
│   ├── .env          # Runtime credentials (git-ignored)
│   └── .env.example  # Template with placeholder values
├── frontend/         # React + TypeScript + Vite
│   ├── src/          # React components and tests
│   ├── package.json  # Node dependencies
│   └── vite.config.ts
├── docs/             # Project documentation
│   ├── FINAL_THIRD_YEAR_AUDIT.md
│   ├── ML_EVALUATION.md
│   ├── TEST_REPORT.md
│   └── ... (other doc files)
└── README.md         # Project entry point
```

## Module Summary

| Module | Purpose | Tests | Status |
|--------|---------|-------|--------|
| Data Generator | Generate 8 scenario types via FAO-56 | 62 | ✅ Pass |
| ML Pipeline | Train/predict with RF/XGB; SHAP | 64 | ✅ Pass |
| Feature Engineering | Encode categorical features; train/test split | Included in ML pipeline | ✅ Pass |
| Farmer Agents | Utility computation, BATNA, concessions | 96 | ✅ Pass |
| Conflict Detector | 5 conflict types, severity mapping | 88 | ✅ Pass |
| LP Allocator | GLOP LP with constraints and fallbacks | 86 | ✅ Pass |
| Negotiation Engine | Nash bargaining, BATNA, stagnation | 123 | ✅ Pass |
| Explainability | SHAP global + local explanations | 113 | ✅ Pass |
| API Integration | 72 FastAPI endpoint tests | 72 | ✅ Pass (after psycopg2-binary) |
| **Total** | **Full system** | **704** | **100% pass** |

## Limitations

1. **Synthetic data only** — All water demands, scenarios, and model outputs are algorithmically generated. No real farmer records or field data are used. Metrics reflect model fit to synthetic signals, not real-world agricultural accuracy.
2. **PostgreSQL dependency** — API test suite requires psycopg2-binary and optionally a running PostgreSQL instance. Core 704 tests function without a database.
3. **Model retraining required** — Model artifacts (`data/models/`) are not persisted in the repository. Must run `run_training_pipeline()` to generate them.
4. **Single-crop assumption** — FAO-56 method assumes one crop type per farmer; multi-crop scenarios are not modeled.
5. **No real-time data** — Weather parameters are synthetically generated; no integration with live meteorological services.

## Future Work

- Real agronomic validation with farmer-collected water usage data
- Integration with live ET₀ weather services
- Multi-crop FAO-56 extension (dual or triple crop coefficients)
- Reinforcement-learning-based negotiation policy
- Deployment-ready Docker configuration with PostgreSQL
- Expanded i18n (additional Indian languages, user documentation)

## Contacts / Attribution

- **Project Type**: B.Tech CSE Final Year Prototype
- **Disclaimer**: This system uses fully synthetic, agronomically grounded data. All model metrics and experimental results reflect synthetic-signal fit only. Real-world agricultural accuracy requires independent field validation.