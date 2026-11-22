/**
 * Centralized API Service for AquaMediAI.
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

const isDev = import.meta.env.DEV;

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  (isDev ? 'http://localhost:8000' : '');

if (!API_BASE_URL && !isDev) {
  throw new Error(
    'VITE_API_BASE_URL is required in production. Set it in the Vercel dashboard or .env.'
  );
}

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

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function apiFetch(
  path: string,
  init: RequestInit,
  timeoutMs: number,
  retry: boolean
): Promise<Response> {
  const url = `${API_BASE_URL}${path}`;
  const method = (init.method || 'GET').toUpperCase();
  const isGet = method === 'GET';
  const attempts = isGet && retry ? 2 : 1;
  let lastError: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fetchWithTimeout(url, init, timeoutMs);
    } catch (err) {
      lastError = err;
      if (i < attempts - 1) {
        await new Promise((resolve) => setTimeout(resolve, 300 * (i + 1)));
      }
    }
  }
  throw lastError;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    try {
      localStorage.removeItem('aquamedi_auth_session');
      localStorage.removeItem('aquamedi_auth_token');
    } catch {
      // storage unavailable
    }
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  if (response.status === 204) {
    return null as T;
  }

  const contentLength = response.headers?.get?.('content-length') ?? null;
  if (contentLength === '0') {
    return null as T;
  }

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
      errorDetail = response.statusText || errorDetail;
    }

    const sanitizedDetail = errorDetail.split('\n')[0].replace(/File ".*?", line \d+/g, '');
    throw new ApiServiceError(sanitizedDetail, response.status, errorType);
  }

  try {
    return (await response.json()) as T;
  } catch {
    return null as T;
  }
}

export const api = {
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

  getAuthToken(): string | null {
    return _authToken;
  },

  async createGuestSession(): Promise<GuestSessionResponse> {
    const response = await apiFetch('/api/v1/auth/guest-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    }, 30000, false);
    const data = await handleResponse<GuestSessionResponse>(response);
    if (data) this.setAuthToken(data.access_token);
    return data as GuestSessionResponse;
  },

  async loginExpert(request: ExpertLoginRequest): Promise<ExpertLoginResponse> {
    const response = await apiFetch('/api/v1/auth/expert/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(request),
    }, 30000, false);
    const data = await handleResponse<ExpertLoginResponse>(response);
    if (data) this.setAuthToken(data.access_token);
    return data as ExpertLoginResponse;
  },

  async getIdentity(): Promise<IdentityResponse> {
    const response = await apiFetch('/api/v1/auth/me', {
      method: 'GET',
      headers: getAuthHeaders(),
    }, 30000, true);
    return handleResponse<IdentityResponse>(response);
  },

  async logout(): Promise<{ status: string; message: string } | null> {
    try {
      const response = await apiFetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: getAuthHeaders(),
      }, 30000, false);
      return await handleResponse<{ status: string; message: string }>(response);
    } finally {
      this.setAuthToken(null);
    }
  },

  async getHealth(): Promise<HealthResponse> {
    try {
      const response = await apiFetch('/api/v1/health', {
        method: 'GET',
        headers: { Accept: 'application/json' },
      }, 30000, true);
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

  async runScenario(request: ScenarioRunRequest): Promise<ScenarioRunResponse> {
    try {
      const response = await apiFetch('/api/v1/scenarios/run', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(request),
      }, 120000, false);
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

  async predictSingle(request: PredictionRequest): Promise<PredictionResponse> {
    const response = await apiFetch('/api/v1/predictions', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    }, 30000, false);
    return handleResponse<PredictionResponse>(response);
  },

  async predictBatch(request: PredictionBatchRequest): Promise<PredictionBatchResponse> {
    const response = await apiFetch('/api/v1/predictions/batch', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    }, 30000, false);
    return handleResponse<PredictionBatchResponse>(response);
  },

  async detectConflicts(request: ConflictRequest): Promise<ScenarioConflictReportResponse> {
    const response = await apiFetch('/api/v1/conflicts', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    }, 30000, false);
    return handleResponse<ScenarioConflictReportResponse>(response);
  },

  async runAllocation(request: AllocationRequest): Promise<AllocationResponse> {
    const response = await apiFetch('/api/v1/allocations', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    }, 30000, false);
    return handleResponse<AllocationResponse>(response);
  },

  async runNegotiation(request: NegotiationRequest): Promise<NegotiationResponse> {
    const response = await apiFetch('/api/v1/negotiations', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    }, 30000, false);
    return handleResponse<NegotiationResponse>(response);
  },

  getBaseUrl(): string {
    return API_BASE_URL;
  },
};
