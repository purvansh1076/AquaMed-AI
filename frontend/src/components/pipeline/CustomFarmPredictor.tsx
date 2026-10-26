import React, { useState } from 'react';
import {
  Cpu,
  Sparkles,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Info,
} from 'lucide-react';
import { api } from '../../services/api';
import type {
  FarmerInputData,
  PredictionRequest,
  PredictionResponse,
  ShadowComparisonDetails,
} from '../../types/api';
import { formatWater } from '../../utils/formatters';
import { Badge } from '../common/Badge';

// Valid enum values strictly aligned with backend fitted encoders and schemas
export const SUPPORTED_CROPS = [
  { value: 'cotton', label: 'Cotton' },
  { value: 'groundnut', label: 'Groundnut' },
  { value: 'maize', label: 'Maize' },
  { value: 'rice', label: 'Rice / Paddy' },
  { value: 'soybean', label: 'Soybean' },
  { value: 'sugarcane', label: 'Sugarcane' },
  { value: 'sunflower', label: 'Sunflower' },
  { value: 'wheat', label: 'Wheat' },
] as const;

export const SUPPORTED_SOIL_TYPES = [
  { value: 'clay', label: 'Clay' },
  { value: 'clay_loam', label: 'Clay Loam' },
  { value: 'loam', label: 'Loam' },
  { value: 'sandy', label: 'Sandy' },
  { value: 'silt', label: 'Silt' },
] as const;

export const SUPPORTED_GROWTH_STAGES = [
  { value: 'germination', label: 'Germination / Initial' },
  { value: 'vegetative', label: 'Vegetative' },
  { value: 'flowering', label: 'Flowering / Mid-Season' },
  { value: 'maturity', label: 'Maturity / Late' },
  { value: 'harvest', label: 'Harvest' },
] as const;

export const SUPPORTED_SEASONS = [
  { value: 'kharif', label: 'Kharif (Monsoon)' },
  { value: 'rabi', label: 'Rabi (Winter)' },
  { value: 'zaid', label: 'Zaid (Summer)' },
] as const;

// Default initial state for form inputs
const DEFAULT_FORM_VALUES: FarmerInputData = {
  farmer_id: 'CUSTOM_FARM_01',
  crop_type: 'wheat',
  soil_type: 'loam',
  growth_stage: 'vegetative',
  season: 'rabi',
  farm_area_hectares: 2.5,
  et0_mm_per_day: 4.5,
  kc_value: 0.85,
  etc_mm_per_day: 3.83, // 4.5 * 0.85 = 3.825 rounded
  soil_whc_mm_per_m: 125.0,
  temperature_celsius: 26.0,
  humidity_percent: 55.0,
  rainfall_mm: 0.0,
  preferred_start_hour: 6,
  irrigation_window_hours: 4,
  flexibility_score: 0.5,
  urgency_score: 0.5,
  crop_stress_index: 0.4,
};

export interface CustomFarmPredictorProps {
  onPredictionSuccess?: (prediction: PredictionResponse) => void;
}

