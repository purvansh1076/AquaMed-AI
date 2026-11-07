/**
 * AquaMedi AI — Agricultural Irrigation Advisory
 * ===============================================
 * Formal advisory service computing reference evapotranspiration (ET0),
 * crop-specific water requirements (ETc), and optimal irrigation scheduling.
 */

import React, { useState } from 'react';
import { CloudSun, Droplets, Thermometer, Wind, CheckCircle2 } from 'lucide-react';
import { MetricCard } from '../components/common/MetricCard';

interface CropAdvisory {
  crop: string;
  kc_current: number;
  etc_mm_day: number;
  recommended_interval_days: number;
  water_depth_mm: number;
  volume_per_ha_m3: number;
  next_irrigation: string;
}

const CROP_ADVISORIES: CropAdvisory[] = [
  { crop: 'Sugarcane', kc_current: 1.25, etc_mm_day: 6.8, recommended_interval_days: 9, water_depth_mm: 61, volume_per_ha_m3: 610, next_irrigation: 'Within 2 days' },
  { crop: 'Cotton', kc_current: 1.15, etc_mm_day: 6.2, recommended_interval_days: 12, water_depth_mm: 74, volume_per_ha_m3: 740, next_irrigation: 'Within 4 days' },
  { crop: 'Soybean', kc_current: 1.05, etc_mm_day: 5.7, recommended_interval_days: 8, water_depth_mm: 45, volume_per_ha_m3: 450, next_irrigation: 'Tomorrow' },
  { crop: 'Wheat', kc_current: 1.15, etc_mm_day: 5.4, recommended_interval_days: 14, water_depth_mm: 75, volume_per_ha_m3: 750, next_irrigation: 'Within 5 days' },
  { crop: 'Maize', kc_current: 1.10, etc_mm_day: 5.9, recommended_interval_days: 10, water_depth_mm: 59, volume_per_ha_m3: 590, next_irrigation: 'Within 3 days' },
  { crop: 'Groundnut', kc_current: 1.05, etc_mm_day: 5.6, recommended_interval_days: 9, water_depth_mm: 50, volume_per_ha_m3: 500, next_irrigation: 'Within 2 days' },
];

export const IrrigationAdvisoryPage: React.FC = () => {
  const [selectedCrop, setSelectedCrop] = useState<string>('Sugarcane');

  const activeAdvisory = CROP_ADVISORIES.find((c) => c.crop === selectedCrop) || CROP_ADVISORIES[0];

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', paddingBottom: '32px' }}>
      {/* ── Banner ── */}
      <div
        style={{
          background: '#FFFFFF',
          border: '1px solid var(--border-default)',
          borderLeft: '4px solid #12315B',
          padding: '16px 20px',
          marginBottom: '20px',
        }}
      >
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#12315B', margin: 0 }}>
          Agricultural Irrigation Advisory Service
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0 0' }}>
          Meteorological reference evapotranspiration (\(ET_0\)) and scientific irrigation scheduling for canal command farmers.
        </p>
      </div>

      {/* ── Meteorological Conditions ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <MetricCard
          label="Reference ET0"
          value="5.4 mm/day"
          footnote="Penman-Monteith equation"
          icon={<CloudSun size={18} style={{ color: '#12315B' }} />}
        />
        <MetricCard
          label="Mean Temperature"
          value="29.4 °C"
          footnote="Daily max: 34.2 °C | min: 21.6 °C"
          icon={<Thermometer size={18} style={{ color: '#176B45' }} />}
        />
        <MetricCard
          label="Relative Humidity"
          value="48%"
          footnote="Semi-arid command area"
          icon={<Droplets size={18} style={{ color: '#12315B' }} />}
        />
        <MetricCard
          label="Wind Velocity"
          value="2.2 m/s"
          footnote="2-meter standard anemometer"
          icon={<Wind size={18} style={{ color: '#176B45' }} />}
        />
      </div>

      {/* ── Crop-Specific Advisory Schedule ── */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          border: '1px solid var(--border-default)',
          marginBottom: '24px',
        }}
      >
        <div
          style={{
            padding: '14px 18px',
            backgroundColor: '#F5F7F9',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div>
            <h2 style={{ fontSize: '14px', fontWeight: 700, color: '#12315B', margin: 0 }}>
              Crop Water Demand &amp; Irrigation Schedule
            </h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Select a crop to inspect current crop coefficient (\(K_c\)) and recommended water dosage
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Select Crop:</span>
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              style={{
                padding: '4px 10px',
                fontSize: '12px',
                border: '1px solid var(--border-default)',
                borderRadius: '3px',
                backgroundColor: '#FFFFFF',
                fontWeight: 600,
                color: '#12315B',
              }}
            >
              {CROP_ADVISORIES.map((c) => (
                <option key={c.crop} value={c.crop}>
                  {c.crop}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Selected Crop Detail Card */}
        <div style={{ padding: '20px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              backgroundColor: '#fafbfc',
              padding: '16px',
              border: '1px solid var(--border-subtle)',
              marginBottom: '20px',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>CROP COEFFICIENT (\(K_c\))</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#12315B', marginTop: '2px' }}>
                {activeAdvisory.kc_current.toFixed(2)}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Mid-season peak coefficient</div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>CROP TRANSPIRATION (\(ET_c\))</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#176B45', marginTop: '2px' }}>
                {activeAdvisory.etc_mm_day} mm/day
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>\(ET_c = ET_0 \times K_c\)</div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>RECOMMENDED INTERVAL</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#12315B', marginTop: '2px' }}>
                {activeAdvisory.recommended_interval_days} Days
              </div>
              <div style={{ fontSize: '11px', color: '#176B45', fontWeight: 600 }}>
                Next due: {activeAdvisory.next_irrigation}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>APPLICATION VOLUME</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#12315B', marginTop: '2px' }}>
                {activeAdvisory.volume_per_ha_m3} m³/ha
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Equivalent to {activeAdvisory.water_depth_mm} mm depth</div>
            </div>
          </div>

          {/* Full Crop Advisory Comparison Table */}
          <div className="table-responsive">
            <table className="gov-data-table" aria-label="Crop Advisory Schedule">
              <thead>
                <tr>
                  <th>Crop</th>
                  <th style={{ textAlign: 'right' }}>Current \(K_c\)</th>
                  <th style={{ textAlign: 'right' }}>Water Use (\(ET_c\))</th>
                  <th style={{ textAlign: 'right' }}>Interval (Days)</th>
                  <th style={{ textAlign: 'right' }}>Recommended Volume</th>
                  <th>Irrigation Status</th>
                </tr>
              </thead>
              <tbody>
                {CROP_ADVISORIES.map((c) => (
                  <tr
                    key={c.crop}
                    style={{
                      backgroundColor: c.crop === selectedCrop ? '#f0f5fb' : undefined,
                    }}
                  >
                    <td style={{ fontWeight: 600, color: '#12315B' }}>{c.crop}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {c.kc_current.toFixed(2)}
                    </td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {c.etc_mm_day} mm/day
                    </td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {c.recommended_interval_days} days
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: '#176B45' }}>
                      {c.volume_per_ha_m3} m³/ha
                    </td>
                    <td>
                      <span className="status-badge-adequate">
                        <CheckCircle2 size={11} />
                        {c.next_irrigation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
