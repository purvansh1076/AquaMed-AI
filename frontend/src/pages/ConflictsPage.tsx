import React from 'react';
import { AlertTriangle, AlertOctagon, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { EmptyState } from '../components/common/EmptyState';
import { MetricCard } from '../components/common/MetricCard';
import { ConflictListTable } from '../components/tables/ConflictListTable';
import { formatWater, formatPercent, capitalize } from '../utils/formatters';
import { Badge } from '../components/common/Badge';

export const ConflictsPage: React.FC = () => {
  const { scenarioResult } = useScenario();

  if (!scenarioResult) {
    return (
      <div>
        <div className="page-heading">
          <h1 className="page-title">Conflict Detection Engine</h1>
          <p className="page-description">Phase 4: Rule-based agrarian conflict detection across 5 distinct conflict topologies.</p>
        </div>
        <EmptyState />
      </div>
    );
  }

  const { conflicts, available_water_m3, total_demand_m3 } = scenarioResult;
  const conflictList = conflicts?.conflicts || [];
  const totalConflicts = conflicts?.total_conflicts ?? 0;
  const highestSeverity = conflicts?.highest_severity || 'none';
  const resourceGap = conflicts?.resource_gap_m3 ?? 0;
  const shortageRatio = conflicts?.overall_shortage_ratio ?? 0;

  const getSeverityVariant = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'critical';
      case 'high':
        return 'high';
      case 'medium':
        return 'medium';
      case 'low':
        return 'low';
      default:
        return 'neutral';
    }
  };

  return (
    <div>
      <div className="page-heading">
        <h1 className="page-title">Conflict Detection Engine</h1>
        <p className="page-description">
          Phase 4 rule-based conflict detector evaluates resource scarcity, canal delivery bottlenecks, overlapping schedules, and priority tensions.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <MetricCard
          label="Total Conflicts Detected"
          value={totalConflicts}
          unit="disputes"
          footnote="Triggering automated mediation"
          icon={<AlertTriangle size={18} />}
        />
        <MetricCard
          label="Highest Severity Level"
          value={capitalize(highestSeverity)}
          footnote="Determines urgency weighting"
          icon={<AlertOctagon size={18} />}
        />
        <MetricCard
          label="System Resource Gap"
          value={formatWater(resourceGap)}
          footnote={`Shortage Ratio: ${formatPercent(shortageRatio)}`}
          icon={<ShieldAlert size={18} />}
        />
        <MetricCard
          label="Canal Availability vs Demand"
          value={`${formatWater(available_water_m3)} / ${formatWater(total_demand_m3)}`}
          footnote="Physical constraint envelope"
        />
      </div>

      {/* Detailed Conflict Cards */}
      {totalConflicts === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
          <CheckCircle2 size={40} style={{ color: 'var(--status-success)', margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>
            Zero Conflicts Detected
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', maxWidth: '440px', margin: '6px auto 0 auto' }}>
            Canal water supply exceeds aggregate demand ({formatWater(available_water_m3)} ≥ {formatWater(total_demand_m3)}).
            No allocation rationing or concession rounds needed.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
          {conflictList.map((c) => (
            <div
              key={c.conflict_id}
              className="card"
              style={{
                marginBottom: 0,
                borderLeft: `4px solid ${
                  c.severity.toLowerCase() === 'critical'
                    ? 'var(--severity-critical)'
                    : c.severity.toLowerCase() === 'high'
                    ? 'var(--severity-high)'
                    : 'var(--severity-medium)'
                }`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                      {c.conflict_type.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    <Badge variant={getSeverityVariant(c.severity)}>
                      SEVERITY: {c.severity.toUpperCase()} (Score: {c.severity_score.toFixed(2)})
                    </Badge>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '2px', fontFamily: 'monospace' }}>
                    Conflict ID: {c.conflict_id}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Resource Deficit
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--status-error)' }}>
                    {formatWater(c.resource_gap_m3)}
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', margin: '12px 0', padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>AFFECTED FARMERS</div>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                    {c.involved_farmer_ids.map((id) => (
                      <span
                        key={id}
                        style={{
                          fontFamily: 'monospace',
                          fontSize: '12px',
                          background: '#ffffff',
                          border: '1px solid var(--border-default)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontWeight: 600,
                        }}
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>WATER ENVELOPE</div>
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>
                    Demand: <strong>{formatWater(c.total_demand_m3)}</strong> | Available: <strong>{formatWater(c.available_water_m3)}</strong>
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: '4px' }}>
                  Detection Rationale:
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.5' }}>
                  {c.explanation}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Complete Conflict Table View */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">All Conflict Records</div>
            <div className="card-subtitle">Tabular synthesis from Phase 4 detector</div>
          </div>
        </div>
        <ConflictListTable conflicts={conflictList} />
      </div>
    </div>
  );
};
