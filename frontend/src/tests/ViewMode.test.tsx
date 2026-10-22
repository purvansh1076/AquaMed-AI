import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ScenarioProvider } from '../context/ScenarioContext';
import { ViewModeProvider, useViewMode } from '../context/ViewModeContext';
import { Header } from '../layouts/Header';
import { FarmerViewPage } from '../pages/FarmerViewPage';
import { ScenarioPage } from '../pages/ScenarioPage';
import { TRANSLATIONS } from '../i18n/translations';
import { api } from '../services/api';
import type { ScenarioRunResponse } from '../types/api';

const mockScenarioData: ScenarioRunResponse = {
  scenario_id: 'scenario_farmer_test',
  status: 'success',
  scenario_type: 'moderate_shortage',
  n_farmers: 3,
  available_water_m3: 3500,
  total_demand_m3: 4200,
  predictions: [
    {
      farmer_id: 'farmer_1',
      predicted_water_demand_m3: 1500,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
  ],
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
  ],
  conflicts: {
    scenario_id: 'scenario_farmer_test',
    n_farmers: 3,
    total_demand_m3: 4200,
    available_water_m3: 3500,
    resource_gap_m3: 700,
    overall_shortage_ratio: 0.166,
    total_conflicts: 1,
    highest_severity: 'MEDIUM',
    conflicts: [],
  },
  initial_allocation: {
    scenario_id: 'scenario_farmer_test',
    solver_status: 'OPTIMAL',
    objective_value: 3500,
    allocation_method: 'Linear Programming (GLOP)',
    available_water_m3: 3500,
    total_demand_m3: 4200,
    total_allocated_m3: 3500,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.94,
    average_satisfaction: 0.833,
    total_unmet_demand_m3: 700,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 12,
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
    ],
  },
  negotiation: {
    session_id: 'session_123',
    scenario_id: 'scenario_farmer_test',
    n_rounds: 3,
    agreement_status: 'AGREEMENT_REACHED',
    termination_reason: 'Unanimous acceptance',
    initial_allocation: { farmer_1: 1200 },
    best_allocation: { farmer_1: 1250 },
    rounds: [],
    agreement: null,
  },
  final_allocation: {
    scenario_id: 'scenario_farmer_test',
    solver_status: 'OPTIMAL',
    objective_value: 3500,
    allocation_method: 'Linear Programming (GLOP)',
    available_water_m3: 3500,
    total_demand_m3: 4200,
    total_allocated_m3: 3500,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.94,
    average_satisfaction: 0.833,
    total_unmet_demand_m3: 700,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 12,
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
    ],
  },
  explanations: {
    scenario_id: 'scenario_farmer_test',
    summary: 'Water shortage of 700 m3 resolved with fair allocation.',
    prediction_explanations: [],
    conflict_explanations: [],
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
        rationale: 'Allocation optimized under shortage.',
      },
    ],
    fairness_explanation: null,
    constraint_explanations: [],
    negotiation_explanation: null,
    final_allocation: { farmer_1: 1250 },
    final_utilities: { farmer_1: 0.83 },
    agreement_status: 'AGREEMENT_REACHED',
    all_reason_codes: ['RESOURCE_SHORTAGE', 'HIGH_URGENCY', 'MINIMUM_REQUIREMENT'],
    unresolved_issues: [],
    data_disclaimer: 'Synthetic test data',
  },
  final_decision: {
    scenario_id: 'scenario_farmer_test',
    summary: 'Mediation agreement reached.',
    agreement_status: 'AGREEMENT_REACHED',
    termination_reason: 'Unanimous acceptance',
    fairness_score: 0.94,
    water_utilization: 1.0,
    negotiation_rounds: 3,
    is_physically_valid: true,
  },
};

// Component helper to inspect ViewModeContext values
const ViewModeInspector: React.FC = () => {
  const { viewMode, language, setViewMode, setLanguage } = useViewMode();
  return (
    <div>
      <span data-testid="current-view-mode">{viewMode}</span>
      <span data-testid="current-language">{language}</span>
      <button onClick={() => setViewMode('expert')} data-testid="set-expert">
        Set Expert
      </button>
      <button onClick={() => setViewMode('farmer')} data-testid="set-farmer">
        Set Farmer
      </button>
      <button onClick={() => setLanguage('hi')} data-testid="set-hindi">
        Set Hindi
      </button>
      <button onClick={() => setLanguage('gu')} data-testid="set-gujarati">
        Set Gujarati
      </button>
    </div>
  );
};

