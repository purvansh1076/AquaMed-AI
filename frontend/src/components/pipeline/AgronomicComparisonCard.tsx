import {
  Scale,
  CheckCircle2,
  AlertTriangle,
  Info,
  Layers,
} from 'lucide-react';
import type { PredictionResponse, ShadowComparisonDetails } from '../../types/api';
import { Badge } from '../common/Badge';

export interface AgronomicComparisonCardProps {
  prediction: PredictionResponse;
  farmerId?: string;
}

export const AgronomicComparisonCard: React.FC<AgronomicComparisonCardProps> = ({
  prediction,
  farmerId,
}) => {
  const comparison = prediction.shadow_comparison as ShadowComparisonDetails | undefined;
  const agronomicEstimate = prediction.shadow_agronomic_estimate_m3;
  const legacyPrediction = prediction.predicted_water_demand_m3;

  const isAvailable =
    comparison?.status === 'available' &&
    agronomicEstimate !== null &&
    agronomicEstimate !== undefined;

  const isUnavailable =
    comparison?.status === 'unavailable' ||
    (!comparison && (agronomicEstimate === null || agronomicEstimate === undefined));

  const inputValidation = comparison?.input_validation;
  const isValidInputs = inputValidation ? inputValidation.is_valid : isAvailable;
  const inputErrors = inputValidation?.errors || [];

  const diffM3 =
    comparison?.difference_m3 !== undefined && comparison?.difference_m3 !== null
      ? comparison.difference_m3
      : isAvailable
        ? Number((legacyPrediction - (agronomicEstimate ?? 0)).toFixed(2))
        : null;

  const diffPercent = comparison?.difference_percent;
  const isBaselineZero = isAvailable && agronomicEstimate === 0;

  return (
    <section
      className="card"
      style={{
        marginTop: '20px',
        borderLeft: '4px solid var(--color-teal)',
        background: '#ffffff',
      }}
      aria-label="Agronomic Baseline Comparison"
    >
      {/* Header */}
      <div className="card-header" style={{ marginBottom: '14px', paddingBottom: '10px' }}>
        <div>
          <div
            className="card-title"
            style={{
              color: 'var(--color-primary-dark)',
              fontSize: '15px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Scale size={18} style={{ color: 'var(--color-teal)' }} />
            <span>Theoretical Agronomic Baseline (FAO-56) & Shadow Comparison</span>
          </div>
          <div className="card-subtitle" style={{ fontSize: '12px', color: 'var(--text-subtle)' }}>
            Research benchmark for Farmer {farmerId || prediction.farmer_id || 'Selected'}: Comparing legacy ML prediction against deterministic FAO-56 crop water requirement.
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isAvailable ? (
            <Badge variant="info" icon={<Layers size={13} style={{ marginRight: '4px' }} />}>
              FAO-56 Shadow Active
            </Badge>
          ) : (
            <Badge variant="warning" icon={<AlertTriangle size={13} style={{ marginRight: '4px' }} />}>
              Baseline Unavailable
            </Badge>
          )}
        </div>
      </div>

      {/* Primary Comparison KPI Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '14px',
          marginBottom: '16px',
        }}
      >
        {/* Metric 1: Legacy ML Prediction */}
        <div
          style={{
            padding: '14px',
            background: '#f8fafc',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-subtle)',
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>Legacy ML Prediction</span>
            <Badge variant="neutral" className="text-xs">Synthetic Model</Badge>
          </div>
          <div style={{ margin: '8px 0 4px 0', display: 'flex', alignItems: 'baseline', gap: '4px' }}>
            <span
              style={{
                fontSize: '22px',
                fontWeight: 700,
                color: 'var(--color-primary-dark)',
                fontFamily: 'monospace',
              }}
              data-testid="legacy-prediction-val"
            >
              {legacyPrediction.toFixed(2)}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>m³/day</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Trained on synthetic academic data ({prediction.model_name || 'XGBoost'} v{prediction.model_version || '1.0.0'})
          </div>
        </div>

        {/* Metric 2: Theoretical Agronomic Baseline */}
        <div
          style={{
            padding: '14px',
            background: '#f8fafc',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-subtle)',
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>Agronomic Baseline</span>
            <Badge variant="info" className="text-xs">FAO-56 Standard</Badge>
          </div>
          <div style={{ margin: '8px 0 4px 0', display: 'flex', alignItems: 'baseline', gap: '4px' }}>
            {isAvailable ? (
              <>
                <span
                  style={{
                    fontSize: '22px',
                    fontWeight: 700,
                    color: 'var(--color-teal)',
                    fontFamily: 'monospace',
                  }}
                  data-testid="agronomic-baseline-val"
                >
                  {(agronomicEstimate ?? 0).toFixed(2)}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>m³/day</span>
              </>
            ) : (
              <span
                style={{
                  fontSize: '18px',
                  fontWeight: 600,
                  color: 'var(--status-warning)',
                }}
                data-testid="agronomic-baseline-unavailable"
              >
                Unavailable
              </span>
            )}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Calculated irrigation requirement (not measured delivery)
          </div>
        </div>

        {/* Metric 3: Comparative Difference (Variance) */}
        <div
          style={{
            padding: '14px',
            background: '#f8fafc',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-subtle)',
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
            }}
          >
            Agronomic Variance (Δ)
          </div>
          <div style={{ margin: '8px 0 4px 0', display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            {isAvailable && diffM3 !== null ? (
              <>
                <span
                  style={{
                    fontSize: '22px',
                    fontWeight: 700,
                    color: 'var(--text-main)',
                    fontFamily: 'monospace',
                  }}
                  data-testid="difference-m3-val"
                >
                  {diffM3 > 0 ? `+${diffM3.toFixed(2)}` : diffM3.toFixed(2)}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>m³/day</span>
              </>
            ) : (
              <span style={{ fontSize: '18px', color: 'var(--text-subtle)', fontWeight: 600 }}>—</span>
            )}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-subtle)', lineHeight: '1.4' }}>
            {isBaselineZero ? (
              <span data-testid="zero-baseline-subtext" style={{ color: 'var(--color-teal)' }}>
                Baseline is 0.00 m³/day (percentage undefined)
              </span>
            ) : diffPercent !== null && diffPercent !== undefined ? (
              <span data-testid="difference-percent-val">
                {diffPercent > 0 ? `+${diffPercent.toFixed(1)}%` : `${diffPercent.toFixed(1)}%`} variance
              </span>
            ) : (
              <span>Not calculable</span>
            )}
          </div>
        </div>

        {/* Metric 4: Input Validation Status */}
        <div
          style={{
            padding: '14px',
            background: '#f8fafc',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-subtle)',
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
            }}
          >
            Input Validation Status
          </div>
          <div style={{ margin: '8px 0 6px 0' }}>
            {isValidInputs ? (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--status-success)',
                  fontWeight: 600,
                  fontSize: '14px',
                }}
                data-testid="input-valid-badge"
              >
                <CheckCircle2 size={16} /> Physical Inputs Verified
              </span>
            ) : (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--status-warning)',
                  fontWeight: 600,
                  fontSize: '14px',
                }}
                data-testid="input-invalid-badge"
              >
                <AlertTriangle size={16} /> Inputs Missing / Invalid
              </span>
            )}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            {isValidInputs
              ? 'Area > 0, ET₀ ≥ 0, Kc > 0, Rainfall verified'
              : `${inputErrors.length} validation rule(s) unfulfilled`}
          </div>
        </div>
      </div>

      {/* Unavailable State Callout (when agronomic baseline cannot be verified) */}
      {isUnavailable && (
        <div
          style={{
            padding: '12px 16px',
            background: '#fffbeb',
            border: '1px solid #fef3c7',
            borderRadius: 'var(--radius-md)',
            marginBottom: '14px',
            fontSize: '12px',
          }}
          data-testid="unavailable-state-callout"
        >
          <div
            style={{
              fontWeight: 600,
              color: '#92400e',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginBottom: '4px',
            }}
          >
            <AlertTriangle size={15} />
            <span>Agronomic Baseline Unavailable for this Farm Record</span>
          </div>
          <p style={{ color: '#78350f', margin: '0 0 6px 0', lineHeight: '1.4' }}>
            Required physical inputs could not be confirmed. Under scientific non-fabrication protocols, synthetic or assumed weather and crop parameters are never substituted for missing data.
          </p>
          {inputErrors.length > 0 && (
            <ul style={{ margin: '0', paddingLeft: '20px', color: '#92400e' }}>
              {inputErrors.map((err, idx) => (
                <li key={idx} style={{ marginTop: '2px' }}>
                  {err}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Physical Variables & Assumptions Breakdown */}
      <div
        style={{
          padding: '12px 14px',
          background: '#f1f5f9',
          borderRadius: 'var(--radius-md)',
          marginBottom: '14px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '10px',
          fontSize: '12px',
        }}
      >
        <div>
          <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '11px' }}>Farm Area</span>
          <strong>{prediction.input_summary?.farm_area_hectares != null ? String(prediction.input_summary.farm_area_hectares) : '—'} ha</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '11px' }}>Reference ET₀</span>
          <strong>{prediction.input_summary?.et0_mm_per_day != null ? String(prediction.input_summary.et0_mm_per_day) : '—'} mm/day</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '11px' }}>Crop Coeff (Kc)</span>
          <strong>{prediction.input_summary?.kc_value != null ? String(prediction.input_summary.kc_value) : '—'}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '11px' }}>Gross Rainfall</span>
          <strong>{prediction.input_summary?.rainfall_mm != null ? String(prediction.input_summary.rainfall_mm) : '—'} mm</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '11px' }}>Application Eff (Ea)</span>
          <strong>
            {comparison?.application_efficiency
              ? `${(Number(comparison.application_efficiency) * 100).toFixed(0)}% (surface)`
              : '70% (surface)'}
          </strong>
        </div>
      </div>

      {/* Scientific Data Provenance & Methodology Disclaimers */}
      <div
        style={{
          padding: '12px 14px',
          background: '#f8fafc',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          lineHeight: '1.5',
        }}
      >
        <div
          style={{
            fontWeight: 600,
            color: 'var(--color-primary-dark)',
            marginBottom: '4px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
          }}
        >
          <Info size={14} style={{ color: 'var(--color-teal)' }} />
          <span>Research Methodology & Scientific Data Provenance</span>
        </div>
        <ul style={{ margin: '0', paddingLeft: '18px' }}>
          <li>
            <strong>Synthetic Model Provenance:</strong> The legacy ML model ({prediction.model_name || 'XGBoost'}) was trained on synthetic academic demonstration data. It has not been calibrated against real-world measured on-farm water deliveries.
          </li>
          <li>
            <strong>Deterministic Agronomic Formulation:</strong> The FAO-56 baseline deterministically computes crop evapotranspiration (ETc = ET₀ × Kc) and USDA-SCS effective precipitation. It represents calculated irrigation requirement, not measured delivery.
          </li>
          <li>
            <strong>Non-Empirical Difference Disclaimer:</strong> Differences between legacy ML and the baseline are comparative benchmark metrics. They do <em>not</em> constitute empirical model error, model accuracy, or proven real-world improvement.
          </li>
        </ul>
      </div>
    </section>
  );
};
