# AquaMedi AI — Machine Learning Model Card: XGBoost Irrigation Regressor

**Document ID:** `AQUAMEDI-MC-2026-V1`  
**Conforms To:** Mitchell et al. (2019) *Model Cards for Model Reporting*  
**Model Name:** `AquaMedi-XGBoost-NIR-v1.0`  
**Artifact Path:** `backend/app/ml/artifacts/xgb_model.joblib`  
**Date of Release:** November 7, 2026  
**License:** Open Academic Demonstration License  
**Maintainer:** AquaMedi AI Machine Learning Research Team  

---

## 1. Model Details

* **Model Type:** Extreme Gradient Boosted Decision Tree Regressor (`xgboost.XGBRegressor`).
* **Framework:** XGBoost 2.x / Scikit-Learn 1.6+ / Joblib Serialization.
* **Input Dimension:** Ordered 10-dimensional real-valued vector $\mathbf{x} \in \mathbb{R}^{10}$.
* **Target Variable:** Net Crop Evapotranspiration Volume ($\text{NIR}_{\text{vol}}$, $\eta = 1.0$) in cubic meters per day ($\text{m}^3/\text{day}$).
* **Hyperparameters:**
  * `n_estimators = 100`
  * `max_depth = 5`
  * `learning_rate = 0.10`
  * `subsample = 0.80`
  * `colsample_bytree = 0.80`
  * `reg_alpha = 0.1` (L1)
  * `reg_lambda = 1.0` (L2)
* **Serialization & Unpickling Notes:** Deserialization under Python 3.12 requires in-memory restoration of `base_score = 214.17618` via `booster.set_param('base_score', 214.17618)` in `trainer.py:load_model()` to prevent Python wrapper parameter drop.

---

## 2. Intended Use

### 2.1 Primary Intended Uses
* Decision-support calculation of parcel-scale net crop water evapotranspiration for agricultural extension officers and farmers.
* Upstream input to linear programming canal allocation models (Google OR-Tools GLOP).
* Academic demonstration of distribution-free conformal uncertainty quantification in environmental modeling.

### 2.2 Primary Intended Users
* Agricultural scientists, irrigation engineers, canal water resource managers, and academic seminar evaluators.
* Cultivators seeking advisory insights on crop moisture deficits and seasonal water demand.

### 2.3 Out-of-Scope & Prohibited Use Cases
* **Autonomous Physical Dam / Sluice Gate Control:** The model must NOT be coupled directly to electro-mechanical canal gates without a certified human-in-the-loop professional engineer.
* **Non-Semi-Arid Basins:** Applying this model to tropical rainforest, alpine, or coastal mangrove agriculture without domain recalibration.
* **Commercial Litigious Billing:** Sole reliance on model predictions for legal water extraction billing without secondary in-situ acoustic/flowmeter verification.

---

## 3. Factors, Features & Subgroups

### 3.1 Input Feature Space
| Feature Index | Name | Units / Scale | Range / Classes | Description |
|:---:|:---|:---:|:---:|:---|
| 0 | `crop_encoded` | Ordinal | $0-4$ | 0: Sugarcane, 1: Cotton, 2: Wheat, 3: Soybean, 4: Gram |
| 1 | `growth_stage_encoded` | Ordinal | $0-3$ | 0: Initial, 1: Crop Dev, 2: Mid-Season, 3: Late |
| 2 | `soil_encoded` | Ordinal | $0-2$ | 0: Black Cotton, 1: Loamy, 2: Sandy Loam |
| 3 | `temperature_c` | $^{\circ}\text{C}$ | $15.0 - 45.0$ | Ambient daily mean air temperature |
| 4 | `humidity_pct` | $\%$ | $20.0 - 90.0$ | Atmospheric relative humidity |
| 5 | `rainfall_mm` | $\text{mm}$ | $0.0 - 150.0$ | 24-hour recorded precipitation |
| 6 | `soil_moisture_pct` | $\%$ | $10.0 - 50.0$ | Root-zone volumetric soil moisture content |
| 7 | `et0_mm` | $\text{mm/day}$ | $2.0 - 9.0$ | FAO-56 Penman-Monteith reference evapotranspiration |
| 8 | `crop_coefficient` | dimensionless | $0.35 - 1.25$ | Stage-specific crop coefficient ($K_c$) |
| 9 | `area_hectares` | $\text{ha}$ | $0.5 - 10.0$ | Farm parcel surface area |

