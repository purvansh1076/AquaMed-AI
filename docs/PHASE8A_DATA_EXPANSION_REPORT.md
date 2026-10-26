# AquaMediAI Phase 8A — Historical Data Verification & Multi-Year Expansion Audit Report

**Date**: October 2026  
**Auditor**: Senior Data Engineer & Agricultural ML Validation Engineer  
**Pilot Region**: Ahmednagar, Maharashtra, India (Pravara-Mula Canal Command, Centroid: 19.09° N, 74.74° E, Elevation: 540 m)  
**Primary Target**: Theoretical daily net crop-water requirement ($m^3/\text{day}$)  
**Decision / Status**: `GO_FOR_MULTI_YEAR_EVALUATION` (Data Preparation Phase Complete)

---

## 1. Discrepancy Diagnosis & Root Cause Analysis

### 1.1 The Reported Discrepancy
In Phase 7, the candidate models were trained on a dataset covering only **365 unique dates in 2023**, despite terminal execution logs showing an attempt to download NASA POWER agroclimatology data for **2021–2022**.

### 1.2 Forensics & Evidence
A forensic investigation into the repository filesystem and process logs established the following facts:

1. **Terminal Command Attempted in Phase 7**:
   A background task (`task-824`) attempted to execute:
   ```python
   c.fetch_daily_weather('20210101', '20221231', save_raw=True)
   ```
2. **Terminal Failure Recorded**:
   The HTTP request failed at `backend/app/data/nasa_power_client.py:148` with:
   ```text
   httpcore.ConnectError: [Errno 11001] getaddrinfo failed
   httpx.ConnectError: [Errno 11001] getaddrinfo failed
   ```
   This error represents a transient DNS resolution failure on the local Windows networking stack.
3. **Absence of Raw Payload**:
   Because `httpx.get` raised an uncaught `ConnectError`, execution never reached line 154 (which writes the raw JSON file to disk).
4. **No Filesystem Persistence**:
   Inspection of `backend/data/raw/` confirmed only `nasa_power_maharashtra_ahmednagar_20230101_20231231.json` was present. The 2021–2022 data was never downloaded, never saved elsewhere, and was therefore never incorporated into `clean_daily_weather_maharashtra_ahmednagar.csv`.
5. **Mitigation Implemented in Phase 8A**:
   - Added **bounded retries (3 attempts)** with exponential backoff on `(httpx.TransportError, httpx.TimeoutException, httpx.HTTPStatusError)`.
   - Added **disk-caching verification**: cached JSON files in `backend/data/raw/` are loaded immediately to avoid redundant API queries.
   - Added automated multi-year orchestration: `fetch_multi_year_weather(years, save_raw, use_cache)`.

---

## 2. Expanded Multi-Year Weather Data Inventory (2021–2025)

The NASA POWER agroclimatology service was successfully queried for the complete 5-year span from **2021-01-01 to 2025-12-31**:

### 2.1 Yearly Meteorological Coverage Breakdown

| Calendar Year | Date Range (YYYY-MM-DD) | Days Available | Expected Days | Completeness | Raw File Path | Raw Size | Missing Cells |
| :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| **2021** | 2021-01-01 to 2021-12-31 | 365 | 365 | **100.0%** | `backend/data/raw/nasa_power_maharashtra_ahmednagar_20210101_20211231.json` | 71,996 B | 0 |
| **2022** | 2022-01-01 to 2022-12-31 | 365 | 365 | **100.0%** | `backend/data/raw/nasa_power_maharashtra_ahmednagar_20220101_20221231.json` | 71,953 B | 0 |
| **2023** | 2023-01-01 to 2023-12-31 | 365 | 365 | **100.0%** | `backend/data/raw/nasa_power_maharashtra_ahmednagar_20230101_20231231.json` | 71,935 B | 0 |
| **2024** | 2024-01-01 to 2024-12-31 | 366 | 366 (leap) | **100.0%** | `backend/data/raw/nasa_power_maharashtra_ahmednagar_20240101_20241231.json` | 72,157 B | 0 |
| **2025** | 2025-01-01 to 2025-12-31 | 365 | 365 | **100.0%** | `backend/data/raw/nasa_power_maharashtra_ahmednagar_20250101_20251231.json` | 71,918 B | 0 |
| **Total** | **2021-01-01 to 2025-12-31** | **1,826** | **1,826** | **100.0%** | **5 Raw JSON Payloads Preserved** | **359,959 B** | **0** |

