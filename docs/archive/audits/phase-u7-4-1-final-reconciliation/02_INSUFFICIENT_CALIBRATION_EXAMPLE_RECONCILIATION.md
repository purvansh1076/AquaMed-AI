# Phase U7.4.1 — Audit Document 02: Reconciliation of the n=450 Insufficient-Calibration Example

**Document ID:** `AQUA-AUDIT-U7.4.1-N450-RECON`  
**Date:** 2026-11-15  
**Auditor:** Antigravity Autonomous Systems Engineering & Verification  
**Audit Target:** Commit `a76f410` on branch `fix/conformal-small-sample-remediation`  
**Base Commit:** `origin/main` at `f4d573d42929aca616c9f3f72b084f5e3514673d`  
**Mode:** STRICT READ-ONLY AUDIT  

---

## 1. Executive Summary

During Phase U7.4, an example payload was presented in Section 3 showing an unavailable interval with `"status": "INSUFFICIENT_CALIBRATION_DATA"`, `"upper_bound_m3": null`, and `"calibration_sample_size": 450`.

Because a calibration sample size of $N=450$ at $\alpha=0.10$ requires order statistic index $k = \lceil 451 \times 0.90 \rceil = 406 \le 450$, $N=450$ observations are mathematically **more than sufficient** to compute a finite nonconformity quantile.

This investigation reconciled the discrepancy:
1. The reported payload was **an artificially forced test harness artifact**, created specifically to probe the wire-level JSON serialization of `float('inf')` through Starlette and FastAPI.
2. In naturally occurring production usage, the static global endpoint `conformal_predictor` operates with $\hat{q}_{\text{norm}} = 25.6610\text{ m}^3$ derived from the $N=450$ validation split and **always yields `status: "SUCCESS"` with finite bounds**.
3. In dynamic group calibration (`GroupConformalPredictor`), when insufficient calibration naturally occurs ($n < \frac{1-\alpha}{\alpha}$), the reported `calibration_sample_size` accurately reflects the small sample count ($n \in \{0, \dots, 8\}$), not 450.
4. The static global endpoint path and the dynamic group-calibration path were conflated in the presentation of the U7.4 serialization test.

---

## 2. Mathematical Fact Verification

For nominal confidence $1 - \alpha = 0.90$ ($\alpha = 0.10$):
- **Theoretical Lower Bound on Sample Size:**
  $$
  n \ge \frac{1-\alpha}{\alpha} = \frac{0.90}{0.10} = 9
  $$
- **Evaluation at $N = 450$:**
  $$
  k^* = \lceil(450 + 1)(1 - 0.10)\rceil = \lceil 451 \times 0.90 \rceil = \lceil 405.90 \rceil = 406
  $$
- **Theoretical Coverage of Order Statistic $S_{(406)}$:**
  $$
  \mathbb{P}(S_{451} \le S_{(406)}) = \frac{406}{451} \approx 90.0222\% \ge 90.0\%
  $$

Because $k^* = 406 \le 450$, a finite discrete order statistic strictly exists within a sample of 450 points. A dataset with $N=450$ valid observations can **never** naturally produce an insufficient-calibration state under standard split conformal prediction at $\alpha=0.10$.

---

## 3. Investigation of the U7.4 Test Setup

### 3.1 How the Example was Generated
In the Phase U7.4 audit runner (`scratch/phase_u7_4_audit_runner.py`), the test harness investigated Section 3 ("Critical API serialization audit") by testing what happens when the internal threshold is `float('inf')`.

The test harness executed:
```python
# Deliberately force an infinite threshold on the global singleton:
from app.ml.conformal_predictor import conformal_predictor
orig_q_norm = conformal_predictor.q_norm
try:
    conformal_predictor.q_norm = float("inf")
    resp_inf = client.post("/api/v1/predictions/conformal-interval", json=normal_payload, headers=auth_headers)
    ...
finally:
    conformal_predictor.q_norm = orig_q_norm
```

