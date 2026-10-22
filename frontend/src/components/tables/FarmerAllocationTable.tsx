import React from 'react';
import type { FarmerAllocationResponse } from '../../types/api';
import { formatWater, formatPercent, capitalize } from '../../utils/formatters';
import { Badge } from '../common/Badge';

interface FarmerAllocationTableProps {
  allocations: FarmerAllocationResponse[];
}

export const FarmerAllocationTable: React.FC<FarmerAllocationTableProps> = ({ allocations }) => {
  return (
    <div className="table-responsive">
      <table className="data-table">
        <thead>
          <tr>
            <th>Farmer ID</th>
            <th>Crop</th>
            <th>Stage</th>
            <th className="numeric">Urgency</th>
            <th className="numeric">Predicted Demand</th>
            <th className="numeric">Min Req (FAO-56)</th>
            <th className="numeric">Allocated Water</th>
            <th className="numeric">Unmet Demand</th>
            <th className="numeric">Satisfaction</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {allocations.map((a) => {
            const isFull = a.satisfaction_ratio >= 0.99;
            const isDeficit = a.unmet_demand_m3 > 0.05;
            const statusVariant =
              a.constraint_status === 'satisfied'
                ? isFull
                  ? 'success'
                  : 'info'
                : a.constraint_status === 'relaxed'
                ? 'warning'
                : 'critical';

            return (
              <tr key={a.farmer_id}>
                <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>{a.farmer_id}</td>
                <td>
                  <span style={{ fontWeight: 500 }}>{capitalize(a.crop)}</span>
                </td>
                <td style={{ color: 'var(--text-muted)' }}>{capitalize(a.growth_stage)}</td>
                <td className="numeric">
                  <span
                    style={{
                      color: a.urgency > 0.7 ? 'var(--severity-critical)' : 'inherit',
                      fontWeight: a.urgency > 0.7 ? 600 : 'normal',
                    }}
                  >
                    {a.urgency.toFixed(2)}
                  </span>
                </td>
                <td className="numeric">{formatWater(a.predicted_demand_m3)}</td>
                <td className="numeric" style={{ color: 'var(--text-muted)' }}>
                  {formatWater(a.minimum_requirement_m3)}
                </td>
                <td className="numeric" style={{ fontWeight: 600, color: 'var(--color-primary-dark)' }}>
                  {formatWater(a.allocated_water_m3)}
                </td>
                <td className="numeric" style={{ color: isDeficit ? 'var(--status-warning)' : 'inherit' }}>
                  {formatWater(a.unmet_demand_m3)}
                </td>
                <td className="numeric" style={{ fontWeight: 600 }}>
                  {formatPercent(a.satisfaction_ratio)}
                </td>
                <td>
                  <Badge variant={statusVariant}>{capitalize(a.constraint_status)}</Badge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
