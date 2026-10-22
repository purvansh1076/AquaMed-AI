import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Lightbulb,
  Droplet,
  Sprout,
  Waves,
  Handshake,
  ChevronDown,
  ChevronUp,
  Scale,
  ShieldCheck,
  Code2,
  ExternalLink,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { EmptyState } from '../components/common/EmptyState';
import { Badge } from '../components/common/Badge';
import { groupConflicts, type GroupedConflict } from '../utils/conflictGrouping';
import { formatWater } from '../utils/formatters';
import type { Translations } from '../i18n/translations';

export const ExplainabilityPage: React.FC = () => {
  const { scenarioResult } = useScenario();
  const { viewMode } = useViewMode();

  if (!scenarioResult) {
    return (
      <div>
        <div className="page-heading">
          <h1 className="page-title">
            {viewMode === 'farmer' ? '💧 Why Did I Get This Much Water?' : '🔬 Decision Explanation'}
          </h1>
          <p className="page-description">
            {viewMode === 'farmer'
              ? 'Run a water sharing plan to see your allocation explanation.'
              : 'Execute a mediation scenario to inspect causal rationales, constraint verification, and negotiation traces.'}
          </p>
        </div>
        <EmptyState
          title="No Water Plan Loaded"
          description="Configure an agrarian scenario to inspect decisions, optimization results, and explainability."
          actionText={viewMode === 'farmer' ? 'Start Water Sharing' : 'Configure Scenario'}
          actionHref="/scenario"
        />
      </div>
    );
  }

  return viewMode === 'farmer' ? (
    <FarmerExplainabilityView scenarioResult={scenarioResult} />
  ) : (
    <ExpertExplainabilityView scenarioResult={scenarioResult} />
  );
};

/* ==========================================================================
   1. 👨‍🌾 FARMER VIEW — Human-First Agricultural Explanation
   ========================================================================== */

interface ViewProps {
  scenarioResult: NonNullable<ReturnType<typeof useScenario>['scenarioResult']>;
}

