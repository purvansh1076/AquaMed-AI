# Production Deployment Checklist

- Set APP_ENV=production, APP_DEBUG=false.
- Set JWT_SECRET_KEY, EXPERT_DEFAULT_PASSWORD, SECRET_KEY.
- Run alembic upgrade head.
- Build Docker images.
- Run health checks /api/v1/health/ready.
- Run backend/frontend tests.
- Verify model artifact hashes.
