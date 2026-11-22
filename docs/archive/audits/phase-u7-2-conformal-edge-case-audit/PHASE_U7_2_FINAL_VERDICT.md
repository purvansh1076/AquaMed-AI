# Phase U7.2 — Final Audit Verdict: Conformal Prediction Edge-Case & Fallback Audit

**Document ID:** `AQUA-AUDIT-U7.2-FINAL`  
**Date:** 2026-11-15  
**Audit Authority:** Antigravity Autonomous Systems Auditor  
**Target Repository:** [purvansh1076/AquaMed-AI on GitHub](https://github.com/purvansh1076/AquaMed-AI)  
**Official Branch:** `main`  
**Verified `main` HEAD Commit:** [`f4d573d42929aca616c9f3f72b084f5e3514673d`](https://github.com/purvansh1076/AquaMed-AI/commit/f4d573d42929aca616c9f3f72b084f5e3514673d)  
**Working Tree State:** Clean (untracked audit dossiers only; zero source code changes)  

---

## 1. Executive Summary

This independent mathematical audit evaluated AquaMedi AI's conformal prediction algorithms under small calibration sample sizes, group fallback pathways, and finite-sample coverage boundary conditions.

The investigation proved via mathematical derivation and Monte Carlo simulation ($50,000$ trials) that:
1. When calibration sample size $n < \frac{1-\alpha}{\alpha}$, the production function `_finite_sample_quantile_level` clamps the quantile level to $1.0$. This selects the sample maximum $s_{(n)}$, delivering empirical coverage of only $\frac{n}{n+1} < 1 - \alpha$ (as low as $50\%$ for $n=1$, $83.3\%$ for $n=5$) while asserting a distribution-free finite-sample guarantee.
2. When a group calibration size falls below `min_group_size = 30`, the engine silently substitutes the pooled `global_q`. For heterogeneous minority strata with elevated error variance, this fallback achieves as low as **$27.08\%$ test coverage** while claiming a 90% confidence guarantee.

---

## 2. Specification of Confirmed Implementation Defects

### Defect CP-01: Mathematical Finite-Sample Quantile Boundary Violation
- **Affected File:** `backend/app/ml/group_conformal.py`
- **Affected Function:** `GroupConformalPredictor._finite_sample_quantile_level(n: int, alpha: float) -> float`
- **Defective Lines:**
  ```python
  level = math.ceil((n + 1) * (1.0 - alpha)) / n
  return min(1.0, max(0.0, level))
  ```
- **Reproduction Case:**
  Call `GroupConformalPredictor._finite_sample_quantile_level(n=5, alpha=0.10)`.
  The function returns `1.0`.
  `np.quantile(scores, 1.0)` selects $s_{(5)}$.
  Under exchangeability, $\mathbb{P}(S_6 \le s_{(5)}) = 5/6 = 83.33\% < 90.0\%$.
  The theoretical finite-sample guarantee is broken.
- **Root Mathematical Cause:**
  A finite $(1-\alpha)$ order statistic within $n$ samples exists if and only if $n \ge \frac{1-\alpha}{\alpha}$. When $k > n$, the true theoretical threshold is $\infty$ (unbounded interval) or the algorithm must abstain. Clamping to $1.0$ violates the finite-sample guarantee.
- **Recommended Remediation (Future Phase):**
  When $k = \lceil(n+1)(1-\alpha)\rceil > n$, the function must return `float('inf')` or raise an `InsufficientCalibrationError`, prompting `predict_interval()` to output an unbounded interval or abstain with `"status": "INSUFFICIENT_CALIBRATION_DATA"`.

---

### Defect CP-02: Silent Fallback Without Group-Conditional Guarantee
- **Affected File:** `backend/app/ml/group_conformal.py`
- **Affected Function:** `GroupConformalPredictor.predict_interval()`
- **Defective Line:**
  ```python
  q = self.group_q.get(str(group), self.global_q) if group is not None else self.global_q
  ```
- **Reproduction Case:**
  In a population where Group A (loam, $\sigma=5$) is $90\%$ of calibration and Group B (sand, $\sigma=30$) is $10\%$ ($n_B = 20 < 30$), Group B falls back to `global_q`.
  Monte Carlo test set evaluation yields only **$27.08\%$ empirical coverage** for Group B farmers, yet the returned dictionary claims a 90% statistical confidence guarantee for that group.
- **Recommended Remediation (Future Phase):**
  When fallback to `global_q` occurs, the return payload must explicitly declare `"coverage_type": "marginal_fallback"`, `"group_conditional_guarantee": false`, and warn that the interval reflects population-wide marginal variance rather than a stratum-specific guarantee.

---

## 3. Real-World Exposure Analysis

- **Production API Exposure:** The active REST endpoint `/api/v1/predictions/conformal-interval` (`backend/app/api/agronomy_routes.py`) currently uses the static pre-computed global normalized threshold $\hat{q}_{\text{norm}} = 25.6610\text{ m}^3$ derived from the global validation split ($n = 450 \ge 9$).
- **Deployment Safety:** In current single-endpoint production usage with $n=450$, the system does not crash and marginal coverage ($90.47\%$) is preserved on the global simulation distribution.
- **Scientific Integrity:** However, because `group_conformal.py` is committed to `main` as an exported component, Defects CP-01 and CP-02 represent genuine mathematical and algorithmic defects that must be addressed prior to operational agricultural deployment.

---

## 4. Phase U7.2 Audit Deliverables Index

All 5 audit reports are recorded locally in `docs/audits/phase-u7-2-conformal-edge-case-audit/`:

1. [01_FINITE_SAMPLE_MATHEMATICAL_REVIEW.md](file:///C:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/audits/phase-u7-2-conformal-edge-case-audit/01_FINITE_SAMPLE_MATHEMATICAL_REVIEW.md) — Mathematical derivation of the $k > n$ boundary violation.
2. [02_SMALL_GROUP_FALLBACK_REVIEW.md](file:///C:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/audits/phase-u7-2-conformal-edge-case-audit/02_SMALL_GROUP_FALLBACK_REVIEW.md) — Analysis of group fallback under-coverage and distinction between marginal and conditional guarantees.
3. [03_INDEPENDENT_EDGE_CASE_TESTS.md](file:///C:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/audits/phase-u7-2-conformal-edge-case-audit/03_INDEPENDENT_EDGE_CASE_TESTS.md) — Monte Carlo simulations across $n \in \{0 \dots 450\}$ and $\alpha \in \{0.05, 0.10, 0.20\}$.
4. [04_COVERAGE_CLAIMS_REVIEW.md](file:///C:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/audits/phase-u7-2-conformal-edge-case-audit/04_COVERAGE_CLAIMS_REVIEW.md) — Review of user-facing statements and recommended precision bounding.
5. [PHASE_U7_2_FINAL_VERDICT.md](file:///C:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/audits/phase-u7-2-conformal-edge-case-audit/PHASE_U7_2_FINAL_VERDICT.md) — Executive audit synthesis and formal verdict.

---

## 5. Final Executive Verdict

# **U7.2C — IMPLEMENTATION DEFECT IDENTIFIED**

### Formal Declaration:
- **Defect Identified:** `GroupConformalPredictor._finite_sample_quantile_level` clamps `level` to `1.0` when $k > n$, substituting the sample maximum and failing the theoretical finite-sample coverage guarantee for small $n < \frac{1-\alpha}{\alpha}$.
- **Fallback Limitation Identified:** Silent fallback to `global_q` for small minority groups ($n_g < 30$) fails to provide group-conditional coverage, yielding empirical test coverage as low as $27.08\%$ in high-variance strata.
- **Safety Boundaries Affirmed:** In accordance with strict read-only audit rules, **no source code has been modified, no commits made, and no settings altered.** A dedicated remediation phase is recommended to resolve Defects CP-01 and CP-02.
