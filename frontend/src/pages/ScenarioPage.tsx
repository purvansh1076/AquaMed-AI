import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  Sparkles,
  AlertCircle,
  Check,
  Minus,
  Plus,
  ArrowRight,
  HelpCircle,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import {
  type ScenarioRunRequest,
  type ScenarioType,
  SCENARIO_TYPE_LABELS,
} from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const ScenarioPage: React.FC = () => {
  const { viewMode } = useViewMode();

  return viewMode === 'farmer' ? <FarmerScenarioConfig /> : <ExpertScenarioConfig />;
};

/* ==========================================================================
   1. 👨‍🌾 FARMER VIEW — Simplified Agronomic Scenario Configuration
   ========================================================================== */

const FarmerScenarioConfig: React.FC = () => {
  const { runScenario, isLoading, error } = useScenario();
  const { t, setViewMode } = useViewMode();
  const navigate = useNavigate();

  // Question 1: Water situation (mapped to real backend ScenarioType)
  const [selectedSituation, setSelectedSituation] = useState<ScenarioType>('moderate_shortage');

  // Question 2: Number of farmers (2 to 20, default 4)
  const [nFarmers, setNFarmers] = useState<number>(4);

  // Question 5: Available water override (optional)
  const [waterAvailable, setWaterAvailable] = useState<string>('');
  const [unknownWater, setUnknownWater] = useState<boolean>(false);

  const [validationError, setValidationError] = useState<string | null>(null);

  const handleDecrementFarmers = () => {
    if (nFarmers > 2) {
      setNFarmers(nFarmers - 1);
    }
  };

  const handleIncrementFarmers = () => {
    if (nFarmers < 20) {
      setNFarmers(nFarmers + 1);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    let parsedWater: number | null = null;
    if (!unknownWater && waterAvailable.trim() !== '') {
      const val = parseFloat(waterAvailable);
      if (isNaN(val) || val < 0) {
        setValidationError('Please enter a valid positive water amount or select "I don\'t know".');
        return;
      }
      parsedWater = val;
    }

    // Backend payload: automatic seed (42) and default model ('XGBoost')
    const payload: ScenarioRunRequest = {
      scenario_type: selectedSituation,
      n_farmers: nFarmers,
      seed: 42,
      model_name: 'XGBoost',
      available_water_override_m3: parsedWater,
    };

    const success = await runScenario(payload);
    if (success) {
      // Direct the farmer to the simple Farmer View result
      setViewMode('farmer');
      navigate('/farmer');
    }
  };

  // Farmer Loading Screen: 5 visual stages of the actual backend pipeline
  if (isLoading) {
    return (
      <div className="farmer-finding-container">
        <div className="farmer-finding-card">
          <div className="farmer-finding-header">
            <div className="farmer-finding-icon">💧</div>
            <h2 className="farmer-finding-title">{t('findingWaterPlanTitle')}</h2>
            <p className="farmer-finding-sub">
              {t('findWaterPlanBtnHelper')}
            </p>
          </div>

          <div className="farmer-stages-timeline">
            <div className="farmer-stage-row active">
              <span className="farmer-stage-dot" />
              <span className="farmer-stage-text">{t('findingStage1')}</span>
            </div>
            <div className="farmer-stage-row active">
              <span className="farmer-stage-dot" />
              <span className="farmer-stage-text">{t('findingStage2')}</span>
            </div>
            <div className="farmer-stage-row active">
              <span className="farmer-stage-dot" />
              <span className="farmer-stage-text">{t('findingStage3')}</span>
            </div>
            <div className="farmer-stage-row active">
              <span className="farmer-stage-dot" />
              <span className="farmer-stage-text">{t('findingStage4')}</span>
            </div>
            <div className="farmer-stage-row active">
              <span className="farmer-stage-dot" />
              <span className="farmer-stage-text">{t('findingStage5')}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="farmer-scenario-wrapper">
      {/* Page Title & Subtitle */}
      <div className="farmer-scenario-heading">
        <h1 className="farmer-scenario-title">{t('startWaterSharingTitle')}</h1>
        <p className="farmer-scenario-subtitle">{t('startWaterSharingSubtitle')}</p>
      </div>

      <form onSubmit={handleSubmit} className="farmer-scenario-form">
        {(validationError || error) && (
          <div className="alert alert-error" style={{ marginBottom: '16px' }}>
            <AlertCircle size={18} />
            <span>{validationError || error}</span>
          </div>
        )}

        {/* QUESTION 1: How is the water situation today? (4 Large Cards) */}
        <section className="farmer-form-section">
          <h2 className="farmer-question-title">{t('q1SituationTitle')}</h2>

          <div className="farmer-situation-grid">
            {/* OPTION 1: Enough Water -> normal_water */}
            <div
              className={`farmer-situation-card ${selectedSituation === 'normal_water' ? 'selected' : ''}`}
              onClick={() => setSelectedSituation('normal_water')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedSituation('normal_water')}
            >
              <div className="farmer-situation-top">
                <span className="farmer-situation-emoji">💧</span>
                {selectedSituation === 'normal_water' && <span className="farmer-selected-check"><Check size={16} /></span>}
              </div>
              <h3 className="farmer-situation-name">{t('q1OptEnoughTitle')}</h3>
              <p className="farmer-situation-desc">{t('q1OptEnoughDesc')}</p>
            </div>

            {/* OPTION 2: Some Shortage -> moderate_shortage */}
            <div
              className={`farmer-situation-card ${selectedSituation === 'moderate_shortage' ? 'selected' : ''}`}
              onClick={() => setSelectedSituation('moderate_shortage')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedSituation('moderate_shortage')}
            >
              <div className="farmer-situation-top">
                <span className="farmer-situation-emoji">💧</span>
                {selectedSituation === 'moderate_shortage' && <span className="farmer-selected-check"><Check size={16} /></span>}
              </div>
              <h3 className="farmer-situation-name">{t('q1OptSomeShortageTitle')}</h3>
              <p className="farmer-situation-desc">{t('q1OptSomeShortageDesc')}</p>
            </div>

            {/* OPTION 3: Serious Shortage -> severe_shortage */}
            <div
              className={`farmer-situation-card ${selectedSituation === 'severe_shortage' ? 'selected' : ''}`}
              onClick={() => setSelectedSituation('severe_shortage')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedSituation('severe_shortage')}
            >
              <div className="farmer-situation-top">
                <span className="farmer-situation-emoji">🚨</span>
                {selectedSituation === 'severe_shortage' && <span className="farmer-selected-check"><Check size={16} /></span>}
              </div>
              <h3 className="farmer-situation-name">{t('q1OptSeriousShortageTitle')}</h3>
              <p className="farmer-situation-desc">{t('q1OptSeriousShortageDesc')}</p>
            </div>

            {/* OPTION 4: Crops Need Water Urgently -> high_urgency_farmer */}
            <div
              className={`farmer-situation-card ${selectedSituation === 'high_urgency_farmer' ? 'selected' : ''}`}
              onClick={() => setSelectedSituation('high_urgency_farmer')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedSituation('high_urgency_farmer')}
            >
              <div className="farmer-situation-top">
                <span className="farmer-situation-emoji">🌱</span>
                {selectedSituation === 'high_urgency_farmer' && <span className="farmer-selected-check"><Check size={16} /></span>}
              </div>
              <h3 className="farmer-situation-name">{t('q1OptCropsUrgentTitle')}</h3>
              <p className="farmer-situation-desc">{t('q1OptCropsUrgentDesc')}</p>
            </div>
          </div>
        </section>

        {/* QUESTION 2: How many farmers are sharing the water? (Stepper [-] 4 [+]) */}
        <section className="farmer-form-section">
          <h2 className="farmer-question-title">{t('q2FarmersTitle')}</h2>
          <p className="farmer-question-helper">{t('q2FarmersHelper')}</p>

          <div className="farmer-stepper-box">
            <span className="farmer-stepper-label">{t('q2FarmersLabel')}:</span>
            <div className="farmer-stepper-controls">
              <button
                type="button"
                className="farmer-stepper-btn"
                onClick={handleDecrementFarmers}
                disabled={nFarmers <= 2}
                aria-label="Decrease farmers count"
              >
                <Minus size={20} />
              </button>
              <span className="farmer-stepper-value" data-testid="farmer-count-val">
                {nFarmers}
              </span>
              <button
                type="button"
                className="farmer-stepper-btn"
                onClick={handleIncrementFarmers}
                disabled={nFarmers >= 20}
                aria-label="Increase farmers count"
              >
                <Plus size={20} />
              </button>
            </div>
          </div>
        </section>

        {/* QUESTION 5: How much water is available? (Optional canal amount) */}
        <section className="farmer-form-section">
          <h2 className="farmer-question-title">{t('q5WaterAvailableTitle')}</h2>
          <p className="farmer-question-helper">{t('q5WaterAvailableHelper')}</p>

          <div className="farmer-water-input-row">
            <div className="farmer-input-wrapper">
              <input
                id="farmer-water-input"
                type="number"
                min={0}
                step="10"
                placeholder="e.g. 3500"
                className="farmer-text-input"
                value={unknownWater ? '' : waterAvailable}
                onChange={(e) => {
                  setWaterAvailable(e.target.value);
                  if (unknownWater) setUnknownWater(false);
                }}
                disabled={unknownWater}
              />
              <span className="farmer-input-unit">m³</span>
            </div>

            <label className="farmer-checkbox-label">
              <input
                type="checkbox"
                checked={unknownWater}
                onChange={(e) => {
                  setUnknownWater(e.target.checked);
                  if (e.target.checked) setWaterAvailable('');
                }}
                className="farmer-checkbox"
              />
              <span>{t('q5UnknownCheckbox')}</span>
            </label>
          </div>
        </section>

        {/* Usage reassurance note */}
        <div className="farmer-usage-note">
          <HelpCircle size={18} style={{ color: 'var(--color-primary)' }} />
          <span>{t('farmerConfigUsageNote')}</span>
        </div>

        {/* Main CTA button */}
        <div className="farmer-submit-bar">
          <button
            type="submit"
            className="farmer-btn-large-primary"
            id="farmer-submit-plan-btn"
          >
            <span>{t('findWaterPlanBtn')}</span>
            <ArrowRight size={22} />
          </button>
          <span className="farmer-submit-helper">{t('findWaterPlanBtnHelper')}</span>
        </div>
      </form>
    </div>
  );
};

/* ==========================================================================
   2. 🔬 EXPERT VIEW — Comprehensive Technical Research Configuration
   ========================================================================== */

const ExpertScenarioConfig: React.FC = () => {
  const { runScenario, isLoading, error } = useScenario();
  const navigate = useNavigate();

  const [scenarioType, setScenarioType] = useState<ScenarioType>('moderate_shortage');
  const [nFarmers, setNFarmers] = useState<number>(4);
  const [seed, setSeed] = useState<number>(42);
  const [modelName, setModelName] = useState<'XGBoost' | 'RandomForest'>('XGBoost');
  const [waterOverride, setWaterOverride] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (nFarmers < 2 || nFarmers > 20) {
      setValidationError('Farmer count must be between 2 and 20.');
      return;
    }

    if (seed < 0 || !Number.isInteger(seed)) {
      setValidationError('Seed must be a non-negative integer.');
      return;
    }

    let parsedOverride: number | null = null;
    if (waterOverride.trim() !== '') {
      const val = parseFloat(waterOverride);
      if (isNaN(val) || val < 0) {
        setValidationError('Available water override must be a non-negative number.');
        return;
      }
      parsedOverride = val;
    }

    const payload: ScenarioRunRequest = {
      scenario_type: scenarioType,
      n_farmers: nFarmers,
      seed: seed,
      model_name: modelName,
      available_water_override_m3: parsedOverride,
    };

    const success = await runScenario(payload);
    if (success) {
      navigate('/overview');
    }
  };

  const setPreset = (type: ScenarioType, farmers: number, sd: number, override?: string) => {
    setScenarioType(type);
    setNFarmers(farmers);
    setSeed(sd);
    setWaterOverride(override || '');
    setValidationError(null);
  };

  if (isLoading) {
    return (
      <div className="card" style={{ maxWidth: '640px', margin: '40px auto', textAlign: 'center' }}>
        <LoadingSpinner
          message="Running AquaMediAI Mediation Pipeline"
          subMessage="Predicting demand with XGBoost → Detecting conflicts → Solving OR-Tools GLOP LP → Running Nash bargaining negotiation → Computing explanations..."
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      <div className="page-heading">
        <h1 className="page-title">Configure & Run Mediation Scenario</h1>
        <p className="page-description">
          Set up synthetic agrarian conditions, choose farmer population size, and initiate the end-to-end multi-agent resolution pipeline.
        </p>
      </div>

      {/* Preset Scenario Cards */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: '12px' }}>
          <Sparkles size={16} style={{ color: 'var(--color-primary)' }} />
          Quick Academic Demo Presets
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPreset('moderate_shortage', 4, 42)}
            style={{ textAlign: 'left', justifyContent: 'flex-start', padding: '10px' }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>Moderate Drought</div>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>4 Farmers, 75% supply</div>
            </div>
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPreset('severe_shortage', 5, 101)}
            style={{ textAlign: 'left', justifyContent: 'flex-start', padding: '10px' }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>Severe Scarcity</div>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>5 Farmers, Concessions</div>
            </div>
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPreset('normal_water', 8, 42)}
            style={{ textAlign: 'left', justifyContent: 'flex-start', padding: '10px' }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>8-Farm Demo</div>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>8 Farmers, Seed 42</div>
            </div>
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPreset('normal_water', 3, 42)}
            style={{ textAlign: 'left', justifyContent: 'flex-start', padding: '10px' }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>Normal Supply</div>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>3 Farmers, Ample water</div>
            </div>
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPreset('high_urgency_farmer', 4, 7)}
            style={{ textAlign: 'left', justifyContent: 'flex-start', padding: '10px' }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>Crop Stress Urgency</div>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>4 Farmers, Critical need</div>
            </div>
          </button>
        </div>
      </div>

      {/* Main Configuration Form */}
      <form onSubmit={handleSubmit} className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Scenario Parameters (POST /api/v1/scenarios/run)</div>
            <div className="card-subtitle">Values validated directly against FastAPI Pydantic schema</div>
          </div>
        </div>

        {(validationError || error) && (
          <div className="alert alert-error" style={{ marginBottom: '16px' }}>
            <AlertCircle size={16} />
            <span>{validationError || error}</span>
          </div>
        )}

        {/* 1. Scenario Type */}
        <div className="form-group">
          <label className="form-label" htmlFor="scenario-type">
            Scenario Type *
          </label>
          <select
            id="scenario-type"
            className="form-control"
            value={scenarioType}
            onChange={(e) => setScenarioType(e.target.value as ScenarioType)}
            style={{ fontWeight: 500 }}
          >
            {(Object.keys(SCENARIO_TYPE_LABELS) as ScenarioType[]).map((key) => (
              <option key={key} value={key}>
                {SCENARIO_TYPE_LABELS[key].label} ({key})
              </option>
            ))}
          </select>
          <div className="form-hint">
            {SCENARIO_TYPE_LABELS[scenarioType]?.description}
          </div>
        </div>

        {/* 2. Number of Farmers & Seed */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="n-farmers">
              Number of Farmers (2 – 20) *
            </label>
            <input
              id="n-farmers"
              type="number"
              min={2}
              max={20}
              className="form-control"
              value={nFarmers}
              onChange={(e) => setNFarmers(parseInt(e.target.value, 10) || 2)}
              required
            />
            <div className="form-hint">Autonomous digital twin agents instantiated in simulation.</div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="seed">
              Random Seed (Deterministic) *
            </label>
            <input
              id="seed"
              type="number"
              min={0}
              className="form-control"
              value={seed}
              onChange={(e) => setSeed(parseInt(e.target.value, 10) || 0)}
              required
            />
            <div className="form-hint">Ensures reproducible results for research verification.</div>
          </div>
        </div>

        {/* 3. ML Model & Water Override */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="model-name">
              ML Demand Prediction Model *
            </label>
            <select
              id="model-name"
              className="form-control"
              value={modelName}
              onChange={(e) => setModelName(e.target.value as 'XGBoost' | 'RandomForest')}
            >
              <option value="XGBoost">XGBoost (Primary — R² = 0.9736)</option>
              <option value="RandomForest">Random Forest (Baseline — R² = 0.9737)</option>
            </select>
            <div className="form-hint">Trained model artifact loaded from backend/data/models/.</div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="water-override">
              Canal Water Supply Override (m³) <span style={{ color: 'var(--text-subtle)' }}>(Optional)</span>
            </label>
            <input
              id="water-override"
              type="number"
              step="0.1"
              min={0}
              placeholder="Leave blank to use scenario supply"
              className="form-control"
              value={waterOverride}
              onChange={(e) => setWaterOverride(e.target.value)}
            />
            <div className="form-hint">Overrides default supply to simulate custom scarcity.</div>
          </div>
        </div>

        {/* Submit CTA */}
        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ padding: '10px 24px', fontSize: '14px' }}
            disabled={isLoading}
          >
            <Play size={16} />
            <span>Run AI Mediation</span>
          </button>
        </div>
      </form>
    </div>
  );
};
