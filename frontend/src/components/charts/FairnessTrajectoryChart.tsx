import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface FairnessTrajectoryChartProps {
  fairnessHistory: number[];
  nashHistory?: number[];
}

export const FairnessTrajectoryChart: React.FC<FairnessTrajectoryChartProps> = ({
  fairnessHistory,
  nashHistory = [],
}) => {
  if (!fairnessHistory || fairnessHistory.length === 0) {
    return <div style={{ color: 'var(--text-subtle)', fontStyle: 'italic', padding: '16px' }}>No round history data available.</div>;
  }

  const data = fairnessHistory.map((fairness, index) => {
    const roundNum = index + 1;
    const nash = nashHistory[index] !== undefined ? Number(nashHistory[index].toFixed(4)) : null;
    return {
      round: `Round ${roundNum}`,
      fairness: Number(fairness.toFixed(4)),
      nash,
    };
  });

  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 15, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="round" tick={{ fill: '#475569', fontSize: 12 }} tickLine={{ stroke: '#cbd5e1' }} />
          <YAxis
            yAxisId="left"
            domain={[0, 1]}
            tick={{ fill: '#475569', fontSize: 12 }}
            tickLine={{ stroke: '#cbd5e1' }}
            label={{ value: "Jain's Fairness Index", angle: -90, position: 'insideLeft', fill: '#475569', fontSize: 11 }}
          />
          {nashHistory.length > 0 && (
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: '#087e8b', fontSize: 12 }}
              tickLine={{ stroke: '#cbd5e1' }}
              label={{ value: 'Log-Nash Objective', angle: 90, position: 'insideRight', fill: '#087e8b', fontSize: 11 }}
            />
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '12px',
            }}
          />
          <Legend wrapperStyle={{ paddingTop: 10, fontSize: 12 }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="fairness"
            name="Fairness Index"
            stroke="#1b4332"
            strokeWidth={2}
            activeDot={{ r: 6 }}
            dot={{ r: 4 }}
          />
          {nashHistory.length > 0 && (
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="nash"
              name="Log-Nash Objective"
              stroke="#087e8b"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={{ r: 4 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
