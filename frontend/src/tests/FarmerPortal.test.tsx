import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../App';
import { FarmerPortalPage } from '../pages/FarmerPortalPage';
import { ScenarioProvider } from '../context/ScenarioContext';
import { ViewModeProvider } from '../context/ViewModeContext';
import { api } from '../services/api';
import type { PredictionResponse, HealthResponse } from '../types/api';

describe('FarmerPortalPage & Phase 14 Farmer Route Flow', () => {
  const mockHealth: HealthResponse = {
    status: 'healthy',
    service: 'AquaMediAI',
    version: '1.0.0',
    pipeline: 'available',
    disclaimer: 'Synthetic test disclaimer',
  };

  const mockPrediction: PredictionResponse = {
    farmer_id: 'FARMER_PORTAL',
    predicted_water_demand_m3: 112.5,
    model_name: 'XGBoost',
    model_version: '1.0.0',
    warning: null,
    input_summary: {
      crop_type: 'wheat',
      growth_stage: 'vegetative',
      soil_type: 'loam',
      farm_area_hectares: 2.0,
      temperature_celsius: 26,
      humidity_percent: 55,
      rainfall_mm: 0,
    },
    shadow_agronomic_estimate_m3: 120.0,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'getHealth').mockResolvedValue(mockHealth);
  });

  it('renders FarmerPortalPage via /farmer-portal and /farmer/portal routes in App', async () => {
    // 1. Test /farmer-portal
    const { unmount: u1 } = render(
      <MemoryRouter initialEntries={['/farmer-portal']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: /Enter Your Farm Details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Calculate My Water Need/i })).toBeInTheDocument();
    u1();

    // 2. Test /farmer/portal
    const { unmount: u2 } = render(
      <MemoryRouter initialEntries={['/farmer/portal']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: /Enter Your Farm Details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Calculate My Water Need/i })).toBeInTheDocument();
    u2();
  });

  it('renders all crop options, stage, soil, and numeric inputs with sensible defaults', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <FarmerPortalPage />
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Verify crop buttons
    expect(screen.getByRole('button', { name: /Wheat \(Gehu\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Rice \/ Paddy \(Dhan\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cotton \(Kapas\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sugarcane \(Ganna\)/i })).toBeInTheDocument();

    // Verify dropdowns
    expect(screen.getByLabelText(/What stage is your crop in\?/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/What type of soil does your farm have\?/i)).toBeInTheDocument();

    // Verify inputs
    const areaInput = screen.getByLabelText(/Farm area \(hectares\)/i) as HTMLInputElement;
    expect(areaInput).toBeInTheDocument();
    expect(parseFloat(areaInput.value)).toBe(2.0);

    const tempInput = screen.getByLabelText(/Today's temperature \(°C\)/i) as HTMLInputElement;
    expect(tempInput).toBeInTheDocument();
    expect(parseFloat(tempInput.value)).toBe(26);

    const humidityInput = screen.getByLabelText(/Relative humidity \(%\)/i) as HTMLInputElement;
    expect(humidityInput).toBeInTheDocument();
    expect(parseFloat(humidityInput.value)).toBe(55);

    const rainInput = screen.getByLabelText(/Recent rainfall today \(mm\)/i) as HTMLInputElement;
    expect(rainInput).toBeInTheDocument();
    expect(parseFloat(rainInput.value)).toBe(0);
  });

  it('validates client-side inputs and blocks invalid submissions', async () => {
    const predictSpy = vi.spyOn(api, 'predictSingle');

    render(
      <MemoryRouter>
        <ViewModeProvider>
          <FarmerPortalPage />
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Set invalid farm area (0)
    const areaInput = screen.getByLabelText(/Farm area \(hectares\)/i);
    fireEvent.change(areaInput, { target: { value: '0' } });

    const submitBtn = screen.getByRole('button', { name: /Calculate My Water Need/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Farm area must be greater than 0/i)).toBeInTheDocument();
    expect(predictSpy).not.toHaveBeenCalled();

    // Set invalid temperature (60°C)
    fireEvent.change(areaInput, { target: { value: '2.5' } });
    const tempInput = screen.getByLabelText(/Today's temperature \(°C\)/i);
    fireEvent.change(tempInput, { target: { value: '60' } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Temperature must be between 5°C and 50°C/i)).toBeInTheDocument();
    expect(predictSpy).not.toHaveBeenCalled();
  });

  it('submits valid inputs to prediction API and displays result card correctly', async () => {
    const predictSpy = vi.spyOn(api, 'predictSingle').mockResolvedValue(mockPrediction);

    render(
      <MemoryRouter>
        <ViewModeProvider>
          <FarmerPortalPage />
        </ViewModeProvider>
      </MemoryRouter>
    );

    // Select Cotton
    const cottonBtn = screen.getByRole('button', { name: /Cotton \(Kapas\)/i });
    fireEvent.click(cottonBtn);

    // Set area to 3.0
    const areaInput = screen.getByLabelText(/Farm area \(hectares\)/i);
    fireEvent.change(areaInput, { target: { value: '3.0' } });

    // Click submit
    const submitBtn = screen.getByRole('button', { name: /Calculate My Water Need/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(predictSpy).toHaveBeenCalledTimes(1);
    });

    // Check payload passed to api.predictSingle
    const callArgs = predictSpy.mock.calls[0][0];
    expect(callArgs.model_name).toBe('XGBoost');
    expect(callArgs.farmer_data.crop_type).toBe('cotton');
    expect(callArgs.farmer_data.farm_area_hectares).toBe(3.0);
    expect(callArgs.farmer_data.kc_value).toBeGreaterThan(0);
    expect(callArgs.farmer_data.et0_mm_per_day).toBeGreaterThan(0);

    // Check result display
    expect(await screen.findByText('Water Demand Estimate Ready')).toBeInTheDocument();
    expect(screen.getByText('112.5')).toBeInTheDocument();
    expect(screen.getByText('m³ / day')).toBeInTheDocument();
    expect(screen.getByText(/Calculated by: XGBoost AI Model/i)).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument(); // shadow estimate
  });

  it('handles reset button and resets inputs to defaults', async () => {
    vi.spyOn(api, 'predictSingle').mockResolvedValue(mockPrediction);

    render(
      <MemoryRouter>
        <ViewModeProvider>
          <FarmerPortalPage />
        </ViewModeProvider>
      </MemoryRouter>
    );

    const areaInput = screen.getByLabelText(/Farm area \(hectares\)/i) as HTMLInputElement;
    fireEvent.change(areaInput, { target: { value: '5.5' } });
    expect(areaInput.value).toBe('5.5');

    const resetBtn = screen.getByRole('button', { name: /Reset/i });
    fireEvent.click(resetBtn);

    expect(areaInput.value).toBe('2');
  });

  it('renders Farmer View navigation tabs in MainLayout when in Farmer View', async () => {
    render(
      <MemoryRouter initialEntries={['/farmer']}>
        <ScenarioProvider>
          <App />
        </ScenarioProvider>
      </MemoryRouter>
    );

    const nav = screen.getByRole('navigation', { name: /Farmer View Navigation/i });
    expect(nav).toBeInTheDocument();
    expect(within(nav).getByRole('link', { name: /My Water Sharing/i })).toBeInTheDocument();
    expect(within(nav).getByRole('link', { name: /Check My Farm Water Need/i })).toBeInTheDocument();
    expect(within(nav).getByRole('link', { name: /Water Sharing Scenario/i })).toBeInTheDocument();
  });
});
