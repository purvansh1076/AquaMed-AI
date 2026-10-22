/**
 * Centralized API Service for AquaMediAI.
 * Connects directly to the Phase 8 FastAPI backend.
 *
 * All request/response types mirror the backend Pydantic models.
 */

import type {
  AllocationRequest,
  AllocationResponse,
  ConflictRequest,
  HealthResponse,
  NegotiationRequest,
  NegotiationResponse,
  PredictionBatchRequest,
  PredictionBatchResponse,
  PredictionRequest,
  PredictionResponse,
  ScenarioConflictReportResponse,
  ScenarioRunRequest,
  ScenarioRunResponse,
} from '../types/api';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000';

class ApiServiceError extends Error {
  statusCode: number;
  errorType: string;

  constructor(message: string, statusCode = 500, errorType = 'api_error') {
    super(message);
    this.name = 'ApiServiceError';
    this.statusCode = statusCode;
    this.errorType = errorType;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    let errorType = 'http_error';

    try {
      const errorJson = await response.json();
      if (typeof errorJson === 'object' && errorJson !== null) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (typeof errorJson.detail === 'object' && errorJson.detail !== null) {
          errorDetail = errorJson.detail.detail || errorJson.detail.error || JSON.stringify(errorJson.detail);
          errorType = errorJson.detail.error || errorType;
        } else if (errorJson.message) {
          errorDetail = errorJson.message;
        }
      }
    } catch {
      // Body not JSON, fallback to statusText
      errorDetail = response.statusText || errorDetail;
    }

    // Clean any accidental Python tracebacks from showing to user
    const sanitizedDetail = errorDetail.split('\n')[0].replace(/File ".*?", line \d+/g, '');
    throw new ApiServiceError(sanitizedDetail, response.status, errorType);
  }

  return response.json() as Promise<T>;
}

export const api = {
  /**
   * Check backend health and model pipeline availability.
   * Calls GET /api/v1/health.
   */
  async getHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      return await handleResponse<HealthResponse>(response);
    } catch (err: unknown) {
      if (err instanceof ApiServiceError) throw err;
      throw new ApiServiceError(
        'FastAPI backend is unavailable. Start the AquaMediAI backend on port 8000 and try again.',
        0,
        'connection_refused'
      );
    }
  },

  /**
   * Run the primary full AquaMediAI mediation pipeline.
   * Calls POST /api/v1/scenarios/run.
   */
  async runScenario(request: ScenarioRunRequest): Promise<ScenarioRunResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/scenarios/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(request),
      });
      return await handleResponse<ScenarioRunResponse>(response);
    } catch (err: unknown) {
      if (err instanceof ApiServiceError) throw err;
      throw new ApiServiceError(
        'Failed to execute scenario. Check backend connectivity or configuration.',
        500,
        'pipeline_error'
      );
    }
  },

  /**
   * Predict water demand for a single farmer.
   * Calls POST /api/v1/predictions.
   */
  async predictSingle(request: PredictionRequest): Promise<PredictionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/predictions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<PredictionResponse>(response);
  },

  /**
   * Batch predict water demand for multiple farmers.
   * Calls POST /api/v1/predictions/batch.
   */
  async predictBatch(request: PredictionBatchRequest): Promise<PredictionBatchResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/predictions/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<PredictionBatchResponse>(response);
  },

  /**
   * Detect water-sharing conflicts.
   * Calls POST /api/v1/conflicts.
   */
  async detectConflicts(request: ConflictRequest): Promise<ScenarioConflictReportResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/conflicts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<ScenarioConflictReportResponse>(response);
  },

  /**
   * Run LP water allocation solve.
   * Calls POST /api/v1/allocations.
   */
  async runAllocation(request: AllocationRequest): Promise<AllocationResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/allocations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<AllocationResponse>(response);
  },

  /**
   * Run multi-agent negotiation.
   * Calls POST /api/v1/negotiations.
   */
  async runNegotiation(request: NegotiationRequest): Promise<NegotiationResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/negotiations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<NegotiationResponse>(response);
  },

  getBaseUrl(): string {
    return API_BASE_URL;
  },
};
