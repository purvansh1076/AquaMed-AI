# AquaMediAI — Dataset Provenance & Ingestion Documentation

**Document Version**: 2.0.0 (Phase 2)  
**Date**: October 2026  
**Primary Pilot Region**: Pravara-Mula Canal Command (Ahmednagar, Central Maharashtra, India)  

---

## 1. Executive Summary

AquaMediAI Phase 2 establishes a reproducible, scientifically grounded data pipeline that ingests real agroclimatological observations from **NASA POWER** (Prediction Of Worldwide Energy Resources). It replaces purely synthetic random numbers with real daily atmospheric forcing for pilot canal command areas in Maharashtra, India.

> [!IMPORTANT]
> **Separation of Raw vs. Processed Data**:
> - Raw unmodified API payloads are stored permanently in `backend/data/raw/` in their native JSON format.
> - Validated, quality-controlled, and feature-engineered datasets are output to `backend/data/processed/`.
> - Raw files are never overwritten or altered by the cleaning pipeline.

---

## 2. Pilot Region Inventory & Geographic Resolution

Rather than fabricating private farm coordinates, the pipeline defines regional centroid anchors for major canal irrigation systems in Maharashtra.

| Region ID | Description / Basin | Centroid Coordinates | Elevation | Predominant Soils | Key Crops |
|---|---|---|---|---|---|
| `maharashtra_ahmednagar` *(Default Pilot)* | Pravara-Mula Canal Command (Godavari Basin) | **19.0900° N, 74.7400° E** | 540 m MSL | Clay (Vertisols), Clay Loam, Loam | Sugarcane, Wheat, Soybean, Onion, Cotton, Maize, Gram |
| `maharashtra_baramati` | Nira Left/Right Bank Command (Krishna-Bhima Basin) | **18.1500° N, 74.5800° E** | 550 m MSL | Clay Loam, Loam, Sandy Loam | Sugarcane, Wheat, Maize, Horticulture |
| `maharashtra_paithan` | Jayakwadi Reservoir Command (Godavari Basin) | **19.4800° N, 75.3800° E** | 458 m MSL | Deep Black Clay (Vertisols) | Cotton, Soybean, Wheat, Sweet Orange |

**Spatial Resolution**: NASA POWER provides global agroclimatology at **0.5° × 0.5° latitude and longitude** grid cell resolution (~50 km × 50 km).

---

## 3. Data Source Investigation & Licensing

| Source | Domain / Coverage | Access Restrictions & License | Applicability to AquaMediAI |
|---|---|---|---|
| **NASA POWER** | Global daily surface meteorology & solar irradiance (1981–present) | **Open Access / Public Domain (NASA Open Science Data)**. No API key required; rate-limit friendly. | **PRIMARY SOURCE**: Provides all 7 parameters required for FAO-56 Penman-Monteith reference evapotranspiration ($ET_0$). |
| **IMD** (India Meteorological Department) | Daily gridded rainfall ($0.25^\circ \times 0.25^\circ$) & temperature ($1^\circ \times 1^\circ$) for India | **Restricted / Paid Licensing**: Gridded datasets require institutional credentials, formal research clearance, or commercial payment. Not freely redistributable in open-source repositories. | **Reference Benchmark**: Historical IMD rainfall averages used to validate NASA POWER precipitation distributions. |
| **ICAR / MPKV** (Mahatma Phule Krishi Vidyapeeth, Rahuri) | Crop coefficient ($K_c$) tables, sowing dates, and water requirement guidelines | **Open Academic Literature**: Published research bulletins and ICAR agronomic guidelines. | **AGRONOMIC GROUNDING**: Used for $K_c$ crop coefficients across phenological growth stages for Maharashtra crops. |
| **India-WRIS / CWC** (Water Resources Information System / Central Water Commission) | Major dam storage telemetry, reservoir levels, canal head discharge | **Open Government Data (data.gov.in / WRIS)**: Basin-level and reservoir telemetry publicly accessible via web portal. | **ALLOCATION BENCHMARK**: Used to calibrate canal capacity ranges ($18 - 80\text{ m}^3/\text{hour}$) in scenario configurations. No open farm-gate metering API exists. |

---

## 4. Ingested Weather Parameters & Data Dictionary

