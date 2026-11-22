# Phase F CI/CD

## Workflow

.github/workflows/ci.yml runs backend pytest and frontend test+build on push/PR.

## Required secrets

APP_ENV, DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY, EXPERT_DEFAULT_PASSWORD, ENABLE_DEV_DEMO_CREDENTIALS, RANDOM_SEED, MODEL_DIR, DATA_DIR.
