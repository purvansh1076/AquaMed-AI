# Phase U7.4 — Audit Document 04: Group Coverage, Fallback Semantics & Conditional Guarantees (CP-02)

**Document ID:** `AQUA-AUDIT-U7.4-GROUP`  
**Date:** 2026-11-15  
**Auditor:** Antigravity Autonomous Systems Engineering & Verification  
**Audit Target:** Commit `a76f410` on branch `fix/conformal-small-sample-remediation`  
**Mode:** STRICT READ-ONLY AUDIT  

---

## 1. Executive Summary

This document independently audits the group-conditional selection logic, fallback taxonomy, and statistical coverage assertions in `GroupConformalPredictor` and `ConformalPredictor`.

The audit evaluated seven distinct operational pathways:
1. Valid group-specific calibration ($n_g \ge 30, k_g \le n_g$).
2. Group sample size below `min_group_size` ($n_g < 30$).
3. Unknown / unseen group identifier.
4. No group supplied (`group=None`).
5. Empty group string (`group=""`).
6. Insufficient group-specific calibration ($k_g > n_g$).
7. Insufficient global calibration ($k_{\text{global}} > n_{\text{global}}$).

Every execution pathway was independently verified to return accurate, non-deceptive metadata.

---

## 2. Comprehensive Pathway Trace Matrix

| Pathway / Scenario | Trigger Condition | `coverage_type` | `group_conditional_guarantee` | `calibration_source` | `calibration_sample_size` | `fallback_reason` | `status` | Interpretation Semantics |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **1. Valid Group Calibration** | $g \in \text{group\_q}$ ($n_g \ge 30$) | `"group_specific"` | **`True`** | `"group"` | $n_g$ | `None` | `"SUCCESS"` | Asserts nominal confidence with group-specific calibration for $g$. |
| **2. Group Size Below Threshold** | $g \in \text{group\_n}$ but $n_g < 30$ | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"INSUFFICIENT_GROUP_SAMPLE_SIZE"` | `"SUCCESS"` | Asserts marginal confidence; explicitly states group-conditional coverage NOT guaranteed for $g$. |
| **3. Unknown Group** | $g \notin \text{group\_n}$ | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"UNKNOWN_GROUP"` | `"SUCCESS"` | Asserts marginal confidence; explicitly states group-conditional coverage NOT guaranteed for $g$. |
| **4. No Group Specified** | `group is None` | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"NO_GROUP_SPECIFIED"` | `"SUCCESS"` | Asserts marginal confidence with global calibration. |
| **5. Empty Group String** | `group == ""` | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"UNKNOWN_GROUP"` | `"SUCCESS"` | Handled cleanly as unknown group. |
| **6. Insufficient Group Size ($k_g > n_g$)** | $n_g < 9$ ($\alpha=0.10$) | `"marginal_fallback"` | **`False`** | `"global"` | $n_{\text{global}}$ | `"INSUFFICIENT_GROUP_SAMPLE_SIZE"` or `"INSUFFICIENT_CALIBRATION_DATA"` | `"SUCCESS"` (if global valid) | Falls back to global without claiming group coverage. |
| **7. Insufficient Global Calibration** | $k_{\text{global}} > n_{\text{global}}$ ($n_{\text{global}} < 9$) | `"unavailable"` | **`False`** | `None` | $n_{\text{global}}$ | `"INSUFFICIENT_CALIBRATION_DATA"` | `"INSUFFICIENT_CALIBRATION_DATA"` | Abstains from interval construction; states calibration data insufficient. |

All seven pathways were confirmed through independent script execution.

---

## 3. Critical Mathematical Assessment of `group_conditional_guarantee`

### 3.1 Strict Conditions for Group-Conditional Validity

A true group-conditional split-conformal guarantee:
$$
\mathbb{P}_{(X, Y) \sim P}\left(Y \in \mathcal{C}(X) \mid G = g\right) \ge 1 - \alpha
$$
requires three strict mathematical preconditions:
1. **Intra-Group Exchangeability:** The test sample $(X_{n+1}, Y_{n+1})$ conditioned on $G_{n+1} = g$ must be exchangeable with the calibration samples conditioned on $G = g$.
2. **Sufficient Group Calibration Sample Size:** The group sample size must satisfy $n_g \ge \frac{1-\alpha}{\alpha}$ ($n_g \ge 9$ for $90\%$ confidence) so that an order statistic exists.
3. **Discrete Order Statistic Selection:** The threshold must be chosen as $s_{(k_g)}^{(g)}$ where $k_g = \lceil(n_g + 1)(1-\alpha)\rceil$.

### 3.2 The Role and Limitation of `min_group_size = 30`

The parameter `min_group_size = 30` in `GroupConformalPredictor` is an engineering heuristic chosen to ensure variance stabilization of the quantile estimate. It is **not** a mathematical guarantee that all empirical subgroups will have identical test distribution properties:
- If a group experiences covariate shift or concept drift between calibration and test time, exchangeability is violated and coverage may degrade.
- The `group_conditional_guarantee` field in AquaMedi AI indicates that **split-conformal calibration was executed on samples belonging strictly to group $g$**, satisfying theoretical exchangeability under the data generation model.
- Crucially, commit `a76f410` ensures that `group_conditional_guarantee` is **never set to `True`** when falling back to the pooled global threshold `global_q`.

### 3.3 Protection Against Over-Promoting Marginal Guarantees

In `ConformalPredictor` (the global predictor) and in all fallback paths of `GroupConformalPredictor`:
- `group_conditional_guarantee` is hardcoded to `False`.
- The interpretation prose explicitly clarifies:
  > `"With nominal 90% marginal statistical confidence (global calibration, N=...; group-conditional coverage not guaranteed...)"`
- This prevents downstream decision engines (such as the linear programming water allocator) from assuming minority farms have guaranteed bounds.

---

## 4. Audit Conclusion

The group coverage selection logic and fallback semantics in commit `a76f410` are **statistically accurate, transparent, and completely free of false confidence assertions**.
