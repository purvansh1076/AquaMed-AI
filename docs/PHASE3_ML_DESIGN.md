# AquaMediAI — Phase 3: Feature Engineering and ML Pipeline Redesign

**Document Version**: 3.0.0  
**Date**: October 2026  
**Auditor & Lead Data Scientist**: AquaMediAI Senior Engineering Team  

---

## 1. Audit of the Current Pipeline & Artifacts

### 1.1 Ingested Data Inventory vs. Model Training Requirements
Phase 2 successfully created an automated ingestion pipeline for NASA POWER daily agroclimatology observations. The ingested dataset (`backend/data/processed/clean_daily_weather_maharashtra_ahmednagar.csv`) contains **365 continuous days (year 2023)** of real meteorological data for the Ahmednagar pilot region ($19.09^\circ\text{ N}, 74.74^\circ\text{ E}$):
- `temperature_celsius` (daily mean, min, max)
- `humidity_percent`
- `rainfall_mm` & `effective_precipitation_mm`
- `wind_speed_m_per_s`
- `solar_radiation_mj_per_m2`
- `et0_fao56_mm_per_day` (calculated via FAO-56 Penman-Monteith)

### 1.2 The Missing Field Problem
While atmospheric forcing is genuine, the processed weather file contains:
- **No farm area**
- **No crop types or planting dates**
- **No soil profile measurements**
- **No observed farmer-level water extraction meter logs**

Consequently, any model trained to predict volumetric farm water demand ($\text{m}^3/\text{day}$) on this weather series must pair weather with **simulated farm profiles** and a **calculated target label**.

---

## 2. Feature Leakage & Contamination Audit

An automated audit of the legacy feature engineering pipeline ([backend/app/ml/feature_engineering.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/ml/feature_engineering.py)) and data generator was performed using [backend/app/ml/leakage_audit.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/ml/leakage_audit.py).

### Finding 1: Tautological Feature Collinearity (`area_x_etc`) — [CRITICAL]
- **Target Variable**:
  $$\text{water\_demand\_m}^3 = (\text{etc\_mm\_per\_day} \times \text{farm\_area\_hectares} \times 10.0) \times \mathcal{N}(1.0, 0.10)$$
- **Engineered Feature**:
  $$\text{area\_x\_etc} = \text{farm\_area\_hectares} \times \text{etc\_mm\_per\_day}$$
- **Audit Verdict**: `area_x_etc` is literally $0.1 \times \text{target}$. The Random Forest and XGBoost regression trees merely learn a constant scale factor ($\approx 10.0$). This explains the artificially inflated historical metrics ($R^2 \approx 0.97 - 0.99$, MAE $\approx 17\text{ m}^3/\text{day}$). It produces an illusion of machine learning prowess while in fact acting as an opaque, compute-heavy multiplier of a single input feature.

### Finding 2: Identity Feature Duplication (`et0_x_kc`) — [HIGH]
- `et0_x_kc` is mathematically defined as $\text{ET}_0 \times K_c$.
- However, `etc_mm_per_day` is *already present* in the feature matrix with identical values. This introduces strict multi-collinearity without providing additional agronomic information.

### Finding 3: Operational Agent Contamination — [MEDIUM]
- The legacy pipeline fed operational negotiation variables into the crop demand predictor:
  - `preferred_start_hour`
  - `irrigation_window_hours`
  - `flexibility_score`
  - `urgency_score`
  - `crop_stress_index`
- **Why this is invalid**: A farmer's schedule flexibility or willingness to negotiate does not alter the physical biophysical rate at which solar radiation and vapor pressure deficit evaporate moisture from the plant stomata. Conflating behavioral decision variables with biophysical crop water demand contaminates the predictor.

### Finding 4: Temporal Shuffling & Future Lookahead — [HIGH]
- The legacy `train_val_test_split()` used `df.sample(frac=1)` with random stratification across rows.
- In time-series weather data, random splitting allows weather from December 2023 to appear in the training set while predicting November 2023 in the test set. This temporal lookahead creates artificially optimistic evaluation metrics.

---

