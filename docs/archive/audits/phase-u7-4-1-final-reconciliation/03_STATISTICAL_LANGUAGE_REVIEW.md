# Phase U7.4.1 — Audit Document 03: Review of Statistical Interpretation Language & Coverage Guarantees

**Document ID:** `AQUA-AUDIT-U7.4.1-LANG-REVIEW`  
**Date:** 2026-11-15  
**Auditor:** Antigravity Autonomous Systems Engineering & Verification  
**Audit Target:** Commit `a76f410` on branch `fix/conformal-small-sample-remediation`  
**Base Commit:** `origin/main` at `f4d573d42929aca616c9f3f72b084f5e3514673d`  
**Mode:** STRICT READ-ONLY AUDIT  

---

## 1. Executive Summary

This document reviews the scientific terminology, coverage guarantees, and human-readable interpretation messages produced across all execution pathways in AquaMedi AI's conformal prediction engine.

The audit verified that commit `a76f410`:
1. Distinguishes marginal population-average coverage from group-conditional split-conformal coverage.
2. Avoids false Bayesian posterior claims for individual fixed observations.
3. Explicitly flags that `min_group_size = 30` is an empirical stabilization heuristic that requires within-group exchangeability to guarantee group coverage.
4. Ensures that metadata describes the actual threshold and calibration source used rather than merely echoing requested query parameters.
5. Verifies that zero responses report successful finite calibration when an interval is unavailable.

---

## 2. Statistical Definitions and Theoretical Distinctions

### 2.1 The Conformal Prediction Guarantee
Split conformal prediction provides a **frequentist guarantee over the joint distribution of calibration and test data**:
$$
\mathbb{P}_{(X_1, Y_1), \dots, (X_{n+1}, Y_{n+1}) \sim P^{n+1}}\left(Y_{n+1} \in \hat{\mathcal{C}}(X_{n+1})\right) \ge 1 - \alpha
$$
**Crucial Distinction:** This is a property of the *calibration-prediction procedure* over repeated draws of the training, calibration, and test data. It does **not** assert that for a single realized calibration set $\mathcal{D}_{\text{cal}}$ and single realized farm query $x^*$, the true parameter $y^*$ falls into the interval with posterior probability $1-\alpha$.

### 2.2 Marginal vs. Group-Conditional Validity
1. **Marginal Coverage (Global Predictor):**
   Averages over all crop types, soil types, and farm sizes:
   $$
   \mathbb{E}_{G}\left[\mathbb{P}(Y \in \hat{\mathcal{C}}(X) \mid G)\right] \ge 1 - \alpha
   $$
   Subgroups with higher-than-average residual variance may have empirical coverage well below $1-\alpha$ (e.g., $27.08\%$ as shown in Phase U7.2).
2. **Group-Conditional Coverage (`GroupConformalPredictor`):**
   Requires conditioning on stratum $G = g$:
   $$
   \mathbb{P}(Y_{n+1} \in \hat{\mathcal{C}}_g(X_{n+1}) \mid G_{n+1} = g) \ge 1 - \alpha
   $$
   **Required Assumptions:**
   - **Intra-Group Exchangeability:** The test sample $(X_{n+1}, Y_{n+1})$ conditioned on $G = g$ is exchangeable with the calibration samples conditioned on $G = g$.
   - **Order-Statistic Existence:** $n_g \ge \frac{1-\alpha}{\alpha}$.
   - **Heuristic Stabilization:** $n_g \ge \text{min\_group\_size} = 30$ reduces finite-sample quantile variance.

---

## 3. String Template and Prose Inspection

### 3.1 Global Marginal Predictor (Success)
- **Code Reference:** `backend/app/ml/conformal_predictor.py#L137-L141`
- **Generated String:**
  > `"With nominal 90% marginal statistical confidence (global calibration, N=450; group-conditional coverage not guaranteed), actual field crop water requirement lies between 74.34 m³ and 125.66 m³."`
- **Assessment:**
  - Accurately specifies *nominal marginal* confidence.
  - Explicitly states *group-conditional coverage not guaranteed*.
  - Accurately reports sample size $N=450$.

