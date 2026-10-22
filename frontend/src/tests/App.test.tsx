import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ScenarioProvider } from '../context/ScenarioContext';
import { App } from '../App';
import { api } from '../services/api';
import type { HealthResponse, ScenarioRunResponse } from '../types/api';

const mockHealthResponse: HealthResponse = {
  status: 'healthy',
  service: 'AquaMediAI',
  version: '1.0.0',
  pipeline: 'available',
  disclaimer: 'Synthetic test disclaimer',
};

const mockScenarioResponse: ScenarioRunResponse = {
  scenario_id: 'scenario_test999',
  status: 'agreed',
  scenario_type: 'moderate_shortage',
  n_farmers: 3,
  available_water_m3: 450,
  total_demand_m3: 500,
  predictions: [
    {
      farmer_id: 'FARM_0001',
      predicted_water_demand_m3: 180,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
    {
      farmer_id: 'FARM_0002',
      predicted_water_demand_m3: 170,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
    {
      farmer_id: 'FARM_0003',
      predicted_water_demand_m3: 150,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {},
    },
  ],
  farmers: [
    {
      farmer_id: 'FARM_0001',
      crop: 'wheat',
      growth_stage: 'vegetative',
      urgency: 0.8,
      flexibility: 0.2,
      crop_sensitivity: 0.9,
    },
    {
      farmer_id: 'FARM_0002',
      crop: 'rice',
      growth_stage: 'tillering',
      urgency: 0.6,
      flexibility: 0.4,
      crop_sensitivity: 1.1,
    },
    {
      farmer_id: 'FARM_0003',
      crop: 'maize',
      growth_stage: 'tasseling',
      urgency: 0.5,
      flexibility: 0.5,
      crop_sensitivity: 0.8,
    },
  ],
  conflicts: {
    scenario_id: 'scenario_test999',
    n_farmers: 3,
    total_demand_m3: 500,
    available_water_m3: 450,
    resource_gap_m3: 50,
    overall_shortage_ratio: 0.1,
    total_conflicts: 1,
    highest_severity: 'high',
    conflicts: [
      {
        conflict_id: 'conf_101',
        conflict_type: 'resource_shortage',
        severity: 'high',
        severity_score: 0.75,
        involved_farmer_ids: ['FARM_0001', 'FARM_0002', 'FARM_0003'],
        available_water_m3: 450,
        total_demand_m3: 500,
        resource_gap_m3: 50,
        explanation: 'Overall deficit of 50 m³ in canal branch',
      },
    ],
  },
  initial_allocation: {
    scenario_id: 'scenario_test999',
    solver_status: 'optimal',
    objective_value: 412.5,
    allocation_method: 'lp_optimal',
    available_water_m3: 450,
    total_demand_m3: 500,
    total_allocated_m3: 450,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.985,
    average_satisfaction: 0.9,
    total_unmet_demand_m3: 50,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 1.5,
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
        farmer_id: 'FARM_0001',
        crop: 'wheat',
        growth_stage: 'vegetative',
        urgency: 0.8,
        crop_sensitivity: 0.9,
        predicted_demand_m3: 180,
        minimum_requirement_m3: 90,
        maximum_requirement_m3: 200,
        allocated_water_m3: 170,
        unmet_demand_m3: 10,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.944,
        constraint_status: 'satisfied',
      },
      {
        farmer_id: 'FARM_0002',
        crop: 'rice',
        growth_stage: 'tillering',
        urgency: 0.6,
        crop_sensitivity: 1.1,
        predicted_demand_m3: 170,
        minimum_requirement_m3: 85,
        maximum_requirement_m3: 190,
        allocated_water_m3: 150,
        unmet_demand_m3: 20,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.882,
        constraint_status: 'satisfied',
      },
      {
        farmer_id: 'FARM_0003',
        crop: 'maize',
        growth_stage: 'tasseling',
        urgency: 0.5,
        crop_sensitivity: 0.8,
        predicted_demand_m3: 150,
        minimum_requirement_m3: 75,
        maximum_requirement_m3: 170,
        allocated_water_m3: 130,
        unmet_demand_m3: 20,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.867,
        constraint_status: 'satisfied',
      },
    ],
  },
  negotiation: {
    session_id: 'session_test123',
    scenario_id: 'scenario_test999',
    n_rounds: 1,
    agreement_status: 'agreed',
    termination_reason: 'All farmers accepted proposed allocation in round 1.',
    initial_allocation: { FARM_0001: 170, FARM_0002: 150, FARM_0003: 130 },
    best_allocation: { FARM_0001: 170, FARM_0002: 150, FARM_0003: 130 },
    rounds: [],
    agreement: {
      agreement_id: 'agree_test123',
      session_id: 'session_test123',
      final_allocation: { FARM_0001: 170, FARM_0002: 150, FARM_0003: 130 },
      participating_farmers: ['FARM_0001', 'FARM_0002', 'FARM_0003'],
      final_utilities: { FARM_0001: 0.92, FARM_0002: 0.85, FARM_0003: 0.83 },
      batna_utilities: { FARM_0001: 0.5, FARM_0002: 0.5, FARM_0003: 0.5 },
      final_surplus: { FARM_0001: 0.42, FARM_0002: 0.35, FARM_0003: 0.33 },
      concessions: [],
      fairness_score: 0.985,
      water_utilization: 1.0,
      negotiation_rounds: 1,
      agreement_status: 'agreed',
      termination_reason: 'All farmers accepted proposed allocation in round 1.',
      round_fairness_history: [0.985],
      round_nash_history: [-0.95],
      is_physically_valid: true,
    },
  },
  final_allocation: {
    scenario_id: 'scenario_test999',
    solver_status: 'optimal',
    objective_value: 412.5,
    allocation_method: 'lp_optimal',
    available_water_m3: 450,
    total_demand_m3: 500,
    total_allocated_m3: 450,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.985,
    average_satisfaction: 0.9,
    total_unmet_demand_m3: 50,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 1.5,
    verification: {
      is_valid: true,
      total_water_ok: true,
      non_negative_ok: true,
      maximum_ok: true,
      no_nan_ok: true,
      all_farmers_present: true,
      violations: [],
    },
    allocations: [],
  },
  explanations: {
    scenario_id: 'scenario_test999',
    summary: 'Allocation solved via GLOP LP maximizing urgency-weighted crop satisfaction.',
    prediction_explanations: [],
    conflict_explanations: [],
    allocation_explanations: [],
    fairness_explanation: null,
    constraint_explanations: [],
    negotiation_explanation: null,
    final_allocation: { FARM_0001: 170, FARM_0002: 150, FARM_0003: 130 },
    final_utilities: { FARM_0001: 0.92, FARM_0002: 0.85, FARM_0003: 0.83 },
    agreement_status: 'agreed',
    all_reason_codes: ['RESOURCE_SHORTAGE', 'HIGH_URGENCY', 'MINIMUM_REQUIREMENT'],
    unresolved_issues: [],
    data_disclaimer: 'Synthetic demonstration disclaimer.',
  },
  final_decision: {
    scenario_id: 'scenario_test999',
    summary: 'Allocation solved via GLOP LP maximizing urgency-weighted crop satisfaction.',
    agreement_status: 'agreed',
    termination_reason: 'All farmers accepted proposed allocation in round 1.',
    fairness_score: 0.985,
    water_utilization: 1.0,
    negotiation_rounds: 1,
    is_physically_valid: true,
  },
};