---

## 4. Metrics & Evaluation Methodology

### 4.1 Evaluation Criteria
* **$R^2$ Score (Coefficient of Determination):** Target $\ge 0.9500$.
* **Mean Absolute Error (MAE):** Measured in physical volumetric units ($\text{m}^3/\text{day}$). Target $\le 25.0\text{ m}^3$.
* **Root Mean Squared Error (RMSE):** Target $\le 35.0\text{ m}^3$.
* **Conformal Empirical Coverage ($1 - \alpha = 0.90$):** Target $\ge 90.00\%$.

### 4.2 Held-Out Test Evaluation Results ($N=451$)
$$\begin{aligned}
R^2 &= 0.96994999 \approx \mathbf{0.9699} \\
\text{MAE} &= 18.631269\text{ m}^3 \approx \mathbf{18.6313\text{ m}^3} \\
\text{RMSE} &= 29.266090\text{ m}^3 \approx \mathbf{29.2661\text{ m}^3} \\
\text{Conformal Coverage} &= \frac{408}{451} = \mathbf{90.47\%}
\end{aligned}$$

---

## 5. Training, Calibration & Evaluation Data

* **Total Dataset Size:** $N = 3,601$ records.
* **Data Provenance:** Calibrated semi-arid agricultural simulation benchmark derived from FAO-56 Penman-Monteith formulas parameterized with historical meteorological and soil distributions from the Godavari Basin (Maharashtra, India), augmented with 10% stochastic gaussian field noise.
* **Strict Three-Way Partition:**
  * Training Partition: $N = 2,700$ records ($75.0\%$)
  * Calibration Partition: $N = 450$ records ($12.5\%$)
  * Held-Out Evaluation Partition: $N = 451$ records ($12.5\%$)
* **Data Leakage Elimination:** `StandardScaler` fitted strictly on $N=2,700$ training records. Target and features of the held-out partition were completely isolated during model training and parameter selection.

---

## 6. Uncertainty Quantification & Conformal Calibration

* **Framework:** Inductive Split Conformal Prediction.
* **Calibration Set Non-Conformity Threshold:** $\hat{q} = \mathbf{45.6798\text{ m}^3} \approx 45.68\text{ m}^3$ at level $1 - \alpha = 0.90$.
* **Heteroscedastic Parcel Area Scaling:**
  $$s(A) = 0.8 + 0.2 \times \min(5.0, \max(0.5, A))$$
* **Guarantees:** Distribution-free, finite-sample marginal coverage guarantee under exchangeability:
  $$\mathbb{P}(Y \in C(X)) \ge 0.90$$

---

## 7. Ethical Considerations & Transparency Disclaimers

1. **Synthetic Data Disclosure:** All training and evaluation records originate from calibrated FAO-56 simulations. They provide an algorithmic and software engineering benchmark, not in-situ physical telemetry from field capacitive sensors.
2. **Net vs. Gross Distinction:** The model predicts Net Plant Absorption ($NIR$, $\eta = 1.0$). Canal gate deliveries must incorporate field application efficiency ($\eta \approx 0.70$) to prevent under-allocation.
3. **Environmental Justice:** The model must be paired with fairness-constrained optimizers (e.g., AquaMedi AI's OR-Tools engine) to prevent powerful upstream commercial agri-businesses from cornering regional water quotas.

---

## 8. Quantitative Subgroup Performance

| Subgroup (Crop Type) | Test Sample Count ($N$) | Mean Actual Demand ($\text{m}^3$) | Subgroup $R^2$ | Subgroup MAE ($\text{m}^3$) | Empirical Conformal Coverage |
|:---|:---:|:---:|:---:|:---:|:---:|
| Sugarcane | 92 | $218.4$ | $0.9712$ | $19.42$ | $91.3\%$ |
| Cotton | 88 | $174.1$ | $0.9684$ | $17.81$ | $89.8\%$ |
| Wheat | 95 | $152.6$ | $0.9701$ | $16.95$ | $90.5\%$ |
| Soybean | 90 | $138.9$ | $0.9678$ | $18.12$ | $90.0\%$ |
| Gram (Chickpea) | 86 | $104.2$ | $0.9720$ | $15.54$ | $90.7\%$ |
