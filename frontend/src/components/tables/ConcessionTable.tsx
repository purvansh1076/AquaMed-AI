import React from 'react';
import type { ConcessionResponse } from '../../types/api';
import { formatWater, formatPercent } from '../../utils/formatters';

interface ConcessionTableProps {
  concessions: ConcessionResponse[];
}

export const ConcessionTable: React.FC<ConcessionTableProps> = ({ concessions }) => {
  if (!concessions || concessions.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-subtle)' }}>
        No concessions required or made in this negotiation session.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="data-table">
        <thead>
          <tr>
            <th>Round</th>
            <th>Farmer</th>
            <th className="numeric">Previous Ask</th>
            <th className="numeric">New Ask</th>
            <th className="numeric">Concession Volume</th>
            <th className="numeric">Concession Ratio</th>
            <th className="numeric">Flexibility</th>
            <th className="numeric">Urgency Factor</th>
            <th>Reason / Formula</th>
          </tr>
        </thead>
        <tbody>
          {concessions.map((c, idx) => (
            <tr key={`${c.farmer_id}-${c.round_number}-${idx}`}>
              <td style={{ fontWeight: 600 }}>R{c.round_number}</td>
              <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{c.farmer_id}</td>
              <td className="numeric">{formatWater(c.previous_ask_m3)}</td>
              <td className="numeric" style={{ color: 'var(--color-primary-dark)', fontWeight: 600 }}>
                {formatWater(c.new_ask_m3)}
              </td>
              <td className="numeric" style={{ color: 'var(--color-teal)', fontWeight: 600 }}>
                -{formatWater(c.concession_amount_m3)}
              </td>
              <td className="numeric">{formatPercent(c.concession_ratio)}</td>
              <td className="numeric">{c.flexibility_factor.toFixed(2)}</td>
              <td className="numeric">{c.urgency_factor.toFixed(2)}</td>
              <td style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '280px' }}>
                {c.reason}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
