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
  ExpertLoginRequest,
  ExpertLoginResponse,
  GuestSessionResponse,
  HealthResponse,
  IdentityResponse,
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

let _authToken: string | null = null;
try {
  _authToken = localStorage.getItem('aquamedi_auth_token');
} catch {
  // Local storage unavailable
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (_authToken) {
    headers['Authorization'] = `Bearer ${_authToken}`;
  }
  return headers;
}

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
  /** Set active auth token for all subsequent requests. */
  setAuthToken(token: string | null): void {
    _authToken = token;
    try {
      if (token) {
        localStorage.setItem('aquamedi_auth_token', token);
      } else {
        localStorage.removeItem('aquamedi_auth_token');
      }
    } catch {
      // storage unavailable
    }
  },

  /** Get active auth token. */
  getAuthToken(): string | null {
    return _authToken;
  },

  /** Create an uncredentialed guest session for farmers. */
  async createGuestSession(): Promise<GuestSessionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/guest-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    });
    const data = await handleResponse<GuestSessionResponse>(response);
    this.setAuthToken(data.access_token);
    return data;
  },

  /** Sign in as an Agricultural Expert. */
  async loginExpert(request: ExpertLoginRequest): Promise<ExpertLoginResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/expert/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    });
    const data = await handleResponse<ExpertLoginResponse>(response);
    this.setAuthToken(data.access_token);
    return data;
  },

  /** Get profile of the current session. */
  async getIdentity(): Promise<IdentityResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    return handleResponse<IdentityResponse>(response);
  },

  /** Terminate session. */
  async logout(): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      return await handleResponse<{ status: string; message: string }>(response);
    } finally {
      this.setAuthToken(null);
    }
  },

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
        headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
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
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    return handleResponse<NegotiationResponse>(response);
  },

  getBaseUrl(): string {
    return API_BASE_URL;
  },
};
