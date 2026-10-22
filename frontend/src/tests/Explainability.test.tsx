import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import React from 'react';
import { ScenarioContext } from '../context/ScenarioContext';
import { ViewModeProvider, useViewMode } from '../context/ViewModeContext';
import { ExplainabilityPage } from '../pages/ExplainabilityPage';
import { DebugPage } from '../pages/DebugPage';
import type { ScenarioRunResponse } from '../types/api';

const mockExplainabilityScenario: ScenarioRunResponse = {
  scenario_id: 'scenario_explain_test',
  status: 'success',
  scenario_type: 'moderate_shortage',
  n_farmers: 3,
  available_water_m3: 3500,
  total_demand_m3: 4200,
  farmers: [
    {
      farmer_id: 'farmer_1',
      crop_type: 'Wheat',
      farm_area_hectares: 2.5,
    },
    {
      farmer_id: 'farmer_2',
      crop_type: 'Cotton',
      farm_area_hectares: 3.0,
    },
    {
      farmer_id: 'farmer_3',
      crop_type: 'Gram',
      farm_area_hectares: 1.8,
    },
  ],
  predictions: [
    {
      farmer_id: 'farmer_1',
      predicted_water_demand_m3: 1500,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
    {
      farmer_id: 'farmer_2',
      predicted_water_demand_m3: 1700,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
    {
      farmer_id: 'farmer_3',
      predicted_water_demand_m3: 1000,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
  ],
  conflicts: {
    scenario_id: 'scenario_explain_test',
    n_farmers: 3,
    total_demand_m3: 4200,
    available_water_m3: 3500,
    resource_gap_m3: 700,
    overall_shortage_ratio: 0.166,
    total_conflicts: 3,
    highest_severity: 'HIGH',
    conflicts: [
      {
        conflict_id: 'conf_1',
        conflict_type: 'RESOURCE_SHORTAGE',
        severity: 'HIGH',
        severity_score: 0.85,
        involved_farmer_ids: ['farmer_1', 'farmer_2', 'farmer_3'],
        resource_gap_m3: 700,
        explanation: 'Total available water was lower than total farmer demand.',
      },
      {
        conflict_id: 'conf_2',
        conflict_type: 'IRRIGATION_WINDOW_OVERLAP',
        severity: 'MEDIUM',
        severity_score: 0.65,
        involved_farmer_ids: ['farmer_1', 'farmer_2'],
        resource_gap_m3: 0,
        explanation: 'Some farmers needed water during overlapping irrigation periods.',
      },
      {
        conflict_id: 'conf_3',
        conflict_type: 'IRRIGATION_WINDOW_OVERLAP',
        severity: 'MEDIUM',
        severity_score: 0.62,
        involved_farmer_ids: ['farmer_2', 'farmer_3'],
        resource_gap_m3: 0,
        explanation: 'Some farmers needed water during overlapping irrigation periods.',
      },
    ],
  },
  initial_allocation: {
    scenario_id: 'scenario_explain_test',
    solver_status: 'OPTIMAL',
    objective_value: 3500,
    allocation_method: 'lp_optimal',
    available_water_m3: 3500,
    total_demand_m3: 4200,
    total_allocated_m3: 3500,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.9412,
    average_satisfaction: 0.833,
    total_unmet_demand_m3: 700,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 10,
    verification: {
      is_valid: true,
      total_water_ok: true,
      non_negative_ok: true,
      maximum_ok: true,
      no_nan_ok: true,
      all_farmers_present: true,
      violations: [],
    },
    allocations: [
      {
        farmer_id: 'farmer_1',
        allocated_water_m3: 1250,
        predicted_demand_m3: 1500,
        minimum_requirement_m3: 600,
        maximum_requirement_m3: 1500,
        unmet_demand_m3: 250,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.833,
        urgency: 0.75,
        crop_sensitivity: 0.8,
        growth_stage: 'Vegetative',
        crop: 'Wheat',
        constraint_status: 'SATISFIED',
      },
      {
        farmer_id: 'farmer_2',
        allocated_water_m3: 1450,
        predicted_demand_m3: 1700,
        minimum_requirement_m3: 700,
        maximum_requirement_m3: 1700,
        unmet_demand_m3: 250,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.852,
        urgency: 0.8,
        crop_sensitivity: 0.85,
        growth_stage: 'Flowering',
        crop: 'Cotton',
        constraint_status: 'SATISFIED',
      },
      {
        farmer_id: 'farmer_3',
        allocated_water_m3: 800,
        predicted_demand_m3: 1000,
        minimum_requirement_m3: 400,
        maximum_requirement_m3: 1000,
        unmet_demand_m3: 200,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.8,
        urgency: 0.65,
        crop_sensitivity: 0.7,
        growth_stage: 'Vegetative',
        crop: 'Gram',
        constraint_status: 'SATISFIED',
      },
    ],
  },
  negotiation: {
    session_id: 'session_explain_1',
    scenario_id: 'scenario_explain_test',
    n_rounds: 3,
    agreement_status: 'AGREEMENT_REACHED',
    termination_reason: 'Unanimous acceptance',
    initial_allocation: { farmer_1: 1200, farmer_2: 1400, farmer_3: 900 },
    best_allocation: { farmer_1: 1250, farmer_2: 1450, farmer_3: 800 },
    rounds: [
      {
        round_number: 1,
        n_accepting: 1,
        n_requesting_change: 2,
        n_rejecting: 0,
        nash_objective: 3.45,
        fairness_score: 0.91,
        solver_status: 'OPTIMAL',
      },
      {
        round_number: 2,
        n_accepting: 2,
        n_requesting_change: 1,
        n_rejecting: 0,
        nash_objective: 3.52,
        fairness_score: 0.93,
        solver_status: 'OPTIMAL',
      },
      {
        round_number: 3,
        n_accepting: 3,
        n_requesting_change: 0,
        n_rejecting: 0,
        nash_objective: 3.58,
        fairness_score: 0.9412,
        solver_status: 'OPTIMAL',
      },
    ],
    agreement: null,
  },
  final_allocation: {
    scenario_id: 'scenario_explain_test',
    solver_status: 'OPTIMAL',
    objective_value: 3500,
    allocation_method: 'lp_optimal',
    available_water_m3: 3500,
    total_demand_m3: 4200,
    total_allocated_m3: 3500,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.9412,
    average_satisfaction: 0.833,
    total_unmet_demand_m3: 700,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 10,
    verification: {
      is_valid: true,
      total_water_ok: true,
      non_negative_ok: true,
      maximum_ok: true,
      no_nan_ok: true,
      all_farmers_present: true,
      violations: [],
    },
    allocations: [
      {
        farmer_id: 'farmer_1',
        allocated_water_m3: 1250,
        predicted_demand_m3: 1500,
        minimum_requirement_m3: 600,
        maximum_requirement_m3: 1500,
        unmet_demand_m3: 250,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.833,
        urgency: 0.75,
        crop_sensitivity: 0.8,
        growth_stage: 'Vegetative',
        crop: 'Wheat',
        constraint_status: 'SATISFIED',
      },
      {
        farmer_id: 'farmer_2',
        allocated_water_m3: 1450,
        predicted_demand_m3: 1700,
        minimum_requirement_m3: 700,
        maximum_requirement_m3: 1700,
        unmet_demand_m3: 250,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.852,
        urgency: 0.8,
        crop_sensitivity: 0.85,
        growth_stage: 'Flowering',
        crop: 'Cotton',
        constraint_status: 'SATISFIED',
      },
      {
        farmer_id: 'farmer_3',
        allocated_water_m3: 800,
        predicted_demand_m3: 1000,
        minimum_requirement_m3: 400,
        maximum_requirement_m3: 1000,
        unmet_demand_m3: 200,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.8,
        urgency: 0.65,
        crop_sensitivity: 0.7,
        growth_stage: 'Vegetative',
        crop: 'Gram',
        constraint_status: 'SATISFIED',
      },
    ],
  },
  explanations: {
    scenario_id: 'scenario_explain_test',
    summary: 'Available water was lower than total demand. Allocations optimized under constraints.',
    prediction_explanations: [
      {
        farmer_id: 'farmer_1',
        predicted_demand_m3: 1500,
        model_name: 'XGBoost',
        shap_available: false,
        summary: 'Predicted demand driven by vegetative growth stage and baseline ET0.',
        top_contributors: [],
      },
      {
        farmer_id: 'farmer_2',
        predicted_demand_m3: 1700,
        model_name: 'XGBoost',
        shap_available: true,
        summary: 'Predicted demand driven by flowering stage.',
        top_contributors: [
          { feature: 'growth_stage', direction: 'increases', impact_score: 0.4 },
        ],
      },
    ],
    conflict_explanations: [
      {
        conflict_id: 'conf_1',
        conflict_type: 'RESOURCE_SHORTAGE',
        severity: 'HIGH',
        severity_score: 0.85,
        involved_farmer_ids: ['farmer_1', 'farmer_2', 'farmer_3'],
        resource_gap_m3: 700,
        explanation: 'Total water available was lower than total farmer demand.',
      },
      {
        conflict_id: 'conf_2',
        conflict_type: 'IRRIGATION_WINDOW_OVERLAP',
        severity: 'MEDIUM',
        severity_score: 0.65,
        involved_farmer_ids: ['farmer_1', 'farmer_2'],
        resource_gap_m3: 0,
        explanation: 'Some farmers needed water during overlapping irrigation periods.',
      },
      {
        conflict_id: 'conf_3',
        conflict_type: 'IRRIGATION_WINDOW_OVERLAP',
        severity: 'MEDIUM',
        severity_score: 0.62,
        involved_farmer_ids: ['farmer_2', 'farmer_3'],
        resource_gap_m3: 0,
        explanation: 'Some farmers needed water during overlapping irrigation periods.',
      },
    ],
    allocation_explanations: [
      {
        farmer_id: 'farmer_1',
        predicted_demand_m3: 1500,
        allocated_m3: 1250,
        unmet_demand_m3: 250,
        minimum_requirement_m3: 600,
        maximum_requirement_m3: 1500,
        satisfaction_ratio: 0.833,
        urgency: 0.75,
        crop_sensitivity: 0.8,
        growth_stage: 'Vegetative',
        crop: 'Wheat',
        constraint_status: 'SATISFIED',
        reason_codes: ['RESOURCE_SHORTAGE', 'HIGH_URGENCY', 'MINIMUM_REQUIREMENT'],
        constraint_explanations: [],
        rationale: 'The allocation reflects a combination of predicted demand, urgency, crop sensitivity and the active constraints.',
      },
    ],
    fairness_explanation: {
      fairness_score: 0.9412,
      rationale: 'Jain’s Fairness Index measured at 0.9412, indicating balanced distribution.',
      is_fair: true,
    },
    constraint_explanations: [
      {
        constraint_name: 'Total Water Availability',
        status: 'satisfied',
        rationale: 'Total allocated water 3500 m³ <= available supply 3500 m³.',
      },
      {
        constraint_name: 'Minimum Survival Requirement',
        status: 'satisfied',
        rationale: 'All farmers received at least their minimum requirement.',
      },
    ],
    negotiation_explanation: {
      session_id: 'session_explain_1',
      scenario_id: 'scenario_explain_test',
      farmer_ids: ['farmer_1', 'farmer_2', 'farmer_3'],
      available_water_m3: 3500,
      n_rounds: 3,
      agreement_status: 'AGREEMENT_REACHED',
      termination_reason: 'Unanimous acceptance',
      round_explanations: [
        { round_number: 1, n_accepting: 1, n_requesting_change: 2, n_rejecting: 0 },
        { round_number: 2, n_accepting: 2, n_requesting_change: 1, n_rejecting: 0 },
        { round_number: 3, n_accepting: 3, n_requesting_change: 0, n_rejecting: 0 },
      ],
      batna_explanations: [
        { farmer_id: 'farmer_1', batna_utility: 0.5, protected: true },
        { farmer_id: 'farmer_2', batna_utility: 0.5, protected: true },
      ],
      concession_explanations: [
        { farmer_id: 'farmer_2', concession_amount_m3: 50 },
      ],
      nash_objective_explanation: {
        formula: 'sum(log(utility - batna))',
        interpretation: 'The system’s negotiation objective uses a surplus-based logarithmic formulation inspired by Nash bargaining. It is not a full Nash Bargaining Solution.',
      },
      final_fairness_score: 0.9412,
      final_water_utilization: 1.0,
      final_allocation: { farmer_1: 1250, farmer_2: 1450, farmer_3: 800 },
      final_utilities: { farmer_1: 0.83, farmer_2: 0.85, farmer_3: 0.8 },
      summary: 'Farmer agents evaluated the proposed allocation and reached unanimous agreement in round 3.',
    },
    final_allocation: { farmer_1: 1250, farmer_2: 1450, farmer_3: 800 },
    final_utilities: { farmer_1: 0.83, farmer_2: 0.85, farmer_3: 0.8 },
    agreement_status: 'AGREEMENT_REACHED',
    all_reason_codes: ['RESOURCE_SHORTAGE', 'HIGH_URGENCY', 'MINIMUM_REQUIREMENT'],
    unresolved_issues: [],
    data_disclaimer: 'Synthetic agronomic data for research verification.',
  },
  final_decision: {
    scenario_id: 'scenario_explain_test',
    summary: 'Mediation decision reached based on agronomic LP optimization and agent utility.',
    agreement_status: 'AGREEMENT_REACHED',
    termination_reason: 'Unanimous acceptance',
    fairness_score: 0.9412,
    water_utilization: 1.0,
    negotiation_rounds: 3,
    is_physically_valid: true,
  },
} as any as ScenarioRunResponse;

const mockScenarioContextValue: any = {
  scenarioResult: mockExplainabilityScenario,
  isLoading: false,
  error: null,
  runScenario: vi.fn(),
  resetScenario: vi.fn(),
  activeTab: 'explainability',
  setActiveTab: vi.fn(),
  history: [],
};

// Helper component that can switch viewMode
const ExplainabilityTestContainer: React.FC<{ initialMode?: 'farmer' | 'expert' }> = ({
  initialMode = 'farmer',
}) => {
  const { setViewMode } = useViewMode();

  React.useEffect(() => {
    setViewMode(initialMode);
  }, [initialMode, setViewMode]);

  return <ExplainabilityPage />;
};

describe('Explainability Page Redesign — Farmer View and Expert View', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('1. Farmer explanation summary renders with decision summary', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Title and Subtitle
    expect(screen.getByText('💧 Why Did I Get This Much Water?')).toBeInTheDocument();
    expect(screen.getByText(/AquaMediAI looked at the water available/i)).toBeInTheDocument();

    // Summary Card
    expect(screen.getByText('💧 Your Water Result')).toBeInTheDocument();
    expect(screen.getByText('1,250')).toBeInTheDocument(); // Water given
    expect(screen.getByText('1,500')).toBeInTheDocument(); // Water needed
    expect(screen.getByText('3,500')).toBeInTheDocument(); // Water available
  });

  it('2. Farmer-friendly reason codes render in plain language', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Reason code cards should display human translations
    expect(screen.getByText('💧 Water was limited')).toBeInTheDocument();
    expect(screen.getByText('🚨 Urgent crop needs')).toBeInTheDocument();
    expect(screen.getByText('💧 Minimum water need considered')).toBeInTheDocument();
    expect(
      screen.getByText('The system considered the minimum water requirement while allocating the available water.')
    ).toBeInTheDocument();
  });

  it('3. Raw reason codes are hidden from primary Farmer View until accordion expanded', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Raw reason code should NOT be visible initially
    expect(screen.queryByText('RESOURCE_SHORTAGE, HIGH_URGENCY, MINIMUM_REQUIREMENT')).not.toBeInTheDocument();

    // Expand accordion
    const accordionBtn = screen.getByRole('button', { name: /Technical Details/i });
    fireEvent.click(accordionBtn);

    // Now technical reason codes are visible inside the accordion
    expect(screen.getByText('RESOURCE_SHORTAGE, HIGH_URGENCY, MINIMUM_REQUIREMENT')).toBeInTheDocument();
  });

  it('4. Conflict grouping renders with count and human explanations', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('⚠️ What affected the water sharing?')).toBeInTheDocument();
    expect(screen.getByText('💧 Water shortage')).toBeInTheDocument();
    expect(screen.getByText('🕐 Timing conflicts')).toBeInTheDocument();
    expect(screen.getByText('2 timing conflicts were detected.')).toBeInTheDocument();
  });

  it('5. Agreement status renders correctly in Farmer View', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('🤝 Agreement Reached')).toBeInTheDocument();
    expect(screen.getByText('🤝 How was the plan agreed?')).toBeInTheDocument();
    expect(screen.getByText(/The system’s farmer agents evaluated the proposed water allocation/i)).toBeInTheDocument();
  });

  it('6. Expert Decision Summary renders with human-readable labels', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('🔬 Decision Explanation')).toBeInTheDocument();
    expect(screen.getByText(/Trace how AquaMediAI moved from predicted water demand/i)).toBeInTheDocument();
    expect(screen.getByText('1. Decision Summary')).toBeInTheDocument();
    expect(screen.getByText('Allocation Method: Optimal constrained allocation')).toBeInTheDocument();
  });

  it('7. Expert technical details remain structured and accessible across 7 sections', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('1. Decision Summary')).toBeInTheDocument();
    expect(screen.getByText('2. Why Water Was Needed')).toBeInTheDocument();
    expect(screen.getByText('3. What Problems Were Detected?')).toBeInTheDocument();
    expect(screen.getByText('4. How Was Water Allocated?')).toBeInTheDocument();
    expect(screen.getByText('5. Why Did Different Farmers Receive Different Amounts?')).toBeInTheDocument();
    expect(screen.getByText('6. Negotiation / Mediation')).toBeInTheDocument();
    expect(screen.getByText('🤝 Final Water-Sharing Agreement')).toBeInTheDocument();
  });

  it('8. SHAP unavailable state is handled gracefully with clear message', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    // For farmer_1, shap_available is false
    expect(
      screen.getByText('Detailed feature attribution was not available for this prediction.')
    ).toBeInTheDocument();

    // For farmer_2, shap_available is true with top contributors
    expect(screen.getByText('growth_stage')).toBeInTheDocument();
  });

  it('9. Actual fairness value is displayed only from API data', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    // 0.9412 formatted to 3 decimals is 0.941
    const fairnessElements = screen.getAllByText(/0.941/);
    expect(fairnessElements.length).toBeGreaterThanOrEqual(1);
  });

  it('10. Actual allocation method is displayed with plain-language explanation', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(
      screen.getByText('The optimization process found a feasible allocation while respecting the defined water constraints.')
    ).toBeInTheDocument();
  });

  it('11. Negotiation information is displayed with BATNA and Nash definitions', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('BATNA')).toBeInTheDocument();
    expect(screen.getByText('"Minimum acceptable alternative used by the negotiation logic."')).toBeInTheDocument();

    expect(screen.getByText('Nash-inspired objective')).toBeInTheDocument();
    expect(
      screen.getByText(
        '"The system\'s negotiation objective uses a surplus-based logarithmic formulation inspired by Nash bargaining. It is not a full Nash Bargaining Solution."'
      )
    ).toBeInTheDocument();
  });

  it('12. Raw API page still works as a separate developer link', () => {
    render(
      <MemoryRouter initialEntries={['/explainability']}>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <Routes>
              <Route path="/explainability" element={<ExplainabilityTestContainer initialMode="expert" />} />
              <Route path="/debug" element={<DebugPage />} />
            </Routes>
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    const link = screen.getByRole('link', { name: /View Raw API Payload/i });
    expect(link).toHaveAttribute('href', '/debug');
  });

  it('13. Farmer View and Expert View use the exact same scenario data', () => {
    const { unmount } = render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('1,250')).toBeInTheDocument();
    expect(screen.getByText('3,500')).toBeInTheDocument();
    unmount();

    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="expert" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    expect(screen.getAllByText(/3,500(\.0)?\s*m³/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/4,200(\.0)?\s*m³/i).length).toBeGreaterThanOrEqual(1);
  });

  it('14. No voice UI exists (no mic, speech, or audio controls)', () => {
    const { container } = render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioContext.Provider value={mockScenarioContextValue}>
            <ExplainabilityTestContainer initialMode="farmer" />
          </ScenarioContext.Provider>
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Verify absence of mic / speech / audio
    expect(container.querySelector('[aria-label*="voice" i]')).toBeNull();
    expect(container.querySelector('[aria-label*="mic" i]')).toBeNull();
    expect(container.querySelector('.voice-btn')).toBeNull();
    expect(container.querySelector('.mic-button')).toBeNull();
    expect(screen.queryByText(/voice/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/microphone/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/speech/i)).not.toBeInTheDocument();
  });
});
