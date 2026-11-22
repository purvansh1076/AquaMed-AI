# Phase U7.2 — Audit Report 01: Finite-Sample Quantile Mathematical Review & Small-Sample Boundary Analysis

**Document ID:** `AQUA-AUDIT-U7.2-01`  
**Date:** 2026-11-15  
**Review Type:** Deep Mathematical & Statistical Integrity Audit  
**Component:** `backend/app/ml/group_conformal.py` (`GroupConformalPredictor._finite_sample_quantile_level`)  

---

## 1. Executive Summary

This report delivers a rigorous mathematical examination of the finite-sample quantile selection algorithm implemented in AquaMedi AI. Specifically, it audits how the system behaves when the finite-sample order-statistic index $k$ exceeds the available calibration sample size $n$.

**Key Finding:**  
The implementation in `GroupConformalPredictor._finite_sample_quantile_level(n, alpha)` contains a **mathematical implementation defect** for small calibration sample sizes where $n < \frac{1 - \alpha}{\alpha}$. Instead of returning an infinite threshold ($\hat{q} = \infty$), generating an unbounded interval, or safely abstaining, the code clamps `level` to $1.0$. This selects the sample maximum $s_{(n)}$, which yields empirical coverage of only $\frac{n}{n + 1} < 1 - \alpha$ while returning user-facing claims of a "Distribution-Free Finite-Sample Guarantee".

---

## 2. Theoretical Ground Truth: Split Conformal Finite-Sample Quantiles

In standard distribution-free split conformal prediction (Vovk et al., 2005; Lei et al., 2018; Angelopoulos & Bates, 2021):

Let $S_1, \dots, S_n$ be non-conformity calibration scores, assumed exchangeable with the test score $S_{n+1}$. The rank of $S_{n+1}$ among $\{S_1, \dots, S_n, S_{n+1}\}$ is uniformly distributed over $\{1, \dots, n + 1\}$.

To guarantee:
$$\mathbb{P}(S_{n+1} \le \hat{q}) \ge 1 - \alpha$$
the threshold $\hat{q}$ must be selected as the $k$-th smallest value (order statistic $S_{(k)}$) of the augmented set:
$$k = \lceil (n + 1)(1 - \alpha) \rceil$$

### 2.1 The Small-Sample Feasibility Condition
For a finite sample threshold to exist within the calibration set $\{S_{(1)}, \dots, S_{(n)}\}$, the order-statistic index $k$ cannot exceed the available sample count $n$:
$$k \le n \iff \lceil (n + 1)(1 - \alpha) \rceil \le n \iff n \ge \frac{1 - \alpha}{\alpha}$$

- **For $\alpha = 0.10$ ($90\%$ Target Confidence):**
  $$n \ge \frac{1 - 0.10}{0.10} = \frac{0.9}{0.1} = 9$$
  At least **9 calibration samples** are required for a finite $90\%$ threshold to exist.
- **For $\alpha = 0.05$ ($95\%$ Target Confidence):**
  $$n \ge \frac{1 - 0.05}{0.05} = \frac{0.95}{0.05} = 19$$
  At least **19 calibration samples** are required for a finite $95\%$ threshold to exist.

### 2.2 Behavior When $k > n$ ($n < \frac{1-\alpha}{\alpha}$)
When $k = n + 1 > n$, the augmented sample rank requires $S_{(n+1)} = \infty$.
The true theoretical conformal prediction set is:
$$\hat{C}(X_{n+1}) = (-\infty, \infty)$$
or the algorithm must explicitly **abstain** by declaring that the calibration sample is too small to provide the requested coverage guarantee.

---

## 3. Code Inspection of Production Implementation

In `backend/app/ml/group_conformal.py` (lines 21–29):
```python
@staticmethod
def _finite_sample_quantile_level(n: int, alpha: float) -> float:
    # Standard split conformal finite-sample correction:
    # k = ceil((n + 1) * (1 - alpha)); level = k / n, capped at 1.0.
    if n <= 0:
        return 1.0
    import math
    level = math.ceil((n + 1) * (1.0 - alpha)) / n
    return min(1.0, max(0.0, level))
```

And during calibration (lines 35, 41):
```python
self.global_q = float(np.quantile(scores, self._finite_sample_quantile_level(len(scores), alpha)))
...
self.group_q[str(g)] = float(np.quantile(scores[mask], self._finite_sample_quantile_level(n_g, alpha)))
```

