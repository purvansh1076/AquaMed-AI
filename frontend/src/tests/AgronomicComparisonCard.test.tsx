import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgronomicComparisonCard } from '../components/pipeline/AgronomicComparisonCard';
import type { PredictionResponse } from '../types/api';

describe('AgronomicComparisonCard — Phase 5 Expert Mode UI', () => {
  const samplePopulatedPrediction: PredictionResponse = {
    farmer_id: 'FARM_0004',
    predicted_water_demand_m3: 128.48,
    model_name: 'XGBoost',
    model_version: '1.0.0',
    warning: null,
    input_summary: {
      farm_area_hectares: 9.304,
      et0_mm_per_day: 5.909,
      kc_value: 0.6,
      rainfall_mm: 2.34,
      crop_type: 'wheat',
    },
    shadow_agronomic_estimate_m3: 471.23,
    shadow_comparison: {
      status: 'available',
      agronomic_demand_m3: 471.23,
      legacy_prediction_m3: 128.48,
      difference_m3: -342.75,
      difference_percent: -72.74,
      method: 'FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall',
      application_efficiency: 0.7,
      is_empirical_error: false,
      input_validation: {
        is_valid: true,
        errors: [],
      },
      provenance_note:
        'Legacy ML models (RandomForest, XGBoost) were trained on synthetic data. The agronomic estimate is a deterministic physical calculation, NOT measured delivery.',
      disclaimer:
        'Differences between legacy predictions and deterministic baseline are comparison metrics, NOT empirical model error, because no measured real-world delivery ground truth is available.',
    },
  };

  it('1. renders populated legacy ML and theoretical agronomic baseline values correctly', () => {
    render(<AgronomicComparisonCard prediction={samplePopulatedPrediction} farmerId="FARM_0004" />);

    // Heading & Card existence
    expect(screen.getByText(/Theoretical Agronomic Baseline \(FAO-56\) & Shadow Comparison/i)).toBeInTheDocument();
    expect(screen.getByText(/Research benchmark for Farmer FARM_0004/i)).toBeInTheDocument();

    // Legacy ML prediction
    const legacyVal = screen.getByTestId('legacy-prediction-val');
    expect(legacyVal).toHaveTextContent('128.48');
    expect(screen.getByText(/Trained on synthetic academic data \(XGBoost v1.0.0\)/i)).toBeInTheDocument();

    // Agronomic baseline
    const baselineVal = screen.getByTestId('agronomic-baseline-val');
    expect(baselineVal).toHaveTextContent('471.23');
    expect(screen.getByText(/Calculated irrigation requirement \(not measured delivery\)/i)).toBeInTheDocument();

    // Difference and percentage
    const diffM3 = screen.getByTestId('difference-m3-val');
    expect(diffM3).toHaveTextContent('-342.75');

    const diffPct = screen.getByTestId('difference-percent-val');
    expect(diffPct).toHaveTextContent('-72.7% variance');

    // Input verification badge
    expect(screen.getByTestId('input-valid-badge')).toHaveTextContent(/Physical Inputs Verified/i);

    // Input variables in summary
    expect(screen.getByText(/9.304 ha/i)).toBeInTheDocument();
    expect(screen.getByText(/5.909 mm\/day/i)).toBeInTheDocument();
    expect(screen.getByText(/70% \(surface\)/i)).toBeInTheDocument();
  });

  it('2. handles unavailable baseline safely without showing zero or fabricating values', () => {
    const unavailablePrediction: PredictionResponse = {
      farmer_id: 'FARM_UNAVAIL',
      predicted_water_demand_m3: 55.0,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: 'Input warning',
      input_summary: {
        farm_area_hectares: 0.0,
        et0_mm_per_day: 5.0,
        kc_value: 1.0,
        rainfall_mm: 0.0,
      },
      shadow_agronomic_estimate_m3: null,
      shadow_comparison: {
        status: 'unavailable',
        agronomic_demand_m3: null,
        legacy_prediction_m3: 55.0,
        difference_m3: null,
        difference_percent: null,
        method: 'FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall',
        application_efficiency: 0.7,
        is_empirical_error: false,
        input_validation: {
          is_valid: false,
          errors: ['farm_area_hectares must be > 0, got 0.0'],
        },
        provenance_note: 'Synthetic legacy model note',
        disclaimer: 'Comparative disclaimer',
      },
    };

    render(<AgronomicComparisonCard prediction={unavailablePrediction} farmerId="FARM_UNAVAIL" />);

    // Must display "Unavailable" instead of zero (0.0 m³)
    const unavailBadge = screen.getByTestId('agronomic-baseline-unavailable');
    expect(unavailBadge).toHaveTextContent('Unavailable');
    expect(screen.queryByText('0.00 m³/day')).not.toBeInTheDocument();

    // Callout alert box rendered with exact validation error
    const alertBox = screen.getByTestId('unavailable-state-callout');
    expect(alertBox).toBeInTheDocument();
    expect(screen.getByText(/Agronomic Baseline Unavailable for this Farm Record/i)).toBeInTheDocument();
    expect(screen.getByText(/farm_area_hectares must be > 0, got 0.0/i)).toBeInTheDocument();

    // Difference and percentage not calculable
    expect(screen.getByTestId('input-invalid-badge')).toHaveTextContent(/Inputs Missing \/ Invalid/i);
    expect(screen.getByText(/Not calculable/i)).toBeInTheDocument();
  });

  it('3. handles zero baseline safely without displaying an undefined percentage', () => {
    const zeroBaselinePrediction: PredictionResponse = {
      farmer_id: 'FARM_RAIN_SATURATED',
      predicted_water_demand_m3: 5.0,
      model_name: 'XGBoost',
      model_version: '1.0.0',
      warning: null,
      input_summary: {
        farm_area_hectares: 2.0,
        et0_mm_per_day: 4.0,
        kc_value: 0.7,
        rainfall_mm: 35.0, // Heavy storm event exceeding ETc
      },
      shadow_agronomic_estimate_m3: 0.0,
      shadow_comparison: {
        status: 'available',
        agronomic_demand_m3: 0.0,
        legacy_prediction_m3: 5.0,
        difference_m3: 5.0,
        difference_percent: null, // Safely None because denominator is 0
        method: 'FAO-56 Single Crop Coefficient + USDA SCS Effective Rainfall',
        application_efficiency: 0.7,
        is_empirical_error: false,
        input_validation: {
          is_valid: true,
          errors: [],
        },
        provenance_note: 'Synthetic provenance',
        disclaimer: 'Non-empirical disclaimer',
      },
    };

    render(<AgronomicComparisonCard prediction={zeroBaselinePrediction} farmerId="FARM_RAIN_SATURATED" />);

    // Baseline displays 0.00 m³
    expect(screen.getByTestId('agronomic-baseline-val')).toHaveTextContent('0.00');

    // Difference displays +5.00 m³
    expect(screen.getByTestId('difference-m3-val')).toHaveTextContent('+5.00');

    // Zero baseline subtext explicitly states percentage is undefined
    const zeroSubtext = screen.getByTestId('zero-baseline-subtext');
    expect(zeroSubtext).toHaveTextContent(/Baseline is 0.00 m³\/day \(percentage undefined\)/i);
    expect(screen.queryByText(/NaN%/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Infinity%/i)).not.toBeInTheDocument();
  });

  it('4. displays research data provenance and non-empirical error disclaimers', () => {
    render(<AgronomicComparisonCard prediction={samplePopulatedPrediction} />);

    // Provenance statements
    expect(screen.getByText(/Research Methodology & Scientific Data Provenance/i)).toBeInTheDocument();
    expect(screen.getByText(/Differences between legacy ML and the baseline are comparative benchmark metrics/i)).toBeInTheDocument();
    expect(screen.getByText(/constitute empirical model error, model accuracy, or proven real-world improvement/i)).toBeInTheDocument();
  });
});
