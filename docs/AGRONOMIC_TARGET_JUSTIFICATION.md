# AquaMediAI — Agronomic Target Variable Justification & Data Availability Gap Analysis

**Document Version**: 2.0.0 (Phase 2)  
**Date**: October 2026  
**Focus**: Scientific Formulation, Target Definition, and Empirical Limitations  

---

## 1. Mathematical Formulation of the Agronomic Target

In agricultural water management, crop water demand follows the internationally standardized **FAO-56 Irrigation and Drainage framework** (Allen et al., 1998; endorsed by ICAR and ASCE).

The target variable for water allocation in AquaMediAI represents the **daily volumetric irrigation requirement delivered to a farm's canal turnout ($V_{\text{demand}}$, in $\text{m}^3/\text{day}$)**:

### Step 1: Reference Evapotranspiration ($ET_0$)
Computed via the standard FAO-56 Penman-Monteith equation driven by real daily weather forcing:
$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T_{\text{mean}} + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
Where $R_n$ is net radiation ($\text{MJ/m}^2/\text{day}$), $G \approx 0$ is soil heat flux, $T_{\text{mean}}$ is air temperature ($^\circ\text{C}$), $u_2$ is wind speed ($\text{m/s}$), $e_s - e_a$ is vapor pressure deficit ($\text{kPa}$), $\Delta$ is the slope of the saturation vapor pressure curve, and $\gamma$ is the psychrometric constant.

### Step 2: Potential Crop Evapotranspiration ($ET_c$)
$$ET_c = K_c \times ET_0$$
Where $K_c$ is the crop coefficient determined by crop type and phenological growth stage (germination, vegetative, flowering, maturity, harvest).

### Step 3: Net Irrigation Requirement ($I_{\text{net}}$)
Not all rainfall infiltrates or remains available to roots. Daily effective precipitation ($P_{\text{eff}}$) is computed via the USDA Soil Conservation Service (SCS) method:
$$P_{\text{eff}} = \begin{cases} 
0.0 & \text{if } P < 3.0\text{ mm (evaporative loss)} \\ 
P \times \frac{125 - 0.2 P}{125} & \text{if } 3.0 \le P \le 250.0\text{ mm} \\ 
125 + 0.1 P & \text{if } P > 250.0\text{ mm} 
\end{cases}$$

The net water depth required from irrigation is:
$$I_{\text{net}} = \max\left(0.0, ET_c - P_{\text{eff}}\right) \quad (\text{mm/day})$$

### Step 4: Gross Volumetric Delivery Requirement ($V_{\text{demand}}$)
Accounting for field application efficiency and conveyance losses in gravity canal networks ($E_a \approx 0.65 - 0.75$ for surface furrow/flood, $0.85 - 0.90$ for pressurized drip):
$$I_{\text{gross}} = \frac{I_{\text{net}}}{E_a} \quad (\text{mm/day})$$

Converting depth over land area into cubic meters:
$$V_{\text{demand}} = I_{\text{gross}} \times A_{\text{farm}} \times 10.0 \quad (\text{m}^3/\text{day})$$
*(Since $1\text{ mm} \times 1\text{ ha} = 0.001\text{ m} \times 10,000\text{ m}^2 = 10\text{ m}^3$)*

---

## 2. Rigorous Distinction: Agronomic Estimate vs. Measured Irrigation

> [!CAUTION]
> **Scientific Integrity Requirement**:
> We must never claim that a calculated agronomic requirement ($V_{\text{demand}}$) represents *measured empirical farmer water withdrawals*.

In public hydrological records in India:
1. **Atmospheric Forcing is Measured**: Temperature, radiation, humidity, precipitation, and wind speed from NASA POWER and IMD are genuine physical observations.
2. **Crop Water Requirement is Calculated**: $ET_0$, $ET_c$, and $I_{\text{net}}$ are physically based agronomic calculations derived from meteorological forcing and FAO-56 crop physiology.
3. **Farm Gate Water Extraction is Unmetered**: In Indian surface canal systems (governed under the Maharashtra Management of Irrigation Systems by Farmers Act, MMISFA), canal water is released on rotational schedules (*warabandi* or *RWS*) through distributaries to Water Users Associations (WUAs). Individual farm boundaries typically lack digital ultrasonic or electromagnetic flow meters.

Therefore, when AquaMediAI predicts water demand, it is predicting the **scientifically justified agronomic water need** required to prevent crop stress, which provides a neutral, equitable benchmark for conflict mediation.

---

## 3. Data Availability Gap Analysis

To train a purely empirical supervised ML model on *observed* farm-level water consumption, the following inputs would be required but are currently unavailable in open public databases:

| Missing Component | Why It Is Missing | Impact on ML Pipeline |
|---|---|---|
| **High-Frequency In-Situ Plot Flow Meters** | Flow meters are not installed on individual smallholder plots (0.5–2 ha) in canal command systems. | Cannot measure exact daily volume ($m^3$) extracted by a specific farmer. |
| **Continuous Soil Moisture Telemetry** | TDR/capacitance soil moisture probes are limited to specialized agricultural research stations (MPKV Rahuri). | Daily root zone depletion ($D_r$) must be modeled via water balance equations rather than sensor readings. |
| **Sluice Gate Operation Timestamp Logs** | Minor canal gate operations by local *patkaris* / canal ditch-riders are recorded in manual paper logbooks, not open APIs. | Exact timing and duration of canal turn deliveries cannot be ingested digitally in real time. |
| **Micro-Plot Crop Sowing Rosters** | Official village land records (7/12 extract in Maharashtra) record seasonal crop acreages but lack precise planting dates per plot. | Stage transitions ($K_c$ timing) must rely on standard ICAR regional sowing windows. |

---

## 4. Phase 2 Recommendation & Transition to Phase 3

Because measured plot-level irrigation meters do not exist in public open data, **the most defensible and reproducible strategy** is:
1. **Use Real Meteorological Forcing**: Drive all baseline evaporative demand using real daily NASA POWER weather observations for the pilot region.
2. **Implement Daily Soil-Water Balance Modeling**: Model realistic field heterogeneity (soil WHC, effective rooting depth, antecedent precipitation) rather than static formula multiplication.
3. **Decouple Tautological Features**: In Phase 3 data preparation, remove the direct collinear leakage feature (`area_x_etc`) and allow the ML model to learn complex non-linear interactions between weather variables, phenological stages, and soil properties.