### 3.2 Group Predictor: Group-Specific Calibration (Success)
- **Code Reference:** `backend/app/ml/group_conformal.py#L181-L185`
- **Generated String:**
  > `"With nominal 90% statistical confidence (group-specific calibration for 'wheat', N=50), actual field crop water requirement lies between 90.0 m³ and 110.0 m³."`
- **Assessment:**
  - Transparently identifies the specific stratum (`'wheat'`) and sample size ($N=50$).
  - Avoids claiming certainty for an individual farm; states nominal procedure confidence.

### 3.3 Group Predictor: Marginal Fallback (Success with Fallback)
- **Code Reference:** `backend/app/ml/group_conformal.py#L187-L192`
- **Generated String:**
  > `"With nominal 90% marginal confidence (global calibration fallback, N=115; group-conditional coverage not guaranteed for 'minority_crop'), actual field crop water requirement lies between 70.0 m³ and 130.0 m³."`
- **Assessment:**
  - Explicitly warns the user that global fallback occurred.
  - Explicitly warns that group-conditional coverage is **not guaranteed** for the specified group.

### 3.4 Insufficient Calibration (Unavailable)
- **Code Reference:** `backend/app/ml/group_conformal.py#L170-L173`, `conformal_predictor.py#L110-L113`
- **Generated String:**
  > `"Calibration sample size is insufficient to guarantee 90% finite-sample coverage."`
- **Assessment:**
  - Clear, concise refusal to fabricate confidence when mathematical conditions fail.

---

## 4. Metadata Integrity Matrix

Every response was audited across seven operational states to verify that metadata describes the **actual threshold used**:

| Operational State | Actual Threshold $q$ Used | `coverage_type` | `group_conditional_guarantee` | `calibration_source` | `calibration_sample_size` | `fallback_reason` | `status` |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Group Calibrated ($n_g \ge 30$)** | Group threshold $\hat{q}_g$ | `"group_specific"` | **`True`** | `"group"` | $n_g$ | `None` | `"SUCCESS"` |
| **Undersized Group ($n_g < 30$)** | Global threshold $\hat{q}_{\text{global}}$ | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"INSUFFICIENT_GROUP_SAMPLE_SIZE"` | `"SUCCESS"` |
| **Unknown Group** | Global threshold $\hat{q}_{\text{global}}$ | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"UNKNOWN_GROUP"` | `"SUCCESS"` |
| **No Group Specified** | Global threshold $\hat{q}_{\text{global}}$ | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"NO_GROUP_SPECIFIED"` | `"SUCCESS"` |
| **Global Predictor Endpoint** | Global threshold $\hat{q}_{\text{norm}}$ | `"marginal"` | **`False`** | `"global"` | $450$ | `None` | `"SUCCESS"` |
| **Insufficient Group ($n_g < 9$)** | Global threshold $\hat{q}_{\text{global}}$ | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"INSUFFICIENT_GROUP_SAMPLE_SIZE"` | `"SUCCESS"` |
| **Insufficient Global ($n < 9$)** | Infinite ($\infty$) | `"unavailable"` | **`False`** | `None` | $n_{\text{global}}$ | `"INSUFFICIENT_CALIBRATION_DATA"` | `"INSUFFICIENT_CALIBRATION_DATA"` |

### Key Metadata Invariants Verified:
1. When `status == "INSUFFICIENT_CALIBRATION_DATA"`, `coverage_type` is strictly `"unavailable"`, `group_conditional_guarantee` is strictly `False`, and `calibration_source` is `None`.
2. `group_conditional_guarantee` is **never `True`** when falling back to global quantiles.
3. In all instances, metadata reflects the **actual threshold applied to the prediction interval**, eliminating the risk of misrepresenting fallback intervals as group-specific guarantees.

---

## 5. Audit Conclusion

The statistical interpretation language and metadata assignments in commit `a76f410` are **scientifically defensible, assumption-transparent, and free of over-claimed coverage guarantees**.
