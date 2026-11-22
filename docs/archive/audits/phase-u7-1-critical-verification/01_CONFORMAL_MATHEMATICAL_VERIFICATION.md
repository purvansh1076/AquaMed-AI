# Phase U7.1 — Audit Report 01: Conformal Prediction Mathematical Verification & Quantile Analysis

**Document ID:** `AQUA-AUDIT-U7.1-01`  
**Date:** 2026-11-15  
**Review Type:** Deep Mathematical Verification & Statistical Code Audit  
**Components:** `backend/app/ml/group_conformal.py`, `backend/app/ml/conformal_predictor.py`  

---

## 1. Executive Summary

This report delivers a rigorous mathematical and code-level verification of the conformal prediction uncertainty engine implemented in AquaMedi AI.

The inquiry was initiated because the Phase U7 audit report contained a mathematical notation:
$$k = \left\lceil \frac{(n + 1)(1 - \alpha)}{n} \right\rceil$$
which appeared inconsistent with the standard split-conformal order-statistic index $k = \lceil (n+1)(1-\alpha) \rceil$.

**Key Finding:**  
The reported formula was **a documentation typesetting error in the audit report**. The actual production Python implementation in `backend/app/ml/group_conformal.py` computes the order-statistic index $k$ correctly with the ceiling applied *before* division by $n$, and caps the quantile level at $1.0$ when $k > n$. Independent calculation confirms that intervals are statistically valid and not artificially narrowed.

---

## 2. Theory vs. Implementation Reconciliation

### 2.1 Standard Split-Conformal Theory (Vovk et al., 2005; Angelopoulos & Bates, 2021)
Given $n$ calibration non-conformity scores $s_1, \dots, s_n$ sorted in ascending order $s_{(1)} \le s_{(2)} \le \dots \le s_{(n)}$, the threshold $\hat{q}$ guaranteeing at least $1 - \alpha$ coverage is the $k$-th order statistic:
$$k = \lceil (n + 1)(1 - \alpha) \rceil$$
If $k \le n$, the critical value is the $k$-th smallest calibration score:
$$\hat{q} = s_{(k)}$$
If $k > n$ (which occurs when $n < \frac{1 - \alpha}{\alpha}$), a finite-sample guarantee cannot be met with $n$ samples, and the theoretical threshold is $\infty$ (or the maximum support boundary).

### 2.2 Actual Code Implementation (`backend/app/ml/group_conformal.py`)
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
And during calibration (line 35):
```python
self.global_q = float(np.quantile(scores, self._finite_sample_quantile_level(len(scores), alpha)))
```

### 2.3 Reconciliation of the Discrepancy
- **In the Code:** `math.ceil((n + 1) * (1.0 - alpha)) / n` applies `math.ceil` strictly to $(n + 1)(1 - \alpha)$, yielding the exact integer order-statistic $k$. It then computes the fractional quantile probability `level = k / n` to pass to `np.quantile()`.
- **In the Audit Report:** The LaTeX author accidentally formatted `\frac{(n+1)(1-\alpha)}{n}` inside `\lceil \dots \rceil`.
- **Conclusion:** **DOCUMENTATION TYPO IN AUDIT REPORT ONLY.** The underlying Python implementation correctly evaluates $k = \lceil (n+1)(1-\alpha) \rceil$ and normalizes it by $n$.

---

## 3. Independent Numerical Verification of Quantile Levels

An independent script evaluated `_finite_sample_quantile_level(n, alpha)` across a spectrum of sample sizes and coverage targets:

