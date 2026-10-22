import React, { createContext, useContext, useEffect, useState } from 'react';
import type { HealthResponse, ScenarioRunRequest, ScenarioRunResponse } from '../types/api';
import { api } from '../services/api';

export type HealthStatus = 'checking' | 'connected' | 'offline';

interface ScenarioContextType {
  scenarioResult: ScenarioRunResponse | null;
  isLoading: boolean;
  loadingMessage: string;
  error: string | null;
  health: HealthResponse | null;
  healthStatus: HealthStatus;
  runScenario: (request: ScenarioRunRequest) => Promise<boolean>;
  checkHealth: () => Promise<void>;
  clearError: () => void;
  resetScenario: () => void;
}

export const ScenarioContext = createContext<ScenarioContextType | undefined>(undefined);

export const ScenarioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [scenarioResult, setScenarioResult] = useState<ScenarioRunResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('Executing pipeline...');
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('checking');

  const checkHealth = async () => {
    setHealthStatus('checking');
    try {
      const response = await api.getHealth();
      setHealth(response);
      setHealthStatus('connected');
    } catch {
      setHealth(null);
      setHealthStatus('offline');
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const runScenario = async (request: ScenarioRunRequest): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    setLoadingMessage('Running AquaMediAI mediation pipeline...');

    try {
      const result = await api.runScenario(request);
      setScenarioResult(result);
      setIsLoading(false);
      return true;
    } catch (err: unknown) {
      setIsLoading(false);
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setError(message);
      return false;
    }
  };

  const clearError = () => setError(null);
  const resetScenario = () => {
    setScenarioResult(null);
    setError(null);
  };

  return (
    <ScenarioContext.Provider
      value={{
        scenarioResult,
        isLoading,
        loadingMessage,
        error,
        health,
        healthStatus,
        runScenario,
        checkHealth,
        clearError,
        resetScenario,
      }}
    >
      {children}
    </ScenarioContext.Provider>
  );
};

export function useScenario(): ScenarioContextType {
  const context = useContext(ScenarioContext);
  if (!context) {
    throw new Error('useScenario must be used within a ScenarioProvider');
  }
  return context;
}
