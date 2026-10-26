/**
 * AquaMediAI — Farmer Portal Page (Phase 14)
 *
 * A simple, mobile-friendly entry point for individual farmers.
 * Farmers enter basic farm details and receive a plain-language
 * water-demand estimate directly from the live ML model.
 *
 * Design Principles:
 * - Zero technical jargon (no "ETo", "Kc", "ETc", "SHAP" etc.)
 * - Guided inputs with sensible defaults and helpful hints
 * - Clear result display in m³/day
 * - Link to multi-farmer scenario for water-sharing simulation
 * - Localized (en/hi/gu)
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sprout,
  Thermometer,
  Droplets,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Info,
  CloudRain,
  Leaf,
} from 'lucide-react';
import { api } from '../services/api';
import { useViewMode } from '../context/ViewModeContext';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

// ─── Crop options with farmer-friendly labels ─────────────────────────────────

const CROPS = [
  { value: 'wheat', label: 'Wheat (Gehu)', icon: '🌾', kc: 0.85, season: 'rabi' },
  { value: 'rice', label: 'Rice / Paddy (Dhan)', icon: '🌾', kc: 1.15, season: 'kharif' },
  { value: 'cotton', label: 'Cotton (Kapas)', icon: '🪴', kc: 0.85, season: 'kharif' },
  { value: 'sugarcane', label: 'Sugarcane (Ganna)', icon: '🎋', kc: 1.25, season: 'kharif' },
  { value: 'maize', label: 'Maize (Makka)', icon: '🌽', kc: 0.85, season: 'kharif' },
  { value: 'soybean', label: 'Soybean (Soya)', icon: '🫘', kc: 0.85, season: 'kharif' },
  { value: 'groundnut', label: 'Groundnut (Moongfali)', icon: '🥜', kc: 0.80, season: 'kharif' },
  { value: 'sunflower', label: 'Sunflower (Surajmukhi)', icon: '🌻', kc: 0.85, season: 'rabi' },
] as const;

const GROWTH_STAGES = [
  { value: 'germination', label: 'Sowing / Germination (Early)', kc_mult: 0.7 },
  { value: 'vegetative', label: 'Growing Stage (Vegetative)', kc_mult: 1.0 },
  { value: 'flowering', label: 'Flowering / Fruit Setting', kc_mult: 1.15 },
  { value: 'maturity', label: 'Grain Filling / Maturity', kc_mult: 0.9 },
  { value: 'harvest', label: 'Near Harvest', kc_mult: 0.65 },
] as const;

const SOIL_TYPES = [
  { value: 'clay', label: 'Heavy Clay / Black Soil', whc: 175 },
  { value: 'clay_loam', label: 'Clay-Loam (Medium Heavy)', whc: 150 },
  { value: 'loam', label: 'Loam (Medium Soil)', whc: 125 },
  { value: 'silt', label: 'Silt / River Alluvial', whc: 135 },
  { value: 'sandy', label: 'Sandy / Light Soil', whc: 75 },
] as const;

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface FarmerForm {
  crop_type: string;
  growth_stage: string;
  soil_type: string;
  farm_area_hectares: number;
  temperature_celsius: number;
  humidity_percent: number;
  rainfall_mm: number;
}

interface PredictionDisplay {
  demand_m3: number;
  model_name: string;
  warning: string | null;
  shadow_estimate_m3: number | null;
}

// ─── Helper: derive agronomic values from farmer inputs ───────────────────────

function deriveAgronomicInputs(form: FarmerForm) {
  const crop = CROPS.find((c) => c.value === form.crop_type) ?? CROPS[0];
  const stage = GROWTH_STAGES.find((s) => s.value === form.growth_stage) ?? GROWTH_STAGES[1];
  const soil = SOIL_TYPES.find((s) => s.value === form.soil_type) ?? SOIL_TYPES[2];

  // Estimate ETo from temperature and humidity using simplified approximation
  const temp = form.temperature_celsius;
  const rh = form.humidity_percent;
  const et0_estimated = Math.max(
    2.0,
    Math.min(12.0, 0.0023 * (temp + 17.8) * Math.sqrt(Math.abs(temp - rh / 5)) * 4.0)
  );
  const et0 = parseFloat(et0_estimated.toFixed(2));

  // Kc from crop and stage
  const kc = parseFloat((crop.kc * stage.kc_mult).toFixed(3));

  // ETc = ETo × Kc
  const etc = parseFloat((et0 * kc).toFixed(3));

  // Season from crop default
  const season = crop.season;

  // Urgency and stress from growth stage
  const urgencyMap: Record<string, number> = {
    flowering: 0.75, vegetative: 0.6, maturity: 0.5, germination: 0.4, harvest: 0.25,
  };
  const stressMap: Record<string, number> = {
    flowering: 0.7, vegetative: 0.55, maturity: 0.45, germination: 0.35, harvest: 0.25,
  };

  return {
    farmer_id: 'FARMER_PORTAL',
    crop_type: form.crop_type,
    growth_stage: form.growth_stage,
    soil_type: form.soil_type,
    season,
    farm_area_hectares: form.farm_area_hectares,
    et0_mm_per_day: et0,
    kc_value: kc,
    etc_mm_per_day: etc,
    soil_whc_mm_per_m: soil.whc,
    temperature_celsius: form.temperature_celsius,
    humidity_percent: form.humidity_percent,
    rainfall_mm: form.rainfall_mm,
    preferred_start_hour: 6,
    irrigation_window_hours: 6,
    flexibility_score: 0.5,
    urgency_score: urgencyMap[form.growth_stage] ?? 0.5,
    crop_stress_index: stressMap[form.growth_stage] ?? 0.4,
  };
}

// ─── Sub-component ────────────────────────────────────────────────────────────

function FormField({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: '18px' }}>
      <label
        htmlFor={htmlFor}
        style={{
          display: 'block',
          fontWeight: 600,
          fontSize: '14px',
          color: 'var(--color-primary-dark)',
          marginBottom: '6px',
        }}
      >
        {label}
      </label>
      {children}
      {hint && (
        <p
          style={{
            fontSize: '12px',
            color: 'var(--text-subtle)',
            marginTop: '4px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Info size={11} />
          {hint}
        </p>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export const FarmerPortalPage: React.FC = () => {
  const { t } = useViewMode();

  const [form, setForm] = useState<FarmerForm>({
    crop_type: 'wheat',
    growth_stage: 'vegetative',
    soil_type: 'loam',
    farm_area_hectares: 2.0,
    temperature_celsius: 26,
    humidity_percent: 55,
    rainfall_mm: 0,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PredictionDisplay | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedCrop = CROPS.find((c) => c.value === form.crop_type) ?? CROPS[0];

  const handleChange = (field: keyof FarmerForm, val: string | number) => {
    setForm((prev) => ({ ...prev, [field]: val }));
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (form.farm_area_hectares <= 0) {
      setError('Farm area must be greater than 0.');
      return;
    }
    if (form.temperature_celsius < 5 || form.temperature_celsius > 50) {
      setError('Temperature must be between 5°C and 50°C.');
      return;
    }
    if (form.humidity_percent < 10 || form.humidity_percent > 100) {
      setError('Humidity must be between 10% and 100%.');
      return;
    }
    if (form.rainfall_mm < 0) {
      setError('Rainfall cannot be negative.');
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        farmer_data: deriveAgronomicInputs(form),
        model_name: 'XGBoost',
      };
      const res = await api.predictSingle(payload);
      setResult({
        demand_m3: res.predicted_water_demand_m3,
        model_name: res.model_name,
        warning: res.warning ?? null,
        shadow_estimate_m3: res.shadow_agronomic_estimate_m3 ?? null,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Could not reach the prediction server.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setForm({
      crop_type: 'wheat',
      growth_stage: 'vegetative',
      soil_type: 'loam',
      farm_area_hectares: 2.0,
      temperature_celsius: 26,
      humidity_percent: 55,
      rainfall_mm: 0,
    });
    setResult(null);
    setError(null);
  };

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '0 4px' }}>
      {/* ── Hero Banner ── */}
      <div
        style={{
          background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-teal) 100%)',
          borderRadius: '12px',
          padding: '28px 32px',
          color: '#fff',
          marginBottom: '28px',
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          flexWrap: 'wrap',
        }}
      >
        <div
          style={{
            background: 'rgba(255,255,255,0.15)',
            borderRadius: '50%',
            width: '64px',
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Droplets size={32} />
        </div>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, marginBottom: '6px', lineHeight: 1.3 }}>
            💧 {t('farmerPortalTitle')}
          </h1>
          <p style={{ fontSize: '14px', opacity: 0.88, lineHeight: 1.5 }}>
            {t('farmerPortalDesc')}
          </p>
        </div>
      </div>

      {/* ── Prediction Form ── */}
      <div className="card" style={{ padding: '28px 28px 24px', marginBottom: '20px' }}>
        <h2
          style={{
            fontSize: '16px',
            fontWeight: 700,
            color: 'var(--color-primary-dark)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Leaf size={18} style={{ color: 'var(--color-mint)' }} />
          Enter Your Farm Details
        </h2>

        <form onSubmit={handleSubmit} id="farmer-portal-form" noValidate>
          {/* Crop Type — visual buttons */}
          <FormField
            label="What crop are you growing?"
            hint="Select your current crop. This helps estimate water needs."
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(175px, 1fr))',
                gap: '8px',
              }}
            >
              {CROPS.map((crop) => (
                <button
                  key={crop.value}
                  type="button"
                  id={`crop-btn-${crop.value}`}
                  onClick={() => handleChange('crop_type', crop.value)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: `2px solid ${
                      form.crop_type === crop.value
                        ? 'var(--color-primary)'
                        : 'var(--border-default)'
                    }`,
                    background: form.crop_type === crop.value ? 'var(--color-mint-light)' : '#fff',
                    color: form.crop_type === crop.value ? 'var(--color-primary-dark)' : 'var(--text-main)',
                    fontWeight: form.crop_type === crop.value ? 600 : 400,
                    fontSize: '13px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'all 0.15s',
                  }}
                >
                  <span style={{ fontSize: '18px' }}>{crop.icon}</span>
                  <span>{crop.label}</span>
                </button>
              ))}
            </div>
          </FormField>

          {/* Growth Stage */}
          <FormField
            label="What stage is your crop in?"
            htmlFor="farmer-growth-stage"
            hint="Earlier stages generally need less water. Flowering needs the most."
          >
            <select
              id="farmer-growth-stage"
              value={form.growth_stage}
              onChange={(e) => handleChange('growth_stage', e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-default)',
                fontSize: '14px',
                background: '#fff',
                color: 'var(--text-main)',
                cursor: 'pointer',
              }}
            >
              {GROWTH_STAGES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </FormField>

          {/* Soil Type */}
          <FormField
            label="What type of soil does your farm have?"
            htmlFor="farmer-soil-type"
            hint="Heavier soils hold more water. Sandy soils drain quickly."
          >
            <select
              id="farmer-soil-type"
              value={form.soil_type}
              onChange={(e) => handleChange('soil_type', e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-default)',
                fontSize: '14px',
                background: '#fff',
                color: 'var(--text-main)',
                cursor: 'pointer',
              }}
            >
              {SOIL_TYPES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </FormField>

          {/* Numeric inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <FormField label="Farm area (hectares)"
              htmlFor="farmer-area" hint="1 hectare ≈ 2.5 acres">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sprout size={16} style={{ color: 'var(--color-primary)', flexShrink: 0 }} />
                <input
                  id="farmer-area"
                  type="number"
                  min={0.1}
                  max={200}
                  step={0.1}
                  value={form.farm_area_hectares}
                  onChange={(e) => handleChange('farm_area_hectares', parseFloat(e.target.value) || 0)}
                  style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-default)', fontSize: '14px' }}
                />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)', flexShrink: 0 }}>ha</span>
              </div>
            </FormField>

            <FormField label="Today's temperature (°C)"
              htmlFor="farmer-temperature" hint="Use current or forecasted daytime temperature">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Thermometer size={16} style={{ color: '#e07a5f', flexShrink: 0 }} />
                <input
                  id="farmer-temperature"
                  type="number"
                  min={5}
                  max={50}
                  step={0.5}
                  value={form.temperature_celsius}
                  onChange={(e) => handleChange('temperature_celsius', parseFloat(e.target.value) || 20)}
                  style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-default)', fontSize: '14px' }}
                />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)', flexShrink: 0 }}>°C</span>
              </div>
            </FormField>

            <FormField label="Relative humidity (%)"
              htmlFor="farmer-humidity" hint="Check weather app or use 50–65% for dry season">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Droplets size={16} style={{ color: 'var(--color-teal)', flexShrink: 0 }} />
                <input
                  id="farmer-humidity"
                  type="number"
                  min={10}
                  max={100}
                  step={1}
                  value={form.humidity_percent}
                  onChange={(e) => handleChange('humidity_percent', parseFloat(e.target.value) || 50)}
                  style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-default)', fontSize: '14px' }}
                />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)', flexShrink: 0 }}>%</span>
              </div>
            </FormField>

            <FormField label="Recent rainfall today (mm)"
              htmlFor="farmer-rainfall" hint="Enter 0 if no rain today">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CloudRain size={16} style={{ color: '#4a90d9', flexShrink: 0 }} />
                <input
                  id="farmer-rainfall"
                  type="number"
                  min={0}
                  max={300}
                  step={0.5}
                  value={form.rainfall_mm}
                  onChange={(e) => handleChange('rainfall_mm', parseFloat(e.target.value) || 0)}
                  style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-default)', fontSize: '14px' }}
                />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)', flexShrink: 0 }}>mm</span>
              </div>
            </FormField>
          </div>

          {/* Validation Error */}
          {error && (
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                padding: '12px 16px',
                background: 'var(--status-error-bg)',
                border: '1px solid var(--status-error-border)',
                borderRadius: '8px',
                marginBottom: '16px',
              }}
            >
              <AlertCircle size={18} style={{ color: 'var(--status-error)', flexShrink: 0, marginTop: '1px' }} />
              <span style={{ fontSize: '13px', color: 'var(--status-error)' }}>{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '4px', flexWrap: 'wrap' }}>
            <button
              type="submit"
              id="farmer-portal-submit"
              disabled={isLoading}
              style={{
                flex: '1 1 200px',
                padding: '13px 20px',
                background: isLoading ? 'var(--color-primary-light)' : 'var(--color-primary)',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '15px',
                fontWeight: 700,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'background 0.2s',
              }}
            >
              {isLoading ? (
                <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Calculating…</>
              ) : (
                <><Droplets size={16} /> Calculate My Water Need</>
              )}
            </button>
            <button
              type="button"
              id="farmer-portal-reset"
              onClick={handleReset}
              style={{
                padding: '13px 18px',
                background: 'transparent',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-default)',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <RefreshCw size={14} /> Reset
            </button>
          </div>
        </form>
      </div>

      {/* ── Loading ── */}
      {isLoading && (
        <div style={{ padding: '24px', textAlign: 'center' }}>
          <LoadingSpinner message="Running AI water-demand model…" />
        </div>
      )}

      {/* ── Result Card ── */}
      {result && !isLoading && (
        <div
          id="farmer-portal-result"
          className="card"
          style={{
            padding: '28px',
            border: '2px solid var(--status-success-border)',
            background: 'var(--status-success-bg)',
            marginBottom: '20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <CheckCircle2 size={28} style={{ color: 'var(--status-success)', flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--status-success)', marginBottom: '2px' }}>
                Water Demand Estimate Ready
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)' }}>
                {selectedCrop.icon} {selectedCrop.label} •{' '}
                {GROWTH_STAGES.find((s) => s.value === form.growth_stage)?.label} •{' '}
                {form.farm_area_hectares} ha
              </div>
            </div>
          </div>

          {/* Main result */}
          <div
            style={{
              textAlign: 'center',
              padding: '20px',
              background: '#fff',
              borderRadius: '10px',
              marginBottom: '20px',
              border: '1px solid var(--status-success-border)',
            }}
          >
            <div style={{ fontSize: '13px', color: 'var(--text-subtle)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
              Estimated Daily Water Requirement
            </div>
            <div style={{ fontSize: '48px', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1, marginBottom: '6px' }}>
              {result.demand_m3.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}
            </div>
            <div style={{ fontSize: '18px', color: 'var(--text-muted)', fontWeight: 600 }}>m³ / day</div>
            <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '6px' }}>
              Calculated by: {result.model_name} AI Model
            </div>
          </div>

          {/* Interpretation Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: '#fff', borderRadius: '8px', padding: '14px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600, marginBottom: '4px' }}>PER ACRE (APPROX.)</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                {(result.demand_m3 / form.farm_area_hectares / 2.47).toLocaleString(undefined, { maximumFractionDigits: 1 })}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>m³ / day / acre</div>
            </div>
            <div style={{ background: '#fff', borderRadius: '8px', padding: '14px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600, marginBottom: '4px' }}>WEEKLY ESTIMATE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                {(result.demand_m3 * 7).toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>m³ for 7 days</div>
            </div>
            {result.shadow_estimate_m3 !== null && (
              <div style={{ background: '#fff', borderRadius: '8px', padding: '14px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-subtle)', fontWeight: 600, marginBottom: '4px' }}>FORMULA CHECK</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-teal)' }}>
                  {result.shadow_estimate_m3.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>m³ (agronomic formula)</div>
              </div>
            )}
          </div>

          {/* Warning */}
          {result.warning && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '10px 14px', background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-border)', borderRadius: '6px', marginBottom: '16px', fontSize: '12px', color: 'var(--status-warning)' }}>
              <AlertCircle size={14} style={{ flexShrink: 0, marginTop: '1px' }} />
              <span>{result.warning}</span>
            </div>
          )}

          {/* Disclaimer */}
          <div style={{ fontSize: '11px', color: 'var(--text-subtle)', display: 'flex', alignItems: 'flex-start', gap: '6px', padding: '10px 14px', background: '#f8fafc', borderRadius: '6px', lineHeight: 1.5 }}>
            <Info size={13} style={{ flexShrink: 0, marginTop: '1px' }} />
            <span>
              <strong>Note:</strong> This estimate uses an AI model trained on agronomic formulas
              (FAO-56 Penman-Monteith method). It is a guidance tool, not a replacement for field
              measurements. Actual needs may vary with weather, irrigation efficiency, and local conditions.
            </span>
          </div>
        </div>
      )}

      {/* ── Quick Link to Scenario ── */}
      <div
        className="card"
        style={{
          padding: '20px 24px',
          marginBottom: '28px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: '3px' }}>
            Need water allocation between multiple farmers?
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Run a multi-farmer mediation scenario to see fair water sharing.
          </div>
        </div>
        <Link
          to="/scenario"
          className="btn btn-outline btn-sm"
          style={{ textDecoration: 'none', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <span>Water Sharing Scenario</span>
          <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  );
};
