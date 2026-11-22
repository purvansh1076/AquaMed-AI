# AquaMedi AI — Phase U7.5 Audit: Conformal Mathematical Verification

**Document ID:** `02_CONFORMAL_MATHEMATICAL_VERIFICATION.md`  
**Phase:** U7.5 — Final Independent Conformal Remediation & Merge-Readiness Audit  
**Repository:** `https://github.com/purvansh1076/AquaMed-AI`  
**Audit Status:** STRICT READ-ONLY VERIFICATION  
**Author:** Independent Engineering & Statistical Auditor  
**Date:** November 15, 2026  

---

## 1. Executive Summary

This document presents a rigorous mathematical and algorithmic verification of the finite-sample conformal prediction quantile calculation remediated under defect **CP-01**.

In split conformal prediction (Vovk et al., 2005; Lei et al., 2018; Angelopoulos & Bates, 2021), valid distribution-free marginal prediction intervals require selecting the order statistic index $k$ such that the probability that a new test point's nonconformity score falls within the calibration interval is at least $1 - \alpha$:

\[
P(Y_{n+1} \in C(X_{n+1})) \ge 1 - \alpha
\]

Under exchangeability, this guarantee holds if and only if:

\[
k = \left\lceil (n + 1)(1 - \alpha) \right\rceil
\]

where $n$ is the number of exchangeable calibration instances, and nonconformity scores are sorted in non-descending order: $s_{(1)} \le s_{(2)} \le \dots \le s_{(n)}$.

Our audit verifies that the remediated implementation in `conformal_predictor.py` and `group_conformal.py` rigorously adheres to this finite-sample derivation, completely eliminating the invalid clamping defect identified in Phase U7.2.

---

## 2. Order-Statistic Index Derivation

### 2.1 Theoretical Proof & Finite-Sample Boundary

Let $S_1, \dots, S_n, S_{n+1}$ be exchangeable real-valued nonconformity scores. The ranks of these $n+1$ scores are uniformly distributed over all permutations. The probability that the test score $S_{n+1}$ is among the $k$ smallest scores is:

\[
P(S_{n+1} \le s_{(k)}) = \frac{k}{n + 1}
\]

To guarantee marginal coverage of at least $1 - \alpha$, we must have:

\[
\frac{k}{n + 1} \ge 1 - \alpha \implies k \ge (n + 1)(1 - \alpha)
\]

Since $k$ must be an integer:

\[
k = \left\lceil (n + 1)(1 - \alpha) \right\rceil
\]

Because only $n$ calibration scores are available ($s_{(1)}, \dots, s_{(n)}$), the maximum possible finite order statistic that can be chosen from the sample is $s_{(n)}$ ($k = n$). If $k > n$, it is mathematically impossible to guarantee $1 - \alpha$ coverage from $n$ calibration samples:

\[
k > n \iff \lceil (n + 1)(1 - \alpha) \rceil > n \iff (n + 1)(1 - \alpha) > n - 1 + \epsilon \iff n < \left\lceil \frac{1}{\alpha} - 1 \right\rceil
\]

For nominal $90\%$ coverage ($\alpha = 0.10$):

\[
n_{\text{min}} = \left\lceil \frac{1}{0.10} - 1 \right\rceil = \lceil 10 - 1 \rceil = 9
\]

For any sample size $n < 9$ at $\alpha = 0.10$, finite-sample distribution-free coverage of $90\%$ cannot be constructed from the data without external assumptions.

---

## 3. Mathematical Verification Across Calibration Sample Sizes

We independently evaluate $k = \lceil (n + 1)(1 - \alpha) \rceil$, the 0-based array index, the empirical quantile level, and the true finite-sample coverage guarantee across the required test matrix:

