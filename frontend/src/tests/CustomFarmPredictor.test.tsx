import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CustomFarmPredictor } from '../components/pipeline/CustomFarmPredictor';
import { PredictionsPage } from '../pages/PredictionsPage';
import { ScenarioContext, ScenarioProvider } from '../context/ScenarioContext';
import { api } from '../services/api';
import type { PredictionResponse, ScenarioRunResponse } from '../types/api';

describe('CustomFarmPredictor Component & Phase 14 UI Flow', () => {
  const mockPredictionSuccess: PredictionResponse = {
    farmer_id: 'CUSTOM_TEST_PLOT',
    predicted_water_demand_m3: 185.65,
    model_name: 'XGBoost',
    model_version: '1.0.0',
    warning: null,
    input_summary: {
      crop_type: 'sugarcane',
      soil_type: 'clay_loam',
      growth_stage: 'mid_season',
      season: 'kharif',
      farm_area_hectares: 3.5,
      et0_mm_per_day: 5.2,
      kc_value: 1.15,
      temperature_celsius: 30.0,
      rainfall_mm: 0.0,
    },
    shadow_agronomic_estimate_m3: 299.0,
    shadow_comparison: {
      status: 'available',
      agronomic_demand_m3: 299.0,
      legacy_prediction_m3: 185.65,
      difference_m3: -113.35,
      difference_percent: -37.91,
      method: 'FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall',
      application_efficiency: 0.7,
      is_empirical_error: false,
      input_validation: {
        is_valid: true,
        errors: [],
      },
      provenance_note: 'Agronomic reference note.',
      disclaimer: 'Academic disclaimer note.',
    },
  };

  const mockPredictionWithClamp: PredictionResponse = {
    farmer_id: 'SMALL_PLOT_01',
    predicted_water_demand_m3: 5.0,
    model_name: 'XGBoost',
    model_version: '1.0.0',
    warning: 'Predicted water demand (-12.40 m3/day) is below minimum physical threshold; clamped to 5.00 m3/day.',
    input_summary: {
      crop_type: 'wheat',
      farm_area_hectares: 0.5,
    },
    shadow_agronomic_estimate_m3: 27.5,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('1. renders all required form controls with supported agronomic options', () => {
    render(<CustomFarmPredictor />);

    expect(screen.getByLabelText(/Farmer \/ Plot Identifier \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Crop Type \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Farm Area \(hectares\) \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Soil Texture \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Growth Stage \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cropping Season \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Reference Evapotranspiration ETo \(mm\/day\) \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Crop Coefficient Kc \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Crop ETc \(mm\/day\) \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Model Architecture \*/i)).toBeInTheDocument();

    // Verify submit button exists
    expect(
      screen.getByRole('button', { name: /Calculate Water Demand/i })
    ).toBeInTheDocument();
  });

  it('2. validates that farm area must be greater than zero and blocks submission', async () => {
    const predictSpy = vi.spyOn(api, 'predictSingle');
    render(<CustomFarmPredictor />);

    const areaInput = screen.getByLabelText(/Farm Area \(hectares\) \*/i);
    fireEvent.change(areaInput, { target: { value: '0' } });

    const submitBtn = screen.getByRole('button', { name: /Calculate Water Demand/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Farm area must be greater than 0 hectares/i)
    ).toBeInTheDocument();
    expect(predictSpy).not.toHaveBeenCalled();
  });

  it('3. validates that farmer ID cannot be blank', async () => {
    const predictSpy = vi.spyOn(api, 'predictSingle');
    render(<CustomFarmPredictor />);

    const idInput = screen.getByLabelText(/Farmer \/ Plot Identifier \*/i);
    fireEvent.change(idInput, { target: { value: '   ' } });

    const submitBtn = screen.getByRole('button', { name: /Calculate Water Demand/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Farmer ID \/ Plot Identifier is required/i)
    ).toBeInTheDocument();
    expect(predictSpy).not.toHaveBeenCalled();
  });

  it('4. automatically synchronizes ETc = ETo * Kc when ETo changes', () => {
    render(<CustomFarmPredictor />);

    const et0Input = screen.getByLabelText(/Reference Evapotranspiration ETo \(mm\/day\) \*/i);
    const kcInput = screen.getByLabelText(/Crop Coefficient Kc \*/i);
    const etcInput = screen.getByLabelText(/Crop ETc \(mm\/day\) \*/i);

    fireEvent.change(et0Input, { target: { value: '6.0' } });
    fireEvent.change(kcInput, { target: { value: '1.2' } });

    // 6.0 * 1.2 = 7.2
    expect((etcInput as HTMLInputElement).value).toBe('7.2');
  });

  it('5. submits valid form to api.predictSingle and displays API-returned predictions', async () => {
    const predictSpy = vi
      .spyOn(api, 'predictSingle')
      .mockResolvedValueOnce(mockPredictionSuccess);

    render(<CustomFarmPredictor />);

    const idInput = screen.getByLabelText(/Farmer \/ Plot Identifier \*/i);
    fireEvent.change(idInput, { target: { value: 'CUSTOM_TEST_PLOT' } });

    const submitBtn = screen.getByRole('button', { name: /Calculate Water Demand/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(predictSpy).toHaveBeenCalledTimes(1);
    });

    // Check payload passed
    expect(predictSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        farmer_data: expect.objectContaining({
          farmer_id: 'CUSTOM_TEST_PLOT',
        }),
        model_name: 'XGBoost',
      })
    );

    // Verify prediction result is displayed
    expect(await screen.findByText(/Predicted Water Demand for CUSTOM_TEST_PLOT/i)).toBeInTheDocument();
    expect(screen.getByText('185.7 m³')).toBeInTheDocument();
    expect(screen.getByText('299.0 m³')).toBeInTheDocument(); // Agronomic physical reference
    expect(screen.getByText('-113.35 m³')).toBeInTheDocument(); // Model discrepancy
  });

  it('6. displays warnings when returned by the model (e.g., minimum physical clamp)', async () => {
    vi.spyOn(api, 'predictSingle').mockResolvedValueOnce(mockPredictionWithClamp);

    render(<CustomFarmPredictor />);

    const submitBtn = screen.getByRole('button', { name: /Calculate Water Demand/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/below minimum physical threshold; clamped to 5.00 m3\/day/i)
    ).toBeInTheDocument();
    expect(screen.getByText('5.0 m³')).toBeInTheDocument();
  });

  it('7. displays error alert when API request fails and does not invent mock fallback data', async () => {
    vi.spyOn(api, 'predictSingle').mockRejectedValueOnce(
      new Error('FastAPI backend connection refused on port 8000')
    );

    render(<CustomFarmPredictor />);

    const submitBtn = screen.getByRole('button', { name: /Calculate Water Demand/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/FastAPI backend connection refused on port 8000/i)
    ).toBeInTheDocument();

    // Ensure no fake demand result is displayed
    expect(screen.queryByText(/Predicted Water Demand for/i)).not.toBeInTheDocument();
  });

  it('8. resets form and cleared results when Reset Defaults button is clicked', async () => {
    vi.spyOn(api, 'predictSingle').mockResolvedValueOnce(mockPredictionSuccess);

    render(<CustomFarmPredictor />);

    // Change value and submit
    const idInput = screen.getByLabelText(/Farmer \/ Plot Identifier \*/i);
    fireEvent.change(idInput, { target: { value: 'ALTERED_ID' } });
    fireEvent.click(screen.getByRole('button', { name: /Calculate Water Demand/i }));

    expect(await screen.findByText(/Predicted Water Demand for CUSTOM_TEST_PLOT/i)).toBeInTheDocument();

    // Click Reset
    const resetBtn = screen.getByRole('button', { name: /Reset Defaults/i });
    fireEvent.click(resetBtn);

    // Form should reset to default and result should disappear
    expect((idInput as HTMLInputElement).value).toBe('CUSTOM_FARM_01');
    expect(screen.queryByText(/Predicted Water Demand for/i)).not.toBeInTheDocument();
  });

  it('9. PredictionsPage integrates CustomFarmPredictor and discloses static training references', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <PredictionsPage />
        </ScenarioProvider>
      </MemoryRouter>
    );

    // Page title
    expect(screen.getByText('ML Water Demand Predictions')).toBeInTheDocument();

    // Static training benchmark disclosure
    expect(screen.getAllByText(/STATIC REFERENCE VALUES/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Academic Transparency Notice/i)).toBeInTheDocument();

    // Custom Farm Predictor exists
    expect(screen.getByText('Custom Farm Water Demand Predictor')).toBeInTheDocument();
    expect(screen.getByText('Synthetic Scenario Demonstration Data')).toBeInTheDocument();
  });

  it('10. PredictionsPage clearly labels scenario demo data when a scenario result is loaded', () => {
    const mockScenarioWithFarmers: Partial<ScenarioRunResponse> = {
      scenario_id: 'scenario_test123',
      status: 'success',
      predictions: [
        {
          farmer_id: 'FARM_0001',
          predicted_water_demand_m3: 110.5,
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
          farm_area_hectares: 2.0,
          et0_mm_per_day: 4.0,
          kc_value: 0.8,
        } as any,
      ],
      explanations: {
        prediction_explanations: [],
      } as any,
    };

    const mockContextValue: any = {
      scenarioResult: mockScenarioWithFarmers,
      isLoading: false,
      loadingMessage: '',
      error: null,
      health: null,
      healthStatus: 'connected',
      runScenario: vi.fn(),
      checkHealth: vi.fn(),
      clearError: vi.fn(),
      resetScenario: vi.fn(),
    };

    render(
      <MemoryRouter>
        <ScenarioContext.Provider value={mockContextValue}>
          <PredictionsPage />
        </ScenarioContext.Provider>
      </MemoryRouter>
    );

    // Scenario section labeled as synthetic demo records
    expect(screen.getByText('SIMULATED DEMO RECORDS')).toBeInTheDocument();
    expect(screen.getByText('FARM_0001')).toBeInTheDocument();
    expect(screen.getAllByText('110.5 m³').length).toBeGreaterThanOrEqual(1);
  });
});
