# Phase U3 — Branch Protection Recommendation Report

**Target Branch:** `main`  
**Repository:** `https://github.com/purvansh1076/AquaMed-AI`  
**Date:** 2026-11-15  
**Auditor:** AquaMedi AI Release Engineering  

---

## 1. Current State Assessment

A live query via the GitHub API confirmed:
```json
{
  "name": "main",
  "protected": false
}
```
Branch protection is currently disabled on `main`, meaning direct pushes, unprotected merges, and branch deletion are technically permitted by default.

---

## 2. Recommended Protection Policy Specification

To ensure government-grade engineering integrity and protect the codebase post-merge, the following rules should be configured in GitHub Repository Settings (`Settings` $\to$ `Branches` $\to$ `Branch protection rules`):

### Rule 1: Require Pull Request Reviews Prior to Merging
- **Setting:** `Require a pull request before merging`
- **Required Approvals:** At least 1 approving review from an authorized maintainer.
- **Dismiss Stale Approvals:** Enabled (new commits invalidate previous approvals).
- **Require Code Owner Review:** Optional for single-maintainer, recommended for team handovers.

### Rule 2: Require Status Checks to Pass
- **Setting:** `Require status checks to pass before merging`
- **Require Branches to be Up-to-Date:** Enabled (strictly prevents semantic merge conflicts).
- **Required Status Checks:**
  - `backend` (GitHub Actions CI workflow)
  - `frontend` (GitHub Actions CI workflow)

### Rule 3: Enforce Non-Destructive Operations
- **Block Force Pushes:** `Do not allow force pushes` (strictly enforced).
- **Block Branch Deletion:** `Do not allow branch deletions` (strictly enforced).
- **Enforce Linear History:** Enabled (encourages clean fast-forward or non-squashed rebase integrations).

---

## 3. Governance Safeguards

In strict compliance with Phase U3 safeguards, **no settings were altered on GitHub**. This specification serves as the formal recommendation for the repository administrator.
