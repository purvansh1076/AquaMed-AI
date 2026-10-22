import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { FarmerAllocationResponse } from '../../types/api';

interface SatisfactionBarChartProps {
  allocations: FarmerAllocationResponse[];
}

export const SatisfactionBarChart: React.FC<SatisfactionBarChartProps> = ({ allocations }) => {
  const data = allocations.map((item) => ({
    farmer: item.farmer_id,
    satisfaction: Number((item.satisfaction_ratio * 100).toFixed(1)),
    crop: item.crop,
  }));

  const getColor = (val: number) => {
    if (val >= 90) return '#15803d'; // Green
    if (val >= 65) return '#087e8b'; // Teal
    if (val >= 40) return '#b45309'; // Amber
    return '#b91c1c'; // Red
  };

  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="farmer"
            tick={{ fill: '#475569', fontSize: 12 }}
            tickLine={{ stroke: '#cbd5e1' }}
          />
          <YAxis
            domain={[0, 100]}
            unit="%"
            label={{ value: 'Satisfaction Ratio (%)', angle: -90, position: 'insideLeft', fill: '#475569', fontSize: 12 }}
            tick={{ fill: '#475569', fontSize: 12 }}
            tickLine={{ stroke: '#cbd5e1' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '12px',
            }}
            formatter={(val: unknown) => [`${val}%`, 'Satisfaction']}
          />
          <ReferenceLine y={65} stroke="#b45309" strokeDasharray="3 3" label={{ value: '65% Accept Threshold', fill: '#b45309', fontSize: 10, position: 'right' }} />
          <ReferenceLine y={100} stroke="#15803d" strokeDasharray="3 3" />
          <Bar dataKey="satisfaction" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.satisfaction)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
