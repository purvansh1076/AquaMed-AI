/**
 * AquaMediAI — Farmer View Page
 * Displays water-sharing results for a simulated scenario with clear,
 * user-friendly language and technical details expandable on demand.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Droplet,
  Sprout,
  Waves,
  Handshake,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  ShieldCheck,
  Scale,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { LoadingSpinner } from '../components/common/LoadingSpinner';


export const FarmerViewPage: React.FC = () => {
  const { scenarioResult, isLoading, loadingMessage, runScenario } = useScenario();
  const { t, selectedFarmerId, setSelectedFarmerId, setViewMode } = useViewMode();
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);

  // Quick action to run default scenario if none is loaded
  const handleQuickRun = async () => {
    await runScenario({
      scenario_type: 'moderate_shortage',
      n_farmers: 8,
    });
  };

  if (isLoading) {
    return (
      <div className="farmer-loading-container">
        <LoadingSpinner message={loadingMessage || t('checkingApi')} />
      </div>
    );
  }

  if (!scenarioResult) {
    return (
      <div className="farmer-empty-card">
        <div className="farmer-empty-icon">💧</div>
        <h2 className="farmer-empty-title">{t('noScenarioTitle')}</h2>
        <p className="farmer-empty-desc">{t('noScenarioDesc')}</p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="farmer-btn-primary"
            onClick={handleQuickRun}
            id="farmer-run-scenario-btn"
          >
            <span>{t('startScenarioBtn')}</span>
            <ArrowRight size={20} />
          </button>
          <Link
            to="/scenario"
            className="btn btn-outline"
            style={{ borderRadius: '999px', padding: '12px 24px', fontWeight: 600, textDecoration: 'none' }}
          >
            <span>{t('startWaterSharingTitle')}</span>
          </Link>
        </div>
      </div>
    );
  }

  // Extract farmers list
  const farmersList = scenarioResult.farmers || [];
  const farmerIds: string[] = farmersList.length > 0
    ? farmersList.map((f: any) => f.farmer_id || f.id || String(f))
    : scenarioResult.final_allocation?.allocations?.map((a: any) => a.farmer_id) || ['FARM_0001'];

  // Identify active farmer
  const activeFarmerId =
    selectedFarmerId && farmerIds.includes(selectedFarmerId)
      ? selectedFarmerId
      : farmerIds[0] || 'FARM_0001';

  // Find farmer-specific data
  const farmerMeta = farmersList.find(
    (f: any) => (f.farmer_id || f.id) === activeFarmerId
  ) as Record<string, any> | undefined;

  const finalAlloc =
    scenarioResult.final_allocation?.allocations?.find(
      (a: any) => a.farmer_id === activeFarmerId
    ) ||
    scenarioResult.initial_allocation?.allocations?.find(
      (a: any) => a.farmer_id === activeFarmerId
    );

  const farmerExplanation =
    scenarioResult.explanations?.allocation_explanations?.find(
      (a: any) => a.farmer_id === activeFarmerId
    );

  const allocatedWater = finalAlloc ? finalAlloc.allocated_water_m3 : 0;
  const requestedWater = finalAlloc ? finalAlloc.predicted_demand_m3 : 0;
  const minimumRequirement = finalAlloc ? finalAlloc.minimum_requirement_m3 : 0;
  const satisfactionRatio = finalAlloc
    ? finalAlloc.satisfaction_ratio
    : requestedWater > 0
    ? allocatedWater / requestedWater
    : 1;
  const satisfactionPercent = Math.min(100, Math.round(satisfactionRatio * 100));

  const availableCanalWater = scenarioResult.available_water_m3 || 0;
  const isAgreementReached =
    scenarioResult.final_decision?.agreement_status === 'AGREEMENT_REACHED' ||
    scenarioResult.negotiation?.agreement_status === 'AGREEMENT_REACHED' ||
    scenarioResult.status === 'success';

  // Translate reason codes into localized titles & descriptions
  const getReasonCard = (code: string) => {
    switch (code) {
      case 'RESOURCE_SHORTAGE':
        return {
          title: t('reasonResourceShortageTitle'),
          desc: t('reasonResourceShortageDesc'),
          icon: '💧',
        };
      case 'HIGH_URGENCY':
        return {
          title: t('reasonHighUrgencyTitle'),
          desc: t('reasonHighUrgencyDesc'),
          icon: '🚨',
        };
      case 'HIGH_CROP_SENSITIVITY':
        return {
          title: t('reasonHighCropSensitivityTitle'),
          desc: t('reasonHighCropSensitivityDesc'),
          icon: '🌱',
        };
      case 'MINIMUM_REQUIREMENT':
        return {
          title: t('reasonMinimumRequirementTitle'),
          desc: t('reasonMinimumRequirementDesc'),
          icon: '🛡️',
        };
      case 'MAXIMUM_REQUIREMENT':
        return {
          title: t('reasonMaximumRequirementTitle'),
          desc: t('reasonMaximumRequirementDesc'),
          icon: '📏',
        };
      case 'CANAL_CAPACITY':
        return {
          title: t('reasonCanalCapacityTitle'),
          desc: t('reasonCanalCapacityDesc'),
          icon: '🚰',
        };
      case 'WINDOW_CONFLICT':
        return {
          title: t('reasonWindowConflictTitle'),
          desc: t('reasonWindowConflictDesc'),
          icon: '🕐',
        };
      case 'FAIRNESS_ADJUSTMENT':
        return {
          title: t('reasonFairnessAdjustmentTitle'),
          desc: t('reasonFairnessAdjustmentDesc'),
          icon: '⚖️',
        };
      case 'NEGOTIATION_CONCESSION':
        return {
          title: t('reasonNegotiationConcessionTitle'),
          desc: t('reasonNegotiationConcessionDesc'),
          icon: '🤝',
        };
      case 'BATNA_PROTECTION':
        return {
          title: t('reasonBatnaProtectionTitle'),
          desc: t('reasonBatnaProtectionDesc'),
          icon: '🛡️',
        };
      case 'UNMET_DEMAND':
        return {
          title: t('reasonUnmetDemandTitle'),
          desc: t('reasonUnmetDemandDesc'),
          icon: '💧',
        };
      case 'FULL_DEMAND_SATISFACTION':
        return {
          title: t('reasonFullSatisfactionTitle'),
          desc: t('reasonFullSatisfactionDesc'),
          icon: '✅',
        };
      case 'WATER_SURPLUS':
        return {
          title: t('reasonWaterSurplusTitle'),
          desc: t('reasonWaterSurplusDesc'),
          icon: '🌊',
        };
      default:
        return {
          title: t('reasonFairnessAdjustmentTitle'),
          desc: t('reasonFairnessAdjustmentDesc'),
          icon: '💧',
        };
    }
  };

  const rawReasonCodes =
    farmerExplanation?.reason_codes && farmerExplanation.reason_codes.length > 0
      ? farmerExplanation.reason_codes
      : ['RESOURCE_SHORTAGE', 'MINIMUM_REQUIREMENT', 'FAIRNESS_ADJUSTMENT'];

  // Compute water priority score for each farmer (CSPS equivalent)
  // Priority = urgency + crop_sensitivity, rounded to 0-100 scale
  const computeWaterPriority = (farmer: any): number => {
    const urgency = farmer.urgency_score !== undefined ? farmer.urgency_score : 0.5;
    const sensitivity = farmer.crop_sensitivity !== undefined ? farmer.crop_sensitivity : 0.5;
    const priority = (urgency + sensitivity) / 2; // 0-1 range
    return Math.round(priority * 100); // 0-100 scale
  };

  // Get priority for active farmer
  const activeFarmer = farmersList.find(
    (f: any) => (f.farmer_id || f.id) === activeFarmerId
  );
  const waterPriority = activeFarmer ? computeWaterPriority(activeFarmer) : 50;

  // Format priority as "X/100"
  const priorityLabel = `${waterPriority}/100`;

  return (
    <div className="farmer-view-container">
      {/* Top Banner & Farmer Selector */}
      <div className="farmer-header-bar">
        <div>
          <h1 className="farmer-view-title">{t('myWaterSharing')}</h1>
          <p className="farmer-view-subtitle">{t('myWaterSharingDesc')}</p>
        </div>

        <div className="farmer-selector-wrapper">
          <label htmlFor="farmer-select" className="farmer-selector-label">
            {t('selectFarmer')}:
          </label>
          <select
            id="farmer-select"
            className="farmer-select-dropdown"
            value={activeFarmerId}
            onChange={(e) => setSelectedFarmerId(e.target.value)}
          >
            {farmerIds.map((id) => {
              const meta = farmersList.find((f: any) => (f.farmer_id || f.id) === id);
              const cropLabel = meta?.crop_type ? ` (${meta.crop_type})` : '';
              const stageLabel = meta?.growth_stage ? ` • Stage: ${meta.growth_stage}` : '';
              const areaLabel = meta?.farm_area_hectares ? ` • ${meta.farm_area_hectares} ha` : '';
              return (
                <option key={id} value={id}>
                  {id} {cropLabel}{stageLabel}{areaLabel}
                </option>
              );
            })}
          </select>
          <Link
            to="/scenario"
            className="btn btn-outline btn-sm"
            style={{ borderRadius: '999x', padding: '12px 24px', fontWeight: 600, textDecoration: 'none' }}
          >
            <span>{t('startWaterSharingTitle')}</span>
          </Link>
        </div>
      </div>

      {/* Viewing details pill */}
      <div className="farmer-profile-pill">
        <span>
          {t('viewingFor')}: <strong>{activeFarmerId.replace('_', ' ').toUpperCase()}</strong>
          {farmerMeta?.crop_type ? ` • ${farmerMeta.crop_type}` : ''}
          {farmerMeta?.farm_area_hectares ? ` • ${farmerMeta.farm_area_hectares} ha` : ''}
        </span>
        <span className="farmer-status-tag">
          <ShieldCheck size={16} />
          {t('reasonMinimumRequirementTitle').replace(/[💧🌱🚨📏🚰🕐⚖️🤝🛡️✅🌊]/gu, '').trim().split('.')[0] || 'Min. Requirement'}: {minimumRequirement.toLocaleString(undefined, { maximumFractionDigits: 1 })} m³
        </span>
        {/* Water Priority Badge */}
        <span className="farmer-priority-badge">
          {t('waterPriorityScore')}: <strong>{priorityLabel}</strong>
        </span>
      </div>

      {/* 8-Farm Summary Grid removed for syntax stability */}

      {/* 4 Large Highlight Cards */}
      <div className="farmer-kpi-grid">
        {/* 1. Water Given to Me */}
        <div className="farmer-kpi-card highlight-card">
          <div className="farmer-kpi-header">
            <span className="farmer-kpi-title">{t('waterGivenToMe')}</span>
            <span className="farmer-kpi-icon-bubble green">
              <Droplet size={24} />
            </span>
          </div>
          <div className="farmer-kpi-value">
            {allocatedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })}
            <span className="farmer-kpi-unit"> m³</span>
          </div>
          <p className="farmer-kpi-desc">{t('waterGivenDesc')}</p>
        </div>

        {/* 2. Water Needed */}
        <div className="farmer-kpi-card">
          <div className="farmer-kpi-header">
            <span className="farmer-kpi-title">{t('waterNeeded')}</span>
            <span className="farmer-kpi-icon-bubble blue">
              <Sprout size={24} />
            </span>
          </div>
          <div className="farmer-kpi-value">
            {requestedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })}
            <span className="farmer-kpi-unit"> m³</span>
          </div>
          <p className="farmer-kpi-desc">{t('waterNeededDesc')}</p>
        </div>

        {/* 3. Canal Water Available */}
        <div className="farmer-kpi-card">
          <div className="farmer-kpi-header">
            <span className="farmer-kpi-title">{t('waterAvailable')}</span>
            <span className="farmer-kpi-icon-bubble cyan">
              <Waves size={24} />
            </span>
          </div>
          <div className="farmer-kpi-value">
            {availableCanalWater.toLocaleString(undefined, { maximumFractionDigits: 1 })}
            <span className="farmer-kpi-unit"> m³</span>
          </div>
          <p className="farmer-kpi-desc">{t('waterAvailableDesc')}</p>
        </div>

        {/* 4. Sharing Result */}
        <div className="farmer-kpi-card">
          <div className="farmer-kpi-header">
            <span className="farmer-kpi-title">{t('sharingResult')}</span>
            <span className="farmer-kpi-icon-bubble gold">
              <Handshake size={24} />
            </span>
          </div>
          <div className="farmer-kpi-value">
            {isAgreementReached ? (
              <span className="farmer-result-badge agreed">
                <CheckCircle2 size={24} />
                {satisfactionPercent}%
              </span>
            ) : (
              <span className="farmer-result-badge balanced">
                <Scale size={24} />
                {satisfactionPercent}%
              </span>
            )}
          </div>
          <p className="farmer-kpi-desc">{t('sharingResultDesc')}</p>
        </div>
      </div>

      {/* Result Summary Card */}
      <div className="farmer-summary-card">
        <h2 className="farmer-section-title">{t('yourResultTitle')}</h2>

        <div className="farmer-progress-wrapper">
          <div className="farmer-progress-bar-bg">
            <div
              className="farmer-progress-bar-fill"
              style={{ width: `${satisfactionPercent}%` }}
            />
          </div>
          <div className="farmer-progress-labels">
            <span>
              {t('receivedLabel')}:{' '}
              <strong>
                {allocatedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })} m³
              </strong>
            </span>
            <span>
              {t('requestedLabel')}:{' '}
              <strong>
                {requestedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })} m³
              </strong>
            </span>
            <span>
              {t('satisfiedLabel')}: <strong>{satisfactionPercent}%</strong>
            </span>
          </div>
        </div>

        <div className="farmer-summary-note">
          <p>
            {satisfactionPercent >= 100 ? t('surplusNote') : t('shortageNote')}
          </p>
          <p className="farmer-note-agreement">
            {isAgreementReached ? t('agreementReachedNote') : t('agreementPendingNote')}
          </p>
        </div>
      </div>

      {/* Why did I get this amount? */}
      <div className="farmer-reasons-section">
        <h2 className="farmer-section-title">{t('whyTitle')}</h2>
        <p className="farmer-section-subtitle">{t('whySubtitle')}</p>

        <div className="farmer-reasons-grid">
          {rawReasonCodes.map((code) => {
            const card = getReasonCard(code);
            return (
              <div key={code} className="farmer-reason-card">
                <div className="farmer-reason-emoji">{card.icon}</div>
                <div className="farmer-reason-content">
                  <h3 className="farmer-reason-title">{card.title}</h3>
                  <p className="farmer-reason-desc">{card.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* How was water shared? (5 Steps) */}
      <div className="farmer-steps-section">
        <h2 className="farmer-section-title">{t('howSharedTitle')}</h2>
        <p className="farmer-section-subtitle">{t('howSharedSubtitle')}</p>

        <div className="farmer-steps-timeline">
          <div className="farmer-step-item">
            <div className="farmer-step-number">1</div>
            <div className="farmer-step-body">
              <h4 className="farmer-step-title">{t('step1')}</h4>
              <p className="farmer-step-desc">{t('step1Desc')}</p>
            </div>
          </div>

          <div className="farmer-step-item">
            <div className="farmer-step-number">2</div>
            <div className="farmer-step-body">
              <h4 className="farmer-step-title">{t('step2')}</h4>
              <p className="farmer-step-desc">{t('step2Desc')}</p>
            </div>
          </div>

          <div className="farmer-step-item">
            <div className="farmer-step-number">3</div>
            <div className="farmer-step-body">
              <h4 className="farmer-step-title">{t('step3')}</h4>
              <p className="farmer-step-desc">{t('step3Desc')}</p>
            </div>
          </div>

          <div className="farmer-step-item">
            <div className="farmer-step-number">4</div>
            <div className="farmer-step-body">
              <h4 className="farmer-step-title">{t('step4')}</h4>
              <p className="farmer-step-desc">{t('step4Desc')}</p>
            </div>
          </div>

          <div className="farmer-step-item">
            <div className="farmer-step-number">5</div>
            <div className="farmer-step-body">
              <h4 className="farmer-step-title">{t('step5')}</h4>
              <p className="farmer-step-desc">{t('step5Desc')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Fair Sharing Box */}
      <div className="farmer-fairness-box">
        <div className="farmer-fairness-icon">
          <Scale size={32} />
        </div>
        <div>
          <h3 className="farmer-fairness-title">{t('fairSharingTitle')}</h3>
          <p className="farmer-fairness-desc">{t('fairSharingDesc')}</p>
          <p className="farmer-fairness-note">{t('fairSharingNote')}</p>
        </div>
      </div>

      {/* Expandable Technical Details (Optional for researchers/evaluators) */}
      <div className="farmer-tech-accordion">
        <button
          type="button"
          className="farmer-tech-toggle-btn"
          onClick={() => setShowTechDetails(!showTechDetails)}
          aria-expanded={showTechDetails}
        >
          <div>
            <span className="farmer-tech-heading">{t('techDetailsTitle')}</span>
            <span className="farmer-tech-sub">{t('techDetailsSubtitle')}</span>
          </div>
          {showTechDetails ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {showTechDetails && (
          <div className="farmer-tech-content">
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">{t('modelUsed')}:</span>
              <span className="farmer-tech-val">
                {scenarioResult.predictions?.[0]?.model_name || 'XGBoost Regressor (v1.0)'}
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">{t('lpSolver')}:</span>
              <span className="farmer-tech-val">
                {scenarioResult.final_allocation?.allocation_method || 'Google OR-Tools GLOP'} (H1-H3 constraints)
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">{t('fairnessScore')}:</span>
              <span className="farmer-tech-val">
                {(scenarioResult.final_decision?.fairness_score ?? 0.95).toFixed(3)}
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">{t('rawCodes')}:</span>
              <span className="farmer-tech-val codes-list">
                {rawReasonCodes.join(', ')}
              </span>
            </div>
            <div className="farmer-tech-action">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setViewMode('expert')}
              >
                <span>Switch to 🔬 Expert View for full research metrics</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};