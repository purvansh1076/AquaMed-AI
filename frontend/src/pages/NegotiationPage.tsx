import React from 'react';
import { Handshake, GitCommit, ShieldAlert, TrendingUp } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { EmptyState } from '../components/common/EmptyState';
import { MetricCard } from '../components/common/MetricCard';
import { ConcessionTable } from '../components/tables/ConcessionTable';
import { FairnessTrajectoryChart } from '../components/charts/FairnessTrajectoryChart';
import { formatWater, capitalize } from '../utils/formatters';
import { Badge } from '../components/common/Badge';

export const NegotiationPage: React.FC = () => {
  const { scenarioResult } = useScenario();

  if (!scenarioResult) {
    return (
      <div>
        <div className="page-heading">
          <h1 className="page-title">Multi-Agent Negotiation</h1>
          <p className="page-description">Phase 6: Nash-bargaining-inspired iterative dispute mediation protocol.</p>
        </div>
        <EmptyState />
      </div>
    );
  }

  const { negotiation, explanations } = scenarioResult;
  const agreement = negotiation?.agreement;
  const rounds = negotiation?.rounds || [];
  const concessions = agreement?.concessions || [];
  const status = agreement?.agreement_status || negotiation?.agreement_status || scenarioResult.status;
  const terminationReason = agreement?.termination_reason || negotiation?.termination_reason || 'Initial allocation accepted.';

  const fairnessHistory = agreement?.round_fairness_history || [];
  const nashHistory = agreement?.round_nash_history || [];
  const batnaExplanations = explanations?.negotiation_explanation?.batna_explanations || [];

  return (
    <div>
      <div className="page-heading">
        <h1 className="page-title">Multi-Agent Negotiation</h1>
        <p className="page-description">
          Phase 6 protocol: Autonomous digital twins evaluate utility functions, protect BATNA floors, offer concessions, and reach verifiable consensus.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <MetricCard
          label="Negotiation Outcome"
          value={capitalize(status)}
          footnote={`Status: ${status.toUpperCase()}`}
          icon={<Handshake size={18} />}
        />
        <MetricCard
          label="Negotiation Rounds"
          value={agreement?.negotiation_rounds ?? (negotiation?.n_rounds ?? 1)}
          unit="rounds"
          footnote="Bounded by max_rounds = 5"
          icon={<GitCommit size={18} />}
        />
        <MetricCard
          label="Total Concessions Made"
          value={concessions.length}
          unit="actions"
          footnote="Flexibility & urgency-scaled reductions"
          icon={<TrendingUp size={18} />}
        />
        <MetricCard
          label="BATNA Protection"
          value="ENFORCED"
          footnote="Survival requirement floor guaranteed"
          icon={<ShieldAlert size={18} />}
        />
      </div>

      {/* Outcome Banner */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          background: status === 'agreed' ? 'var(--status-success-bg)' : 'var(--status-warning-bg)',
          borderLeft: `4px solid ${status === 'agreed' ? 'var(--status-success)' : 'var(--status-warning)'}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Badge variant={status === 'agreed' ? 'success' : 'warning'}>
            {status.replace(/_/g, ' ').toUpperCase()}
          </Badge>
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>
            Termination Reason: {terminationReason}
          </span>
        </div>
        {explanations?.negotiation_explanation?.summary && (
          <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            {explanations.negotiation_explanation.summary}
          </p>
        )}
      </div>

      {/* Round-by-Round Timeline (only real rounds) */}
      {rounds.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recorded Negotiation Rounds Timeline</div>
              <div className="card-subtitle">
                Authentic audit trail: Farmer response counts, Nash objective, and LP re-optimization per round
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {rounds.map((r) => (
              <div
                key={r.round_number}
                style={{
                  padding: '14px 16px',
                  background: '#f8fafc',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--color-primary-dark)' }}>
                      Round {r.round_number}
                    </span>
                    <Badge variant={r.solver_status.toLowerCase() === 'optimal' ? 'success' : 'warning'}>
                      LP: {r.solver_status}
                    </Badge>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>
                    Log-Nash Objective: <strong>{r.nash_objective.toFixed(4)}</strong> | Jain's Fairness: <strong>{r.fairness_score.toFixed(4)}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <span className="badge badge-success">{r.n_accepting} Accept</span>
                  <span className="badge badge-warning">{r.n_requesting_change} Request Change</span>
                  <span className="badge badge-critical">{r.n_rejecting} Reject</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trajectory Chart (Fairness & Nash) */}
      {fairnessHistory.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Convergence Trajectory: Fairness & Nash Objective</div>
              <div className="card-subtitle">
                Iterative progress across negotiation rounds (Nash-bargaining-inspired utility heuristic)
              </div>
            </div>
          </div>
          <FairnessTrajectoryChart fairnessHistory={fairnessHistory} nashHistory={nashHistory} />
        </div>
      )}

      {/* BATNA Protection Analysis */}
      {batnaExplanations.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">BATNA (Best Alternative to a Negotiated Agreement) Audit</div>
              <div className="card-subtitle">
                Guarantees no farmer is coerced into an allocation below their FAO-56 survival threshold
              </div>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Farmer ID</th>
                  <th className="numeric">BATNA Utility</th>
                  <th className="numeric">BATNA Water Floor</th>
                  <th className="numeric">Negotiated Utility</th>
                  <th className="numeric">Negotiated Allocation</th>
                  <th className="numeric">Utility Surplus</th>
                  <th>BATNA Status</th>
                </tr>
              </thead>
              <tbody>
                {batnaExplanations.map((b) => (
                  <tr key={b.farmer_id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{b.farmer_id}</td>
                    <td className="numeric">{b.batna_utility.toFixed(4)}</td>
                    <td className="numeric">{formatWater(b.batna_allocation_m3)}</td>
                    <td className="numeric" style={{ fontWeight: 600 }}>
                      {b.negotiated_utility !== null ? b.negotiated_utility.toFixed(4) : '—'}
                    </td>
                    <td className="numeric" style={{ fontWeight: 600, color: 'var(--color-primary-dark)' }}>
                      {formatWater(b.negotiated_allocation_m3)}
                    </td>
                    <td
                      className="numeric"
                      style={{
                        fontWeight: 600,
                        color: (b.surplus ?? 0) >= 0 ? 'var(--status-success)' : 'var(--status-error)',
                      }}
                    >
                      {b.surplus !== null ? (b.surplus >= 0 ? `+${b.surplus.toFixed(4)}` : b.surplus.toFixed(4)) : '—'}
                    </td>
                    <td>
                      <Badge variant={b.is_above_batna ? 'success' : 'critical'}>
                        {b.is_above_batna ? 'ABOVE BATNA' : 'BELOW BATNA'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Concessions Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Concession Log</div>
            <div className="card-subtitle">
              Computational concessions formula: Δ ask = (ask - min_req) × (flexibility × (1 - urgency))
            </div>
          </div>
        </div>
        <ConcessionTable concessions={concessions} />
      </div>
    </div>
  );
};