### 3.1 The Flaw: Capping at 1.0
When $n < \frac{1-\alpha}{\alpha}$:
1. $k = \lceil(n+1)(1-\alpha)\rceil > n$.
2. The code computes `level = k / n > 1.0`.
3. `min(1.0, level)` forces `level = 1.0`.
4. `np.quantile(scores, 1.0)` selects the maximum observed sample: $\hat{q} = \max(S_1, \dots, S_n) = S_{(n)}$.
5. What is the actual mathematical coverage of $S_{(n)}$?
   $$\mathbb{P}(S_{n+1} \le S_{(n)}) = \frac{n}{n + 1}$$

### 3.2 Mathematical Coverage Breakdown for Capped Quantiles ($\alpha = 0.10$):
| Calibration Size ($n$) | Theoretical $k$ | Code Level | Selected Statistic | Actual Theoretical Coverage | Claimed Confidence | Deficit |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | $1$ | $1.0$ | N/A | **$0.0\%$** | $90.0\%$ | $-90.0\%$ |
| **1** | $2$ | $1.0$ (capped) | $S_{(1)} = \max$ | **$50.0\%$** | $90.0\%$ | **$-40.0\%$** |
| **2** | $3$ | $1.0$ (capped) | $S_{(2)} = \max$ | **$66.67\%$** | $90.0\%$ | **$-23.33\%$** |
| **5** | $6$ | $1.0$ (capped) | $S_{(5)} = \max$ | **$83.33\%$** | $90.0\%$ | **$-6.67\%$** |
| **8** | $9$ | $1.0$ (capped) | $S_{(8)} = \max$ | **$88.89\%$** | $90.0\%$ | **$-1.11\%$** |
| **9** | $9$ | $1.0$ | $S_{(9)} = \max$ | **$90.00\%$** | $90.0\%$ | $0.0\%$ (Valid) |
| **10** | $10$ | $1.0$ | $S_{(10)} = \max$ | **$90.91\%$** | $90.0\%$ | $+0.91\%$ (Valid) |

---

## 4. Assessment Against Audit Criteria

Evaluating against the five potential behaviors specified in the audit charter:
1. **Returns an infinite threshold?** **NO.** It returns `float(np.quantile(scores, 1.0))`, which is finite.
2. **Produces an unbounded interval?** **NO.** It computes $[ \max(0, \hat{y} - \hat{q}s(A)), \hat{y} + \hat{q}s(A) ]$, which is bounded.
3. **Abstains safely?** **NO.** It generates a normal prediction dictionary with HTTP 200.
4. **Uses an explicitly documented fallback without claiming the guarantee?** **NO.** In `conformal_predictor.py` lines 92–96, the output payload claims:
   - `"method": "Split Conformal Prediction (Distribution-Free Finite-Sample Guarantee)"`
   - `"interpretation": "With 90% statistical confidence, actual field crop water requirement lies between..."`
5. **Incorrectly substitutes the maximum observed score?** **YES.** When $k > n$, it substitutes $S_{(n)}$, which mathematically under-covers the target confidence level.

---

## 5. Scope of Exposure in AquaMedi AI

- **Global Calibration:** In `candidate_trainer.py`, the global validation split has $n = 450 \ge 9$. Here $k = 406 \le 450$. Capping does not trigger in the pre-calibrated global model.
- **Group Calibration:** In `group_conformal.py`, `min_group_size = 30`. For $\alpha = 0.10$, $30 \ge 9$, so capping does not trigger for $\alpha=0.10$. However:
  - If a caller instantiates `GroupConformalPredictor(confidence_level=0.97)` ($\alpha = 0.03$), the minimum $n$ required is $\lceil 0.97/0.03 \rceil = 33 > 30$. Groups with $n \in [30, 32]$ will trigger capping at 1.0 and fail the $97\%$ guarantee.
  - If a caller invokes `_finite_sample_quantile_level(n, alpha)` directly on small datasets ($n < 9$), the returned level violates finite-sample coverage.

---

## 6. Verdict

**Finding:** **IMPLEMENTATION DEFECT IDENTIFIED (DEFECT ID: CP-01)**  
`GroupConformalPredictor._finite_sample_quantile_level` incorrectly clamps `level` to $1.0$ when $k > n$, substituting the sample maximum and producing bounded intervals that violate the theoretical finite-sample coverage guarantee for small $n$.
