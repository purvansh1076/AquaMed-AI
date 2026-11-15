# Phase F Security Audit

## Implemented

- Removed insecure default JWT secret from compose (now required).
- Dev credentials gated to non-production.
- No client-side auth fallback.
- .dockerignore excludes secrets/tests.

## Remaining

- Dependency vulnerability scanning in CI (recommended).
- Rate limiting distributed (recommended).
