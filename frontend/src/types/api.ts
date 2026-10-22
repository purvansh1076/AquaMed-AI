/**
 * AquaMediAI — TypeScript API Definitions
 * Matches FastAPI Pydantic schemas in backend/app/schemas/api_models.py
 * and backend/app/explainability/explanation_types.py exactly.
 *
 * NOTE: All data represents synthetic academic demonstration scenarios.
 */

// --- Scenario Types ---
export type ScenarioType =
  | 'normal_water'
  | 'moderate_shortage'
  | 'severe_shortage'
  | 'sudden_rainfall'
  | 'canal_reduction'
  | 'simultaneous_demand'
  | 'high_urgency_farmer'
  | 'flexible_farmer';

export const SCENARIO_TYPE_LABELS: Record<ScenarioType, { label: string; description: string }> = {
  normal_water: {
    label: 'Normal Water Supply',
    description: 'Adequate canal water supply (~125% of aggregate demand). Minimal resource tension.',
  },
  moderate_shortage: {
    label: 'Moderate Water Shortage',
    description: 'Canal flow reduced to ~70-80% of aggregate demand. Minor allocation trade-offs required.',
  },
  severe_shortage: {
    label: 'Severe Water Shortage',
    description: 'Critical drought conditions (~40-60% supply). Multi-agent negotiation and concessions tested.',
  },
  sudden_rainfall: {
    label: 'Sudden Rainfall Event',
    description: 'Unplanned precipitation reduces farmer irrigation demands mid-cycle.',
  },
  canal_reduction: {
    label: 'Canal Capacity Reduction',
    description: 'Upstream infrastructure maintenance limits peak canal delivery capacity.',
  },
  simultaneous_demand: {
    label: 'Simultaneous Peak Demand',
    description: 'Multiple farmers request peak water during identical daily irrigation time windows.',
  },
  high_urgency_farmer: {
    label: 'High Urgency Farmer',
    description: 'One farmer exhibits high crop water stress index, requiring prioritized allocation.',
  },
  flexible_farmer: {
    label: 'Flexible Farmer Concessions',
    description: 'One or more farmers have drought-tolerant crops and wide window flexibility.',
  },
};

// --- Reason Codes (from Phase 7) ---
export const REASON_CODES = {
  RESOURCE_SHORTAGE: 'RESOURCE_SHORTAGE',
  WATER_SURPLUS: 'WATER_SURPLUS',
  HIGH_URGENCY: 'HIGH_URGENCY',
  HIGH_CROP_SENSITIVITY: 'HIGH_CROP_SENSITIVITY',
  MINIMUM_REQUIREMENT: 'MINIMUM_REQUIREMENT',
  MAXIMUM_REQUIREMENT: 'MAXIMUM_REQUIREMENT',
  CANAL_CAPACITY: 'CANAL_CAPACITY',
  WINDOW_CONFLICT: 'WINDOW_CONFLICT',
  FAIRNESS_ADJUSTMENT: 'FAIRNESS_ADJUSTMENT',
  NEGOTIATION_CONCESSION: 'NEGOTIATION_CONCESSION',
  BATNA_PROTECTION: 'BATNA_PROTECTION',
  UNMET_DEMAND: 'UNMET_DEMAND',
  FULL_DEMAND_SATISFACTION: 'FULL_DEMAND_SATISFACTION',
} as const;

export type ReasonCode = (typeof REASON_CODES)[keyof typeof REASON_CODES];

// --- Request Schemas ---

export interface ScenarioRunRequest {
  scenario_type: ScenarioType;
  n_farmers?: number;
  seed?: number;
  model_name?: 'XGBoost' | 'RandomForest' | string;
  available_water_override_m3?: number | null;
}

export interface FarmerInputData {
  farmer_id: string;
  crop_type: string;
  soil_type?: string;
  growth_stage?: string;
  season?: string;
  farm_area_hectares: number;
  et0_mm_per_day: number;
  kc_value: number;
  etc_mm_per_day: number;
  soil_whc_mm_per_m?: number;
  preferred_start_hour?: number;
  irrigation_window_hours?: number;
  flexibility_score?: number;
  urgency_score?: number;
  crop_stress_index?: number;
  temperature_celsius?: number;
  humidity_percent?: number;
  rainfall_mm?: number;
}

export interface PredictionRequest {
  farmer_data: FarmerInputData;
  model_name?: string;
}

export interface PredictionBatchRequest {
  farmers: FarmerInputData[];
  model_name?: string;
}

export interface ConflictRequest {
  scenario_type: ScenarioType;
  n_farmers?: number;
  seed?: number;
  model_name?: string;
  available_water_override_m3?: number | null;
}

