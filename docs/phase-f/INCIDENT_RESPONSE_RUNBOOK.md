# Incident Response Runbook

- Backend outage: restart service, check logs.
- Database outage: verify connectivity, restore from backup.
- Auth failure: verify secrets and rate limiter.
- Weather API failure: fallback to synthetic ranges (documented).
- Solver failure: proportional fallback.
- High latency: check DB queries and model loading.
