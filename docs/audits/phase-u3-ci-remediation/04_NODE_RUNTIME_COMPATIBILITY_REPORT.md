# Phase U3 — Node.js Runtime Compatibility & Deprecation Report

**Date:** 2026-11-15  
**Auditor:** AquaMedi AI Release Engineering  

---

## 1. Node.js 20 Deprecation Notice Investigation

During the initial CI execution on GitHub Actions, the runner emitted:
> *"Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-node@v4."*

### Analysis:
GitHub Actions runner infrastructure is phasing out Node 20 as an execution environment. While internal action shims can bridge runner execution, user jobs that explicitly request `node-version: '20'` force older runtimes that are incompatible with modern tooling like JSDOM 30.

---

## 2. Package Dependency Compatibility Matrix

All frontend dependencies declared in `frontend/package.json` were audited for Node.js 24 compatibility:

| Package | Declared Version | Minimum Engine | Node 24 Compatibility | Verified Locally |
|---|---|---|---|---|
| `react` / `react-dom` | `^19.2.8` | `>=0.10.0` | **Fully Compatible** | Yes |
| `react-router-dom` | `^7.18.4` | `>=18.0.0` | **Fully Compatible** | Yes |
| `recharts` | `^3.10.1` | `>=14.0.0` | **Fully Compatible** | Yes |
| `vite` | `^8.3.0` | `^18.0.0 || >=20.0.0` | **Fully Compatible** | Yes |
| `vitest` | `^5.0.1` | `^18.0.0 || >=20.0.0` | **Fully Compatible** | Yes |
| `jsdom` | `^30.1.1` | `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0` | **Target Engine** | Yes |
| `typescript` | `~6.0.2` | `>=14.17` | **Fully Compatible** | Yes |

---

## 3. Resolution & Lockfile Stability

- Targeting `node-version: '24'` in `.github/workflows/ci.yml` eliminates the deprecation warning and directly satisfies JSDOM's engine constraints.
- No modifications were required in `frontend/package.json` or `frontend/package-lock.json`, preserving complete dependency lockfile stability.

---

## 4. Verdict

**Verdict: VERIFIED PASS**  
Node 24 is fully supported across all installed dependencies and aligns the cloud CI environment with the verified local runtime.
