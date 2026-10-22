# AquaMediAI — Data Dictionary

This document defines all data elements used across the AquaMediAI system, from synthetic data generation through model features, farmer agent attributes, allocation variables, and negotiation state.

## 1. Synthetic Dataset Schema (`data_generator.py`)

The `SyntheticDataGenerator.generate_dataset()` method produces a pandas DataFrame with the following columns:

| Column Name | Type | Description | Generated From |
|-------------|------|-------------|----------------|
| `farm_area_hectares` | float | Cultivated area per farmer | Uniform random: [0.5, 5.0] |
| `et0_mm_per_day` | float | Reference evapotranspiration (mm/day) | Generated from weather params (temp, humidity, wind, radiation) using FAO-56 Penman-Monteith approximate formula |
| `kc_value` | float | Crop coefficient K_c | Uniform random: [0.5, 1.3] depending on crop_type |
| `etc_mm_per_day` | float | Crop evapotranspiration = ET_0 × K_c | `et0_mm_per_day × kc_value` |
| `soil_whc_mm_per_m` | float | Soil water-holding capacity (mm per metre depth) | Uniform random: [60, 200] |
| `preferred_start_hour` | int | Desired irrigation start hour (0-23) | Uniform random: [0, 23] |
| `irrigation_window_hours` | int | Duration of irrigation window (hours) | Uniform random: [2, 8] |
| `flexibility_score` | float | Schedule flexibility [0,1] | Beta distribution (α=2, β=5) → skewed flexible |
| `urgency_score` | float | Urgency level [0,1] | Beta distribution (α=5, β=2) → skewed urgent |
| `crop_stress_index` | float | Crop stress indicator [0,1] | Triangular mode at 0.3 |
| `temperature_celsius` | float | Daily max temperature | Uniform random: [25, 40] |
| `humidity_percent` | float | Relative humidity (%) | Uniform random: [40, 80] |
| `rainfall_mm` | float | Daily rainfall (mm) | Uniform random: [0, 25] |
| `crop_type_encoded` | int | Encoded crop type (0=wheat, 1=sugar_cane, 2=cotton, 3=rice, 5=maize, 6=sorghum, 7=banana, 8=groundnut) | Categorical assignment |
| `soil_type_encoded` | int | Encoded soil type (0=sandy, 1=loamy, 2=clay, 3=lateritic) | Categorical assignment |
| `growth_stage_encoded` | int | Encoded growth stage (0=seedling, 1=vegetative, 2=flowering, 3=maturity, 4=harvest) | Cyclic progression |
| `season_encoded` | int | Encoded season (0=winter, 1=summer, 2=monsoon, 3=post-monsoon) | Seasonal cycling |
| `area_x_etc` | float | `farm_area_hectares × etc_mm_per_day` | Engineered feature |
| `urgency_x_stress` | float | `urgency_score × crop_stress_index` | Engineered feature |
| `et0_x_kc` | float | `et0_mm_per_day × kc_value` (equivalent to ET_c) | Engineered feature |
| `rain_deficit` | float | `potential_demand - rainfall_mm` (simple deficit metric) | Engineered feature |
| `flexibility_window` | float | `flexibility_score × irrigation_window_hours` | Engineered feature |
| `scenario_type` | str | Scenario category | One of 8 values (see below) |
| `water_demand_m3` | float | **Target variable**: demand in m³/day | `etc_mm_per_day × farm_area_hectares × 10` + ±15% Gaussian noise, clamped [5, 800] |

### 1.1 Scenario Types (8 values)

| Scenario Code | Supply/Demand Ratio | Description |
|---------------|---------------------|-------------|
| `normal_water` | 105–130% | Adequate water, no shortage |
| `moderate_shortage` | 70–85% | Moderate water scarcity |
| `severe_shortage` | 40–62% | Severe water scarcity |
| `sudden_rainfall` | 110–150% | +25mm rain bonus increases supply |
| `canal_reduction` | 80–100% | Canal throttled 30–50% |
| `simultaneous_demand` | N/A | All farmers peak same 6-hour window |
| `high_urgency_farmer` | N/A | One farmer at flowering stage (high water need) |
| `flexible_farmer` | N/A | One farmer with wide schedule flexibility |

### 1.2 Train/Val/Test Split

- **Stratified by scenario_type**: each split preserves the 8 scenario proportions
- **Train**: 2100 samples (70%)
- **Validation**: 450 samples (15%)
- **Test**: 451 samples (15%)
- **Seed**: 42 ensures deterministic splits

## 2. Model Feature Set (22 features)

