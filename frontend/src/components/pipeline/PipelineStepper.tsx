import React from 'react';
import { Check, AlertTriangle, HelpCircle } from 'lucide-react';
import type { ScenarioRunResponse } from '../../types/api';

interface PipelineStepperProps {
  scenarioResult: ScenarioRunResponse | null;
  activeStage?: string;
}

interface StageConfig {
  id: string;
  name: string;
  getStatus: (result: ScenarioRunResponse | null) => {
    state: 'completed' | 'active' | 'warning' | 'unavailable';
    label: string;
  };
}

export const PipelineStepper: React.FC<PipelineStepperProps> = ({
  scenarioResult,
}) => {
  const stages: StageConfig[] = [
    {
      id: 'prediction',
      name: 'Demand Prediction',
      getStatus: (res) => {
        if (!res) return { state: 'unavailable', label: 'Idle' };
        if (res.predictions && res.predictions.length > 0) {
          return { state: 'completed', label: `${res.predictions.length} Models Run` };
        }
        return { state: 'warning', label: 'Incomplete' };
      },
    },
    {
      id: 'conflicts',
      name: 'Conflict Detection',
      getStatus: (res) => {
        if (!res) return { state: 'unavailable', label: 'Idle' };
        const conflictsCount = res.conflicts?.total_conflicts ?? 0;
        if (conflictsCount > 0) {
          return { state: 'warning', label: `${conflictsCount} Detected` };
        }
        return { state: 'completed', label: 'Zero Conflicts' };
      },
    },
    {
      id: 'allocation',
      name: 'Water Optimization',
      getStatus: (res) => {
        if (!res) return { state: 'unavailable', label: 'Idle' };
        const status = res.initial_allocation?.solver_status?.toLowerCase();
        if (status === 'optimal') {
          return { state: 'completed', label: 'GLOP Optimal' };
        } else if (status) {
          return { state: 'warning', label: status };
        }
        return { state: 'unavailable', label: 'Unsolved' };
      },
    },
    {
      id: 'negotiation',
      name: 'Multi-Agent Negotiation',
      getStatus: (res) => {
        if (!res) return { state: 'unavailable', label: 'Idle' };
        const status = res.negotiation?.agreement_status || res.status;
        if (status === 'agreed') {
          return { state: 'completed', label: 'Agreed' };
        } else if (status) {
          return { state: 'warning', label: status.replace(/_/g, ' ') };
        }
        return { state: 'unavailable', label: 'Pending' };
      },
    },
    {
      id: 'explainability',
      name: 'Explainability',
      getStatus: (res) => {
        if (!res) return { state: 'unavailable', label: 'Idle' };
        if (res.explanations && res.explanations.all_reason_codes?.length > 0) {
          return { state: 'completed', label: `${res.explanations.all_reason_codes.length} Codes` };
        }
        return { state: 'completed', label: 'Generated' };
      },
    },
    {
      id: 'agreement',
      name: 'Final Agreement',
      getStatus: (res) => {
        if (!res) return { state: 'unavailable', label: 'Idle' };
        const isValid = res.final_decision?.is_physically_valid ?? true;
        if (isValid) {
          return { state: 'completed', label: 'Verified H1-H3' };
        }
        return { state: 'warning', label: 'Unverified' };
      },
    },
  ];

  return (
    <div className="pipeline-stepper">
      {stages.map((stage, idx) => {
        const { state, label } = stage.getStatus(scenarioResult);
        const isLast = idx === stages.length - 1;

        return (
          <React.Fragment key={stage.id}>
            <div className={`pipeline-step ${state}`}>
              <div
                className="step-circle"
                style={{
                  backgroundColor:
                    state === 'completed'
                      ? 'var(--color-primary)'
                      : state === 'warning'
                      ? 'var(--status-warning)'
                      : state === 'active'
                      ? 'var(--color-teal)'
                      : '#e2e8f0',
                  color: state === 'unavailable' ? '#64748b' : '#ffffff',
                }}
              >
                {state === 'completed' && <Check size={14} />}
                {state === 'warning' && <AlertTriangle size={14} />}
                {state === 'unavailable' && <HelpCircle size={14} />}
                {state === 'active' && idx + 1}
              </div>
              <div className="step-info">
                <span className="step-name">{stage.name}</span>
                <span className="step-status">{label}</span>
              </div>
            </div>
            {!isLast && (
              <div
                className={`step-divider ${state === 'completed' ? 'completed' : ''}`}
                style={{
                  backgroundColor: state === 'completed' ? 'var(--color-primary)' : '#e2e8f0',
                }}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