- **Processed Multi-Year File**: `backend/data/processed/clean_daily_weather_maharashtra_ahmednagar_2021_2025.csv` (1,826 rows, 259,628 bytes).
- **Original 2023 Processed File**: `backend/data/processed/clean_daily_weather_maharashtra_ahmednagar.csv` remains completely preserved and untouched.

### 2.2 Variables & Physical Units

| Parameter Code | Agronomic Variable | Physical Units | Bounds / Quality Rule | Observed Pilot Range (2021–2025) |
| :--- | :--- | :---: | :---: | :---: |
| `T2M` | Mean daily air temperature at 2 m | °C | $-5.0 \le T \le 55.0$ | $13.88^\circ\text{C}$ to $36.71^\circ\text{C}$ |
| `T2M_MAX` | Daily maximum air temperature | °C | $T_{max} \ge T_{min}$ | $20.91^\circ\text{C}$ to $43.20^\circ\text{C}$ |
| `T2M_MIN` | Daily minimum air temperature | °C | $T_{min} \le T_{max}$ | $6.84^\circ\text{C}$ to $29.43^\circ\text{C}$ |
| `RH2M` | Mean daily relative humidity | % | $0.0 \le RH \le 100.0$ | $12.19\%$ to $98.15\%$ |
| `PRECTOTCORR` | Corrected gross precipitation | mm/day | $P \ge 0.0$ | $0.00\text{ mm}$ to $118.42\text{ mm}$ |
| `WS2M` | Wind speed at 2 m | m/s | $W \ge 0.1$ | $0.28\text{ m/s}$ to $7.82\text{ m/s}$ |
| `ALLSKY_SFC_SW_DWN` | Downward shortwave solar radiation | $MJ/m^2/\text{day}$ | $R_s \ge 0.0$ | $1.25\text{ MJ/m}^2$ to $28.94\text{ MJ/m}^2$ |
| `et0_fao56_mm_per_day` | FAO-56 Reference Evapotranspiration | mm/day | $ET_0 \ge 0.0$ | $1.74\text{ mm/day}$ to $9.21\text{ mm/day}$ |
| `effective_precipitation_mm` | USDA-SCS Effective Precipitation | mm/day | $P_{eff} \ge 0.0$ | $0.00\text{ mm}$ to $86.42\text{ mm}$ |

---

## 3. Rebuilt Agronomic Multi-Year Dataset (`candidate_v2_dataset.csv`)

The multi-year dataset was generated via `AgronomicDatasetBuilder` joining the 5-year weather record with `CropRegistry v1.0.0`:

- **Processed CSV**: `backend/data/processed/candidate_v2_dataset.csv` (1,714,248 bytes)
- **Manifest File**: `backend/data/processed/candidate_v2_manifest.json`
- **Total Records**: **4,882** multi-crop daily observations
- **Unique Calendar Dates**: **1,826** unique dates
- **Date Range**: **2021-01-01 to 2025-12-31**
- **Plot Area**: Canonical standard $1.0\text{ ha}$ (linear scaling verified: $V(k \cdot A) = k \cdot V(A)$)
- **Zero-Demand Fraction**: 11.8% (monsoon deluge events where effective rainfall exceeds crop evapotranspiration)
- **Mean Net Irrigation Requirement**: $28.56\text{ m}^3/\text{day}$
- **Maximum Daily Net Requirement**: $92.10\text{ m}^3/\text{day}$ (Peak sugarcane grand-growth during hot May Zaid season)

### 3.1 Records by Crop and Year

| Crop ID | 2021 | 2022 | 2023 | 2024 | 2025 | Total Records |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `sugarcane` | 365 | 365 | 365 | 366 | 365 | **1,826** |
| `cotton` | 170 | 170 | 170 | 170 | 170 | **850** |
| `wheat` | 121 | 121 | 121 | 122 | 121 | **606** |
| `groundnut` | 117 | 117 | 117 | 117 | 117 | **585** |
| `maize` | 107 | 107 | 107 | 107 | 107 | **535** |
| `soybean` | 96 | 96 | 96 | 96 | 96 | **480** |
| **Total per Year** | **976** | **976** | **976** | **978** | **976** | **4,882** |

