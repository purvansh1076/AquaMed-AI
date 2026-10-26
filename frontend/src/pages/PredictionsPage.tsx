import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Cpu, Info, Users, Sparkles, ArrowRight } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { ShapFeatureChart } from '../components/charts/ShapFeatureChart';
import { formatWater, capitalize } from '../utils/formatters';
import { Badge } from '../components/common/Badge';
import { AgronomicComparisonCard } from '../components/pipeline/AgronomicComparisonCard';
import { CustomFarmPredictor } from '../components/pipeline/CustomFarmPredictor';

export const PredictionsPage: React.FC = () => {
  const { scenarioResult } = useScenario();
  const [selectedFarmerId, setSelectedFarmerId] = useState<string | null>(null);

  const predictions = scenarioResult?.predictions || [];
  const explanations = scenarioResult?.explanations;
  const farmers = scenarioResult?.farmers;

  const activeFarmerId = selectedFarmerId || predictions[0]?.farmer_id || '';
  const activePrediction = predictions.find((p) => p.farmer_id === activeFarmerId) || predictions[0];
  const activeExplanation = explanations?.prediction_explanations?.find(
    (pe) => pe.farmer_id === activeFarmerId
  );
  const activeFarmerAgent = farmers?.find((f) => (f as { farmer_id: string }).farmer_id === activeFarmerId) as
    | Record<string, unknown>
    | undefined;

  return (
    <div>
      {/* Page Heading */}
      <div className="page-heading">
        <h1 className="page-title">ML Water Demand Predictions</h1>
        <p className="page-description">
          Phase 2 Machine Learning pipeline: Supervised crop evapotranspiration and water demand estimation.
          Calculate individual farm predictions using live model inference, or inspect generated multi-agent scenario demand traces.
        </p>
      </div>

      {/* Model Benchmark Overview (Disclosed as Offline Static Reference) */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          background: '#f8fafc',
          borderLeft: '4px solid var(--color-primary)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} style={{ color: 'var(--color-primary)' }} />
            <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-primary-dark)' }}>
              Supervised ML Model Architecture & Offline Training Reference
            </span>
          </div>
          <Badge variant="neutral">STATIC REFERENCE VALUES</Badge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '10px' }}>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600 }}>PRIMARY MODEL</div>
            <div style={{ fontSize: '14px', fontWeight: 600 }}>{activePrediction?.model_name || 'XGBoost'}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>v{activePrediction?.model_version || '1.0.0'} (Joblib serialized)</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600 }}>HELD-OUT TEST R² (OFFLINE)</div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-primary)' }}>0.9736</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Surrogate fit to synthetic FAO-56 targets</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600 }}>TEST MAE (m³/day)</div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-primary)' }}>17.83 m³</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Theoretical balance reference error</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600 }}>ENGINEERED FEATURES</div>
            <div style={{ fontSize: '14px', fontWeight: 600 }}>22 Features</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>13 agronomic + 4 encoded + 5 interactions</div>
          </div>
        </div>

        <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Info size={13} />
          <span>
            <strong>Academic Transparency Notice:</strong> Metrics above are static reference values from model training evaluated against formula-generated FAO-56 targets. They represent mathematical surrogate fidelity, not physical farm-gate water meter telemetry.
          </span>
        </div>
      </div>

      {/* PHASE 14: Interactive Custom Farm Predictor Section */}
      <CustomFarmPredictor />

      {/* Synthetic Scenario Demonstration Data Section */}
      <div style={{ marginTop: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
          <div>
            <h2
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--color-primary-dark)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Users size={20} style={{ color: 'var(--color-teal)' }} />
              <span>Synthetic Scenario Demonstration Data</span>
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Multi-agent dispute mediation demonstration records (e.g. FARM_0001, FARM_0002) generated algorithmically for pipeline verification.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Badge variant="neutral">SIMULATED DEMO RECORDS</Badge>
            <Link to="/scenario" className="btn btn-outline btn-sm">
              <span>Configure Scenario</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>

        {scenarioResult && predictions.length > 0 ? (
          <>
            {/* Scenario Predictions Table */}
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Scenario Demonstration Farmers (n = {predictions.length})</div>
                  <div className="card-subtitle">
                    Algorithmically generated farm profiles using seed={scenarioResult.scenario_id.slice(-4)}. Click a row to inspect feature contributions.
                  </div>
                </div>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Farmer ID</th>
                      <th>Predicted Demand</th>
                      <th>Model</th>
                      <th>Crop Type</th>
                      <th>Growth Stage</th>
                      <th>Farm Area</th>
                      <th>Reference ETo</th>
                      <th>Kc Value</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((p) => {
                      const agent = farmers?.find((f) => (f as { farmer_id: string }).farmer_id === p.farmer_id) as
                        | Record<string, unknown>
                        | undefined;
                      const isSelected = p.farmer_id === activeFarmerId;

                      return (
                        <tr
                          key={p.farmer_id || 'unknown'}
                          onClick={() => setSelectedFarmerId(p.farmer_id)}
                          style={{
                            cursor: 'pointer',
                            backgroundColor: isSelected ? '#f0fdf4' : 'inherit',
                            fontWeight: isSelected ? 600 : 'normal',
                          }}
                        >
                          <td style={{ fontFamily: 'monospace' }}>{p.farmer_id}</td>
                          <td style={{ color: 'var(--color-primary-dark)', fontWeight: 700 }}>
                            {formatWater(p.predicted_water_demand_m3)}
                          </td>
                          <td>
                            <Badge variant="neutral">{p.model_name}</Badge>
                          </td>
                          <td>{capitalize(String(agent?.crop || agent?.crop_type || '—'))}</td>
                          <td>{capitalize(String(agent?.growth_stage || '—'))}</td>
                          <td>{agent?.farm_area_hectares ? `${agent.farm_area_hectares} ha` : '—'}</td>
                          <td>{agent?.et0_mm_per_day ? `${agent.et0_mm_per_day} mm/d` : '—'}</td>
                          <td>{agent?.kc_value ? `${agent.kc_value}` : '—'}</td>
                          <td>
                            <button
                              type="button"
                              className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedFarmerId(p.farmer_id);
                              }}
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Selected Scenario Farmer Feature Breakdown */}
            {activePrediction && (
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">
                      <TrendingUp size={16} />
                      Feature Contributions for Scenario Farmer: {activeFarmerId}
                    </div>
                    <div className="card-subtitle">
                      Total Predicted Water Demand: <strong>{formatWater(activePrediction.predicted_water_demand_m3)}</strong>
                    </div>
                  </div>
                  {activeExplanation?.shap_available && (
                    <Badge variant="success">SHAP TreeExplainer Active</Badge>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
                  {/* Feature Contributions Chart */}
                  <div>
                    {activeExplanation && (
                      <ShapFeatureChart
                        contributors={activeExplanation.top_contributors || activeExplanation.all_features || []}
                        title="Dominant Agronomic Feature Contributions"
                      />
                    )}
                  </div>

                  {/* Agronomic Context and Input Summary */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontWeight: 600, color: 'var(--color-primary-dark)', fontSize: '13px', marginBottom: '6px' }}>
                        Model Prediction Explanation Summary
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                        {activeExplanation?.summary ||
                          `Water demand for ${activeFarmerId} calculated using ${activePrediction.model_name} from FAO-56 Penman-Monteith crop evapotranspiration coefficients and soil water holding properties.`}
                      </p>
                    </div>

                    {activeFarmerAgent && (
                      <div style={{ padding: '14px', background: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontWeight: 600, color: 'var(--color-primary-dark)', fontSize: '13px', marginBottom: '8px' }}>
                          Agent Parameters (Digital Twin)
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                          <div>Crop Urgency: <strong>{Number(activeFarmerAgent.urgency ?? 0.5).toFixed(2)}</strong></div>
                          <div>Flexibility: <strong>{Number(activeFarmerAgent.flexibility ?? 0.5).toFixed(2)}</strong></div>
                          <div>Crop Sensitivity (Ky): <strong>{Number(activeFarmerAgent.crop_sensitivity ?? 1.0).toFixed(2)}</strong></div>
                          <div>Irrigation Window: <strong>{String(activeFarmerAgent.preferred_start_hour ?? 6)}:00 + {String(activeFarmerAgent.irrigation_window_hours ?? 4)}h</strong></div>
                        </div>
                      </div>
                    )}

                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Info size={14} />
                      <span>Contributions explain feature importance for this prediction; they do not imply independent causality.</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Secondary Agronomic Baseline Comparison Card */}
            {activePrediction && (
              <AgronomicComparisonCard
                prediction={activePrediction}
                farmerId={activeFarmerId}
              />
            )}
          </>
        ) : (
          <div
            className="card"
            style={{
              padding: '24px',
              textAlign: 'center',
              background: '#f8fafc',
              border: '1px dashed var(--border-default)',
            }}
          >
            <Sparkles size={28} style={{ color: 'var(--color-teal)', margin: '0 auto 10px auto' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>
              No Multi-Agent Scenario Currently Loaded
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', maxWidth: '520px', margin: '6px auto 16px auto' }}>
              You can run real custom farm predictions above at any time. If you wish to simulate multi-farmer water dispute mediation, LP optimization, and concessions, launch an academic scenario.
            </p>
            <Link to="/scenario" className="btn btn-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span>Launch Scenario Simulation</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