The ML pipeline uses exactly 22 features for both RandomForest and XGBoost. These are the feature_columns listed in `evaluation_results.json` and `trainer.py`:

| # | Feature Name | Type | Range / Encoding | Description |
|---|-------------|------|------------------|-------------|
| 1 | `farm_area_hectares` | numeric | [0.5, 5.0] | Cultivated area |
| 2 | `et0_mm_per_day` | numeric | [1, 15] | Reference ET₀ |
| 3 | `kc_value` | numeric | [0.5, 1.3] | Crop coefficient |
| 4 | `etc_mm_per_day` | numeric | [1, 20] | ET_c = ET_0 × K_c |
| 5 | `soil_whc_mm_per_m` | numeric | [60, 200] | Soil water-holding capacity |
| 6 | `preferred_start_hour` | integer | [0, 23] | Desired irrigation start |
| 7 | `irrigation_window_hours` | integer | [2, 8] | Irrigation window duration |
| 8 | `flexibility_score` | numeric | [0, 1] | Schedule flexibility |
| 9 | `urgency_score` | numeric | [0, 1] | Urgency level |
| 10 | `crop_stress_index` | numeric | [0, 1] | Crop stress |
| 11 | `temperature_celsius` | numeric | [25, 40] | Daily max temperature |
| 12 | `humidity_percent` | numeric | [40, 80] | Relative humidity |
| 13 | `rainfall_mm` | numeric | [0, 25] | Daily rainfall |
| 14 | `crop_type_encoded` | categorical | {0,...,8} | Crop type encoding |
| 15 | `soil_type_encoded` | categorical | {0,1,2,3} | Soil type encoding |
| 16 | `growth_stage_encoded` | categorical | {0,1,2,3,4} | Phenological stage |
| 17 | `season_encoded` | categorical | {0,1,2,3} | Season encoding |
| 18 | `area_x_etc` | numeric | derived | farm_area_hectares × ET_c |
| 19 | `urgency_x_stress` | numeric | derived | urgency_score × crop_stress_index |
| 20 | `et0_x_kc` | numeric | derived | ET_0 × K_c (= etc_mm_per_day) |
| 21 | `rain_deficit` | numeric | derived | simple deficit metric |
| 22 | `flexibility_window` | numeric | derived | flexibility_score × irrigation_window_hours |

**Encoding details**:
- `crop_type_encoded`, `soil_type_encoded`, `growth_stage_encoded`, `season_encoded` are one-hot or label encoded (handled by `OneHotEncoder` in the preprocessing pipeline)
- All numeric features are scaled via `StandardScaler` fitted on train split only

## 3. Target Variable

| Attribute | Value |
|-----------|-------|
| Name | `water_demand_m3` |
| Units | cubic metres per day (m³/day) |
| Formula | `ET_c × farm_area_hectares × 10` where `ET_c = ET_0 × K_c` |
| Base (no noise) | Deterministic FAO-56 calculation |
| Noise | ±15% Gaussian, clamped to [5, 800] m³/day |
| Disclaimer | "Based on synthetic data generated via FAO-56 single-crop-coefficient method" |

## 4. FarmerAgent Attributes

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `farmer_id` | str | Unique identifier | Generated as `farmer_{i}` |
| `name` | str | Display name | `"Farmer {i}"` |
| `crop` | str | Crop type name | Wheat, sugar_cane, cotton, rice, maize, sorghum, banana, groundnut |
| `farm_area` | float | Farm area in hectares | Same as `farm_area_hectares` |
| `soil_type` | str | Soil type name | Sandy, loamy, clay, lateritic |
| `growth_stage` | str | Growth stage name | Seedling, vegetative, flowering, maturity, harvest |
| `season` | str | Season name | Winter, summer, monsoon, post-monsoon |
| `predicted_water_demand` | float | m³/day demand target | From ML model or scenario generation |
| `minimum_water_requirement` | float | m³/day minimum for crop survival | Derived from FAO-56 crop requirements |
| `maximum_water_requirement` | float | m³/day maximum physical capacity | Derived from irrigation system limits |
| `preferred_start_time` | int | Hour (0-23) preferred for irrigation | From `preferred_start_hour` |
| `urgency` | float | Urgency level [0,1] | From `urgency_score` |
| `crop_sensitivity` | float | Crop sensitivity to water stress [0,1] | From `kc_value` / crop type |
| `flexibility` | float | Schedule flexibility [0,1] | From `flexibility_score` |
| `utility_weights` | dict | Weights for utility function components | Fixed: {water: 0.4, time: 0.3, crop: 0.2, stress: 0.1} |
| `batna` | NamedTuple | BATNA fallback configuration | `fallback_utility` in [0, 1] typically 0.3 |
| `preferences` | NamedTuple | Irrigation preference window | preferred_start_hour, preferred_end_hour, acceptable_start_hour, acceptable_end_hour |