describe('AquaMediAI Frontend Application Flow', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem('aquamedi_view_mode', 'expert');
    vi.spyOn(api, 'getHealth').mockResolvedValue(mockHealthResponse);
  });

  it('renders application layout with Sidebar and Header', async () => {
    render(
      <MemoryRouter initialEntries={['/overview']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Check project branding
    expect(screen.getAllByText('AquaMediAI')[0]).toBeInTheDocument();
    expect(screen.getByText('AI-Powered Water Mediation')).toBeInTheDocument();

    // Check navigation links exist
    expect(screen.getByText('1. Overview')).toBeInTheDocument();
    expect(screen.getByText('2. Scenario Config')).toBeInTheDocument();
    expect(screen.getByText('3. ML Predictions')).toBeInTheDocument();
    expect(screen.getByText('4. Conflict Engine')).toBeInTheDocument();
    expect(screen.getByText('5. LP Allocation')).toBeInTheDocument();
    expect(screen.getByText('6. Negotiation')).toBeInTheDocument();
    expect(screen.getByText('7. Explainability')).toBeInTheDocument();
    expect(screen.getByText('8. Final Agreement')).toBeInTheDocument();

    // Check live health check status
    await waitFor(() => {
      expect(screen.getByText('API Connected')).toBeInTheDocument();
    });
  });

  it('shows empty state initially on Overview page', async () => {
    render(
      <MemoryRouter initialEntries={['/overview']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('API Connected')).toBeInTheDocument();
    });

    expect(screen.getByText('No Scenario Loaded')).toBeInTheDocument();
    expect(screen.getByText('Configure & Run Scenario')).toBeInTheDocument();
  });

  it('navigates to Scenario Config page and renders configuration form', async () => {
    render(
      <MemoryRouter initialEntries={['/scenario']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('API Connected')).toBeInTheDocument();
    });

    expect(screen.getByText('Configure & Run Mediation Scenario')).toBeInTheDocument();
    expect(screen.getByLabelText(/Scenario Type/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Number of Farmers/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Random Seed/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Run AI Mediation/ })).toBeInTheDocument();
  });

  it('submits scenario form and populates dashboard state', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'runScenario').mockResolvedValueOnce(mockScenarioResponse);

    render(
      <MemoryRouter initialEntries={['/scenario']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /Run AI Mediation/ });
    await user.click(submitBtn);

    // After submission, redirects to overview with populated scenario
    await waitFor(() => {
      expect(screen.getByText('scenario_test999')).toBeInTheDocument();
    });

    expect(screen.getByText('Participating Farmers')).toBeInTheDocument();
    expect(screen.getByText('Total Predicted Demand')).toBeInTheDocument();
  });

  it('renders all pipeline pages properly when requested directly', () => {
    // 1. Predictions page
    const { unmount: u1 } = render(
      <MemoryRouter initialEntries={['/predictions']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('ML Water Demand Predictions')).toBeInTheDocument();
    u1();

    // 2. Allocation page
    const { unmount: u2 } = render(
      <MemoryRouter initialEntries={['/allocation']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Water Allocation Optimization')).toBeInTheDocument();
    u2();

    // 3. Conflicts page
    const { unmount: u3 } = render(
      <MemoryRouter initialEntries={['/conflicts']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Conflict Detection Engine')).toBeInTheDocument();
    u3();

    // 4. Negotiation page
    const { unmount: u4 } = render(
      <MemoryRouter initialEntries={['/negotiation']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Multi-Agent Negotiation')).toBeInTheDocument();
    u4();

    // 5. Explainability page
    const { unmount: u5 } = render(
      <MemoryRouter initialEntries={['/explainability']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText(/Why Did I Get This Much Water|Decision Explanation/)).toBeInTheDocument();
    u5();

    // 6. Agreement page
    const { unmount: u6 } = render(
      <MemoryRouter initialEntries={['/agreement']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Final Mediation Agreement')).toBeInTheDocument();
    u6();

    // 7. Debug page
    render(
      <MemoryRouter initialEntries={['/debug']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Developer & Academic Verification View')).toBeInTheDocument();
  });
});