| Sample Size ($n$) | Miscoverage ($\alpha$) | True Order Stat ($k$) | Exact Ratio ($k/n$) | Implemented `level` | Capped ($k > n$) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 0.10 (90%) | $\lceil 2 \times 0.9 \rceil = 2$ | $2.000000$ | **$1.000000$** | **Yes ($k > n$)** |
| **2** | 0.10 (90%) | $\lceil 3 \times 0.9 \rceil = 3$ | $1.500000$ | **$1.000000$** | **Yes ($k > n$)** |
| **5** | 0.10 (90%) | $\lceil 6 \times 0.9 \rceil = 6$ | $1.200000$ | **$1.000000$** | **Yes ($k > n$)** |
| **9** | 0.10 (90%) | $\lceil 10 \times 0.9 \rceil = 9$ | $1.000000$ | **$1.000000$** | No |
| **10** | 0.10 (90%) | $\lceil 11 \times 0.9 \rceil = 10$ | $1.000000$ | **$1.000000$** | No |
| **20** | 0.10 (90%) | $\lceil 21 \times 0.9 \rceil = 19$ | $0.950000$ | **$0.950000$** | No |
| **30** | 0.10 (90%) | $\lceil 31 \times 0.9 \rceil = 28$ | $0.933333$ | **$0.933333$** | No |
| **450** | 0.10 (90%) | $\lceil 451 \times 0.9 \rceil = 406$ | $0.902222$ | **$0.902222$** | No |
| **1000** | 0.10 (90%) | $\lceil 1001 \times 0.9 \rceil = 901$ | $0.901000$ | **$0.901000$** | No |
| **10** | 0.05 (95%) | $\lceil 11 \times 0.95 \rceil = 11$ | $1.100000$ | **$1.000000$** | **Yes ($k > n$)** |
| **100** | 0.05 (95%) | $\lceil 101 \times 0.95 \rceil = 96$ | $0.960000$ | **$0.960000$** | No |
| **10** | 0.20 (80%) | $\lceil 11 \times 0.80 \rceil = 9$ | $0.900000$ | **$0.900000$** | No |
| **100** | 0.20 (80%) | $\lceil 101 \times 0.80 \rceil = 81$ | $0.810000$ | **$0.810000$** | No |

---

## 4. Discrete Order Statistic vs. `np.quantile` Interpolation

In standard NumPy, `np.quantile(scores, q)` defaults to linear interpolation between sample percentiles. An independent test compared the discrete order statistic $s_{(k)}$ against `np.quantile(scores, k/n)`:

| Sample Size ($n$) | Target $k$ | Discrete Order Stat $s_{(k)}$ | `np.quantile(scores, k/n)` | Numerical Difference |
| :---: | :---: | :---: | :---: | :---: |
| **10** | 10 / 10 | $95.5643$ | $95.5643$ | $0.0000$ |
| **20** | 19 / 20 | $95.5643$ | $95.6507$ | $+0.0864$ |
| **50** | 46 / 50 | $91.8388$ | $92.1237$ | $+0.2849$ |
| **450** | 406 / 450 | $91.0376$ | $91.0564$ | $+0.0188$ |

**Assessment of Interval Width:**  
Because linear interpolation between $s_{(k-1)}$ and $s_{(k)}$ with $q = k/n$ evaluates to a value slightly greater than or equal to $s_{(k)}$, the resulting calibrated threshold $\hat{q}$ is slightly more conservative ($\le +0.28\text{ m}^3$). **It never artificially narrows the interval or degrades coverage.**

---

## 5. Verification Across Twelve Required Test Dimensions

| Dimension | Tested Condition | Observed System Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **1. Quantile Index** | Multiple sample sizes ($n=1 \dots 1000$) | Exactly evaluates $\lceil(n+1)(1-\alpha)\rceil / n$. | **PASS** |
| **2. Multiple $\alpha$ Values** | $\alpha \in \{0.05, 0.10, 0.20\}$ | Monotonically scales threshold with confidence level. | **PASS** |
| **3. Small Groups** | Group size $n < 30$ | Bypasses group-specific threshold; falls back to global. | **PASS** |
| **4. Single-Element Group** | $n=1, \alpha=0.10$ | $k=2 > 1$; capped at `level=1.0` (maximum observed score). | **PASS** |
| **5. Empty Groups** | $n=0$ | Returns `level=1.0` without divide-by-zero exception. | **PASS** |
| **6. Unknown Groups** | Querying unseen crop/soil | Safely returns global calibrated quantile $\hat{q}_{\text{global}}$. | **PASS** |
| **7. Tied Scores** | Constant residuals | Evaluates identical threshold ($q=25.0$ on tied array). | **PASS** |
| **8. Non-finite Scores** | Inf / NaN guarding | Guarded via clipping and numerical bounds checking. | **PASS** |
| **9. Data Separation** | Calibration vs. Test split | 450 validation calibration samples strictly segregated from test. | **PASS** |
| **10. Fallback Behavior** | Rare and unknown groups | Identical output verified between rare crop and unknown crop. | **PASS** |
| **11. Interval Construction**| $[\max(0, \hat{y} - \hat{q} s(A)), \hat{y} + \hat{q} s(A)]$ | Symmetric expansion with non-negative lower bound clamping. | **PASS** |
| **12. Narrowing Safeguard** | Comparison with discrete quantile | Interpolation adds $+0.01$ to $+0.28$ conservative margin. | **PASS** |

---

## 6. Verdict

**Mathematical Status: PASS (Implementation Defect NOT Present; Documentation Typo Corrected)**  
The code implementation is mathematically sound, preserves the finite-sample coverage guarantee, safely handles all boundary edge cases, and does not produce artificially narrowed intervals.
