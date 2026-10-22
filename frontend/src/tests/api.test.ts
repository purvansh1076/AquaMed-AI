import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../services/api';
import type { HealthResponse, ScenarioRunRequest, ScenarioRunResponse } from '../types/api';

describe('Central API Service (src/services/api.ts)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getHealth returns healthy response from GET /api/v1/health', async () => {
    const mockHealth: HealthResponse = {
      status: 'healthy',
      service: 'AquaMediAI',
      version: '1.0.0',
      pipeline: 'available',
      disclaimer: 'Synthetic data disclaimer',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await api.getHealth();
    expect(result.status).toBe('healthy');
    expect(result.service).toBe('AquaMediAI');
    expect(result.pipeline).toBe('available');
  });

  it('getHealth handles network failure gracefully', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Connection refused'));

    await expect(api.getHealth()).rejects.toThrow(
      'FastAPI backend is unavailable. Start the AquaMediAI backend on port 8000 and try again.'
    );
  });

  it('runScenario posts request and returns full ScenarioRunResponse', async () => {
    const mockRequest: ScenarioRunRequest = {
      scenario_type: 'normal_water',
      n_farmers: 3,
      seed: 42,
      model_name: 'XGBoost',
    };

    const mockResponse: Partial<ScenarioRunResponse> = {
      scenario_id: 'scenario_test123',
      status: 'agreed',
      scenario_type: 'normal_water',
      n_farmers: 3,
      available_water_m3: 600,
      total_demand_m3: 500,
      predictions: [],
      farmers: [],
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await api.runScenario(mockRequest);
    expect(result.scenario_id).toBe('scenario_test123');
    expect(result.status).toBe('agreed');
    expect(result.n_farmers).toBe(3);
  });

  it('handles backend 422 validation error with clean message', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'Number of farmers must be between 2 and 20' }),
    } as Response);

    await expect(
      api.runScenario({ scenario_type: 'normal_water', n_farmers: 1 })
    ).rejects.toThrow('Number of farmers must be between 2 and 20');
  });

  it('handles backend 500 internal error without leaking stack traces', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({
        detail: 'An internal error occurred: WaterAllocationError\nFile "solver.py", line 42',
      }),
    } as Response);

    await expect(
      api.runScenario({ scenario_type: 'severe_shortage', n_farmers: 4 })
    ).rejects.toThrow('An internal error occurred: WaterAllocationError');
  });
});