## 3. Two Distinct Modeling Approaches

To prevent confusing deterministic calculations with statistical learning, AquaMediAI explicitly separates two distinct approaches:

```
┌────────────────────────────────────────────────────────────────────────┐
│               APPROACH A: Deterministic Agronomic Baseline             │
│  - Closed-form FAO-56 Penman-Monteith + USDA-SCS equation              │
│  - Zero data leakage, zero training, zero overfitting                  │
│  - 100% physically bounded and transparent                            │
│  - Primary benchmark for system operation and conflict mediation      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Evaluated against
┌───────────────────────────────────▼────────────────────────────────────┐
│               APPROACH B: Machine-Learning Approximation               │
│  - Trained surrogate model (e.g., XGBoost, Gradient Boosting)          │
│  - Excludes tautological features (no area_x_etc)                      │
│  - Strictly chronological walk-forward cross-validation                │
│  - Predicts calculated agronomic surrogate (NOT measured water)        │
└────────────────────────────────────────────────────────────────────────┘
```

### Approach A: Deterministic Agronomic Baseline Calculator
- **Implementation**: [backend/app/ml/agronomic_baseline.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/ml/agronomic_baseline.py)
- **Mathematical Invariant**:
  $$V_{\text{demand}} = \frac{\max(0.0, ET_0 \times K_c - P_{\text{eff}})}{E_a} \times A_{\text{farm}} \times 10.0 \quad (\text{m}^3/\text{day})$$
- **Advantages**:
  1. Guaranteed non-negative, physically conserved demand.
  2. Requires zero training data or artifact serialization.
  3. Fully explainable: every cubic meter allocated can be traced to solar radiation, temperature, crop stage ($K_c$), and plot area.

### Approach B: Machine-Learning Approximation
- **Role**: Approximates the non-linear interaction of raw meteorological variables (temperature, relative humidity, wind speed, solar radiation, antecedent precipitation) when $ET_0$ is not pre-computed or when non-linear soil-moisture feedback is modeled.
- **When is Approach A preferable?** For static single-day snapshots where FAO-56 parameters are known, Approach A is mathematically exact and strictly superior to ML.
- **When is Approach B preferable?** Only when predicting future demand under forecast uncertainty ($T+1$ to $T+7$ days) or when empirical smart-meter observations become available to learn real human pumping behavior.

---

## 4. Defensible Feature Dictionary (Approach B)

All proposed features are strictly causal: they only use observations available at prediction time ($t \le 0$).

| Feature Name | Physical Units | Derivation / Formula | Availability Time | Provenance / Source |
|---|---|---|---|---|
| `temperature_celsius` | °C | Daily mean air temperature ($T_{\text{mean}}$) | Day $t$ morning | NASA POWER / IMD |
| `diurnal_temp_range_celsius` | °C | $T_{\max} - T_{\min}$ (atmospheric dryness proxy) | Day $t$ morning | NASA POWER / IMD |
| `humidity_percent` | % | Relative humidity at 2 m ($RH$) | Day $t$ morning | NASA POWER / IMD |
| `wind_speed_m_per_s` | m/s | Wind speed at 2 m ($u_2$) | Day $t$ morning | NASA POWER / IMD |
| `solar_radiation_mj_per_m2` | $\text{MJ/m}^2/\text{day}$ | All-sky surface downward solar irradiance ($R_s$) | Day $t$ morning | NASA POWER / Pyranometer |
| `vpd_proxy_kpa` | kPa | Vapor Pressure Deficit proxy: $e_s(T) \times (1 - RH/100)$ | Day $t$ morning | Derived from $T$ and $RH$ |
| `rainfall_lag1_mm` | mm | Precipitation on day $t-1$ | Day $t-1$ end | Rain gauge / NASA POWER |
| `rainfall_antecedent_3d_mm` | mm | Cumulative rain over $[t-3, t-1]$ | Day $t-1$ end | 3-day causal rolling sum |
| `rainfall_antecedent_7d_mm` | mm | Cumulative rain over $[t-7, t-1]$ | Day $t-1$ end | 7-day causal rolling sum |
| `temp_rolling_mean_3d_celsius`| °C | Mean temperature over $[t-3, t-1]$ | Day $t-1$ end | 3-day causal rolling mean |
| `solar_rad_rolling_mean_3d` | $\text{MJ/m}^2/\text{day}$ | Mean solar radiation over $[t-3, t-1]$ | Day $t-1$ end | 3-day causal rolling mean |
| `doy_sin` | Dimensionless | $\sin(2\pi \cdot \text{day\_of\_year} / 365.25)$ | Calendar (known) | Astronomical calendar |
| `doy_cos` | Dimensionless | $\cos(2\pi \cdot \text{day\_of\_year} / 365.25)$ | Calendar (known) | Astronomical calendar |
| `kc_value` | Dimensionless | FAO-56 crop coefficient for growth stage | Sowing calendar | ICAR / FAO-56 Table 12 |
| `farm_area_hectares` | ha | Cultivated plot area | Farm registration | Land record (7/12 extract) |

