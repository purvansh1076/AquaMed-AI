import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { FarmerAllocationResponse } from '../../types/api';

interface DemandAllocationChartProps {
  allocations: FarmerAllocationResponse[];
}

export const DemandAllocationChart: React.FC<DemandAllocationChartProps> = ({ allocations }) => {
  const data = allocations.map((item) => ({
    farmer: item.farmer_id,
    crop: item.crop,
    demand: Number(item.predicted_demand_m3.toFixed(1)),
    allocated: Number(item.allocated_water_m3.toFixed(1)),
    minimum: Number(item.minimum_requirement_m3.toFixed(1)),
  }));

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="farmer"
            tick={{ fill: '#475569', fontSize: 12 }}
            tickLine={{ stroke: '#cbd5e1' }}
          />
          <YAxis
            label={{ value: 'Water Volume (m³)', angle: -90, position: 'insideLeft', fill: '#475569', fontSize: 12 }}
            tick={{ fill: '#475569', fontSize: 12 }}
            tickLine={{ stroke: '#cbd5e1' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
              fontSize: '12px',
            }}
            formatter={(value: unknown) => [`${value} m³`, '']}
            labelFormatter={(label: unknown) => `Farmer: ${label}`}
          />
          <Legend wrapperStyle={{ paddingTop: 10, fontSize: 12 }} />
          <Bar dataKey="demand" name="Predicted Demand" fill="#087e8b" radius={[4, 4, 0, 0]} />
          <Bar dataKey="allocated" name="Allocated Water" fill="#1b4332" radius={[4, 4, 0, 0]} />
          <Bar dataKey="minimum" name="Min Requirement" fill="#e07a5f" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