## 5. Allocation Result Schema

| Field | Type | Description |
|-------|------|-------------|
| `farmer_id` | str | Farmer identifier |
| `allocated_water_m3` | float | Water allocated (m³), post-solve and verified |
| `predicted_demand_m3` | float | Farmer's predicted water demand (m³) |
| `minimum_requirement_m3` | float | Farmer's minimum requirement (m³) |
| `maximum_requirement_m3` | float | Farmer's maximum permitted allocation (m³) |
| `urgency` | float | Urgency level [0,1] |
| `crop_sensitivity` | float | Crop sensitivity [0,1] |
| `growth_stage` | str | Growth stage name |
| `crop` | str | Crop name |
| `constraint_status` | str | "satisfied", "at_maximum", or "minimum_relaxed" |
| `explanation_metadata` | dict | Round-trip metadata: predicted_demand, allocated, minimum, maximum, unmet_demand, minimum_shortfall, urgency, crop_sensitivity, growth_stage, crop, minimum_requirements_feasible, constraint_status |
| `satisfaction_ratio` | float | allocated / predicted_demand, clamped to [0,1] |

### 5.1 Constraint Verification Result

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | bool | All hard constraints (H1/H2/H3) satisfied |
| `total_water_ok` | bool | total_allocated <= available_water + tolerance |
| `non_negative_ok` | bool | All allocations >= 0 |
| `maximum_ok` | bool | All allocations <= maximum_requirement |
| `no_nan_ok` | bool | No NaN or Inf values |
| `all_farmers_present` | bool | All expected farmer IDs in output |
| `violations` | list[str] | List of constraint violation strings (empty if valid) |
| `tolerance_m3` | float | Tolerance used for water balance check (1e-6) |

## 6. Negotiation Schema

### 6.1 FarmerResponse

| Field | Type | Description |
|-------|------|-------------|
| `farmer_id` | str | Farmer identifier |
| `allocation_m3` | float | Proposed allocation (m³) |
| `utility` | float | U_i ∈ [0,1] at proposed allocation |
| `batna_utility` | float | BATNA fallback utility ∈ [0,1] |
| `surplus` | float | utility - batna_utility |
| `response_type` | ResponseType | ACCEPT / REQUEST_CHANGE / REJECT |
| `is_batna_protected` | bool | True if utility < batna_utility (forces REJECT) |
| `satisfaction_ratio` | float | allocation / predicted_demand, clamped [0,1] |
| `minimum_met` | bool | allocation >= minimum_water_requirement |
| `reason` | str | Human-readable explanation (audit trail) |
| `round_number` | int | Which negotiation round |

### 6.2 Proposal

| Field | Type | Description |
|-------|------|-------------|
| `proposal_id` | str | Unique proposal identifier |
| `round_number` | int | Current round number |
| `proposed_allocation` | dict | farmer_id → m³ (LP-verified) |
| `target_preferences` | dict | farmer_id → negotiated ask (m³) |
| `nash_objective` | float | Σlog(max(surplus_i, 1e-6)) for this proposal |
| `fairness_score` | float | Jain's Index on proposed allocation |
| `solver_status` | str | "optimal", "relaxed", "infeasible", "error" |
| `is_improvement` | bool | True if Nash objective improved vs. previous round |
| `proposed_by` | str | "mediator" or "initial" |

### 6.3 Concession

| Field | Type | Description |
|-------|------|-------------|
| `concession_id` | str | Unique concession identifier |
| `farmer_id` | str | Farmer identifier |
| `round_number` | int | Round in which concession was made |
| `previous_ask_m3` | float | Farmer's ask before this concession (m³) |
| `new_ask_m3` | float | Farmer's ask after this concession (m³) |
| `concession_amount_m3` | float | previous_ask - new_ask (m³) |
| `concession_ratio` | float | concession_amount / (previous_ask - minimum_requirement) |
| `flexibility_factor` | float | farmer's flexibility [0,1] |
| `urgency_factor` | float | 1 - farmer's urgency [0,1] |
| `reason` | str | Computational description |

### 6.4 NegotiationRound