const FarmerExplainabilityView: React.FC<ViewProps> = ({ scenarioResult }) => {
  const { t, selectedFarmerId, setSelectedFarmerId, setViewMode } = useViewMode();
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);

  const {
    available_water_m3 = 0,
    farmers = [],
    final_allocation,
    initial_allocation,
    explanations,
    final_decision,
  } = scenarioResult;

  const farmerIds: string[] = farmers.length > 0
    ? farmers.map((f: any) => f.farmer_id || f.id || String(f))
    : final_allocation?.allocations?.map((a) => a.farmer_id) || ['farmer_1'];

  const activeFarmerId =
    selectedFarmerId && farmerIds.includes(selectedFarmerId)
      ? selectedFarmerId
      : farmerIds[0] || 'farmer_1';

  const farmerMeta = farmers.find(
    (f: any) => (f.farmer_id || f.id) === activeFarmerId
  ) as Record<string, any> | undefined;

  const finalAlloc =
    final_allocation?.allocations?.find((a) => a.farmer_id === activeFarmerId) ||
    initial_allocation?.allocations?.find((a) => a.farmer_id === activeFarmerId);

  const farmerExplanation = explanations?.allocation_explanations?.find(
    (a) => a.farmer_id === activeFarmerId
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

  const isAgreementReached =
    final_decision?.agreement_status === 'AGREEMENT_REACHED' ||
    scenarioResult.negotiation?.agreement_status === 'AGREEMENT_REACHED' ||
    scenarioResult.status === 'success';

  // Map actual Phase 7 reason codes to friendly translations
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
        return null;
    }
  };

  // Only show explanations corresponding to reason codes ACTUALLY returned by backend
  const activeReasonCodes =
    farmerExplanation?.reason_codes && farmerExplanation.reason_codes.length > 0
      ? farmerExplanation.reason_codes
      : explanations?.all_reason_codes || [];

  // Group similar conflicts for clean human presentation
  const allConflicts =
    explanations?.conflict_explanations || scenarioResult.conflicts?.conflicts || [];
  const groupedConflicts: GroupedConflict[] = groupConflicts(allConflicts);

  return (
    <div className="farmer-view-container" style={{ maxWidth: '960px', margin: '0 auto' }}>
      {/* Page Title & Subtitle */}
      <div className="farmer-header-bar">
        <div>
          <h1 className="farmer-view-title">{t('explainPageTitleFarmer')}</h1>
          <p className="farmer-view-subtitle">{t('explainPageSubtitleFarmer')}</p>
        </div>

        {/* Farmer Selector */}
        <div className="farmer-selector-wrapper">
          <label htmlFor="farmer-select-explain" className="farmer-selector-label">
            {t('selectFarmer')}:
          </label>
          <select
            id="farmer-select-explain"
            className="farmer-select-dropdown"
            value={activeFarmerId}
            onChange={(e) => setSelectedFarmerId(e.target.value)}
          >
            {farmerIds.map((id) => {
              const meta = farmers.find((f: any) => (f.farmer_id || f.id) === id);
              const cropLabel = meta?.crop_type ? ` (${meta.crop_type})` : '';
              return (
                <option key={id} value={id}>
                  {id.replace('_', ' ').toUpperCase()} {cropLabel}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {/* Profile info pill */}
      <div className="farmer-profile-pill">
        <span>
          {t('viewingFor')}: <strong>{activeFarmerId.replace('_', ' ').toUpperCase()}</strong>
          {farmerMeta?.crop_type ? ` • ${farmerMeta.crop_type}` : ''}
          {farmerMeta?.farm_area_hectares ? ` • ${farmerMeta.farm_area_hectares} ha` : ''}
        </span>
        <span className="farmer-status-tag">
          <ShieldCheck size={16} />
          {t('reasonMinimumRequirementTitle')}: {minimumRequirement.toLocaleString(undefined, { maximumFractionDigits: 1 })} m³
        </span>
      </div>

      {/* 1. DECISION SUMMARY: Your Water Result */}
      <div className="farmer-summary-card">
        <h2 className="farmer-section-title">{t('explainResultCardTitle')}</h2>

        <div className="farmer-kpi-grid" style={{ marginTop: '16px', marginBottom: '16px' }}>
          <div className="farmer-kpi-card highlight-card">
            <div className="farmer-kpi-header">
              <span className="farmer-kpi-title">{t('waterGivenToMe')}</span>
              <span className="farmer-kpi-icon-bubble green"><Droplet size={22} /></span>
            </div>
            <div className="farmer-kpi-value">
              {allocatedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              <span className="farmer-kpi-unit"> m³</span>
            </div>
            <p className="farmer-kpi-desc">{t('waterGivenDesc')}</p>
          </div>

          <div className="farmer-kpi-card">
            <div className="farmer-kpi-header">
              <span className="farmer-kpi-title">{t('waterNeeded')}</span>
              <span className="farmer-kpi-icon-bubble blue"><Sprout size={22} /></span>
            </div>
            <div className="farmer-kpi-value">
              {requestedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              <span className="farmer-kpi-unit"> m³</span>
            </div>
            <p className="farmer-kpi-desc">{t('waterNeededDesc')}</p>
          </div>

          <div className="farmer-kpi-card">
            <div className="farmer-kpi-header">
              <span className="farmer-kpi-title">{t('waterAvailable')}</span>
              <span className="farmer-kpi-icon-bubble cyan"><Waves size={22} /></span>
            </div>
            <div className="farmer-kpi-value">
              {available_water_m3.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              <span className="farmer-kpi-unit"> m³</span>
            </div>
            <p className="farmer-kpi-desc">{t('waterAvailableDesc')}</p>
          </div>

          <div className="farmer-kpi-card">
            <div className="farmer-kpi-header">
              <span className="farmer-kpi-title">{t('sharingResult')}</span>
              <span className="farmer-kpi-icon-bubble gold"><Handshake size={22} /></span>
            </div>
            <div className="farmer-kpi-value">
              {isAgreementReached ? (
                <span className="farmer-result-badge agreed" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#15803d', fontWeight: 700, fontSize: '16px' }}>
                  🤝 Agreement Reached
                </span>
              ) : (
                <span className="farmer-result-badge balanced" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#d97706', fontWeight: 700, fontSize: '16px' }}>
                  ⚖️ {final_decision?.agreement_status || 'Balanced'}
                </span>
              )}
            </div>
            <p className="farmer-kpi-desc">
              {isAgreementReached ? t('agreementReachedNote') : t('agreementPendingNote')}
            </p>
          </div>
        </div>

        {/* Satisfaction Bar */}
        <div className="farmer-progress-wrapper">
          <div className="farmer-progress-bar-bg">
            <div className="farmer-progress-bar-fill" style={{ width: `${satisfactionPercent}%` }} />
          </div>
          <div className="farmer-progress-labels">
            <span>{t('receivedLabel')}: <strong>{allocatedWater.toLocaleString()} m³</strong></span>
            <span>{t('requestedLabel')}: <strong>{requestedWater.toLocaleString()} m³</strong></span>
            <span>{t('satisfiedLabel')}: <strong>{satisfactionPercent}%</strong></span>
          </div>
        </div>
      </div>

      {/* 2. WHY DID I GET THIS AMOUNT? (Plain-Language Reason Cards) */}
      <div className="farmer-reasons-section">
        <h2 className="farmer-section-title">{t('explainWhySectionTitle')}</h2>
        <p className="farmer-section-subtitle">{t('whySubtitle')}</p>

        <div className="farmer-reasons-grid">
          {activeReasonCodes.map((code) => {
            const card = getReasonCard(code);
            if (!card) return null;
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

      {/* 3. CONFLICTS: What affected the water sharing? (Grouped) */}
      <div className="farmer-summary-card">
        <h2 className="farmer-section-title">{t('explainConflictSectionTitle')}</h2>
        <p className="farmer-section-subtitle">{t('conflictSectionSubtitle')}</p>

        {groupedConflicts.length === 0 ? (
          <p style={{ color: 'var(--status-success)', fontWeight: 600 }}>
            {t('noConflictsFound')}
          </p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginTop: '12px' }}>
            {groupedConflicts.map((group) => (
              <div
                key={group.key}
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                    {group.farmerTitleKey ? t(group.farmerTitleKey as keyof Translations) : group.farmerTitle}
                  </h3>
                  {group.count > 0 && (
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-teal)', backgroundColor: '#e0f2fe', padding: '2px 8px', borderRadius: '999px' }}>
                      {group.count} {group.count === 1 ? 'issue' : 'issues'}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '6px', lineHeight: '1.4' }}>
                  {t(group.farmerExplanationKey as keyof Translations)}
                </p>
                {group.count > 0 && (
                  <p style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '6px', fontStyle: 'italic' }}>
                    {group.key === 'timing_conflict'
                      ? `${group.count} ${t('conflictTimingDetected')}.`
                      : `${group.count} ${group.count === 1 ? t('conflictSingularDetected') : t('conflictPluralDetected')} detected.`}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. FAIRNESS: Was the sharing fair? */}
      <div className="farmer-fairness-box">
        <div className="farmer-fairness-icon">
          <Scale size={32} />
        </div>
        <div>
          <h3 className="farmer-fairness-title">{t('explainFairnessSectionTitle')}</h3>
          <p className="farmer-fairness-desc">{t('explainFairnessText')}</p>
          <p className="farmer-fairness-note">{t('fairSharingNote')}</p>
        </div>
      </div>

      {/* 5. NEGOTIATION: How was the plan agreed? */}
      <div className="farmer-summary-card">
        <h2 className="farmer-section-title">{t('explainNegotiationSectionTitle')}</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '14px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <span style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--color-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700, flexShrink: 0 }}>1</span>
            <p style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '2px' }}>
              {t('explainNegotiationText1')}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <span style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--color-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700, flexShrink: 0 }}>2</span>
            <p style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '2px' }}>
              {t('explainNegotiationText2')}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <span style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--color-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700, flexShrink: 0 }}>3</span>
            <p style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '2px' }}>
              {t('explainNegotiationText3')}
            </p>
          </div>
        </div>
      </div>

      {/* 6. TECHNICAL DETAILS (Expandable Accordion) */}
      <div className="farmer-tech-accordion">
        <button
          type="button"
          className="farmer-tech-toggle-btn"
          onClick={() => setShowTechDetails(!showTechDetails)}
          aria-expanded={showTechDetails}
        >
          <div>
            <span className="farmer-tech-heading">🔬 Technical Details (Optional)</span>
            <span className="farmer-tech-sub">{t('techDetailsSubtitle')}</span>
          </div>
          {showTechDetails ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {showTechDetails && (
          <div className="farmer-tech-content">
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">AI Model:</span>
              <span className="farmer-tech-val">
                {scenarioResult.predictions?.[0]?.model_name || 'XGBoost Regressor (v1.0)'}
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">LP Solver:</span>
              <span className="farmer-tech-val">
                {final_allocation?.allocation_method || 'Google OR-Tools GLOP'}
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">Solver Status:</span>
              <span className="farmer-tech-val">
                {final_allocation?.solver_status || 'Not available'}
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">Fairness Measurement:</span>
              <span className="farmer-tech-val">
                Jain's Index = {final_decision?.fairness_score != null ? final_decision.fairness_score.toFixed(4) : 'Not available'}
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">Negotiation Rounds:</span>
              <span className="farmer-tech-val">
                {scenarioResult.negotiation?.n_rounds ?? final_decision?.negotiation_rounds ?? 1} rounds
              </span>
            </div>
            <div className="farmer-tech-row">
              <span className="farmer-tech-key">Active Reason Codes:</span>
              <span className="farmer-tech-val codes-list">
                {activeReasonCodes.join(', ')}
              </span>
            </div>
            <div className="farmer-tech-action">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setViewMode('expert')}
              >
                <span>Switch to 🔬 Expert View for full mathematical breakdown</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/* ==========================================================================
   2. 🔬 EXPERT VIEW — Structured Multi-Tier Research Explanation
   ========================================================================== */

const ExpertExplainabilityView: React.FC<ViewProps> = ({ scenarioResult }) => {
  const { t } = useViewMode();
  const {
    scenario_id,
    n_farmers,
    available_water_m3,
    total_demand_m3,
    final_allocation,
    initial_allocation,
    explanations,
    final_decision,
  } = scenarioResult;

  const {
    summary,
    prediction_explanations = [],
    conflict_explanations = [],
    allocation_explanations = [],
    fairness_explanation,
    constraint_explanations = [],
    negotiation_explanation,
    all_reason_codes = [],
    data_disclaimer,
  } = explanations || {};

  const totalAllocated = final_allocation?.total_allocated_m3 ?? initial_allocation?.total_allocated_m3 ?? 0;
  const solverStatus = final_allocation?.solver_status || initial_allocation?.solver_status || null;
  const agreementStatus = final_decision?.agreement_status || scenarioResult.negotiation?.agreement_status || null;
  const fairnessScore = final_decision?.fairness_score ?? final_allocation?.fairness_score ?? null;

  // Format allocation method using actual backend value
  const rawMethod = final_allocation?.allocation_method || initial_allocation?.allocation_method || 'lp_optimal';
  const formatAllocationMethod = (method: string) => {
    const lower = method.toLowerCase();
    if (lower.includes('optimal') || lower.includes('glop')) {
      return {
        label: 'Optimal constrained allocation',
        desc: 'The optimization process found a feasible allocation while respecting the defined water constraints.',
      };
    }
    if (lower.includes('relax')) {
      return {
        label: 'Allocation with relaxed minimum requirements',
        desc: 'Minimum survival requirements were relaxed to maintain mathematical feasibility under severe deficit.',
      };
    }
    if (lower.includes('proportional')) {
      return {
        label: 'Proportional fallback allocation',
        desc: 'Water was distributed proportionally to demand as a fallback under constraint violation.',
      };
    }
    return {
      label: method,
      desc: 'The optimization process distributed available water subject to active allocation constraints.',
    };
  };

  const methodMeta = formatAllocationMethod(rawMethod);
  const groupedConflicts = groupConflicts(conflict_explanations.length > 0 ? conflict_explanations : scenarioResult.conflicts?.conflicts);

  return (
    <div style={{ maxWidth: '1040px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="page-heading">
        <h1 className="page-title">{t('explainExpertPageTitle')}</h1>
        <p className="page-description">{t('explainExpertPageSubtitle')}</p>
      </div>

      {/* 1. DECISION SUMMARY */}
      <div className="card" style={{ borderLeft: '4px solid var(--color-primary)' }}>
        <div className="card-header">
          <div className="card-title">
            <Lightbulb size={18} style={{ color: 'var(--color-primary)' }} />
            1. Decision Summary
          </div>
          <Badge variant="neutral">Scenario: {scenario_id}</Badge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', margin: '14px 0' }}>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Farmers</div>
            <div style={{ fontSize: '18px', fontWeight: 700 }}>{n_farmers}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Available Supply</div>
            <div style={{ fontSize: '18px', fontWeight: 700 }}>{formatWater(available_water_m3)}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Predicted Demand</div>
            <div style={{ fontSize: '18px', fontWeight: 700 }}>{formatWater(total_demand_m3)}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Total Allocated</div>
            <div style={{ fontSize: '18px', fontWeight: 700 }}>{formatWater(totalAllocated)}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Solver Status</div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-primary)' }}>{solverStatus || 'Not available'}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Agreement Status</div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#15803d' }}>{agreementStatus || 'Not available'}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Fairness Score</div>
            <div style={{ fontSize: '18px', fontWeight: 700 }}>{fairnessScore != null ? fairnessScore.toFixed(3) : 'Not available'}</div>
          </div>
        </div>

        {/* Human-readable allocation method card */}
        <div style={{ padding: '12px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', marginTop: '10px' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
            Allocation Method: {methodMeta.label}
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-main)', marginTop: '2px' }}>
            {methodMeta.desc}
          </p>
        </div>

        <p style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-main)', marginTop: '14px' }}>
          {summary || final_decision?.summary || 'Mediation decision reached based on agronomic LP optimization and agent utility.'}
        </p>

        {/* Reason code tags */}
        <div style={{ marginTop: '14px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {all_reason_codes.map((code) => (
            <span key={code} style={{ fontSize: '11px', fontFamily: 'monospace', padding: '3px 8px', borderRadius: '4px', backgroundColor: '#e2e8f0', color: '#334155' }}>
              {code}
            </span>
          ))}
        </div>
      </div>

      {/* 2. WHY WATER WAS NEEDED */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">2. Why Water Was Needed</div>
            <div className="card-subtitle">Farmer-by-farmer agronomic requirements and feature contributions</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {prediction_explanations.map((pe) => {
            const rawId = pe.farmer_id || 'Farmer';
            const displayTitle = rawId
              .replace(/^farm_0*/i, 'Farmer ')
              .replace(/^farmer_0*/i, 'Farmer ')
              .toUpperCase();

            return (
              <div
                key={pe.farmer_id || 'farmer'}
                style={{ padding: '14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}
              >
                <h3 style={{ fontSize: '15px', fontWeight: 700, margin: '0 0 10px 0', color: 'var(--color-primary-dark)' }}>
                  {displayTitle}
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', marginBottom: '12px' }}>
                  <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Predicted water need:</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                      {formatWater(pe.predicted_demand_m3)}
                    </div>
                  </div>
                  <div style={{ padding: '8px 12px', background: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Model:</div>
                    <div style={{ fontSize: '15px', fontWeight: 600 }}>
                      {pe.model_name || 'XGBoost'}
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-subtle)', marginBottom: '4px', textTransform: 'uppercase' }}>
                  Technical explanation
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 10px 0' }}>
                  {pe.summary}
                </p>

                {/* SHAP explanation if available */}
                {pe.shap_available && pe.top_contributors && pe.top_contributors.length > 0 ? (
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-subtle)', marginBottom: '6px' }}>
                      Top Influencing Factors (SHAP Attribution)
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
                      {pe.top_contributors.map((c) => (
                        <div
                          key={c.feature}
                          style={{
                            fontSize: '12px',
                            padding: '6px 10px',
                            borderRadius: '4px',
                            background: '#ffffff',
                            border: '1px solid var(--border-subtle)',
                          }}
                        >
                          <span style={{ fontWeight: 600 }}>{c.feature}</span>:{' '}
                          <span style={{ color: c.direction === 'increases' ? '#c2410c' : '#087e8b' }}>
                            {c.direction === 'increases' ? '▲ increases' : '▼ decreases'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: 'var(--text-subtle)', fontStyle: 'italic', marginTop: '6px' }}>
                    {t('shapUnavailableText')}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. WHAT PROBLEMS WERE DETECTED? (Conflict Diagnosis) */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">3. What Problems Were Detected?</div>
            <div className="card-subtitle">Grouped conflict categories, severity distributions, and impacted farmers</div>
          </div>
        </div>

        {groupedConflicts.length === 0 ? (
          <div style={{ color: 'var(--text-subtle)', fontStyle: 'italic', padding: '12px' }}>
            No conflicts detected in this scenario. Water supply satisfies all requirements.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {groupedConflicts.map((group) => (
              <div
                key={group.key}
                style={{ padding: '14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px' }}>{group.expertTitle}</span>
                    <Badge variant={group.highestSeverity === 'CRITICAL' ? 'critical' : group.highestSeverity === 'HIGH' ? 'high' : 'warning'}>
                      {group.highestSeverity}
                    </Badge>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600 }}>Detected: {group.count}</span>
                    <span style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-subtle)', background: '#e2e8f0', padding: '2px 6px', borderRadius: '4px' }}>
                      Technical code: {group.technicalCode}
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '8px', lineHeight: '1.4' }}>
                  {group.expertExplanation}
                </p>

                {group.involvedFarmers.length > 0 && (
                  <div style={{ fontSize: '11px', color: 'var(--text-subtle)', marginTop: '6px' }}>
                    Involved Farmers: {group.involvedFarmers.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. HOW WAS WATER ALLOCATED? (Optimization Logic) */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">4. How Was Water Allocated?</div>
            <div className="card-subtitle">GLOP Linear Program constraint verification and feasibility guarantees</div>
          </div>
        </div>

        {/* Info Grid: Available water, Total demand, Total allocation, Allocation method, Solver status, Fairness measurement */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px', margin: '14px 0' }}>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Available water</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }}>{formatWater(available_water_m3)}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Total demand</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }}>{formatWater(total_demand_m3)}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Total allocation</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }}>{formatWater(totalAllocated)}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Allocation method</div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-primary)' }}>{methodMeta.label}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Solver status</div>
            <div style={{ fontSize: '14px', fontWeight: 700 }}>{solverStatus || 'Not available'}</div>
          </div>
          <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Fairness measurement</div>
            <div style={{ fontSize: '14px', fontWeight: 700 }}>Jain's: {fairnessScore != null ? fairnessScore.toFixed(3) : 'Not available'}</div>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-main)', marginBottom: '14px' }}>
          The optimizer distributed available water subject to the project's allocation constraints.
        </p>

        {/* Global LP Constraints */}
        {constraint_explanations.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
            {constraint_explanations.map((ce, idx) => (
              <div
                key={`${ce.constraint_name}-${idx}`}
                style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, fontSize: '12px' }}>{ce.constraint_name}</span>
                  <Badge variant={ce.status === 'satisfied' ? 'success' : 'warning'}>
                    {ce.status.toUpperCase()}
                  </Badge>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                  {ce.rationale}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Fairness Note */}
        {fairness_explanation && (
          <div style={{ marginTop: '16px', padding: '12px', background: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-primary-dark)' }}>
              Fairness Measurement: Jain's Index = {fairness_explanation.fairness_score.toFixed(4)}
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              {fairness_explanation.rationale}
            </p>
          </div>
        )}
      </div>

      {/* 5. WHY DID DIFFERENT FARMERS RECEIVE DIFFERENT AMOUNTS? */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">5. Why Did Different Farmers Receive Different Amounts?</div>
            <div className="card-subtitle">Causal allocation factors: urgency, crop sensitivity, minimum survival, and active constraints</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {allocation_explanations.map((ae) => (
            <div
              key={ae.farmer_id}
              style={{ padding: '14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{ae.farmer_id}</span>
                <span style={{ fontWeight: 600 }}>
                  Allocated: <strong>{formatWater(ae.allocated_m3)}</strong> / {formatWater(ae.predicted_demand_m3)} ({((ae.satisfaction_ratio || 0) * 100).toFixed(1)}%)
                </span>
              </div>

              <p style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '6px' }}>
                {ae.rationale || 'The allocation reflects a combination of predicted demand, urgency, crop sensitivity and the active constraints.'}
              </p>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px', fontSize: '12px', color: 'var(--text-subtle)' }}>
                <span>Urgency: <strong>{ae.urgency?.toFixed(2) ?? 'N/A'}</strong></span>
                <span>•</span>
                <span>Crop Sensitivity: <strong>{ae.crop_sensitivity?.toFixed(2) ?? 'N/A'}</strong></span>
                <span>•</span>
                <span>Min Requirement: <strong>{formatWater(ae.minimum_requirement_m3)}</strong></span>
              </div>

              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                {ae.reason_codes.map((rc) => (
                  <span key={rc} style={{ fontSize: '11px', fontFamily: 'monospace', padding: '2px 6px', background: '#e2e8f0', borderRadius: '4px' }}>
                    {rc}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. NEGOTIATION / MEDIATION */}
      {negotiation_explanation && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">6. Negotiation / Mediation</div>
              <div className="card-subtitle">Concession trajectories, BATNA protection, and Nash-inspired bargaining metric</div>
            </div>
          </div>

          <p style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.5', marginBottom: '14px' }}>
            {negotiation_explanation.summary}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px', marginBottom: '16px' }}>
            <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Number of rounds</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>{negotiation_explanation.n_rounds}</div>
            </div>
            <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Termination status</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#15803d' }}>{negotiation_explanation.agreement_status}</div>
            </div>
            {negotiation_explanation.round_explanations?.[0] && (() => {
              const lastRound = negotiation_explanation.round_explanations[
                negotiation_explanation.round_explanations.length - 1
              ] as Record<string, any> | undefined;
              return (
                <>
                  <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Acceptances</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#15803d' }}>
                      {Number(lastRound?.n_accepting ?? 0)}
                    </div>
                  </div>
                  <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Requested Changes</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#d97706' }}>
                      {Number(lastRound?.n_requesting_change ?? 0)}
                    </div>
                  </div>
                  <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Rejections</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#dc2626' }}>
                      {Number(lastRound?.n_rejecting ?? 0)}
                    </div>
                  </div>
                </>
              );
            })()}
            <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Concessions</div>
              <div style={{ fontSize: '14px', fontWeight: 700 }}>
                {negotiation_explanation.concession_explanations?.length ?? 0} recorded
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
            {/* BATNA Definition */}
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-primary-dark)' }}>
                BATNA
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                "Minimum acceptable alternative used by the negotiation logic."
              </p>
              {negotiation_explanation.batna_explanations?.length > 0 && (
                <div style={{ fontSize: '11px', color: 'var(--text-subtle)', marginTop: '6px' }}>
                  Protection verified for {negotiation_explanation.batna_explanations.length} farmer agents.
                </div>
              )}
            </div>

            {/* Nash-inspired objective */}
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-primary-dark)' }}>
                Nash-inspired objective
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                "The system's negotiation objective uses a surplus-based logarithmic formulation inspired by Nash bargaining. It is not a full Nash Bargaining Solution."
              </p>
              {negotiation_explanation.nash_objective_explanation && (
                <div style={{ fontSize: '11px', color: 'var(--text-subtle)', marginTop: '4px', fontStyle: 'italic' }}>
                  Formula: {negotiation_explanation.nash_objective_explanation.formula}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 7. FINAL DECISION */}
      <div className="card" style={{ borderLeft: '4px solid #15803d', background: '#f0fdf4' }}>
        <div className="card-header">
          <div className="card-title" style={{ color: '#166534' }}>
            🤝 Final Water-Sharing Agreement
          </div>
          <Badge variant="success">Status: {agreementStatus || 'Not available'}</Badge>
        </div>
        <div style={{ marginTop: '8px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#166534', marginBottom: '4px' }}>
            Why?
          </div>
          <p style={{ fontSize: '13px', color: '#166534', lineHeight: '1.6', margin: 0 }}>
            Available water was lower than total demand. The system therefore had to allocate water under constraints. Crop needs, urgency, sensitivity and other constraints were considered. The resulting allocation was evaluated by the farmer agents and the final agreement status was recorded.
          </p>
        </div>
      </div>

      {/* Link to Raw API Payload (Separated Developer View) */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
        <Link to="/debug" className="btn btn-outline btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <Code2 size={14} />
          <span>View Raw API Payload (Developer / Audit)</span>
          <ExternalLink size={12} />
        </Link>
      </div>

      {/* Disclaimer */}
      <div className="alert alert-disclaimer">
        {data_disclaimer ||
          'All explanations are generated deterministically from synthetic agronomic simulation data. No real farmer records are used.'}
      </div>
    </div>
  );
};
