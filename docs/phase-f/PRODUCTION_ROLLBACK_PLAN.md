# Production Rollback Plan

- Revert to previous application image/commit.
- Restore database from backup if needed.
- Verify model artifact hashes.
- Re-run health checks and smoke tests.
