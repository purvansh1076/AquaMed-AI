# Phase U5 — Audit Report 11: Comprehensive Findings & Recommendations Register

**Document ID:** `AQUA-AUDIT-U5-11`  
**Date:** 2026-11-15  
**Review Type:** Risk Classification & Remediation Tracking  
**Scope:** Full Application, CI/CD, Infrastructure & Git Repository  

---

## 1. Executive Summary

This register consolidates all observations, risks, security notices, and recommendations identified during the Phase U5 Independent Pull Request Review of PR #1.

Findings are categorized across five standard severity levels:
- **Critical (P0):** Immediate exploitation risk or catastrophic system failure — **0 Found.**
- **High (P1):** Serious defect requiring mandatory fix prior to merge — **0 Found.**
- **Medium (P2):** Governance, configuration, or operational gap requiring attention — **2 Found.**
- **Low (P3):** Minor warning, dev dependency notice, or code style improvement — **3 Found.**
- **Informational (P4):** Architecture notes, limitations disclosure, and verified baselines — **4 Found.**

---

## 2. Findings Register Summary Table

| Finding ID | Severity | Category | Title | Status |
| :--- | :--- | :--- | :--- | :--- |
| **M-01** | Medium | Governance | GitHub `main` branch protection is currently disabled | Actionable Advisory |
| **M-02** | Medium | Git Integrity | Phase U4 audit dossier commit (`d9e853a`) is unpushed | Documented & Expected |
| **L-01** | Low | Dependencies | 5 dev-only security advisories in frontend tooling | Analyzed & Non-Critical |
| **L-02** | Low | ML Tooling | XGBoost serialization deprecation warning in pytest | Mitigated & Tested |
| **L-03** | Low | Test Suite | AnyIO BlockingPortal deprecation warning in TestClient | Benign Library Warning |
| **I-01** | Info | Scientific | Agronomic models trained on synthetic simulation data | Disclosed in Docs & UI |
| **I-02** | Info | Hardware | System does not actuate physical canal sluices | Disclosed & Guarded |
| **I-03** | Info | DevOps | Recommendation to avoid Squash Merge on PR #1 | Process Recommendation |
| **I-04** | Info | Security | All 4 production model binary hashes 100% verified | Baseline Verified |

---

## 3. Detailed Finding Descriptions & Remediation Plans

### Finding M-01: GitHub `main` Branch Protection is Currently Disabled
- **Severity:** Medium (P2)
- **Category:** Governance / Branch Security
- **Details:** Querying the GitHub REST API (`GET /repos/purvansh1076/AquaMed-AI/branches/main/protection`) returns HTTP 404 with message `"Branch not protected"`.
- **Impact:** Any collaborator with push access can commit directly to `main` without PR review or bypass CI checks.
- **Remediation:**
  1. Open GitHub repository Settings $\to$ Branches $\to$ Branch protection rules.
  2. Add rule for `main`.
  3. Enable: "Require a pull request before merging", "Require status checks to pass before merging" (selecting `backend` and `frontend`), and "Do not allow force pushes".

### Finding M-02: Phase U4 Audit Dossier Commit is Unpushed
- **Severity:** Medium (P2)
- **Category:** Git Integrity
- **Details:** Local HEAD is on commit `d9e853a` (`docs(audit): record Phase U4 pull request creation audit dossier`), which is 1 commit ahead of the remote PR source commit `c4d68c4`.
- **Impact:** GitHub PR #1 displays files as of `c4d68c4` (which contains full code and Phase U3 CI reports), while the U4 dossier exists only in local workspace history.
- **Remediation:** This state is compliant with authorization protocols requiring explicit consent before pushing. A subsequent commit or push operation can incorporate the U4 and U5 audit documentation into `main` after PR merge, or be pushed to the feature branch if updated PR files are desired before merge.

### Finding L-01: 5 Dev-Only Security Advisories in Frontend Tooling
- **Severity:** Low (P3)
- **Category:** Dependencies
- **Details:** `npm audit` reports 5 advisories (3 Moderate, 2 High) across `vitest`, `source-map-js`, `undici`, and `vite`. `npm audit --omit=dev` reports 0 vulnerabilities.
- **Impact:** Zero impact on production runtime users. Code is not packaged into browser bundles.
- **Remediation:** Plan non-breaking dependency upgrades during a future routine maintenance milestone. Do not execute destructive `npm audit fix --force`.

### Finding L-02: XGBoost Serialization Deprecation Warning
- **Severity:** Low (P3)
- **Category:** ML Serialization
- **Details:** Loading `xgb_model.joblib` emits a warning regarding legacy serialization format.
- **Mitigation:** Codebase implements dynamic `base_score` calibration upon model initialization (`tests/test_agronomy.py::test_xgboost_unpickled_base_score_calibration`), ensuring complete numerical stability.

### Finding L-03: AnyIO BlockingPortal Deprecation Warning
- **Severity:** Low (P3)
- **Category:** Test Suite / Starlette
- **Details:** Starlette TestClient emits a deprecation warning about `anyio.abc.BlockingPortal`.
- **Mitigation:** Benign library warning; Starlette and AnyIO will resolve this in future upstream releases.

### Finding I-01 through I-04: Informational Verifications
- **I-01 & I-02:** Documented limitations regarding synthetic training data and lack of physical actuator control are clearly disclosed across `README.md`, `PR_DESCRIPTION.md`, and `docs/KNOWN_LIMITATIONS.md`.
- **I-03:** "Rebase and Merge" or "Merge Commit" recommended over "Squash Merge" to preserve atomic 27-commit history.
- **I-04:** SHA-256 hashes of `rf_model.joblib`, `xgb_model.joblib`, `encoders.joblib`, and `evaluation_results.json` match baseline byte-for-byte.

---

## 4. Verdict

**Findings Status: 0 BLOCKERS (All identified items are understood, mitigated, or informational)**
