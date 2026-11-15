# AquaMedi AI — Release Checklist

This document details the rigorous pre-release verification checklist required before public branch publication or production staging. Every gate must be verified and checked off prior to publication.

---

## Pre-Publication Gate Verification Matrix

| Checklist Gate | Target Criteria | Actual Status | Verification Method |
|---|---|---|---|
| **1. Branch Isolation** | Working on `feature/aquamedi-ai-product-transformation` | **PASS** | `git branch --show-current` |
| **2. Base Commit Integrity** | Descendant of `main` (`9b32dda`) without merge conflicts | **PASS** | `git merge-base main HEAD` |
| **3. Model Artifact Integrity** | SHA-256 hashes of trained models match verified baseline | **PASS** | `Get-FileHash backend/data/models/*` |
| **4. Backend Regression Suite** | 862 / 862 tests passing | **PASS** | `pytest -q` (862 passed, 5 warnings) |
| **5. Frontend Unit Suite** | 95 / 95 Vitest tests passing | **PASS** | `npm test -- --run` (95 passed) |
| **6. Frontend Build Verification** | TypeScript compilation (`tsc -b`) and Vite bundling pass | **PASS** | `npm run build` (built in 1.58s) |
| **7. Security & Secrets Audit** | Zero tracked `.env` files, no hardcoded credentials | **PASS** | `git grep` and `git ls-files` check |
| **8. Environment Configuration** | Production secret validators active in `config.py` | **PASS** | Code review & unit test verification |
| **9. Database Migration Lineage** | Linear migration path (`0001_initial` -> `0002_add_users_table`) | **PASS** | Inspection of `alembic/versions` |
| **10. Docker Configuration** | Non-root user, healthcheck endpoint, clean ignore rules | **PASS** | Inspection of `Dockerfile` & compose |
| **11. Documentation Currency** | Notes, changelog, limitations, and handover up to date | **PASS** | Release documentation audit |
| **12. Authorization Gate** | Mandatory STOP before `git push` or PR creation | **PENDING** | Explicit User Authorization |

---

## Detailed Gate Verification Procedures

### Gate 1 & 2: Repository and Branch Isolation
- [x] Current working branch is `feature/aquamedi-ai-product-transformation`.
- [x] Branch history is linear and directly branched from `main` (`9b32dda`).
- [x] No uncommitted modifications or accidental staging of scratch files.
- [x] Reproducibility benchmark artifacts preserved in `backend/data/models/`.

### Gate 3: Model Artifact Preservation
- [x] `backend/data/models/encoders.joblib` SHA-256: `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD`
- [x] `backend/data/models/rf_model.joblib` SHA-256: `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75`
- [x] `backend/data/models/xgb_model.joblib` SHA-256: `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56`
- [x] `backend/data/models/evaluation_results.json` SHA-256: `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7`

### Gate 4 & 5: Regression Test Suites
- [x] Backend Pytest Suite:
  - 862 tests executed across 27 test modules.
  - 862 passed, 0 failures, 0 errors.
  - 5 non-fatal library deprecation/version warnings documented.
- [x] Frontend Vitest Suite:
  - 12 test files executed across all UI workflows.
  - 95 passed, 0 failures, 0 errors.

### Gate 6: Production Build & Asset Packaging
- [x] Frontend TypeScript validation (`tsc -b`) succeeds with 0 type errors.
- [x] Vite asset minification and bundling completed successfully (`dist/index.html`, `dist/assets/`).
- [x] Production bundle size verified (~1.02 MB JavaScript, 50.8 KB CSS).

### Gate 7 & 8: Security & Authentication Gating
- [x] Real `.env` files are ignored by `.gitignore` and not tracked in Git.
- [x] Template `.env.example` files contain no actual production secrets.
- [x] `Settings.validate_production_secrets` enforces required production keys (`JWT_SECRET_KEY`, `SECRET_KEY`, `EXPERT_DEFAULT_PASSWORD`).
- [x] Prototype credentials (`admin123`) disabled by default and rejected when `APP_ENV=production`.
- [x] Client-side authentication fallback removed; RBAC boundaries strictly enforced server-side.

### Gate 9 & 10: Database, Deployment & CI
- [x] Alembic migration chain contains no head branches or missing dependencies.
- [x] Backend Docker container runs under unprivileged `appuser` (UID 10001).
- [x] Docker healthcheck verifies `/api/v1/health/ready` with 10s interval, 5s timeout, 5 retries.
- [x] `.github/workflows/ci.yml` validated for continuous integration on push and pull requests.

### Gate 11: Release Documentation & Scientific Transparency
- [x] `RELEASE_NOTES.md` prepared with comprehensive capability and limitation overview.
- [x] `CHANGELOG.md` updated adhering to Keep a Changelog / SemVer format.
- [x] `docs/KNOWN_LIMITATIONS.md` updated to accurately reflect current repository state and scientific boundaries.
- [x] `docs/PROJECT_HANDOVER.md` prepared with deployment instructions, architecture maps, and operational runbooks.
- [x] Scientific boundaries clearly distinguish engineering unit tests from regional empirical validation and physical field pilots.

### Gate 12: Publication Authorization Gate
- [ ] **STOP: Do NOT run `git push` without explicit user authorization.**
- [ ] **STOP: Do NOT create pull requests without explicit user authorization.**
- [ ] **STOP: Do NOT merge into `main` without explicit user authorization.**
- [ ] **STOP: Do NOT trigger external deployment without explicit user authorization.**
