# Phase U7.2 — Audit Report 04: Conformal Coverage Claims & Truthfulness Review

**Document ID:** `AQUA-AUDIT-U7.2-04`  
**Date:** 2026-11-15  
**Review Type:** Scientific Claim Audit & Public Interface Analysis  
**Components:** `backend/app/api/agronomy_routes.py`, `backend/app/ml/conformal_predictor.py`, Frontend UI  

---

## 1. Executive Summary

This report audits the statistical claims presented in user-facing API responses, docstrings, frontend dashboards, and previous audit dossiers regarding AquaMedi AI's conformal prediction intervals.

The audit establishes that while global marginal coverage on the 450-sample calibration set is mathematically and empirically valid ($90.47\%$), the unconditional assertion of a "Distribution-Free Finite-Sample Guarantee" across all subgroups, fallbacks, and boundary conditions is scientifically overbroad and misleading.

---

## 2. Review of User-Facing Claims & Code Disclosures

### 2.1 API Response Dictionary (`backend/app/ml/conformal_predictor.py`)
Lines 92–96 return:
```python
"method": "Split Conformal Prediction (Distribution-Free Finite-Sample Guarantee)",
"interpretation": (
    f"With {int(self.confidence_level * 100)}% statistical confidence, "
    f"actual field crop water requirement lies between {lower} m³ and {upper} m³."
)
```
- **Analysis:** This statement is returned unconditionally, regardless of whether:
  - The parcel belongs to an unseen group.
  - The parcel's group had $n_g < 30$ samples and fell back to `global_q`.
  - The parcel is an extreme outlier.

### 2.2 Endpoint Architecture (`backend/app/api/agronomy_routes.py`)
In `backend/app/api/agronomy_routes.py`:
- Endpoint `/predictions/conformal-interval` directly calls `conformal_predictor.predict_interval()`.
- It does **not** call `GroupConformalPredictor` at all. It uses a static pre-computed global normalized quantile:
  $$\hat{q}_{\text{norm}} = 25.6610\text{ m}^3$$
- **Finding:** In the live production API, all intervals are generated from the **single global normalized quantile**. Group-conditional stratification is currently confined to offline candidate models and Phase E scripts.

---

## 3. Truth-in-Science Claim Evaluation Matrix

| Claim in Documentation / UI | Technical Reality | Scientific Truthfulness |
| :--- | :--- | :--- |
| *"Distribution-Free Guarantee on Global Test Set"* | Evaluated on $N=450$ validation split; yields $90.47\%$ empirical coverage on held-out test split. | **TRUTHFUL** |
| *"Guaranteed 90% confidence for any crop/soil group"* | Small groups ($n_g < 30$) fall back to `global_q` and achieve as low as $27.1\%$ empirical coverage under high variance. | **FALSE / OVERSTATED** |
| *"Finite-Sample Guarantee for any sample size $n$"* | When $n < 9$ for $\alpha=0.10$, the code clamps to $1.0$, producing coverage as low as $50.0\%$. | **FALSE / OVERSTATED** |
| *"Field crop water requirement lies between lower and upper bounds"* | Evaluated strictly on synthetic simulation water balance equations, not real-world in-situ field sensor measurements. | **QUALIFIED / SYNTHETIC ONLY** |

---

## 4. Reconciled Claim Terminology

To align public statements with rigorous statistical science:

1. **Clarify Marginal vs. Conditional:**  
   Replace:
   > *"Distribution-Free Finite-Sample Guarantee"*  
   With:
   > *"Finite-sample marginal coverage guarantee on calibrated simulation distribution under exchangeability."*
2. **Explicit Fallback Notification:**  
   When an unknown or small group receives an interval from `global_q`, the response must include:
   ```json
   {
     "stratum_calibrated": false,
     "coverage_guarantee_type": "marginal_population",
     "note": "Stratum-specific calibration data was unavailable or below sample threshold; interval reflects catchment-wide marginal distribution."
   }
   ```
3. **Synthetic Grounding:**  
   User-facing dashboards must state:
   > *"Prediction intervals reflect calibrated synthetic FAO-56 simulations and have not been validated against live regional field sensors."*

---

## 5. Verdict

**Claim Review Status: DOCUMENTATION & USER-FACING CLAIM OVERSTATEMENT IDENTIFIED**  
Unconditional finite-sample and group-conditional guarantees are claimed in output payloads where only marginal population coverage on synthetic simulations actually exists.
