import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  footnote?: string;
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  footnote,
  icon,
}) => {
  return (
    <div className="metric-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="metric-label">{label}</span>
        {icon && <span style={{ color: 'var(--color-primary-light)' }}>{icon}</span>}
      </div>
      <div className="metric-value-wrap">
        <span className="metric-value">{value}</span>
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {footnote && <span className="metric-footnote">{footnote}</span>}
    </div>
  );
};
