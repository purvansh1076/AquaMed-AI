# Staging Environment Guide

## Modes

- Mode A: Local staging validation (Docker Compose with staging env).
- Mode B: External staging preparation (config only, no deployment).

## Key settings

- APP_ENV=staging, APP_DEBUG=false.
- Separate DB, JWT_SECRET_KEY, CORS_ORIGINS.
- No dev credentials.
- Health endpoints /api/v1/health/live and /ready.
