# Phase U7.4 — Audit Document 05: Production Call Paths, Regression Testing & Backward Compatibility

**Document ID:** `AQUA-AUDIT-U7.4-REGR`  
**Date:** 2026-11-15  
**Auditor:** Antigravity Autonomous Systems Engineering & Verification  
**Audit Target:** Commit `a76f410` on branch `fix/conformal-small-sample-remediation`  
**Mode:** STRICT READ-ONLY AUDIT  

---

## 1. Executive Summary

This document presents the complete production call-path tracing, backward compatibility assessment, regression test results, and cryptographic model artifact verification for commit `a76f410`.

Zero regressions were detected across the 872-test backend suite and the 95-test frontend suite. All model artifacts remain bit-for-bit identical with the pre-remediation baseline.

---

## 2. Production Call-Path Tracing

A comprehensive static analysis was conducted across `backend/app/` to trace all invocations of conformal prediction components.

### 2.1 Component Usage Inventory

| Component | Defining File | Invocations / Consumers | File & Line References | Notes |
|:---|:---|:---|:---|:---|
| `conformal_predictor` (singleton) | `app/ml/conformal_predictor.py` | `app/api/agronomy_routes.py` | Lines 85–90 | Active production singleton used by REST API |
| `ConformalPredictor` (class) | `app/ml/conformal_predictor.py` | `app/ml/group_conformal.py` | Lines 38, 126 | Instantiated as baseline fallback within group predictor |
| `GroupConformalPredictor` (class) | `app/ml/group_conformal.py` | `tests/test_group_conformal.py`<br>`tests/test_group_conformal_remediation.py` | Lines 7, 18 (`test_group_conformal.py`)<br>Lines 8, 14, 28, 48, 62, 77, 90, 102 (`remediation`) | Used in repeated cross-validation and unit tests |
| `group_conformal_predictor` (singleton) | `app/ml/group_conformal.py` | Module export | Line 233 (`group_conformal.py`) | Exported singleton available for group-calibrated flows |
| `_compute_conformal_quantile` | `app/ml/group_conformal.py` | Internal `calibrate()` | Lines 111, 122 (`group_conformal.py`) | Evaluates exact discrete order statistics |
| `_finite_sample_order_statistic_index` | `app/ml/group_conformal.py` | `_finite_sample_quantile_level`, `_compute_conformal_quantile` | Lines 68, 84 (`group_conformal.py`) | Core order statistic calculator |
| `_finite_sample_quantile_level` | `app/ml/group_conformal.py` | Unit tests | Lines 10, 16, 32, 49, 58, 64 (`remediation.py`) | Public helper for quantile level calculation |

### 2.2 Key Findings from Call-Path Audit
1. **REST Endpoint Implementation:** The active endpoint `/api/v1/predictions/conformal-interval` directly calls `conformal_predictor.predict_interval()`.
2. **Static Global Threshold Stability:** The static normalized quantile $\hat{q}_{\text{norm}} = 25.6610\text{ m}^3$ derived from validation split ($N=450$) remains unchanged.
3. **No Caller Bypasses Calculations:** There are no alternate or legacy functions calculating conformal quantiles outside the audited classes.

---

## 3. Backward Compatibility Audit

### 3.1 Field-by-Field Compatibility Matrix

| Field | In Pre-Remediation Response? | In Remediated Response? | Type | Breaking Risk? | Compatibility Verdict |
|:---|:---:|:---:|:---|:---:|:---:|
| `predicted_demand_m3` | Yes | Yes | `float` | None | **100% Compatible** |
| `lower_bound_m3` | Yes | Yes | `float` | None | **100% Compatible** |
| `upper_bound_m3` | Yes | Yes | `float` or `null` | None (null on inf) | **100% Compatible** |
| `interval_width_m3` | Yes | Yes | `float` or `null` | None (null on inf) | **100% Compatible** |
| `confidence_level` | Yes | Yes | `float` | None | **100% Compatible** |
| `is_critical_stage` | Yes | Yes | `bool` | None | **100% Compatible** |
| `method` | Yes | Yes | `str` | None | **100% Compatible** |
| `interpretation` | Yes | Yes | `str` | None | **100% Compatible** |
| `crop_type` | No | Yes (Additive) | `Optional[str]` | None | **100% Compatible** |
| `coverage_type` | No | Yes (Additive) | `str` | None | **100% Compatible** |
| `group_conditional_guarantee` | No | Yes (Additive) | `bool` | None | **100% Compatible** |
| `calibration_source` | No | Yes (Additive) | `Optional[str]` | None | **100% Compatible** |
| `calibration_sample_size` | No | Yes (Additive) | `int` | None | **100% Compatible** |
| `fallback_reason` | No | Yes (Additive) | `Optional[str]` | None | **100% Compatible** |
| `status` | No | Yes (Additive) | `str` | None | **100% Compatible** |

Existing clients expecting the original eight keys receive them with unchanged types and semantics under normal operation. New metadata fields are strictly additive.

---

## 4. Independent Regression Test Execution

All tests were executed without modifying tests or configuration.

### 4.1 Backend Test Results
- **Command:** `python -m pytest -q`
- **Result:** **872 passed, 4 warnings in 32.56s**
- **Regressions:** **0**
- **Failure Count:** **0**

### 4.2 Frontend Test Results
- **Command:** `npm test -- --run`
- **Runner:** Vitest v5.0.1
- **Result:** **95 passed (100%) across 12 test files in 10.63s**
- **Regressions:** **0**

### 4.3 Production Build Results
- **Command:** `npm run build` (`tsc -b && vite build`)
- **Result:** **SUCCESS in 1.07s**
- **TypeScript Errors:** **0**

---

## 5. Model Artifact Cryptographic Integrity (SHA-256)

Every model file in `backend/data/models/` was independently hashed:

```text
encoders.joblib                              -> BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD (MATCH)
rf_model.joblib                              -> 84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75 (MATCH)
xgb_model.joblib                             -> 0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56 (MATCH)
baseline_metrics_phase_b.json                -> 32B08EF9E1E07E72A4A6410AFED7E495247C5A1278528BE2B94A40FDC8700350 (MATCH)
data_leakage_audit_phase_b.json              -> DF6C32E8A8D216A67A76AE1AD3CEC308EAD768720FE1173523AB002FFE855C6B (MATCH)
evaluation_results.json                      -> 85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7 (MATCH)
phase_d_simulation_results.json              -> A27FB4434C21DD5722FD08BB004978CA157255AF7DCBB82BDF0F7B3096C87B6F (MATCH)
phase_e_repeated_cv.json                     -> 6E1AB5A31C1E85CA9542F15D96B85419738C1CE5823B9124B45FFACC9107F20F (MATCH)
allocation_strategy_comparison_phase_c.json  -> C914B4354F54C8C0B8E33319A746DE83F95A473F3CE6FE29CF4FA7D66F94BE2B (MATCH)
.gitkeep                                     -> 3512F2C82D4788DD90543E11D22A8021F7014FA3C0289888AB1C8580962311BD (MATCH)
```

No model retraining, artifact replacement, or data leakage occurred.
