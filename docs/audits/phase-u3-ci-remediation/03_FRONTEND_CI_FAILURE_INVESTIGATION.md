# Phase U3 — Frontend CI Failure Investigation Report

**Target:** `frontend` job in `.github/workflows/ci.yml`  
**Date:** 2026-11-15  
**Auditor:** AquaMedi AI Release Engineering  

---

## 1. Independent Failure Diagnosis

The frontend failure was thoroughly investigated to ensure it was not erroneously conflated with backend database dependencies:

1. **Decoupled Architecture:** The frontend test suite (`frontend/src/tests/`) executes entirely in-memory using jsdom and mocked API clients (`vi.fn()`). It does not connect to PostgreSQL or backend endpoints.
2. **Root Cause Identification:**
   Inspection of `node_modules/jsdom/package.json` revealed an explicit Node.js engine requirement:
   ```json
   "engines": {
     "node": "^22.22.2 || ^24.15.0 || >=26.0.0"
   }
   ```
   The previous CI definition specified `node-version: '20'`. Executing JSDOM 30 under Node 20 resulted in syntax and feature incompatibilities in the headless DOM environment.
3. **Contrast with Local Verified Baseline:**
   Locally, the development environment runs **Node v24.21.0**, which satisfies `^24.15.0`. Under this environment, all 12 test files and 95 tests pass consistently in ~14 seconds.

---

## 2. Implemented Remediation

1. **Node.js Runtime Upgrade:** Updated `actions/setup-node@v4` to target `node-version: '24'`.
2. **Execution Flag:** Added explicit non-watch flag `npm test -- --run` to ensure single-run execution on headless CI runners.
3. **NPM Caching:** Added `cache: 'npm'` with dependency path `frontend/package-lock.json` for deterministic package resolution.

---

## 3. Investigation Verdict

**Verdict: ROOT CAUSE RESOLVED**  
Frontend CI failure was purely an engine version mismatch with JSDOM 30, resolved by targeting Node 24 in CI.
