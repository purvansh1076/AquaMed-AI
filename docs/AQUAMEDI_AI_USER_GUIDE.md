# AquaMedi AI — Operational User Manual & System Guide

**Document ID:** `AQUAMEDI-USER-GUIDE-2026-V1`  
**Classification:** Operational User Manual & Seminar Demonstration Guide  
**Author:** Technical Documentation Specialist & UI/UX Quality Specialist  
**Project:** AquaMedi AI — Agricultural Intelligence & Canal Water Management  
**Branch:** `feature/aquamedi-ai-product-transformation`  
**Date:** November 7, 2026  
**Status:** **ACADEMIC DEMONSTRATION VERIFIED (RELEASE V1.0)**

---

## 1. System Welcome & Role-Based Navigation

Upon accessing AquaMedi AI (`http://localhost:5173/`), users encounter the official bilingual Indian Government Landing Portal (*जल संसाधन विभाग / Department of Water Resources*). The platform offers two primary user pathways:

```
                  ┌────────────────────────────────────────┐
                  │       AquaMedi AI Welcome Portal       │
                  │        (National Tricolor Bar)         │
                  └───────────────────┬────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│     Kisan Portal (Farmer) │                   │    Expert Command Center  │
│  - Zero Login Required    │                   │  - Authenticated Access   │
│  - Public Crop Advisory   │                   │  - Canal Quota Optimizer  │
│  - Water Demand Estimates │                   │  - Multi-Agent Mediation  │
└───────────────────────────┘                   └───────────────────────────┘
```

---

## 2. Farmer (Kisan) Portal Workflow

The Farmer Portal is engineered for zero-friction access, requiring no registration, password entry, or personal credentials.

### 2.1 Calculating Parcel Water Demand
1. From the home screen, click **"किसान पोर्टल प्रवेश / Farmer Portal Access"** or navigate to `/farmer-portal`.
2. Enter your farm parcel parameters:
   * **Crop Type:** Select from Sugarcane, Cotton, Wheat, Soybean, or Gram.
   * **Growth Stage:** Choose Initial, Vegetative Development, Mid-Season, or Late-Season.
   * **Soil Classification:** Select Black Cotton (Clay), Loamy, or Sandy Loam.
   * **Plot Surface Area:** Enter landholding in hectares (e.g., `3.5`).
   * **Observed Soil Moisture:** Enter current soil moisture percentage if known (default: $22\%$).
3. Click **"Calculate Crop Water Demand"**.

### 2.2 Interpreting the Prediction Results
* **XGBoost Net Daily Irrigation Prediction:** Displays the net water volume required at the crop root zone (e.g., **$221.38\text{ m}^3/\text{day}$**).
* **Conformal 90% Confidence Interval:** Displays the mathematically proven uncertainty range (e.g., **$[152.86, 289.90]\text{ m}^3/\text{day}$**). This indicates that true demand will fall within this window with 90% statistical certainty.
* **FAO-56 Gross Application Baseline:** Displays the total volume required at the canal gate (**$299.00\text{ m}^3/\text{day}$**), accounting for the 70% surface application efficiency divisor.

### 2.3 Accessing Crop Health & Irrigation Schedules
* Click **"Crop Health"** to view real-time root-zone depletion metrics and water stress alerts.
* Click **"Irrigation Advisory"** to view recommended irrigation intervals and soil moisture conservation tips.

---

## 3. Expert Command Center & Water Resource Management

The Expert Command Center is designed for irrigation department engineers, canal section officers, and system administrators.

### 3.1 Authentication
1. Navigate to `/login`.
2. Enter verified administrative credentials.
3. Upon successful authentication, a cryptographically signed JWT token is stored securely, unlocking protected administration tabs in the top navigation bar.

### 3.2 Canal Water Distribution Monitoring (`/dashboard`)
* **Reach Balancing Telemetry:** Inspect real-time discharge rates across:
  * **Head Reach (0 – 15 km):** Upstream main branch intake (e.g., $14.2\text{ m}^3/\text{s}$).
  * **Middle Reach (15 – 40 km):** Intermediate distributary flow (e.g., $9.8\text{ m}^3/\text{s}$).
  * **Tail Reach (> 40 km):** Downstream terminal distributary flow (e.g., $3.1\text{ m}^3/\text{s}$).
* **Deficit Alerts:** Automated amber/red warning banners flag when tail-end discharge drops below subsistence thresholds.

### 3.3 Running the Google OR-Tools Water Allocation Optimizer (`/allocation`)
1. Navigate to `/allocation`.
2. Review aggregated parcel demands collected from the distributaries.
3. Enter total available reservoir release volume in the configuration card.
4. Verify the **"Enforce Tail-Reach Equity"** and **"50% Minimum Subsistence Floor"** checkboxes are active.
5. Click **"Run OR-Tools GLOP Optimization"**.
6. **Output Inspection:**
   * Solver completes in $<15\text{ ms}$ with status `OPTIMAL`.
   * Review the optimized allocation table detailing requested vs. allocated volumes per canal branch.
   * Inspect the **Gini Inequality Index** (verified $<0.18$) and **Tail-End Satisfaction Ratio** (verified $>78\%$).
7. Click **"Export Quota Table (CSV)"** to generate official departmental dispatch logs.

### 3.4 Multi-Agent Dispute Mediation (`/dispute-mediation`)
When upstream and downstream water user associations dispute canal gate schedules:
1. Navigate to `/dispute-mediation`.
2. Select the contested canal reach and the disputed demand variance.
3. Click **"Initiate Multi-Agent Negotiation"**.
4. Observe the cooperative bargaining process:
   * **Farmer Advocate Agent** and **Canal Officer Agent** exchange structured concession proposals across 5 rounds.
   * **Neutral Mediator Agent** calculates the Pareto frontier and discovers the Nash Bargaining Solution.
5. Review the final settlement contract and agreement summary.

### 3.5 What-If Climate Crisis Simulation (`/scenarios`)
1. Navigate to `/scenarios`.
2. Select a stress scenario:
   * **Severe Drought (-40% Inflow)**
   * **Main Canal Breach (72-hour Stoppage)**
   * **Heatwave Surge (+5°C Ambient Spike)**
3. Click **"Simulate Impact"**.
4. Review adjusted reservoir drawdown timelines, emergency food-crop rationing schedules, and projected regional yield impacts.

---

## 4. Reports Generation & Audit Logging (`/reports`)

1. Navigate to `/reports`.
2. Select the desired report type:
   * **Daily Water Allocation Audit Log**
   * **Machine Learning Model Accuracy & Drift Report**
   * **Stakeholder Dispute Mediation Settlement Ledger**
3. Select date range and export format (CSV or PDF).
4. Click **"Generate Official Departmental Report"**.
5. All reports automatically include administrative timestamps, system version tags, and demonstration data disclaimers.

---

## 5. Troubleshooting & Frequently Encountered Situations

| Symptom | Root Cause | Resolution |
|:---|:---|:---|
| Prediction button disabled | Required farm parameters (crop, area, soil) incomplete | Complete all input fields with positive numbers |
| `HTTP 401 Unauthorized` | Expert JWT session expired (60-minute limit) | Log out and re-authenticate via `/login` |
| `HTTP 429 Too Many Requests` | More than 10 login attempts within 60 seconds | Wait 60 seconds before retrying login |
| Conformal interval bounds wide | Extreme parcel size ($\ge 5.0\text{ ha}$) or extreme temperature | Normal behavior; area scaling factor widens bounds for large parcels |
