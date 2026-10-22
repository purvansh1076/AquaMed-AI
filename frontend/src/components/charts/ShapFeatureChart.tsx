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
import type { FeatureContributionExplanation } from '../../types/api';

interface ShapFeatureChartProps {
  contributors: FeatureContributionExplanation[];
  title?: string;
}

export const ShapFeatureChart: React.FC<ShapFeatureChartProps> = ({
  contributors,
  title = 'Feature Contributions to Water Demand',
}) => {
  if (!contributors || contributors.length === 0) {
    return <div style={{ color: 'var(--text-subtle)', fontStyle: 'italic', padding: '16px' }}>No feature contribution explanations available.</div>;
  }

  // Sort by absolute shap contribution or rank
  const sorted = [...contributors].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).slice(0, 8);

  const data = sorted.map((c) => ({
    feature: c.feature.replace(/_/g, ' '),
    rawFeature: c.feature,
    shap: Number(c.shap_value.toFixed(2)),
    rawValue: c.raw_value,
    direction: c.direction,
    rationale: c.rationale,
  }));

  return (
    <div>
      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: '8px' }}>
        {title}
      </div>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer>
          <BarChart layout="vertical" data={data} margin={{ top: 10, right: 30, left: 90, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              type="number"
              tick={{ fill: '#475569', fontSize: 11 }}
              tickLine={{ stroke: '#cbd5e1' }}
              label={{ value: 'SHAP Contribution Value (m³)', position: 'insideBottom', offset: -10, fill: '#475569', fontSize: 11 }}
            />
            <YAxis
              type="category"
              dataKey="feature"
              tick={{ fill: '#475569', fontSize: 11 }}
              tickLine={{ stroke: '#cbd5e1' }}
              width={85}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '12px',
                maxWidth: '320px',
              }}
              formatter={(value: unknown) => [`${value} m³`, 'Contribution']}
              labelFormatter={(label: unknown, payload) => {
                const item = payload?.[0]?.payload;
                return `${label} (Value: ${item?.rawValue ?? '—'})`;
              }}
            />
            <ReferenceLine x={0} stroke="#94a3b8" />
            <Bar dataKey="shap" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`shap-cell-${index}`}
                  fill={entry.shap >= 0 ? '#1b4332' : '#087e8b'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', fontSize: '11px', color: 'var(--text-subtle)', marginTop: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: 12, height: 12, backgroundColor: '#1b4332', borderRadius: 2 }} />
          <span>Increases Predicted Demand (Positive Contribution)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: 12, height: 12, backgroundColor: '#087e8b', borderRadius: 2 }} />
          <span>Decreases Predicted Demand (Negative Contribution)</span>
        </div>
      </div>
    </div>
  );
};
