import React from 'react';
import { useScenario } from '../context/ScenarioContext';
import { EmptyState } from '../components/common/EmptyState';
import { RawJsonViewer } from '../components/debug/RawJsonViewer';
import { Server } from 'lucide-react';
import { api } from '../services/api';

export const DebugPage: React.FC = () => {
  const { scenarioResult, health } = useScenario();

  return (
    <div>
      <div className="page-heading">
        <h1 className="page-title">Developer & Academic Verification View</h1>
        <p className="page-description">
          Inspect raw, unmodified JSON responses directly from the FastAPI backend for grading and auditability.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Server size={16} />
            Backend Connection Metadata
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', fontSize: '12px' }}>
          <div>
            <div style={{ color: 'var(--text-subtle)', fontWeight: 600 }}>API BASE URL</div>
            <div style={{ fontFamily: 'monospace', fontWeight: 600 }}>{api.getBaseUrl()}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-subtle)', fontWeight: 600 }}>API SERVICE NAME</div>
            <div>{health?.service || 'AquaMediAI'}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-subtle)', fontWeight: 600 }}>API VERSION</div>
            <div>v{health?.version || '1.0.0'}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-subtle)', fontWeight: 600 }}>PIPELINE ARTIFACTS</div>
            <div>{health?.pipeline || 'available'}</div>
          </div>
        </div>
      </div>

      {scenarioResult ? (
        <RawJsonViewer data={scenarioResult} title="Active Scenario Payload (ScenarioRunResponse)" />
      ) : (
        <EmptyState
          title="No Active Scenario Payload"
          description="Execute a scenario via the Scenario Config page to inspect its complete JSON payload."
          actionText="Go to Scenario Config"
          actionHref="/scenario"
        />
      )}
    </div>
  );
};