> **Note on Soil Properties**: Soil textural classes (`clay`, `clay_loam`, `loam`) are categorical regional descriptors. In-situ available water capacity (`soil_whc_mm_per_m`) should only be used as a scalar prior from FAO-56 soil tables, not claimed as dynamic telemetry.

---

## 5. Evaluation Protocol

To prevent misleading performance claims, any model evaluation in AquaMediAI must follow this protocol:

1. **Benchmark Comparison**: Model predictions must be compared against two baselines:
   - **Baseline 1 (Naive Mean)**: Constant prediction equal to the mean training demand ($\bar{y}_{\text{train}}$).
   - **Baseline 2 (Approach A)**: Deterministic FAO-56 agronomic requirement.
2. **Chronological Holdout Split**:
   - First 70% of chronological observations for training.
   - Next 15% for validation (early stopping).
   - Final 15% for held-out unbiased testing.
   - Zero shuffling, zero temporal overlap ([backend/app/ml/chronological_split.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/ml/chronological_split.py)).
3. **Walk-Forward Cross-Validation**:
   - Rolling-origin validation with 180-day initial training window and 30-day forward evaluation horizons.
4. **Reported Metrics**:
   - MAE ($\text{m}^3/\text{day}$) with sample size $n$.
   - RMSE ($\text{m}^3/\text{day}$).
   - Normalized RMSE ($\text{NRMSE} = \text{RMSE} / \bar{y}$).
   - $R^2$ only reported when target variance is non-zero and non-collinear.

---

## 6. Official Go / No-Go Training Recommendation

### **Recommendation: NO-GO for Retraining Models in Phase 3**

### Technical & Scientific Rationale:
1. **Single Annual Weather Series (365 days)**: A single year (2023) of daily observations for one geographic station (Ahmednagar) contains 365 rows. While sufficient to validate weather data ingestion, 365 rows are **insufficient to train a generalizable ML model** across 8 distinct crops, 5 growth stages, 3 seasons, and variable farm sizes without severe overfitting or memorization.
2. **Absence of Real Target Labels**: Real, observed, metered farm-level water withdrawal records do not exist in public open data for Indian canal command areas. Training an ML model now would simply mean fitting a regression tree to our own deterministic formula (Approach A).
3. **Superiority of Approach A**: Because the target is defined by physical conservation laws (FAO-56 Penman-Monteith), the closed-form calculation is 100% accurate, faster, requires 0 MB of disk space, has no drift, and cannot hallucinate negative water demands.
4. **Preservation of Existing Artifacts**: Retraining models on an incomplete single-year dataset would destabilize the existing working test suite and API contracts.

### Next Steps (Phase 4):
- Retain existing `rf_model.joblib` and `xgb_model.joblib` for backward compatibility with existing API endpoints and UI.
- Use `DeterministicAgronomicBaseline` (Approach A) as the primary agronomic calculation engine.
- If machine learning surrogate training is desired for demonstration, synthesize multi-year weather series (2015–2024) across all 3 Maharashtra pilot regions (Ahmednagar, Baramati, Paithan) to provide at least 10,000 station-days before model fitting.
