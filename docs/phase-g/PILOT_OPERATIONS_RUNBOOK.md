# Pilot Operations Runbook

## Procedures

- Application outage: restart, check logs.
- Database outage: verify connectivity, restore from backup.
- Weather API failure: fallback to synthetic ranges (documented).
- Solver failure: proportional fallback.
- Auth failure: verify secrets and rate limiter.