---

## 4. Multi-Year Temporal Split Recommendations

With 5 complete calendar years, the dataset supports two defensible chronological partitioning strategies:

### Strategy A: Natural Multi-Year Out-of-Year Holdout (Recommended)
- **Training Set (Years 2021–2023, 3 complete years)**:
  - 2,928 multi-crop records across **1,095 unique dates** (2021-01-01 to 2023-12-31).
  - Encodes multi-year seasonal cycles and inter-annual monsoon variability.
- **Validation Set (Year 2024, 1 complete leap year)**:
  - 978 multi-crop records across **366 unique dates** (2024-01-01 to 2024-12-31).
  - Used for hyperparameter tuning and model selection.
- **Final Test Set (Year 2025, 1 complete future year)**:
  - 976 multi-crop records across **365 unique dates** (2025-01-01 to 2025-12-31).
  - Kept completely untouched during all candidate iterations; evaluates genuine out-of-year temporal generalization.

### Strategy B: Standard 70 / 15 / 15 Date-Grouped Split
- **Train (70% of unique dates)**: 3,206 records across 1,278 dates (2021-01-01 to 2024-07-01).
- **Validation (15% of unique dates)**: 850 records across 273 dates (2024-07-02 to 2025-03-31).
- **Test (15% of unique dates)**: 826 records across 275 dates (2025-04-01 to 2025-12-31).

---

## 5. Artifact Preservation & Hash Verification

In compliance with mandatory safety rules:
1. **Production Model Artifacts**: Checked and verified 100% identical:
   - `encoders.joblib`: `BDAA3F8E9332242E49D5FEEE737ADA7D908EF89F8ADCADCE5D5CBAF1B9FA32DD` (MATCH)
   - `evaluation_results.json`: `85C1972FBC5FD32BCD9E1305BDC49DC98D7DDF57BC68C6291CA3F7DD2BB2ECD7` (MATCH)
   - `rf_model.joblib`: `84D37E0D80CF37AA058ACAEC4FEF850C90A10F6C80000D260BEBC14DADD11D75` (MATCH)
   - `xgb_model.joblib`: `0B320F0730FA4C57863A4435C40139FA433CD248CD2991F915A5A657EFD97D56` (MATCH)
2. **Phase 7 Candidate Artifacts**: All files in `backend/data/models/candidate_v1/` remain untouched.
3. **Phase 7 Datasets**: `backend/data/processed/candidate_v1_dataset.csv` and `clean_daily_weather_maharashtra_ahmednagar.csv` remain intact.
4. **No Model Retraining**: No model was retrained or promoted in Phase 8A.

---

## 6. Offline Test Suite Execution

All 7 tests in `backend/tests/test_phase8a_historical_data.py` pass without internet dependencies:
- `test_parse_payload_and_leap_year`: **PASS** (verifies Feb 29 leap-day parsing and doy=60).
- `test_missing_value_imputation`: **PASS** (verifies `-999.0` replacement and linear interpolation).
- `test_cache_retrieval_avoids_network`: **PASS** (verifies disk cache prevents redundant HTTP requests).
- `test_bounded_retries_on_http_error`: **PASS** (verifies 2 retries on connection error before raising clean error).
- `test_multi_year_concatenation`: **PASS** (verifies deduplication and chronological ordering).
- `test_candidate_dataset_v2_manifest_integrity`: **PASS** (verifies 4,882 rows, 1,826 unique dates, 2021–2025).
- `test_production_and_phase7_candidate_hashes_unchanged`: **PASS** (verifies all cryptographic hashes match).

**Full Backend Pytest Suite**: **769 passed, 0 failed in 14.69s**.

---

## 7. Decision & Next Steps

### Verdict: `GO_FOR_MULTI_YEAR_EVALUATION`
With 5 complete calendar years (2021–2025; 1,826 unique dates; 4,882 multi-crop observations) successfully acquired, verified, and processed, multi-year out-of-year temporal evaluation is now fully defensible.
