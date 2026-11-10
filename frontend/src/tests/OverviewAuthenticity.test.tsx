import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React, { useState } from 'react';
import { OverviewPage } from '../pages/OverviewPage';
import { ScenarioContext } from '../context/ScenarioContext';
import type { ScenarioRunResponse } from '../types/api';

// Realistic scenario mock representing live backend ML inference and OR-Tools optimization results
const mockExecutedScenario: ScenarioRunResponse = {
  scenario_id: 'scenario_real_audit_101',
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
      input_summary: { farm_area_hectares: 2.5 },
    },
    {
      farmer_id: 'FARM_0002',
      predicted_water_demand_m3: 170,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: { farm_area_hectares: 2.0 },
    },
    {
      farmer_id: 'FARM_0003',
      predicted_water_demand_m3: 150,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: { farm_area_hectares: 1.8 },
    },
  ],
  farmers: [
    { farmer_id: 'FARM_0001', crop: 'wheat', growth_stage: 'vegetative', urgency: 0.8, flexibility: 0.2, crop_sensitivity: 0.9 },
    { farmer_id: 'FARM_0002', crop: 'cotton', growth_stage: 'flowering', urgency: 0.6, flexibility: 0.4, crop_sensitivity: 1.1 },
    { farmer_id: 'FARM_0003', crop: 'maize', growth_stage: 'tasseling', urgency: 0.5, flexibility: 0.5, crop_sensitivity: 0.8 },
  ],
  conflicts: {
    scenario_id: 'scenario_real_audit_101',
    n_farmers: 3,
    total_demand_m3: 500,
    available_water_m3: 450,
    resource_gap_m3: 50,
    overall_shortage_ratio: 0.1,
    total_conflicts: 1,
    highest_severity: 'medium',
    conflicts: [],
  },
  initial_allocation: {
    scenario_id: 'scenario_real_audit_101',
    solver_status: 'optimal',
    objective_value: 412.5,
    allocation_method: 'lp_optimal',
    available_water_m3: 450,
    total_demand_m3: 500,
    total_allocated_m3: 450,
    remaining_water_m3: 0,
    utilization: 1.0,
    fairness_score: 0.98,
    average_satisfaction: 0.9,
    total_unmet_demand_m3: 50,
    total_minimum_shortfall_m3: 0,
    minimum_requirements_feasible: true,
    n_farmers: 3,
    solver_wall_time_ms: 1.2,
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
        crop: 'cotton',
        growth_stage: 'flowering',
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
        maximum_requirement_m3: 160,
        allocated_water_m3: 130,
        unmet_demand_m3: 20,
        minimum_shortfall_m3: 0,
        satisfaction_ratio: 0.867,
        constraint_status: 'satisfied',
      },
    ],
  },
  negotiation: null,
  final_allocation: {} as any,
  explanations: {} as any,
  final_decision: {} as any,
  timestamp: new Date().toISOString(),
} as unknown as ScenarioRunResponse;

// Helper mock provider to supply explicit scenario state
const MockScenarioContext: React.FC<{
  initialResult: ScenarioRunResponse | null;
  children: React.ReactNode;
}> = ({ initialResult, children }) => {
  const [scenarioResult] = useState<ScenarioRunResponse | null>(initialResult);

  return (
    <ScenarioContext.Provider
      value={{
        scenarioResult,
        isLoading: false,
        loadingMessage: '',
        error: null,
        health: null,
        healthStatus: 'connected',
        runScenario: async () => true,
        checkHealth: async () => {},
        clearError: () => {},
        resetScenario: () => {},
      }}
    >
      {children}
    </ScenarioContext.Provider>
  );
};