export const CustomFarmPredictor: React.FC<CustomFarmPredictorProps> = ({
  onPredictionSuccess,
}) => {
  const [formData, setFormData] = useState<FarmerInputData>(DEFAULT_FORM_VALUES);
  const [modelName, setModelName] = useState<'XGBoost' | 'RandomForest'>('XGBoost');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [autoEtc, setAutoEtc] = useState<boolean>(true);

  // States for API lifecycle
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  // Update field handler with auto ETc calculation
  const handleNumericChange = (field: keyof FarmerInputData, rawValue: string) => {
    const val = parseFloat(rawValue);
    const updated = {
      ...formData,
      [field]: isNaN(val) ? 0 : val,
    };

    // Automatically synchronize ETc = ETo * Kc if autoEtc is enabled
    if (autoEtc && (field === 'et0_mm_per_day' || field === 'kc_value')) {
      const et0 = field === 'et0_mm_per_day' ? (isNaN(val) ? 0 : val) : (formData.et0_mm_per_day || 0);
      const kc = field === 'kc_value' ? (isNaN(val) ? 0 : val) : (formData.kc_value || 0);
      updated.etc_mm_per_day = Math.round(et0 * kc * 100) / 100;
    }

    setFormData(updated);
    setValidationError(null);
  };

  const handleStringChange = (field: keyof FarmerInputData, val: string) => {
    setFormData({
      ...formData,
      [field]: val,
    });
    setValidationError(null);
  };

  const handleReset = () => {
    setFormData(DEFAULT_FORM_VALUES);
    setModelName('XGBoost');
    setAutoEtc(true);
    setValidationError(null);
    setApiError(null);
    setResult(null);
  };

  const validateForm = (): boolean => {
    if (!formData.farmer_id || formData.farmer_id.trim() === '') {
      setValidationError('Farmer ID / Plot Identifier is required.');
      return false;
    }
    if (!formData.crop_type) {
      setValidationError('Please select a valid crop type.');
      return false;
    }
    if (formData.farm_area_hectares <= 0) {
      setValidationError('Farm area must be greater than 0 hectares.');
      return false;
    }
    if (formData.et0_mm_per_day <= 0) {
      setValidationError('Reference evapotranspiration (ETo) must be greater than 0 mm/day.');
      return false;
    }
    if (formData.kc_value <= 0) {
      setValidationError('Crop coefficient (Kc) must be greater than 0.');
      return false;
    }
    if (formData.etc_mm_per_day <= 0) {
      setValidationError('Crop evapotranspiration (ETc) must be greater than 0 mm/day.');
      return false;
    }
    if (
      formData.humidity_percent !== undefined &&
      (formData.humidity_percent < 0 || formData.humidity_percent > 100)
    ) {
      setValidationError('Relative humidity must be between 0% and 100%.');
      return false;
    }
    if (formData.rainfall_mm !== undefined && formData.rainfall_mm < 0) {
      setValidationError('Rainfall cannot be negative.');
      return false;
    }
    if (formData.soil_whc_mm_per_m !== undefined && formData.soil_whc_mm_per_m < 0) {
      setValidationError('Soil water holding capacity cannot be negative.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setApiError(null);

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const payload: PredictionRequest = {
        farmer_data: {
          ...formData,
          farmer_id: formData.farmer_id.trim(),
        },
        model_name: modelName,
      };

      const response = await api.predictSingle(payload);
      setResult(response);
      if (onPredictionSuccess) {
        onPredictionSuccess(response);
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to obtain prediction from FastAPI backend.';
      setApiError(message);
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="card"
      id="custom-farm-predictor"
      style={{
        border: '1px solid var(--border-default)',
        background: '#ffffff',
        marginBottom: '24px',
      }}
    >
      {/* Header */}
      <div className="card-header" style={{ alignItems: 'flex-start' }}>
        <div>
          <div
            className="card-title"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Cpu size={18} style={{ color: 'var(--color-primary)' }} />
            <span>Custom Farm Water Demand Predictor</span>
            <Badge variant="info">Live API Inference</Badge>
          </div>
          <div className="card-subtitle">
            Enter real plot parameters and environmental inputs to obtain predictions directly from the trained ML model, independent of scenario simulations.
          </div>
        </div>

        <button
          type="button"
          onClick={handleReset}
          className="btn btn-outline btn-sm"
          title="Reset to default agronomic test values"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={13} />
          <span>Reset Defaults</span>
        </button>
      </div>

      {/* Validation Error Alert */}
      {validationError && (
        <div
          className="alert alert-error"
          role="alert"
          style={{ marginBottom: '16px' }}
        >
          <AlertCircle size={16} />
          <span>{validationError}</span>
        </div>
      )}

      {/* API Error Alert */}
      {apiError && (
        <div
          className="alert alert-error"
          role="alert"
          style={{ marginBottom: '16px' }}
        >
          <AlertCircle size={16} />
          <span>
            <strong>Prediction Failed:</strong> {apiError}
          </span>
        </div>
      )}

      {/* Prediction Form */}
      <form onSubmit={handleSubmit} noValidate>
        {/* Section 1: Plot Identity & Crop Specification */}
        <div style={{ marginBottom: '18px' }}>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: 'var(--color-primary)',
              letterSpacing: '0.5px',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>1. Plot Identity & Crop Specification</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '14px',
            }}
          >
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-farmer-id">
                Farmer / Plot Identifier *
              </label>
              <input
                id="custom-farmer-id"
                type="text"
                className="form-control"
                value={formData.farmer_id}
                onChange={(e) => handleStringChange('farmer_id', e.target.value)}
                placeholder="e.g. FARM_MY_FIELD"
                required
              />
              <div className="form-hint">Unique identifier for this prediction query.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-crop-type">
                Crop Type *
              </label>
              <select
                id="custom-crop-type"
                className="form-control"
                value={formData.crop_type}
                onChange={(e) => handleStringChange('crop_type', e.target.value)}
                required
              >
                {SUPPORTED_CROPS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
              <div className="form-hint">Supported crops in the fitted encoder.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-farm-area">
                Farm Area (hectares) *
              </label>
              <input
                id="custom-farm-area"
                type="number"
                step="0.1"
                min="0.01"
                className="form-control"
                value={formData.farm_area_hectares}
                onChange={(e) => handleNumericChange('farm_area_hectares', e.target.value)}
                required
              />
              <div className="form-hint">Total cultivated surface area (1 ha = 10,000 m²).</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-soil-type">
                Soil Texture *
              </label>
              <select
                id="custom-soil-type"
                className="form-control"
                value={formData.soil_type || 'loam'}
                onChange={(e) => handleStringChange('soil_type', e.target.value)}
                required
              >
                {SUPPORTED_SOIL_TYPES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <div className="form-hint">Governs infiltration and water holding capacity.</div>
            </div>
          </div>
        </div>

        {/* Section 2: Agronomic Phenology & Evapotranspiration */}
        <div style={{ marginBottom: '18px' }}>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: 'var(--color-primary)',
              letterSpacing: '0.5px',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>2. Agronomic Phenology & Evapotranspiration</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '14px',
            }}
          >
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-growth-stage">
                Growth Stage *
              </label>
              <select
                id="custom-growth-stage"
                className="form-control"
                value={formData.growth_stage || 'vegetative'}
                onChange={(e) => handleStringChange('growth_stage', e.target.value)}
                required
              >
                {SUPPORTED_GROWTH_STAGES.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
              <div className="form-hint">Crop vegetative cycle determines water sensitivity.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-season">
                Cropping Season *
              </label>
              <select
                id="custom-season"
                className="form-control"
                value={formData.season || 'kharif'}
                onChange={(e) => handleStringChange('season', e.target.value)}
                required
              >
                {SUPPORTED_SEASONS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <div className="form-hint">Agricultural season calendar in India.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-et0">
                Reference Evapotranspiration ETo (mm/day) *
              </label>
              <input
                id="custom-et0"
                type="number"
                step="0.1"
                min="0.1"
                className="form-control"
                value={formData.et0_mm_per_day}
                onChange={(e) => handleNumericChange('et0_mm_per_day', e.target.value)}
                required
              />
              <div className="form-hint">FAO-56 Penman-Monteith atmospheric reference.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-kc">
                Crop Coefficient Kc *
              </label>
              <input
                id="custom-kc"
                type="number"
                step="0.05"
                min="0.05"
                max="2.0"
                className="form-control"
                value={formData.kc_value}
                onChange={(e) => handleNumericChange('kc_value', e.target.value)}
                required
              />
              <div className="form-hint">FAO-56 single crop multiplier.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label" htmlFor="custom-etc" style={{ marginBottom: 0 }}>
                  Crop ETc (mm/day) *
                </label>
                <label style={{ fontSize: '11px', color: 'var(--text-subtle)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={autoEtc}
                    onChange={(e) => setAutoEtc(e.target.checked)}
                    style={{ marginRight: '4px' }}
                  />
                  Auto-sync (ETo × Kc)
                </label>
              </div>
              <input
                id="custom-etc"
                type="number"
                step="0.05"
                min="0.05"
                className="form-control"
                style={{ marginTop: '4px' }}
                value={formData.etc_mm_per_day}
                onChange={(e) => {
                  if (autoEtc) setAutoEtc(false);
                  handleNumericChange('etc_mm_per_day', e.target.value);
                }}
                required
              />
              <div className="form-hint">Crop evapotranspiration under standard conditions.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-model-choice">
                Model Architecture *
              </label>
              <select
                id="custom-model-choice"
                className="form-control"
                value={modelName}
                onChange={(e) => setModelName(e.target.value as 'XGBoost' | 'RandomForest')}
              >
                <option value="XGBoost">XGBoost (Production Primary)</option>
                <option value="RandomForest">Random Forest (Baseline)</option>
              </select>
              <div className="form-hint">Model selected for inference on the backend.</div>
            </div>
          </div>
        </div>

        {/* Section 3: Meteorological & Soil Hydrology */}
        <div style={{ marginBottom: '18px' }}>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: 'var(--color-primary)',
              letterSpacing: '0.5px',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>3. Meteorological & Soil Hydrology</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '14px',
            }}
          >
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-temp">
                Daily Mean Temperature (°C)
              </label>
              <input
                id="custom-temp"
                type="number"
                step="0.5"
                className="form-control"
                value={formData.temperature_celsius ?? 28.0}
                onChange={(e) => handleNumericChange('temperature_celsius', e.target.value)}
              />
              <div className="form-hint">Ambient temperature of the pilot region.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-humidity">
                Relative Humidity (%)
              </label>
              <input
                id="custom-humidity"
                type="number"
                min="0"
                max="100"
                step="1"
                className="form-control"
                value={formData.humidity_percent ?? 60.0}
                onChange={(e) => handleNumericChange('humidity_percent', e.target.value)}
              />
              <div className="form-hint">Affects atmospheric vapor pressure deficit.</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-rainfall">
                Rainfall (mm)
              </label>
              <input
                id="custom-rainfall"
                type="number"
                min="0"
                step="0.5"
                className="form-control"
                value={formData.rainfall_mm ?? 0.0}
                onChange={(e) => handleNumericChange('rainfall_mm', e.target.value)}
              />
              <div className="form-hint">Direct precipitation on plot (USDA-SCS effective rain).</div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="custom-whc">
                Soil Water Holding Capacity (mm/m)
              </label>
              <input
                id="custom-whc"
                type="number"
                min="0"
                step="5"
                className="form-control"
                value={formData.soil_whc_mm_per_m ?? 125.0}
                onChange={(e) => handleNumericChange('soil_whc_mm_per_m', e.target.value)}
              />
              <div className="form-hint">Available water capacity of the root zone.</div>
            </div>
          </div>
        </div>

        {/* Collapsible Section 4: Operational Timing & Behavioral Scores */}
        <div style={{ marginBottom: '20px' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              color: 'var(--text-muted)',
            }}
          >
            {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            <span>
              {showAdvanced ? 'Hide' : 'Show'} Advanced Operational & Urgency Parameters
            </span>
          </button>

          {showAdvanced && (
            <div
              style={{
                marginTop: '12px',
                padding: '14px 16px',
                background: '#f8fafc',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '12px',
              }}
            >
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="custom-start-hour">
                  Preferred Start Hour (0–23)
                </label>
                <input
                  id="custom-start-hour"
                  type="number"
                  min="0"
                  max="23"
                  className="form-control"
                  value={formData.preferred_start_hour ?? 6}
                  onChange={(e) => handleNumericChange('preferred_start_hour', e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="custom-window-hours">
                  Window Duration (hours)
                </label>
                <input
                  id="custom-window-hours"
                  type="number"
                  min="1"
                  max="18"
                  className="form-control"
                  value={formData.irrigation_window_hours ?? 4}
                  onChange={(e) => handleNumericChange('irrigation_window_hours', e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="custom-flexibility">
                  Flexibility Score (0.0–1.0)
                </label>
                <input
                  id="custom-flexibility"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  className="form-control"
                  value={formData.flexibility_score ?? 0.5}
                  onChange={(e) => handleNumericChange('flexibility_score', e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="custom-urgency">
                  Crop Urgency Score (0.0–1.0)
                </label>
                <input
                  id="custom-urgency"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  className="form-control"
                  value={formData.urgency_score ?? 0.5}
                  onChange={(e) => handleNumericChange('urgency_score', e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="custom-stress">
                  Crop Stress Index (0.0–1.0)
                </label>
                <input
                  id="custom-stress"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  className="form-control"
                  value={formData.crop_stress_index ?? 0.4}
                  onChange={(e) => handleNumericChange('crop_stress_index', e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        {/* Submit Bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-subtle)',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div
            style={{
              fontSize: '12px',
              color: 'var(--text-subtle)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Info size={14} />
            <span>Sends direct payload to POST /api/v1/predictions on the backend.</span>
          </div>

          <button
            type="submit"
            id="submit-custom-prediction-btn"
            className="btn btn-primary"
            style={{ padding: '10px 22px', fontSize: '14px', fontWeight: 600 }}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <RefreshCw size={15} className="spinner" style={{ animation: 'spin 1s linear infinite' }} />
                <span>Predicting Demand...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Calculate Water Demand</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Prediction Output Section */}
      {result && (
        <div
          id="custom-prediction-result"
          style={{
            marginTop: '24px',
            padding: '20px',
            borderRadius: '8px',
            background: 'var(--bg-subtle)',
            border: '2px solid var(--color-mint)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              flexWrap: 'wrap',
              gap: '10px',
              marginBottom: '16px',
              paddingBottom: '12px',
              borderBottom: '1px solid var(--border-subtle)',
            }}
          >
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontWeight: 700,
                  fontSize: '16px',
                  color: 'var(--color-primary-dark)',
                }}
              >
                <CheckCircle2 size={20} style={{ color: 'var(--status-success)' }} />
                <span>Predicted Water Demand for {result.farmer_id || 'Custom Plot'}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                Computed by model <strong>{result.model_name}</strong> (v{result.model_version})
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <Badge variant="success">INFERENCE SUCCESS</Badge>
              <Badge variant="neutral">{result.model_name}</Badge>
            </div>
          </div>

          {/* Warnings callout */}
          {result.warning && (
            <div
              className="alert alert-warning"
              style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <AlertTriangle size={16} style={{ flexShrink: 0 }} />
              <span style={{ fontSize: '13px' }}>{result.warning}</span>
            </div>
          )}

          {/* Primary Result KPI Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '16px',
            }}
          >
            <div
              style={{
                padding: '16px',
                background: '#ffffff',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>
                PREDICTED WATER DEMAND
              </div>
              <div
                id="custom-predicted-demand-val"
                style={{
                  fontSize: '24px',
                  fontWeight: 800,
                  color: 'var(--color-primary-dark)',
                  margin: '4px 0',
                }}
              >
                {formatWater(result.predicted_water_demand_m3)}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Machine learning surrogate prediction ({result.model_name})
              </div>
            </div>

            {result.shadow_agronomic_estimate_m3 !== undefined &&
              result.shadow_agronomic_estimate_m3 !== null && (
                <div
                  style={{
                    padding: '16px',
                    background: '#ffffff',
                    borderRadius: '6px',
                    border: '1px solid var(--border-subtle)',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>
                    FAO-56 AGRONOMIC PHYSICAL REFERENCE
                  </div>
                  <div
                    style={{
                      fontSize: '24px',
                      fontWeight: 800,
                      color: 'var(--color-teal)',
                      margin: '4px 0',
                    }}
                  >
                    {formatWater(result.shadow_agronomic_estimate_m3)}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Deterministic (ETc × area ÷ 0.70 efficiency)
                  </div>
                </div>
              )}

            {result.shadow_comparison &&
              typeof result.shadow_comparison === 'object' &&
              'difference_m3' in result.shadow_comparison && (
                <div
                  style={{
                    padding: '16px',
                    background: '#ffffff',
                    borderRadius: '6px',
                    border: '1px solid var(--border-subtle)',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-subtle)' }}>
                    MODEL DISCREPANCY FROM FAO-56
                  </div>
                  <div
                    style={{
                      fontSize: '24px',
                      fontWeight: 800,
                      color:
                        Number((result.shadow_comparison as ShadowComparisonDetails).difference_m3 || 0) < 0
                          ? 'var(--status-warning)'
                          : 'var(--color-primary)',
                      margin: '4px 0',
                    }}
                  >
                    {Number(
                      (result.shadow_comparison as ShadowComparisonDetails).difference_m3 || 0
                    ) > 0
                      ? '+'
                      : ''}
                    {Number(
                      (result.shadow_comparison as ShadowComparisonDetails).difference_m3 || 0
                    ).toFixed(2)}{' '}
                    m³
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Difference: {(result.shadow_comparison as ShadowComparisonDetails).difference_percent}%
                  </div>
                </div>
              )}
          </div>

          {/* Agronomic Comparison Notes */}
          {result.shadow_comparison &&
            typeof result.shadow_comparison === 'object' &&
            'provenance_note' in result.shadow_comparison && (
              <div
                style={{
                  padding: '12px 14px',
                  background: '#f1f5f9',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: 'var(--text-muted)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: '16px',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: '4px' }}>
                  Agronomic Ground-Truth Notice
                </div>
                <div>{(result.shadow_comparison as ShadowComparisonDetails).provenance_note}</div>
                <div style={{ marginTop: '4px', fontStyle: 'italic', fontSize: '11px' }}>
                  {(result.shadow_comparison as ShadowComparisonDetails).disclaimer}
                </div>
              </div>
            )}

          {/* Input Summary Echo */}
          {result.input_summary && Object.keys(result.input_summary).length > 0 && (
            <div>
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-subtle)',
                  marginBottom: '6px',
                }}
              >
                Echoed Feature Inputs Received by Model
              </div>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                  fontSize: '11px',
                }}
              >
                {Object.entries(result.input_summary).map(([k, v]) => (
                  <span
                    key={k}
                    style={{
                      background: '#ffffff',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <strong>{k}:</strong> {String(v)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
