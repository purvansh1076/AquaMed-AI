/**
 * AquaMedi AI — Crop Health & Moisture Stress Diagnostics
 * ========================================================
 * Formal government diagnostic dashboard for assessing crop water stress,
 * root-zone moisture deficits, and agronomic risk indicators.
 */

import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, AlertOctagon } from 'lucide-react';
import { MetricCard } from '../components/common/MetricCard';

interface CropHealthRecord {
  plot_id: string;
  farmer_name: string;
  crop: string;
  stage: string;
  soil_type: string;
  stress_index: number; // 0.0 to 1.0
  moisture_pct: number;
  status: 'Optimal' | 'Moderate Stress' | 'Critical Stress';
  recommended_action: string;
}

const SAMPLE_HEALTH_RECORDS: CropHealthRecord[] = [
  { plot_id: 'PLOT-01', farmer_name: 'Ramesh Patil', crop: 'Sugarcane', stage: 'Grand Growth', soil_type: 'Black Vertisol', stress_index: 0.18, moisture_pct: 68, status: 'Optimal', recommended_action: 'Maintain standard 10-day furrow irrigation cycle.' },
  { plot_id: 'PLOT-02', farmer_name: 'Suresh Deshmukh', crop: 'Cotton', stage: 'Boll Development', soil_type: 'Medium Black', stress_index: 0.42, moisture_pct: 46, status: 'Moderate Stress', recommended_action: 'Schedule 35 mm irrigation within next 48 hours.' },
  { plot_id: 'PLOT-03', farmer_name: 'Anand Shinde', crop: 'Soybean', stage: 'Pod Initiation', soil_type: 'Clay Loam', stress_index: 0.76, moisture_pct: 28, status: 'Critical Stress', recommended_action: 'Immediate priority water release needed to prevent pod drop.' },
  { plot_id: 'PLOT-04', farmer_name: 'Kishor Kale', crop: 'Wheat', stage: 'Crown Root', soil_type: 'Sandy Loam', stress_index: 0.35, moisture_pct: 52, status: 'Moderate Stress', recommended_action: 'Light irrigation recommended within 3 days.' },
  { plot_id: 'PLOT-05', farmer_name: 'Sunil Jadhav', crop: 'Maize', stage: 'Tasseling', soil_type: 'Clay Loam', stress_index: 0.82, moisture_pct: 22, status: 'Critical Stress', recommended_action: 'Water stress during pollination will reduce yield severely; urgent supply.' },
  { plot_id: 'PLOT-06', farmer_name: 'Vikas More', crop: 'Groundnut', stage: 'Pegging', soil_type: 'Sandy Loam', stress_index: 0.25, moisture_pct: 62, status: 'Optimal', recommended_action: 'Soil moisture adequate for peg penetration.' },
];

export const CropHealthPage: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const filtered = SAMPLE_HEALTH_RECORDS.filter((r) => {
    if (filterStatus === 'all') return true;
    return r.status === filterStatus;
  });

  const optimalCount = SAMPLE_HEALTH_RECORDS.filter((r) => r.status === 'Optimal').length;
  const moderateCount = SAMPLE_HEALTH_RECORDS.filter((r) => r.status === 'Moderate Stress').length;
  const criticalCount = SAMPLE_HEALTH_RECORDS.filter((r) => r.status === 'Critical Stress').length;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', paddingBottom: '32px' }}>
      {/* ── Title Banner ── */}
      <div
        style={{
          background: '#ffffff',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid #176B45',
          padding: '16px 20px',
          marginBottom: '20px',
        }}
      >
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#12315B', margin: 0 }}>
          Crop Health &amp; Moisture Stress Diagnostics
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0 0' }}>
          Diagnostic assessment of field crop moisture stress derived from FAO-56 evapotranspiration demand and soil water holding capacity.
        </p>
      </div>

      {/* ── KPI Cards ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <MetricCard
          label="Optimal Moisture Plots"
          value={optimalCount}
          unit="plots"
          footnote="Moisture > 60% of field capacity"
          icon={<CheckCircle2 size={18} style={{ color: '#176B45' }} />}
        />
        <MetricCard
          label="Moderate Stress Plots"
          value={moderateCount}
          unit="plots"
          footnote="Irrigation due within 48-72 hours"
          icon={<AlertTriangle size={18} style={{ color: '#C58B20' }} />}
        />
        <MetricCard
          label="Critical Stress Plots"
          value={criticalCount}
          unit="plots"
          footnote="Yield loss risk; high priority release"
          icon={<AlertOctagon size={18} style={{ color: '#B42318' }} />}
        />
      </div>

      {/* ── Table ── */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          border: '1px solid var(--border-default)',
          marginBottom: '20px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '12px 18px',
            backgroundColor: '#F5F7F9',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#12315B' }}>
            Plot-Wise Moisture &amp; Crop Stress Registry
          </div>

          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                border: '1px solid var(--border-default)',
                borderRadius: '3px',
                backgroundColor: '#FFFFFF',
              }}
            >
              <option value="all">All Diagnostic Statuses</option>
              <option value="Optimal">Optimal</option>
              <option value="Moderate Stress">Moderate Stress</option>
              <option value="Critical Stress">Critical Stress</option>
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table className="gov-data-table" aria-label="Crop Health Diagnostics Table">
            <thead>
              <tr>
                <th>Plot ID</th>
                <th>Farmer Name</th>
                <th>Crop</th>
                <th>Growth Stage</th>
                <th>Soil Type</th>
                <th style={{ textAlign: 'right' }}>Soil Moisture</th>
                <th style={{ textAlign: 'right' }}>Stress Index</th>
                <th>Diagnostic Status</th>
                <th>Agronomic Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.plot_id}>
                  <td style={{ fontWeight: 600, color: '#12315B' }}>{r.plot_id}</td>
                  <td style={{ fontWeight: 600 }}>{r.farmer_name}</td>
                  <td>{r.crop}</td>
                  <td>{r.stage}</td>
                  <td>{r.soil_type}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{r.moisture_pct}%</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {r.stress_index.toFixed(2)}
                  </td>
                  <td>
                    {r.status === 'Optimal' && (
                      <span className="status-badge-adequate">
                        <CheckCircle2 size={11} />
                        Optimal
                      </span>
                    )}
                    {r.status === 'Moderate Stress' && (
                      <span className="status-badge-partial">
                        <AlertTriangle size={11} />
                        Moderate Stress
                      </span>
                    )}
                    {r.status === 'Critical Stress' && (
                      <span className="status-badge-shortage">
                        <AlertOctagon size={11} />
                        Critical Stress
                      </span>
                    )}
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-main)' }}>{r.recommended_action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Scientific Transparency Notice ── */}
      <div
        style={{
          background: '#FFFFFF',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid #12315B',
          padding: '12px 16px',
          fontSize: '12px',
          color: 'var(--text-muted)',
        }}
      >
        <strong>Agronomic Methodology:</strong> Crop stress indices are computed from standard FAO-56
        water depletion calculations (Dr &gt; RAW) where RAW is readily available water based on root depth
        and depletion fraction p. Diagnostic advice supports canal rotation priority setting.
      </div>
    </div>
  );
};