export interface AllocationRequest {
  scenario_type: ScenarioType;
  n_farmers?: number;
  seed?: number;
  model_name?: string;
  available_water_override_m3?: number | null;
}

export interface NegotiationRequest {
  scenario_type: ScenarioType;
  n_farmers?: number;
  seed?: number;
  model_name?: string;
  available_water_override_m3?: number | null;
  max_rounds?: number;
  acceptance_threshold?: number;
  rejection_threshold?: number;
}

// --- Response Schemas ---

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  pipeline: string;
  disclaimer: string;
}

export interface PredictionResponse {
  farmer_id: string | null;
  predicted_water_demand_m3: number;
  model_name: string;
  model_version: string;
  warning: string | null;
  input_summary: Record<string, unknown>;
}

export interface PredictionBatchResponse {
  predictions: PredictionResponse[];
  count: number;
}

export interface FarmerAllocationResponse {
  farmer_id: string;
  allocated_water_m3: number;
  predicted_demand_m3: number;
  minimum_requirement_m3: number;
  maximum_requirement_m3: number;
  unmet_demand_m3: number;
  minimum_shortfall_m3: number;
  satisfaction_ratio: number;
  urgency: number;
  crop_sensitivity: number;
  growth_stage: string;
  crop: string;
  constraint_status: string;
}

export interface ConstraintVerificationResponse {
  is_valid: boolean;
  total_water_ok: boolean;
  non_negative_ok: boolean;
  maximum_ok: boolean;
  no_nan_ok: boolean;
  all_farmers_present: boolean;
  violations: string[];
}

export interface AllocationResponse {
  scenario_id: string;
  solver_status: string;
  objective_value: number;
  allocation_method: string;
  available_water_m3: number;
  total_demand_m3: number;
  total_allocated_m3: number;
  remaining_water_m3: number;
  utilization: number;
  fairness_score: number;
  average_satisfaction: number;
  total_unmet_demand_m3: number;
  total_minimum_shortfall_m3: number;
  minimum_requirements_feasible: boolean;
  n_farmers: number;
  solver_wall_time_ms: number;
  verification: ConstraintVerificationResponse;
  allocations: FarmerAllocationResponse[];
}

export interface FarmerResponseModel {
  farmer_id: string;
  allocation_m3: number;
  utility: number;
  batna_utility: number;
  surplus: number;
  response_type: string;
  is_batna_protected: boolean;
  satisfaction_ratio: number;
  minimum_met: boolean;
  reason: string;
  round_number: number;
}

export interface ConcessionResponse {
  farmer_id: string;
  round_number: number;
  previous_ask_m3: number;
  new_ask_m3: number;
  concession_amount_m3: number;
  concession_ratio: number;
  flexibility_factor: number;
  urgency_factor: number;
  reason: string;
  rationale?: string;
}

export interface AgreementResponse {
  agreement_id: string;
  session_id: string;
  final_allocation: Record<string, number>;
  participating_farmers: string[];
  final_utilities: Record<string, number>;
  batna_utilities: Record<string, number>;
  final_surplus: Record<string, number>;
  concessions: ConcessionResponse[];
  fairness_score: number;
  water_utilization: number;
  negotiation_rounds: number;
  agreement_status: string;
  termination_reason: string;
  round_fairness_history: number[];
  round_nash_history: number[];
  is_physically_valid: boolean;
}

export interface NegotiationRoundResponse {
  round_number: number;
  n_accepting: number;
  n_requesting_change: number;
  n_rejecting: number;
  nash_objective: number;
  fairness_score: number;
  solver_status: string;
}

export interface NegotiationResponse {
  session_id: string;
  scenario_id: string;
  n_rounds: number;
  agreement_status: string;
  termination_reason: string;
  initial_allocation: Record<string, number>;
  best_allocation: Record<string, number>;
  rounds: NegotiationRoundResponse[];
  agreement: AgreementResponse | null;
}

export interface ConflictReportResponse {
  conflict_id: string;
  conflict_type: string;
  severity: string;
  severity_score: number;
  involved_farmer_ids: string[];
  available_water_m3: number;
  total_demand_m3: number;
  resource_gap_m3: number;
  explanation: string;
}

export interface ScenarioConflictReportResponse {
  scenario_id: string;
  n_farmers: number;
  total_demand_m3: number;
  available_water_m3: number;
  resource_gap_m3: number;
  overall_shortage_ratio: number;
  total_conflicts: number;
  highest_severity: string;
  conflicts: ConflictReportResponse[];
}