describe('AquaMedi AI — Overview Dashboard Authenticity & Option 1 Clean Empty State', () => {
  it('1. When scenarioResult is null: displays clean empty state and no operational metrics', () => {
    render(
      <MemoryRouter>
        <MockScenarioContext initialResult={null}>
          <OverviewPage />
        </MockScenarioContext>
      </MemoryRouter>
    );

    // Header & EmptyState titles and descriptions must be rendered
    expect(screen.getByText('Water Distribution Dashboard')).toBeInTheDocument();
    expect(screen.getByText('No Active Scenario')).toBeInTheDocument();
    expect(screen.getByText('No Scenario Loaded')).toBeInTheDocument();
    expect(screen.getByText('Configure & Run Scenario')).toBeInTheDocument();
    expect(screen.getByText(/No active water distribution scenario is loaded/i)).toBeInTheDocument();

    // MUST NOT display hardcoded demonstration data banner
    expect(screen.queryByText('Demonstration Data')).not.toBeInTheDocument();

    // MUST NOT display hardcoded sample farmers (SAMPLE_DEMO_ROWS)
    expect(screen.queryByText('Ramesh Patil')).not.toBeInTheDocument();
    expect(screen.queryByText('Suresh Deshmukh')).not.toBeInTheDocument();
    expect(screen.queryByText('Anand Shinde')).not.toBeInTheDocument();
    expect(screen.queryByText('Kishor Kale')).not.toBeInTheDocument();
    expect(screen.queryByText('Sunil Jadhav')).not.toBeInTheDocument();
    expect(screen.queryByText('Vikas More')).not.toBeInTheDocument();

    // MUST NOT display operational KPI cards
    expect(screen.queryByText('Total Available Water')).not.toBeInTheDocument();
    expect(screen.queryByText('Total Predicted Demand')).not.toBeInTheDocument();
    expect(screen.queryByText('Total Allocated Water')).not.toBeInTheDocument();
    expect(screen.queryByText('Estimated Water Deficit')).not.toBeInTheDocument();
    expect(screen.queryByText('Participating Farmers')).not.toBeInTheDocument();
    expect(screen.queryByText('Affected Farmers')).not.toBeInTheDocument();

    // MUST NOT display hardcoded fallback values
    expect(screen.queryByText('6,000 m³')).not.toBeInTheDocument();
    expect(screen.queryByText('7,100 m³')).not.toBeInTheDocument();
    expect(screen.queryByText('5,950 m³')).not.toBeInTheDocument();
    expect(screen.queryByText('1,150 m³')).not.toBeInTheDocument();

    // MUST NOT display operational table or chart titles
    expect(screen.queryByText('Water Allocation Register')).not.toBeInTheDocument();
    expect(screen.queryByText('Requested vs Allocated Water (by Farmer)')).not.toBeInTheDocument();
    expect(screen.queryByText('Crop-Wise Water Demand')).not.toBeInTheDocument();
    expect(screen.queryByText('Canal Reach Allocation Analysis')).not.toBeInTheDocument();
    expect(screen.queryByText('Water Shortage Distribution')).not.toBeInTheDocument();
  });

  it('2. When scenarioResult is loaded: displays real ML predictions, OR-Tools allocations, and charts', () => {
    render(
      <MemoryRouter>
        <MockScenarioContext initialResult={mockExecutedScenario}>
          <OverviewPage />
        </MockScenarioContext>
      </MemoryRouter>
    );

    // EmptyState must be hidden
    expect(screen.queryByText('No Scenario Loaded')).not.toBeInTheDocument();

    // Live status badge must be active
    expect(screen.getByText('Live Scenario Solved')).toBeInTheDocument();
    expect(screen.getByText(/scenario_real_audit_101/i)).toBeInTheDocument();

    // KPI cards with real scenario values
    expect(screen.getByText('Total Available Water')).toBeInTheDocument();
    expect(screen.getAllByText('450.0 m³')).toHaveLength(2); // available_water_m3 & total_allocated_m3

    expect(screen.getByText('Total Predicted Demand')).toBeInTheDocument();
    expect(screen.getByText('500.0 m³')).toBeInTheDocument(); // total_demand_m3 (from XGBoost)

    expect(screen.getByText('Total Allocated Water')).toBeInTheDocument();
    expect(screen.getByText('Estimated Water Deficit')).toBeInTheDocument();
    expect(screen.getByText('50.0 m³')).toBeInTheDocument(); // 500 - 450 = 50.0 m³

    // Table must be populated with scenario farmers
    expect(screen.getByText('Water Allocation Register')).toBeInTheDocument();
    expect(screen.getByText('FARM_0001')).toBeInTheDocument();
    expect(screen.getByText('FARM_0002')).toBeInTheDocument();
    expect(screen.getByText('FARM_0003')).toBeInTheDocument();

    // Chart titles must be rendered
    expect(screen.getByText('Requested vs Allocated Water (by Farmer)')).toBeInTheDocument();
    expect(screen.getByText('Crop-Wise Water Demand')).toBeInTheDocument();
    expect(screen.getByText('Canal Reach Allocation Analysis')).toBeInTheDocument();
    expect(screen.getByText('Water Shortage Distribution')).toBeInTheDocument();

    // Action button points to /scenario for reconfiguration
    const changeScenarioBtn = screen.getByRole('link', { name: /Change Scenario/i });
    expect(changeScenarioBtn).toHaveAttribute('href', '/scenario');
  });

  it('3. Scenario navigation links point to /scenario', () => {
    render(
      <MemoryRouter>
        <MockScenarioContext initialResult={null}>
          <OverviewPage />
        </MockScenarioContext>
      </MemoryRouter>
    );

    const configureLink = screen.getByRole('link', { name: /Configure & Run Scenario/i });
    expect(configureLink).toHaveAttribute('href', '/scenario');

    const topRunLink = screen.getByRole('link', { name: /Run New Scenario/i });
    expect(topRunLink).toHaveAttribute('href', '/scenario');
  });
});
