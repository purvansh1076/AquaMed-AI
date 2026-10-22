import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { OverviewPage } from '../pages/OverviewPage';
import { PredictionsPage } from '../pages/PredictionsPage';
import { ConflictsPage } from '../pages/ConflictsPage';
import { AllocationPage } from '../pages/AllocationPage';
import { NegotiationPage } from '../pages/NegotiationPage';
import { ExplainabilityPage } from '../pages/ExplainabilityPage';
import { AgreementPage } from '../pages/AgreementPage';
import { DebugPage } from '../pages/DebugPage';
import { ScenarioProvider } from '../context/ScenarioContext';
import { ViewModeProvider } from '../context/ViewModeContext';

// We can test each page renders without throwing in empty or default state
describe('Individual Scenario Pages Rendering', () => {
  it('OverviewPage renders heading and empty state', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <OverviewPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Mediation Overview')).toBeInTheDocument();
  });

  it('PredictionsPage renders heading', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <PredictionsPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('ML Water Demand Predictions')).toBeInTheDocument();
  });

  it('ConflictsPage renders heading', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <ConflictsPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Conflict Detection Engine')).toBeInTheDocument();
  });

  it('AllocationPage renders heading', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <AllocationPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Water Allocation Optimization')).toBeInTheDocument();
  });

  it('NegotiationPage renders heading', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <NegotiationPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Multi-Agent Negotiation')).toBeInTheDocument();
  });

  it('ExplainabilityPage renders heading', () => {
    render(
      <MemoryRouter>
        <ViewModeProvider>
          <ScenarioProvider>
            <ExplainabilityPage />
          </ScenarioProvider>
        </ViewModeProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('💧 Why Did I Get This Much Water?')).toBeInTheDocument();
  });

  it('AgreementPage renders heading', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <AgreementPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Final Mediation Agreement')).toBeInTheDocument();
  });

  it('DebugPage renders heading', () => {
    render(
      <MemoryRouter>
        <ScenarioProvider>
          <DebugPage />
        </ScenarioProvider>
      </MemoryRouter>
    );
    expect(screen.getByText('Developer & Academic Verification View')).toBeInTheDocument();
  });
});