export interface FeatureContributionExplanation {
  feature: string;
  raw_value: number;
  shap_value: number;
  direction: 'increases' | 'decreases' | 'negligible';
  abs_shap: number;
  rank: number;
  rationale: string;
}

export interface PredictionExplanation {
  farmer_id: string | null;
  predicted_demand_m3: number;
  model_name: string;
  model_version: string;
  base_value: number;
  top_contributors: FeatureContributionExplanation[];
  positive_contributors: FeatureContributionExplanation[];
  negative_contributors: FeatureContributionExplanation[];
  all_features: FeatureContributionExplanation[];
  shap_available: boolean;
  summary: string;
  data_disclaimer: string;
}

export interface ConstraintExplanation {
  constraint_name: string;
  actual_value: number;
  limit: number;
  status: 'satisfied' | 'violated' | 'relaxed' | 'not_applicable';
  is_hard: boolean;
  rationale: string;
  farmer_id?: string | null;
}

export interface AllocationExplanation {
  farmer_id: string;
  predicted_demand_m3: number;
  allocated_m3: number;
  unmet_demand_m3: number;
  minimum_requirement_m3: number;
  maximum_requirement_m3: number;
  satisfaction_ratio: number;
  urgency: number;
  crop_sensitivity: number;
  growth_stage: string;
  crop: string;
  constraint_status: string;
  reason_codes: string[];
  constraint_explanations: ConstraintExplanation[];
  rationale: string;
}

export interface FairnessExplanation {
  fairness_score: number;
  n_farmers: number;
  satisfaction_ratios: Record<string, number>;
  average_satisfaction: number;
  is_minimum_requirements_feasible: boolean;
  rationale: string;
  note: string;
}

export interface ConflictExplanationEntry {
  conflict_id: string;
  conflict_type: string;
  severity: string;
  severity_score: number;
  involved_farmer_ids: string[];
  available_water_m3: number;
  total_demand_m3: number;
  total_minimum_requirement_m3: number;
  resource_gap_m3: number;
  minimum_requirement_gap_m3: number;
  evidence: Record<string, unknown>;
  rationale: string;
}

export interface BATNAExplanation {
  farmer_id: string;
  batna_utility: number;
  batna_allocation_m3: number;
  negotiated_utility: number | null;
  negotiated_allocation_m3: number | null;
  is_above_batna: boolean | null;
  surplus: number | null;
  rationale: string;
}

export interface NashObjectiveExplanation {
  formula: string;
  floor_value: number;
  final_value: number;
  initial_value: number | null;
  trajectory: number[];
  interpretation: string;
  disclaimer: string;
}

export interface NegotiationExplanation {
  session_id: string;
  scenario_id: string;
  farmer_ids: string[];
  available_water_m3: number;
  n_rounds: number;
  agreement_status: string;
  termination_reason: string;
  round_explanations: Record<string, unknown>[];
  batna_explanations: BATNAExplanation[];
  concession_explanations: Record<string, unknown>[];
  nash_objective_explanation: NashObjectiveExplanation;
  final_fairness_score: number;
  final_water_utilization: number;
  final_allocation: Record<string, number>;
  final_utilities: Record<string, number>;
  summary: string;
}

export interface ExplanationResponse {
  scenario_id: string;
  summary: string;
  prediction_explanations: PredictionExplanation[];
  conflict_explanations: ConflictExplanationEntry[];
  allocation_explanations: AllocationExplanation[];
  fairness_explanation: FairnessExplanation | null;
  constraint_explanations: ConstraintExplanation[];
  negotiation_explanation: NegotiationExplanation | null;
  final_allocation: Record<string, number>;
  final_utilities: Record<string, number>;
  agreement_status: string | null;
  all_reason_codes: string[];
  unresolved_issues: string[];
  data_disclaimer: string;
}

export interface FinalDecisionSummary {
  scenario_id: string;
  summary: string;
  agreement_status: string;
  termination_reason?: string;
  fairness_score: number;
  water_utilization: number;
  negotiation_rounds: number;
  is_physically_valid: boolean;
  [key: string]: unknown;
}

export interface ScenarioRunResponse {
  scenario_id: string;
  status: string;
  scenario_type: string;
  n_farmers: number;
  available_water_m3: number;
  total_demand_m3: number;
  predictions: PredictionResponse[];
  farmers: Record<string, unknown>[];
  conflicts: ScenarioConflictReportResponse;
  initial_allocation: AllocationResponse;
  negotiation: NegotiationResponse | null;
  final_allocation: AllocationResponse;
  explanations: ExplanationResponse;
  final_decision: FinalDecisionSummary;
}

export interface ErrorResponse {
  error: string;
  detail: string;
  status_code: number;
}