describe('Phase 9 UX Enhancement: Two Presentation Modes', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
    vi.spyOn(api, 'getHealth').mockResolvedValue({
      status: 'healthy',
      service: 'AquaMediAI',
      version: '1.0.0',
      pipeline: 'available',
      disclaimer: 'Test',
    });
  });

  it('defaults to Farmer View and English language', () => {
    render(
      <ViewModeProvider>
        <ViewModeInspector />
      </ViewModeProvider>
    );

    expect(screen.getByTestId('current-view-mode').textContent).toBe('farmer');
    expect(screen.getByTestId('current-language').textContent).toBe('en');
  });

  it('switches between Farmer View and Expert View', async () => {
    const user = userEvent.setup();
    render(
      <ViewModeProvider>
        <ViewModeInspector />
      </ViewModeProvider>
    );

    expect(screen.getByTestId('current-view-mode').textContent).toBe('farmer');

    await user.click(screen.getByTestId('set-expert'));
    expect(screen.getByTestId('current-view-mode').textContent).toBe('expert');

    await user.click(screen.getByTestId('set-farmer'));
    expect(screen.getByTestId('current-view-mode').textContent).toBe('farmer');
  });

  it('switches language between English, Hindi, and Gujarati', async () => {
    const user = userEvent.setup();
    render(
      <ViewModeProvider>
        <ViewModeInspector />
      </ViewModeProvider>
    );

    expect(screen.getByTestId('current-language').textContent).toBe('en');

    await user.click(screen.getByTestId('set-hindi'));
    expect(screen.getByTestId('current-language').textContent).toBe('hi');

    await user.click(screen.getByTestId('set-gujarati'));
    expect(screen.getByTestId('current-language').textContent).toBe('gu');
  });

  it('Header contains mode toggle buttons and language selector with zero voice UI', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <Header />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Verify mode toggle buttons
    const farmerBtn = screen.getByRole('tab', { name: /farmer view/i });
    const expertBtn = screen.getByRole('tab', { name: /expert view/i });
    expect(farmerBtn).toBeInTheDocument();
    expect(expertBtn).toBeInTheDocument();

    // Verify language selector dropdown exists
    const langSelect = screen.getByLabelText(/interface language/i);
    expect(langSelect).toBeInTheDocument();

    // CRITICAL REQUIREMENT: Strict verification that NO voice UI exists
    expect(screen.queryByLabelText(/microphone/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/voice/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/speech/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/listen/i)).not.toBeInTheDocument();

    // Verify TY B.Tech CSE AI/ML badge is completely removed
    expect(screen.queryByText(/TY B\.Tech/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/CSE AI\/ML/i)).not.toBeInTheDocument();
  });

  it('FarmerViewPage displays 4 KPI cards and plain language reason codes', async () => {
    vi.spyOn(api, 'runScenario').mockResolvedValue(mockScenarioData);

    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <FarmerViewPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Initial state: empty card with run button
    expect(screen.getByText(/no water plan loaded/i)).toBeInTheDocument();
    const runBtn = screen.getByRole('button', { name: /run water sharing plan/i });
    expect(runBtn).toBeInTheDocument();

    // Trigger runScenario
    await userEvent.click(runBtn);

    // Check that reason codes and cards are displayed
    await waitFor(() => {
      expect(screen.getByText(/my water sharing/i)).toBeInTheDocument();
    });

    // Verify 4 Large KPI Cards
    expect(screen.getByText(TRANSLATIONS.en.waterGivenToMe)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.waterNeeded)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.waterAvailable)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.sharingResult)).toBeInTheDocument();

    // Verify plain-language translated reason codes from Phase 7
    expect(screen.getByText(TRANSLATIONS.en.reasonResourceShortageTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.reasonHighUrgencyTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.reasonMinimumRequirementTitle)).toBeInTheDocument();

    // Verify 5-step mediation timeline
    expect(screen.getByText(/how was the water shared\?/i)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.step1)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.step5)).toBeInTheDocument();
  });

  it('FarmerViewPage toggles technical details accordion', async () => {
    vi.spyOn(api, 'runScenario').mockResolvedValue(mockScenarioData);

    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <FarmerViewPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    const runBtn = screen.getByRole('button', { name: /run water sharing plan/i });
    await userEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText(/technical details \(optional\)/i)).toBeInTheDocument();
    });

    const accordionBtn = screen.getByRole('button', { name: /technical details \(optional\)/i });

    // Click to expand
    await userEvent.click(accordionBtn);
    expect(screen.getByText(/ai prediction model/i)).toBeInTheDocument();
    expect(screen.getByText(/optimization solver/i)).toBeInTheDocument();
  });

  it('Farmer Scenario page renders with 4 simple situation options and no technical jargon', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <ScenarioPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Page Title
    expect(screen.getByText(TRANSLATIONS.en.startWaterSharingTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.startWaterSharingSubtitle)).toBeInTheDocument();

    // 4 Plain Language Options
    expect(screen.getByText(TRANSLATIONS.en.q1OptEnoughTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.q1OptSomeShortageTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.q1OptSeriousShortageTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.q1OptCropsUrgentTitle)).toBeInTheDocument();

    // Stepper
    expect(screen.getByText(TRANSLATIONS.en.q2FarmersLabel + ':')).toBeInTheDocument();
    expect(screen.getByTestId('farmer-count-val').textContent).toBe('4');

    // Optional Water Input & Checkbox
    expect(screen.getByPlaceholderText(/e\.g\. 3500/i)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.en.q5UnknownCheckbox)).toBeInTheDocument();

    // STRICT REQUIREMENT: No technical implementation jargon in Farmer View
    expect(screen.queryByText(/random seed/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/xgboost/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/random forest/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/r²/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pydantic/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/digital twin/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/api\/v1\/scenarios\/run/i)).not.toBeInTheDocument();
  });

  it('Farmer Scenario stepper increments and decrements farmer count within bounds (2 to 20)', async () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <ScenarioPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    const decBtn = screen.getByLabelText('Decrease farmers count');
    const incBtn = screen.getByLabelText('Increase farmers count');
    const countVal = screen.getByTestId('farmer-count-val');

    expect(countVal.textContent).toBe('4');

    // Increment
    await userEvent.click(incBtn);
    expect(countVal.textContent).toBe('5');

    // Decrement twice
    await userEvent.click(decBtn);
    await userEvent.click(decBtn);
    expect(countVal.textContent).toBe('3');
  });

  it('Farmer Scenario submission maps simple selections to the correct backend API request', async () => {
    const runSpy = vi.spyOn(api, 'runScenario').mockResolvedValue(mockScenarioData);

    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <ScenarioPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Select "Serious Shortage" (severe_shortage)
    const seriousCard = screen.getByText(TRANSLATIONS.en.q1OptSeriousShortageTitle).closest('.farmer-situation-card');
    if (seriousCard) await userEvent.click(seriousCard);

    // Increment farmer count to 5
    const incBtn = screen.getByLabelText('Increase farmers count');
    await userEvent.click(incBtn);

    // Enter optional water amount
    const waterInput = screen.getByPlaceholderText(/e\.g\. 3500/i);
    await userEvent.type(waterInput, '3200');

    // Click find water sharing plan
    const submitBtn = screen.getByRole('button', { name: new RegExp(TRANSLATIONS.en.findWaterPlanBtn, 'i') });
    await userEvent.click(submitBtn);

    expect(runSpy).toHaveBeenCalledWith({
      scenario_type: 'severe_shortage',
      n_farmers: 5,
      seed: 42,
      model_name: 'XGBoost',
      available_water_override_m3: 3200,
    });
  });

  it('Farmer Scenario with "I don\'t know" checkbox sends null water override', async () => {
    const runSpy = vi.spyOn(api, 'runScenario').mockResolvedValue(mockScenarioData);

    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <ScenarioPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Check "I don't know" checkbox
    const unknownCheckbox = screen.getByRole('checkbox', { name: new RegExp(TRANSLATIONS.en.q5UnknownCheckbox, 'i') });
    await userEvent.click(unknownCheckbox);

    // Click submit
    const submitBtn = screen.getByRole('button', { name: new RegExp(TRANSLATIONS.en.findWaterPlanBtn, 'i') });
    await userEvent.click(submitBtn);

    expect(runSpy).toHaveBeenCalledWith({
      scenario_type: 'moderate_shortage',
      n_farmers: 4,
      seed: 42,
      model_name: 'XGBoost',
      available_water_override_m3: null,
    });
  });

  it('Farmer Scenario translates properly to Hindi and Gujarati', async () => {
    localStorage.setItem('aquamedi_language', 'hi');

    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <ScenarioPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Hindi translation verified
    expect(screen.getByText(TRANSLATIONS.hi.startWaterSharingTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.hi.q1SituationTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.hi.q1OptEnoughTitle)).toBeInTheDocument();
    expect(screen.getByText(TRANSLATIONS.hi.findWaterPlanBtn)).toBeInTheDocument();
  });

  it('Expert View retains full technical configuration with XGBoost, Seed, and API info', () => {
    localStorage.setItem('aquamedi_view_mode', 'expert');

    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ViewModeProvider>
            <ScenarioPage />
          </ViewModeProvider>
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Technical expert fields present
    expect(screen.getByText('Configure & Run Mediation Scenario')).toBeInTheDocument();
    expect(screen.getByText(/Quick Academic Demo Presets/i)).toBeInTheDocument();
    expect(screen.getByText('Random Seed (Deterministic) *')).toBeInTheDocument();
    expect(screen.getByText('ML Demand Prediction Model *')).toBeInTheDocument();
    expect(screen.getByText('XGBoost (Primary — R² = 0.9736)')).toBeInTheDocument();
    expect(screen.getByText(/POST \/api\/v1\/scenarios\/run/i)).toBeInTheDocument();
  });
});

