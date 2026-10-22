import React from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Droplets,
  TrendingDown,
  AlertOctagon,
  Scale,
  Handshake,
  ArrowRight,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { MetricCard } from '../components/common/MetricCard';
import { PipelineStepper } from '../components/pipeline/PipelineStepper';
import { EmptyState } from '../components/common/EmptyState';
import { DemandAllocationChart } from '../components/charts/DemandAllocationChart';
import { formatWater, formatPercent, capitalize } from '../utils/formatters';
import { Badge } from '../components/common/Badge';

export const OverviewPage: React.FC = () => {
  const { scenarioResult } = useScenario();

  if (!scenarioResult) {
    return (
      <div>
        <div className="page-heading">
          <h1 className="page-title">Mediation Overview</h1>
          <p className="page-description">
            High-level executive dashboard for the AquaMediAI multi-agent water-sharing resolution process.
          </p>
        </div>
        <PipelineStepper scenarioResult={null} />
        <EmptyState
          title="No Scenario Loaded"
          description="Configure an agronomic scenario and run AquaMediAI mediation to inspect decisions, optimization results, and explainability."
          actionText="Configure & Run Scenario"
          actionHref="/scenario"
        />
      </div>
    );
  }

  const {
    scenario_id,
    scenario_type,
    n_farmers,
    available_water_m3,
    total_demand_m3,
    conflicts,
    initial_allocation,
    negotiation,
    final_decision,
  } = scenarioResult;

  const agreementStatus = negotiation?.agreement_status || scenarioResult.status;
  const fairnessScore = final_decision?.fairness_score ?? initial_allocation?.fairness_score;
  const avgSatisfaction = initial_allocation?.average_satisfaction;
  const utilization = final_decision?.water_utilization ?? initial_allocation?.utilization;

  return (
    <div>
      <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Mediation Overview</h1>
          <p className="page-description">
            Scenario: <strong style={{ color: 'var(--color-primary-dark)' }}>{scenario_id}</strong> ({capitalize(scenario_type)})
          </p>
        </div>
        <Link to="/scenario" className="btn btn-outline btn-sm">
          Change Scenario
          <ArrowRight size={14} />
        </Link>
      </div>

      {/* Pipeline Stepper */}
      <PipelineStepper scenarioResult={scenarioResult} />

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <MetricCard
          label="Participating Farmers"
          value={n_farmers}
          unit="agents"
          footnote="Autonomous digital twins"
          icon={<Users size={18} />}
        />
        <MetricCard
          label="Available Canal Water"
          value={formatWater(available_water_m3)}
          footnote={`Utilization: ${formatPercent(utilization)}`}
          icon={<Droplets size={18} />}
        />
        <MetricCard
          label="Total Predicted Demand"
          value={formatWater(total_demand_m3)}
          footnote="Aggregated ML crop predictions"
          icon={<TrendingDown size={18} />}
        />
        <MetricCard
          label="Conflicts Detected"
          value={conflicts?.total_conflicts ?? 0}
          unit="events"
          footnote={`Highest Severity: ${capitalize(conflicts?.highest_severity || 'none')}`}
          icon={<AlertOctagon size={18} />}
        />
        <MetricCard
          label="Avg Farmer Satisfaction"
          value={formatPercent(avgSatisfaction)}
          footnote={`Allocated: ${formatWater(initial_allocation?.total_allocated_m3)}`}
          icon={<Scale size={18} />}
        />
        <MetricCard
          label="Mediation Agreement"
          value={capitalize(agreementStatus)}
          footnote={`Jain's Fairness: ${fairnessScore !== undefined ? fairnessScore.toFixed(3) : '—'}`}
          icon={<Handshake size={18} />}
        />
      </div>

      {/* Two Column Layout: Allocation Chart & Key Insights */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '20px' }}>
        {/* Demand vs Allocation Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Water Allocation by Farmer</div>
              <div className="card-subtitle">
                Predicted Demand vs Solved Allocation (OR-Tools GLOP LP: {initial_allocation?.allocation_method})
              </div>
            </div>
            <Link to="/allocation" className="btn btn-outline btn-sm">
              View Allocation
            </Link>
          </div>
          <DemandAllocationChart allocations={initial_allocation?.allocations || []} />
        </div>

        {/* Pipeline Summary Card */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Mediation Outcome Summary</div>
              <div className="card-subtitle">Algorithmic synthesis across mediation phases</div>
            </div>
            <Link to="/agreement" className="btn btn-outline btn-sm">
              View Agreement
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-subtle)', fontWeight: 600 }}>
                Status & Termination
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
                <Badge variant={agreementStatus === 'agreed' ? 'success' : 'warning'}>
                  {agreementStatus.replace(/_/g, ' ').toUpperCase()}
                </Badge>
                <span style={{ fontSize: '13px', color: 'var(--text-main)', fontWeight: 500 }}>
                  {negotiation?.termination_reason || 'Initial optimal allocation accepted.'}
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600 }}>LP SOLVER STATUS</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)', marginTop: '2px' }}>
                  {capitalize(initial_allocation?.solver_status || '—')}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Wall time: {initial_allocation?.solver_wall_time_ms ? `${initial_allocation.solver_wall_time_ms.toFixed(1)} ms` : '—'}
                </div>
              </div>

              <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600 }}>JAIN'S FAIRNESS INDEX</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)', marginTop: '2px' }}>
                  {fairnessScore !== undefined ? fairnessScore.toFixed(4) : '—'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Scale: [0, 1] (1.0 = equal satisfaction)
                </div>
              </div>
            </div>

            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-subtle)', fontWeight: 600 }}>
                Explainability Reason Codes
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                {(scenarioResult.explanations?.all_reason_codes || []).map((code) => (
                  <Badge key={code} variant="neutral">
                    {code.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
              <Link to="/conflicts" className="btn btn-outline btn-sm" style={{ flex: 1 }}>
                Conflicts ({conflicts?.total_conflicts ?? 0})
              </Link>
              <Link to="/negotiation" className="btn btn-outline btn-sm" style={{ flex: 1 }}>
                Negotiation ({negotiation?.n_rounds ?? 1} Rounds)
              </Link>
              <Link to="/explainability" className="btn btn-primary btn-sm" style={{ flex: 1 }}>
                Explain Decisions
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Academic synthetic disclaimer */}
      <div className="alert alert-disclaimer" style={{ marginTop: '20px' }}>
        <strong>Academic Demonstration Notice:</strong> {scenarioResult.explanations?.data_disclaimer ||
          'All agronomic and dispute mediation data in this system is synthetically generated for academic demonstration purposes.'}
      </div>
    </div>
  );
};