| $n$ | $\alpha$ | Nominal Coverage | Exact $(n+1)(1-\alpha)$ | Conformal Index $k$ | Index vs $n$ | Empirical Level ($k/n$) | True Guarantee ($k/(n+1)$) | Implementation Behavior | Mathematical Verdict |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | 0.10 | 90% | 0.90 | 1 | $1 > 0$ | Undefined | 100.0% | Returns `float('inf')` | **CORRECT** |
| **1** | 0.10 | 90% | 1.80 | 2 | $2 > 1$ | 2.000000 | 100.0% | Returns `float('inf')` | **CORRECT** |
| **5** | 0.10 | 90% | 5.40 | 6 | $6 > 5$ | 1.200000 | 100.0% | Returns `float('inf')` | **CORRECT** |
| **8** | 0.10 | 90% | 8.10 | 9 | $9 > 8$ | 1.125000 | 100.0% | Returns `float('inf')` | **CORRECT** |
| **9** | 0.10 | 90% | 9.00 | 9 | $9 \le 9$ | 1.000000 | **90.00%** | Returns $s_{(9)}$ (`q = scores[8]`) | **CORRECT (Boundary)** |
| **30** | 0.10 | 90% | 27.90 | 28 | $28 \le 30$ | 0.933333 | **90.32%** | Returns $s_{(28)}$ (`q = scores[27]`) | **CORRECT** |
| **450**| 0.10 | 90% | 405.90| 406 | $406 \le 450$| 0.902222 | **90.02%** | Returns $s_{(406)}$ (`q = scores[405]`) | **CORRECT** |
| **450**| 0.05 | 95% | 428.45| **429** | $429 \le 450$| 0.953333 | **95.12%** | Returns $s_{(429)}$ (`q = scores[428]`) | **CORRECT** |

---

## 4. Reconciliation of $n=450, \alpha=0.05$ Derivation

An informal test matrix in early project planning stated `Expected k: 428` for $n=450, \alpha=0.05$. We performed an independent mathematical audit of this discrepancy:

1. **Evaluation of $k=428$:**
   \[
   \frac{k}{n + 1} = \frac{428}{450 + 1} = \frac{428}{451} \approx 0.949002\dots = 94.90\%
   \]
   Setting $k = 428$ yields a coverage guarantee of $94.90\%$, which is **strictly less than the required $95.0\%$ coverage** ($1 - \alpha = 0.95$). Using $k=428$ either originates from neglecting the $+1$ correction ($\lceil 450 \times 0.95 \rceil = 428$) or from truncating/flooring instead of taking the ceiling.
2. **Evaluation of $k=429$:**
   \[
   (n + 1)(1 - \alpha) = 451 \times 0.95 = 428.45 \implies k = \lceil 428.45 \rceil = 429
   \]
   \[
   \frac{k}{n + 1} = \frac{429}{451} \approx 0.951219\dots = 95.12\% \ge 95.0\%
   \]
3. **Audit Finding:**
   The remediated implementation in `GroupConformalPredictor`:
   ```python
   k = math.ceil((n + 1) * (1.0 - alpha))
   ```
   evaluates to exactly `k = 429`. This is mathematically exact and satisfies the fundamental conformal coverage lower bound.

---

## 5. Elimination of Pre-Remediation Clamping Defect

In the pre-remediation implementation on `main`, the quantile logic contained:
```python
# FLAWED PRE-REMEDIATION CODE:
idx = min(len(sorted_scores) - 1, math.ceil((n + 1) * (1.0 - alpha)) - 1)
```
This clamping artificially forced $k$ down to $n$ whenever $k > n$.
For example, with $n=1$ and $\alpha=0.10$:
- Theoretical $k = 2$.
- The code clamped `idx` to $0$ ($k=1$), returning $s_{(1)}$.
- The true finite-sample coverage was $\frac{1}{1 + 1} = 50\%$, yet the system reported to consumers that 90% confidence had been attained.

The remediated code in `GroupConformalPredictor._compute_group_quantile`:
```python
# REMEDIATED MATHEMATICALLY SOUND CODE:
k = math.ceil((n + 1) * (1.0 - alpha))
if k > n:
    return float("inf")
q_idx = k - 1
return float(sorted_scores[q_idx])
```
Now, whenever $k > n$, the function returns `float("inf")`. Downstream interval construction correctly recognizes that finite coverage cannot be guaranteed, setting `upper_bound_m3 = None` and `status = "INSUFFICIENT_CALIBRATION_DATA"`.

---

## 6. Algorithmic Edge-Case Verification

In `test_group_conformal_remediation.py`, the following tests explicitly exercise these mathematical boundary cases:
- `test_remediation_cp01_small_sample_boundary`: Verifies $n \in \{1, 5, 8\}$ returns `inf`, while $n=9$ returns finite score $s_{(9)}$.
- `test_remediation_cp01_quantile_formula_exactness`: Validates exact index mapping for $n=30$ ($k=28$) and $n=450$ ($k=406, 429$).
- `test_remediation_cp01_zero_samples`: Validates $n=0$ gracefully returns `inf` without division-by-zero or index error.

All mathematical properties are verified as sound, rigorous, and fully compliant with distribution-free conformal prediction theory.