In `backend/app/ml/conformal_predictor.py`:
- `self.calibration_sample_size` defaults to `450` (reflecting the historical validation split size).
- When `q_norm` was overridden to `float('inf')`, lines 94–106 executed:
  ```python
  if not np.isfinite(q_val):
      return {
          "predicted_demand_m3": round(point_prediction_m3, 2),
          "lower_bound_m3": 0.0,
          "upper_bound_m3": float("inf"),
          "interval_width_m3": float("inf"),
          ...
          "calibration_sample_size": self.calibration_sample_size,  # Retained static 450
          "status": "INSUFFICIENT_CALIBRATION_DATA",
      }
  ```
The test harness demonstrated that if an infinite threshold were present, it serializes safely to JSON `null`. However, presenting this response in the U7.4 report without explicitly documenting that `q_norm = float('inf')` was artificially injected created the false impression that $N=450$ was insufficient.

---

## 4. Separation of Production Paths

AquaMedi AI contains two distinct conformal prediction paths that must not be conflated:

| Architecture Dimension | Path A: Static Global Endpoint (`ConformalPredictor`) | Path B: Dynamic Stratified Engine (`GroupConformalPredictor`) |
|:---|:---|:---|
| **Location** | `backend/app/ml/conformal_predictor.py` | `backend/app/ml/group_conformal.py` |
| **REST API Consumer** | `POST /api/v1/predictions/conformal-interval` | Module export (`group_conformal_predictor`); Phase E evaluation |
| **Calibration Mode** | Static pre-computed threshold ($\hat{q}_{\text{norm}} = 25.6610\text{ m}^3$) | Dynamic `calibrate(residuals, scales, groups)` |
| **Calibration Sample Size** | Fixed $N=450$ (from validation split) | Dynamic per-group $n_g$ and global pool $n_{\text{global}}$ |
| **Order Statistic Index** | Fixed $k=406$ ($406 \le 450$) | Evaluated dynamically via `_finite_sample_order_statistic_index(n, alpha)` |
| **Production Runtime State** | **Always `SUCCESS` (finite bounds)** | **`SUCCESS` if $n_g \ge 30$; `marginal_fallback` if $n_g < 30$** |
| **Natural Insufficiency Possibility** | None in production (requires manual code corruption) | Occurs naturally when calibration input has $n < 9$ |

---

## 5. Naturally Occurring Insufficient Calibration in Path B

When dynamic calibration in `GroupConformalPredictor` encounters an actual small sample ($n < 9$), the reported sample size is the actual observed count:

```python
gcp = GroupConformalPredictor(confidence_level=0.90)
residuals = np.array([5.0, 10.0, 15.0, 20.0, 25.0])  # n = 5
scales = np.ones_like(residuals)
groups = np.array(["cropA"] * 5)
gcp.calibrate(residuals, scales, groups)

iv = gcp.predict_interval(50.0, group="cropA")
```

**Observed Output:**
```json
{
  "predicted_demand_m3": 50.0,
  "lower_bound_m3": 0.0,
  "upper_bound_m3": null,
  "interval_width_m3": null,
  "confidence_level": 0.9,
  "coverage_type": "unavailable",
  "group_conditional_guarantee": false,
  "calibration_source": null,
  "calibration_sample_size": 5,
  "fallback_reason": "INSUFFICIENT_GROUP_SAMPLE_SIZE",
  "status": "INSUFFICIENT_CALIBRATION_DATA",
  "interpretation": "Calibration sample size is insufficient to guarantee 90% finite-sample coverage."
}
```
Here, `calibration_sample_size` is **`5`**, accurately reflecting that $n=5 < 9$, which correctly justifies `"status": "INSUFFICIENT_CALIBRATION_DATA"`.

---

## 6. Audit Conclusion

The $n=450$ inconsistency is **fully explained and reconciled**:
1. $N=450$ is mathematically sufficient and always yields finite intervals in production.
2. The U7.4 example was a forced test artifact created to verify Starlette JSON null encoding.
3. Natural insufficient calibration correctly reports the true small sample size ($n \le 8$).