The ingested raw dataset (`backend/data/raw/nasa_power_maharashtra_ahmednagar_20230101_20231231.json`) contains daily records from **January 1, 2023 to December 31, 2023 (365 days)**:

| Parameter Key | Name | Physical Units | Valid Range | Missing Code | Description |
|---|---|---|---|---|---|
| `T2M` | Mean Air Temperature | °C | $-5.0 \text{ to } 55.0$ | `-999.0` | Average daily temperature at 2 meters above ground. |
| `T2M_MAX` | Max Air Temperature | °C | $-5.0 \text{ to } 55.0$ | `-999.0` | Daily maximum 2-meter air temperature. |
| `T2M_MIN` | Min Air Temperature | °C | $-5.0 \text{ to } 55.0$ | `-999.0` | Daily minimum 2-meter air temperature. |
| `RH2M` | Relative Humidity | % | $0.0 \text{ to } 100.0$ | `-999.0` | Daily mean relative humidity at 2 meters. |
| `PRECTOTCORR` | Corrected Precipitation | mm/day | $0.0 \text{ to } 400.0$ | `-999.0` | Total daily surface precipitation. |
| `WS2M` | Wind Speed | m/s | $0.1 \text{ to } 35.0$ | `-999.0` | Daily mean wind speed at 2 meters. |
| `ALLSKY_SFC_SW_DWN` | Solar Irradiance | $\text{MJ/m}^2/\text{day}$ | $0.0 \text{ to } 40.0$ | `-999.0` | Daily downward all-sky surface solar radiation. |

---

## 5. Cleaning & Quality Control Pipeline

The pipeline ([backend/app/data/agronomic_pipeline.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/data/agronomic_pipeline.py)) enforces the following validation checks:

1. **Missing Value Handling**: NASA POWER missing value code (`-999.0`) is flagged and converted to `NaN`. Isolated gaps are filled using linear time-series interpolation.
2. **Thermal Sanity Assertion**: Ensures $T_{\min} \le T_{\text{mean}} \le T_{\max}$. In the event of minor sensor inversion, values are automatically ordered.
3. **Physical Clamping**: Relative humidity clamped to $[0.0, 100.0]\%$, solar radiation and precipitation to $\ge 0.0$, and wind speed to $\ge 0.1\text{ m/s}$ (FAO-56 aerodynamic floor).
4. **Agro-climatic Season Classification**:
   - `kharif` (Monsoon): June to October
   - `rabi` (Post-Monsoon / Cool Dry): November to March
   - `zaid` (Summer / Pre-Monsoon): April to May
5. **FAO-56 Reference Evapotranspiration ($ET_0$)**: Computed on each day using the exact FAO-56 Penman-Monteith formulation.
6. **Effective Precipitation ($P_{\text{eff}}$)**: Computed via the USDA Soil Conservation Service (SCS) method to represent rainfall retained in the crop root zone.

### Validation Audit Report (Ahmednagar Pilot, 2023)
- **Total Days**: 365
- **Missing Value Count**: 0 (100% complete)
- **Annual Rainfall**: 520.0 mm (typical for semi-arid central Maharashtra, 450–600 mm range)
- **Effective Rainfall**: 406.0 mm (78.1% retained, balance lost to runoff/deep percolation)
- **Annual Mean $ET_0$**: 5.17 mm/day
- **$ET_0$ Seasonal Range**: Min 2.13 mm/day (cool December), Max 10.95 mm/day (peak May pre-monsoon heatwave)
- **Validation Status**: `PASSED`

---

## 6. How to Reproduce the Ingestion Pipeline

### Live NASA POWER Ingestion
Run from the repository root:
```powershell
python backend/scripts/ingest_weather_data.py --region maharashtra_ahmednagar --start 20230101 --end 20231231
```

### Offline Ingestion (No Internet Required)
Uses the bundled test fixture ([backend/tests/fixtures/nasa_power_ahmednagar_sample.json](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/tests/fixtures/nasa_power_ahmednagar_sample.json)):
```powershell
python backend/scripts/ingest_weather_data.py --offline
```

### Automated Ingestion Tests
```powershell
pytest backend/tests/test_data_ingestion.py -v
```
