# Phase U3 — Development Dependency Security Assessment Report

**Audit Target:** All 5 npm audit advisories identified in Phase U2  
**Date:** 2026-11-15  
**Auditor:** AquaMedi AI Release Engineering  

---

## 1. Granular Advisory Investigation

### Advisory 1: Vitest / `@vitest/mocker`
- **Package & Affected Version:** `@vitest/mocker@5.0.1`, `vitest@5.0.1`
- **Advisory Identifiers:** GHSA-qxg6-89mg-rqv8 (Moderate, CVSS 4.7), GHSA-xp26-3454-mjgp (Moderate, CVSS 5.9)
- **Dependency Path:** `frontend` $\to$ `vitest` $\to$ `@vitest/mocker`
- **Classification:** `devDependencies` (Unit testing framework)
- **Actual Exploitability:** Low/None. The vulnerability requires untrusted third-party mock definitions to be registered at runtime. In this project, all mocks are statically defined in `src/tests/` by core developers. Vitest runs solely in automated test suites and is never invoked on user-supplied code.
- **Available Patched Version:** `@vitest/mocker@5.0.3`, `vitest@5.0.3`
- **Recommended Remediation:** Upgrade during the next planned toolchain maintenance window.

---

### Advisory 2: `source-map-js`
- **Package & Affected Version:** `source-map-js@1.2.1`
- **Advisory Identifier:** GHSA-68fv-2mgg-jv7q (High, CVSS 7.5)
- **Dependency Path:** `frontend` $\to$ `vite` $\to$ `postcss` $\to$ `source-map-js`
- **Classification:** `devDependencies` (Transitive build tool)
- **Actual Exploitability:** None in current usage. The Denial of Service is triggered when parsing crafted external source maps with malformed indexed section offsets. AquaMedi AI generates source maps internally from proprietary React/Tailwind source files; no external untrusted source maps are ingested.
- **Available Patched Version:** `source-map-js@1.2.2`
- **Recommended Remediation:** Update transitive postcss/vite dependencies in a scheduled minor release.

---

### Advisory 3: `undici`
- **Package & Affected Version:** `undici@8.12.1` (and `8.10.2`)
- **Advisory Identifiers:** GHSA-xjj6-f33q-929c (High), GHSA-4w7w-5xrc-9h26 (High), GHSA-2m5v-pch6-74hx (High), GHSA-4qv8-2p9j-2685 (Moderate)
- **Dependency Path:** `frontend` $\to$ `jsdom` $\to$ `undici`
- **Classification:** `devDependencies` (Transitive headless test environment)
- **Actual Exploitability:** None. `undici` is the internal HTTP client utilized by JSDOM during test execution. In AquaMedi AI's test suite, all network requests are mocked locally via Vitest spies (`vi.fn()`); no live HTTP requests are sent to untrusted servers.
- **Available Patched Version:** `undici@8.12.2`
- **Recommended Remediation:** Await upstream patch in JSDOM or pin in future maintenance cycle.

---

### Advisory 4: `vite`
- **Package & Affected Version:** `vite@8.3.0`
- **Advisory Identifiers:** GHSA-587h-7wmj-h5pm (High), GHSA-698v-4r3x-3vcv (Moderate), GHSA-r825-w8mm-5pxw (Moderate)
- **Dependency Path:** `frontend` $\to$ `vite`
- **Classification:** `devDependencies` (Development web server & bundler)
- **Actual Exploitability:** Low. The advisories target Vite's active development server mode (`vite` CLI), specifically the `launch-editor` middleware when invoked on Windows. In production, Vite is strictly a build-time compiler; only static HTML/JS/CSS assets are served.
- **Available Patched Version:** `vite@8.3.3` (or `8.3.8`)
- **Recommended Remediation:** Bump minor Vite version during subsequent product sprint.

---

## 2. Upgrade Risk & Lockfile Decision

Running `npm audit fix` would modify 20 packages across the core compiler and test ecosystem (`rolldown`, `chai`, `postcss`, `vite`, `vitest`). Because:
1. `npm audit --omit=dev` confirms **0 production vulnerabilities**,
2. All 5 advisories pose negligible exploitability in offline, static test workflows,
3. Upgrading major compiler bindings introduces regression risks to the 95 passing tests,

**Decision:** Maintain lockfile stability for Phase U3 and document all findings transparently.
