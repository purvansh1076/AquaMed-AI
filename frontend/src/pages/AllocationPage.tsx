import React from 'react';
import { Scale, CheckCircle, AlertTriangle, ShieldCheck, Clock } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { EmptyState } from '../components/common/EmptyState';
import { MetricCard } from '../components/common/MetricCard';
import { FarmerAllocationTable } from '../components/tables/FarmerAllocationTable';
import { DemandAllocationChart } from '../components/charts/DemandAllocationChart';
import { SatisfactionBarChart } from '../components/charts/SatisfactionBarChart';
import { formatWater, formatPercent, capitalize } from '../utils/formatters';
import { Badge } from '../components/common/Badge';

export const AllocationPage: React.FC = () => {
  const { scenarioResult } = useScenario();

  if (!scenarioResult) {
    return (
      <div>
        <div className="page-heading">
          <h1 className="page-title">Water Allocation Optimization</h1>
          <p className="page-description">Phase 5: Google OR-Tools GLOP Linear Programming (LP) water rationing.</p>
        </div>
        <EmptyState />
      </div>
    );
  }

  const { initial_allocation, available_water_m3, total_demand_m3 } = scenarioResult;
  const {
    solver_status,
    allocation_method,
    total_allocated_m3,
    total_unmet_demand_m3,
    remaining_water_m3,
    utilization,
    fairness_score,
    average_satisfaction,
    solver_wall_time_ms,
    verification,
    allocations,
  } = initial_allocation;

  return (
    <div>
      <div className="page-heading">
        <h1 className="page-title">Water Allocation Optimization</h1>
        <p className="page-description">
          Phase 5 Linear Program solver (Google OR-Tools GLOP) enforces physical conservation, survival minimums, and weighted satisfaction maximization.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <MetricCard
          label="Allocation Method"
          value={allocation_method}
          footnote={`Status: ${capitalize(solver_status)}`}
          icon={<Scale size={18} />}
        />
        <MetricCard
          label="Total Allocated Water"
          value={formatWater(total_allocated_m3)}
          footnote={`Supply: ${formatWater(available_water_m3)} (${formatPercent(utilization)})`}
          icon={<CheckCircle size={18} />}
        />
        <MetricCard
          label="Total Unmet Demand"
          value={formatWater(total_unmet_demand_m3)}
          footnote={`Aggregate Demand: ${formatWater(total_demand_m3)}`}
          icon={<AlertTriangle size={18} />}
        />
        <MetricCard
          label="Jain's Fairness Index"
          value={fairness_score.toFixed(4)}
          footnote={`Avg Satisfaction: ${formatPercent(average_satisfaction)}`}
          icon={<ShieldCheck size={18} />}
        />
      </div>

      {/* Physical Constraint Verification (H1/H2/H3) */}
      <div className="card" style={{ padding: '16px 20px', background: '#f8fafc' }}>
        <div className="card-header" style={{ marginBottom: '12px', paddingBottom: '8px' }}>
          <div>
            <div className="card-title" style={{ fontSize: '14px' }}>
              <ShieldCheck size={16} style={{ color: 'var(--color-primary)' }} />
              Independent Mathematical Constraint Verification (H1, H2, H3)
            </div>
            <div className="card-subtitle">
              Verified by independent post-solve checker before presenting outcome
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-subtle)' }}>
            <Clock size={13} />
            <span>Solver Wall Time: {solver_wall_time_ms ? `${solver_wall_time_ms.toFixed(2)} ms` : '—'}</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
          <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>H1: WATER CONSERVATION</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
              <Badge variant={verification.total_water_ok ? 'success' : 'critical'}>
                {verification.total_water_ok ? 'VERIFIED' : 'VIOLATION'}
              </Badge>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Σ x_i ≤ W</span>
            </div>
          </div>

          <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>H2: NON-NEGATIVITY</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
              <Badge variant={verification.non_negative_ok ? 'success' : 'critical'}>
                {verification.non_negative_ok ? 'VERIFIED' : 'VIOLATION'}
              </Badge>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>x_i ≥ 0</span>
            </div>
          </div>

          <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>H3: MAXIMUM BOUND</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
              <Badge variant={verification.maximum_ok ? 'success' : 'critical'}>
                {verification.maximum_ok ? 'VERIFIED' : 'VIOLATION'}
              </Badge>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>x_i ≤ max_i</span>
            </div>
          </div>

          <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>NUMERICAL STABILITY</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
              <Badge variant={verification.no_nan_ok ? 'success' : 'critical'}>
                {verification.no_nan_ok ? 'NO NAN / INF' : 'NUMERICAL ERROR'}
              </Badge>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Finite values</span>
            </div>
          </div>
        </div>

        {verification.violations.length > 0 && (
          <div className="alert alert-error" style={{ marginTop: '12px', marginBottom: 0 }}>
            <AlertTriangle size={16} />
            <div>Violations detected: {verification.violations.join(', ')}</div>
          </div>
        )}
      </div>

      {/* Visual Charts: Demand vs Allocation and Farmer Satisfaction */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Demand vs Allocation Comparison</div>
              <div className="card-subtitle">Volumetric distribution per farmer agent (m³)</div>
            </div>
          </div>
          <DemandAllocationChart allocations={allocations} />
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Farmer Satisfaction Distribution</div>
              <div className="card-subtitle">
                Satisfaction ratio (Allocated / Predicted Demand). Jain's Index: <strong>{fairness_score.toFixed(3)}</strong>
              </div>
            </div>
          </div>
          <SatisfactionBarChart allocations={allocations} />
        </div>
      </div>

      {/* Complete Farmer-wise Allocation Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Farmer-Wise Allocation Table</div>
            <div className="card-subtitle">
              Remaining unallocated canal water: <strong>{formatWater(remaining_water_m3)}</strong>
            </div>
          </div>
        </div>
        <FarmerAllocationTable allocations={allocations} />
      </div>
    </div>
  );
};
