# Failure Injection and Resilience

## Documented behaviors

- DB unavailable: health degraded, no fabricated data.
- Weather API failure: fallback to synthetic ranges (documented).
- Solver infeasible: proportional fallback.
- Expired token: 401.

## Limitations

- No formal chaos testing performed.
