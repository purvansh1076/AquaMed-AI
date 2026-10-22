/**
 * AquaMediAI — Conflict List Table
 * Displays detected water-sharing conflicts with user-friendly summaries
 * and expandable technical details for academic evaluation.
 */

import React from 'react';
import type { ConflictReportResponse } from '../../types/api';
import { formatWater } from '../../utils/formatters';
import { Badge } from '../common/Badge';

interface ConflictListTableProps {
  conflicts: ConflictReportResponse[];
}

export const ConflictListTable: React.FC<ConflictListTableProps> = ({ conflicts }) => {
  if (!conflicts || conflicts.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-subtle)' }}>
        No operational or resource conflicts detected for this scenario — water supply meets or exceeds total farm demand.
      </div>
    );
  }

  

  const severityLabels: Record<string, string> = {
    critical: 'CRITICAL',
    high: 'HIGH',
    medium: 'MEDIUM',
    low: 'LOW',
  };

  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
        {conflicts.map((c) => (
          <div
            key={c.conflict_id}
            className="card"
            style={{
              marginBottom: 0,
              borderLeft: `4px solid ${severityLabels[c.severity.toLowerCase()] || 'var(--severity-medium)'}`,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '10px',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                    {c.conflict_type.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <Badge variant="info">
                    {severityLabels[c.severity.toLowerCase()] || c.severity.toUpperCase()}
                  </Badge>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '2px', fontFamily: 'monospace' }}>
                  Conflict {c.conflict_id}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Resource Gap
                </div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--status-error)' }}>
                  {formatWater(c.resource_gap_m3)}
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '14px',
                margin: '12px 0',
                padding: '12px',
                background: '#f8fafc',
                borderRadius: '6px',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>
                  Farms Involved
                </div>
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
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>
                  Water Envelope
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  Demand: <strong>{formatWater(c.total_demand_m3)}</strong> | Available: <strong>{formatWater(c.available_water_m3)}</strong>
                </div>
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: '4px' }}>
                Why This Issue Was Flagged:
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.5' }}>
                {c.explanation}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Complete Conflict Table View */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">All Conflict Records</div>
          <div className="card-subtitle">Tabular synthesis from Phase 4 detector — synthetic data, academic demonstration only</div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: 'var(--bg-subtle, #f8fafc)', borderBottom: '2px solid var(--border-default, #e2e8f0)' }}>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--text-subtle)' }}>ID</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--text-subtle)' }}>Type</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--text-subtle)' }}>Severity</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--text-subtle)' }}>Farms</th>
                <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, color: 'var(--text-subtle)' }}>Resource Gap</th>
                <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, color: 'var(--text-subtle)' }}>Total Demand</th>
                <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, color: 'var(--text-subtle)' }}>Available</th>
              </tr>
            </thead>
            <tbody>
              {conflicts.map((c, idx) => (
                <tr
                  key={c.conflict_id}
                  style={{
                    borderBottom: '1px solid var(--border-default, #e2e8f0)',
                    background: idx % 2 === 0 ? 'transparent' : 'var(--bg-subtle, #f8fafc)',
                  }}
                >
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-subtle)' }}>{c.conflict_id}</td>
                  <td style={{ padding: '8px 12px', fontWeight: 500 }}>{c.conflict_type.replace(/_/g, ' ')}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <Badge variant="info">{c.severity.charAt(0).toUpperCase() + c.severity.slice(1).toLowerCase()}</Badge>
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontSize: '12px' }}>{c.involved_farmer_ids.join(', ')}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--status-error)', fontWeight: 600 }}>{formatWater(c.resource_gap_m3)}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>{formatWater(c.total_demand_m3)}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>{formatWater(c.available_water_m3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};