| Field | Type | Description |
|-------|------|-------------|
| `round_number` | int | Round number |
| `current_allocation` | dict | farmer_id → m³ |
| `farmer_responses` | list[FarmerResponse] | One per farmer |
| `utilities` | dict | farmer_id → utility ∈ [0,1] |
| `batna_utilities` | dict | farmer_id → batna_utility ∈ [0,1] |
| `surpluses` | dict | farmer_id → surplus (utility - batna) |
| `nash_objective` | float | Σlog(max(surplus_i, 1e-6)) |
| `fairness_score` | float | Jain's Index |
| `n_accepting` | int | Count of ACCEPT responses |
| `n_requesting_change` | int | Count of REQUEST_CHANGE responses |
| `n_rejecting` | int | Count of REJECT responses |
| `proposed_changes` | dict | farmer_id → proposed_m3 change |
| `accepted_concessions` | list[Concession] | Concessions accepted this round |
| `solver_status` | str | WaterAllocator status |
| `explanation` | str | Human-readable round description |
| `round_start_at` | str | ISO-8601 UTC timestamp |

### 6.5 NegotiationSession

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | str | Unique session identifier |
| `scenario_id` | str | Originating scenario type |
| `farmer_ids` | list[str] | Participating farmer identifiers |
| `available_water_m3` | float | Total available water |
| `initial_allocation` | dict | farmer_id → m³ (first LP solve) |
| `current_allocation` | dict | farmer_id → m³ (latest) |
| `current_round` | int | Current round number |
| `max_rounds` | int | Maximum negotiated rounds |
| `status` | AgreementStatus or None | AGREED/MAX_ROUNDS_REACHED/NO_FEASIBLE_IMPROVEMENT/FAILED |
| `rounds` | list[NegotiationRound] | Full round audit trail |
| `proposals` | list[Proposal] | All proposals made |
| `concessions` | list[Concession] | All concessions made |
| `utility_history` | list[dict] | Per-round {farmer_id: utility} |
| `best_nash_objective` | float | Best Nash objective found during negotiation |
| `best_allocation` | dict | farmer_id → m³ at best Nash point |
| `config` | NegotiationConfig | Negotiation configuration |
| `agreement` | Agreement or None | Final agreement if reached |
| `created_at` | str | ISO-8601 UTC creation timestamp |

### 6.6 Agreement

| Field | Type | Description |
|-------|------|-------------|
| `agreement_id` | str | Unique agreement identifier |
| `session_id` | str | Parent session identifier |
| `final_allocation` | dict | farmer_id → m³ (physically verified) |
| `participating_farmers` | list[str] | Farmer IDs in this negotiation |
| `final_utilities` | dict | farmer_id → utility ∈ [0,1] at final allocation |
| `batna_utilities` | dict | farmer_id → batna_utility ∈ [0,1] |
| `final_surplus` | dict | farmer_id → surplus (final_utility - batna_utility) |
| `concessions` | list[Concession] | Complete concession trail |
| `fairness_score` | float | Jain's Index on final allocation |
| `water_utilization` | float | total_allocated / available_water, clamped [0,1] |
| `negotiation_rounds` | int | Number of rounds that ran |
| `agreement_status` | AgreementStatus | AGREED / MAX_ROUNDS_REACHED / NO_FEASIBLE_IMPROVEMENT / FAILED |
| `termination_reason` | str | Human-readable termination cause |
| `round_fairness_history` | list[float] | Fairness per round (for UI) |
| `round_nash_history` | list[float] | Nash objective per round |
| `is_physically_valid` | bool | Final constraint verification result |
| `created_at` | str | ISO-8601 UTC creation timestamp |

## 7. API Response Schemas (selected endpoints)

| Endpoint | Response Type | Key Fields |
|----------|-------------|-----------|
| `GET /` | dict | message, status |
| `GET /health` | dict | api ("online"), database ("connected"/"unreachable") |
| `GET /scenarios` | dict | scenario_types (8 values) |
| `POST /predict` | dict | predicted_demand_m3, model_name, model_version |
| `POST /allocate` | dict | allocations (list of FarmerAllocation), verification (ConstraintVerificationResult), utilization, fairness_score, allocation_method |
| `POST /negotiate` | dict | agreement (Agreement summary: status, final_allocation, negotiation_rounds, fairness_score, water_utilization, termination_reason, round_nash_history, round_fairness_history) |
| `GET /explain/{farmer_id}` | dict | shap_values (array), base_value, feature_names, explanation_type, disclaimer |
| `GET /determinism-check` | dict | same_input_same_output (bool), seed_used |

---
*Data dictionary generated from source code inspection. Synthetic data disclaimer applies throughout.*