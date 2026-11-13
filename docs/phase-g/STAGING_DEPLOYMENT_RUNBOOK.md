# Staging Deployment Runbook

1. Set environment variables.
2. docker compose build
3. docker compose up -d
4. alembic upgrade head (auto in compose)
5. curl /api/v1/health/ready
6. Run smoke tests.
7. Verify persistence after restart.

External deployment requires explicit user approval.
