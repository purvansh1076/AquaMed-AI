# Phase U7.1 — Audit Report 04: Security Posture, Dependency Claims & Scope Reconciliation

**Document ID:** `AQUA-AUDIT-U7.1-04`  
**Date:** 2026-11-15  
**Review Type:** Security Claim Precision & Dependency Scope Reconciliation  
**Components:** `frontend/package.json`, `backend/requirements.txt`, Repository Tracked Assets  

---

## 1. Executive Summary

This report establishes precise, legally defensible, and technically accurate wording for security and dependency vulnerability claims in AquaMedi AI.

The review resolves ambiguities in earlier reports by strictly distinguishing between production runtime dependencies and development tooling, and by precisely delineating the boundaries of automated pattern-based secret and privacy scans.

---

## 2. Reconciled Dependency Audit Results

### 2.1 Production Runtime Scope
```bash
npm audit --omit=dev
```
- **Observed Result:** `found 0 vulnerabilities`
- **Reconciled Statement:** **No known vulnerabilities were detected in the production runtime dependencies bundled into the user-facing browser application.**

### 2.2 Development & Build Tooling Scope
```bash
npm audit
```
- **Observed Result:** `5 vulnerabilities (2 moderate, 3 high)`
- **Reconciled Statement:** **Five dependency advisories remain active in local development and build tooling.** None are deployed or executed in production client browsers.

### 2.3 Detailed Advisory Breakdown Table
| Package | Severity | Advisory ID | Vulnerability Summary | Runtime Impact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `@vitest/mocker` | Moderate | `GHSA-qxg6-89mg-rqv8`, `GHSA-xp26-3454-mjgp` | Mock registration allowlist bypass in test runner | Build/test only; zero browser exposure | Unresolved in dev dependencies |
| `vitest` | Moderate | Inherited from `@vitest/mocker` | Dependent on vulnerable `@vitest/mocker` | Build/test only; zero browser exposure | Unresolved in dev dependencies |
| `source-map-js` | High | `GHSA-68fv-2mgg-jv7q` | Event-loop denial of service during source map parsing | Build-time compilation only | Unresolved in dev dependencies |
| `undici` | High | `GHSA-4qv8-2p9j-2685`, etc. | Unbounded EventSource memory & TLS options in Node | Build tooling internal HTTP client | Unresolved in dev dependencies |
| `vite` | High | `GHSA-698v-4r3x-3vcv`, etc. | Dev server CLI argument escaping on Windows | Local dev server only; production served by Nginx | Unresolved in dev dependencies |

**Remediation Recommendation:** Do not run `npm audit fix --force`, as it would force breaking major package upgrades. Address dev advisories in a planned non-breaking maintenance cycle.

---

## 3. Secret Containment & Privacy Scan Scopes

### 3.1 Pattern-Based Secret Scan
- **Scan Methodology:** Automated regex pattern matching across all 238 tracked files for private keys (`BEGIN RSA PRIVATE KEY`), cloud API tokens (AWS, GCP, Azure), database connection strings with plaintext passwords, and JWT secrets.
- **Findings:** No secret patterns were detected in tracked files.
- **Precise Claim Statement:** **"Automated pattern-based scanning detected zero secrets, private keys, or API tokens in repository tracked files."** (Avoid blanket assertions of absolute secret absence).

### 3.2 Personally Identifiable Information (PII) Scan
- **Scan Methodology:** Examination of sample datasets, schemas, and test fixtures for real individual names, national identity numbers (Aadhaar), phone numbers, or cadastral land coordinates.
- **Findings:** All entities use synthetic pseudonyms (`FARMER_001`, `FARMER_002`) and simulated coordinate grids.
- **Precise Claim Statement:** **"Automated scanning detected zero real-world personally identifiable information in tracked application data; all agricultural profiles use synthetic pseudonyms."**

---

## 4. Production Security Configuration Controls

- **Startup Validator:** Pydantic `@model_validator` in `backend/app/config.py` blocks startup in `ENVIRONMENT=production` if `JWT_SECRET_KEY` matches default strings or has fewer than 32 characters.
- **Dev Credentials Disabled:** Default demo credentials (`ENABLE_DEV_DEMO_CREDENTIALS`) are strictly disallowed when `ENVIRONMENT=production`.
- **Brute-Force Throttling:** Sliding-window rate limiter active on `/api/v1/auth/login` (5 attempts / 900s).

---

## 5. Verdict

**Security Claim Status: RECONCILED & PRECISE (0 Production CVEs, 5 Dev Advisories Documented, Pattern Scans Bounded)**
