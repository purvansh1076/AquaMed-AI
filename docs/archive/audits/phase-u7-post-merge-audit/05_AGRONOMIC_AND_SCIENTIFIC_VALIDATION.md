# Phase U7 — Audit Report 05: Agronomic Engine & Scientific Methodology Validation

**Document ID:** `AQUA-AUDIT-U7-05`  
**Date:** 2026-11-15  
**Review Type:** Agronomic Rigor, Physical Consistency & Scientific Validation  
**Component:** Agronomy Engine (`backend/app/agronomy/`)  

---

## 1. Executive Summary

This report evaluates the scientific foundation and agronomic algorithms governing crop water requirement calculations in AquaMedi AI.

The review confirms that the agronomic engine faithfully implements the Food and Agriculture Organization (FAO) Irrigation and Drainage Paper No. 56 standard. The audit establishes the three distinct levels of scientific validation and explicitly documents regional empirical boundaries.

---

## 2. FAO-56 Penman-Monteith Reference Evapotranspiration ($ET_0$)

Reference evapotranspiration ($ET_0$) represents the evaporative demand of the atmosphere over a standardized grass reference surface:

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

### 2.1 Physical Formulation Audit (`backend/app/agronomy/fao56.py`)
- **Slope of Saturation Vapor Pressure Curve ($\Delta$):**
  $$\Delta = \frac{4098 [0.6108 \exp(\frac{17.27 T}{T + 237.3})]}{(T + 237.3)^2}$$
- **Psychrometric Constant ($\gamma$):** Calculated dynamically from atmospheric pressure:
  $$\gamma = \frac{C_p P}{\epsilon \lambda} \approx 0.665 \times 10^{-3} P \text{ [kPa/}^\circ\text{C]}$$
  where atmospheric pressure $P$ adjusts for elevation above sea level ($z$).
- **Vapor Pressure Deficit ($e_s - e_a$):** $e_s$ computed from mean saturation vapor pressure at $T_{\max}$ and $T_{\min}$; $e_a$ derived from relative humidity.
- **Net Radiation ($R_n$):** Net shortwave ($R_{ns} = (1 - \alpha) R_s$) minus net longwave radiation ($R_{nl}$). Soil heat flux $G \approx 0$ for daily intervals.
- **Wind Speed ($u_2$):** Standardized to 2 meters above ground level using logarithmic wind profile adjustment if measured at non-standard heights.

---

## 3. Crop Evapotranspiration ($ET_c$) & Crop Coefficients

1. **Single Crop Coefficient Approach:**
   $$ET_c = K_c \times ET_0$$
   Applies stage-specific crop coefficients ($K_{c,\text{ini}}$, $K_{c,\text{mid}}$, $K_{c,\text{end}}$) parameterized for major regional crops (Rice, Wheat, Maize, Cotton, Sugarcane).
2. **Dual Crop Coefficient Approach:**
   $$ET_c = (K_{cb} + K_e) \times ET_0$$
   Separates basal crop transpiration ($K_{cb}$) from soil surface evaporation ($K_e$), providing high-resolution demand modeling after rain or irrigation events.
3. **Soil Water Balance & Stress ($K_s$):**
   When soil root-zone depletion exceeds Readily Available Water ($RAW = p \cdot TAW$), the stress coefficient scales transpiration:
   $$K_s = \frac{TAW - D_r}{(1 - p) TAW}$$

---

## 4. Three Levels of Scientific Validation

To eliminate ambiguity between code correctness and real-world performance, this audit categorizes validation across three strict levels:

| Validation Level | Definition | Scope in AquaMedi AI | Status |
| :--- | :--- | :--- | :--- |
| **Level 1: Mathematical Validation** | Verification of formulas against published FAO-56 benchmark tables. | Unit tests in `tests/test_fao56_reference.py` match published FAO-56 Example 18 ($ET_0 = 7.4\text{ mm/day}$) within $0.01\text{ mm/day}$. | **VERIFIED** |
| **Level 2: Numerical Implementation** | Verification of extreme bounds, missing data handling, and input sanitization. | Unit tests in `tests/test_et0_bounds.py` verify stability across extreme temperatures ($5^\circ\text{C}$ to $48^\circ\text{C}$), high wind ($12\text{ m/s}$), and missing humidity. | **VERIFIED** |
| **Level 3: Regional Empirical Validation** | Calibration against in-situ lysimeter measurements, IMD stations, and CWC canal discharge sensors. | **NOT YET CONDUCTED.** Current release relies on synthetic meteorological distributions and standard FAO tabular defaults. | **DOCUMENTED LIMITATION** |

---

## 5. Agronomic Input Bounds & Missing Weather Data Handling

- **Physical Safeguards:** The engine enforces hard biological bounds:
  - $ET_0 \ge 0.0\text{ mm/day}$ and $ET_0 \le 18.0\text{ mm/day}$.
  - Relative humidity clamped between $1.0\%$ and $100.0\%$.
  - Wind speed at 2m clamped to $\ge 0.1\text{ m/s}$.
- **Missing Data Fallback:** If solar radiation is unmeasured, the engine estimates $R_s$ from temperature range using the Hargreaves-Samani radiation formula ($R_s = k_{Rs} \sqrt{T_{\max} - T_{\min}} R_a$).

---

## 6. Verdict

**Agronomic Status: PASS (Mathematically & Agronomically Valid with Clear Empirical Boundaries)**
