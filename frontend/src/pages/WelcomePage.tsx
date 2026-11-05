/**
 * AquaMediAI — Welcome & Role-Selection Entry Experience
 * ======================================================
 * Official government-grade landing portal providing two distinct paths:
 * A. Frictionless Farmer Access: Immediate guest entry with no credentials.
 * B. Agricultural Expert Access: Authenticated entry for government specialists.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sprout,
  ShieldCheck,
  Droplets,
  CheckCircle2,
  ArrowRight,
  Lock,
  Cpu,
  BarChart3,
  Award,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useViewMode } from '../context/ViewModeContext';

export const WelcomePage: React.FC = () => {
  const { continueAsFarmer, isLoading } = useAuth();
  const { setViewMode, t } = useViewMode();
  const navigate = useNavigate();

  const handleFarmerEntry = async () => {
    setViewMode('farmer');
    await continueAsFarmer();
    navigate('/farmer-portal');
  };

  const handleExpertEntry = () => {
    navigate('/login');
  };

  return (
    <div className="welcome-screen">
      {/* Hero Header */}
      <div className="welcome-hero">
        <div className="welcome-badge-strip">
          <Award size={14} style={{ color: '#1b4332' }} />
          <span>Agricultural Intelligence & Dispute Mediation System</span>
        </div>
        <h1 className="welcome-title">{t('welcomePortalTitle')}</h1>
        <p className="welcome-subtitle">{t('welcomePortalSubtitle')}</p>
      </div>

      {/* Role Selection Prompt */}
      <p
        style={{
          fontSize: '15px',
          fontWeight: 700,
          color: '#1e293b',
          marginBottom: '24px',
          letterSpacing: '-0.2px',
        }}
      >
        {t('welcomeRolePrompt')}
      </p>

      {/* Two Entry Role Cards */}
      <div className="welcome-cards-grid">
        {/* Card A: Farmer Access */}
        <div className="role-card role-card-farmer" id="role-card-farmer">
          <div className="role-card-header">
            <div className="role-icon-box role-icon-farmer">
              <Sprout size={28} />
            </div>
            <div>
              <span className="role-badge badge-farmer">{t('farmerCardBadge')}</span>
              <h2 className="role-title">{t('farmerCardTitle')}</h2>
            </div>
          </div>

          <p className="role-desc">{t('farmerCardDesc')}</p>

          <ul className="role-features-list">
            <li>
              <CheckCircle2 size={16} />
              <span>Instant access — no username or password needed</span>
            </li>
            <li>
              <CheckCircle2 size={16} />
              <span>Calculates today's exact crop water requirement (m³)</span>
            </li>
            <li>
              <CheckCircle2 size={16} />
              <span>Simple, plain-language agricultural recommendations</span>
            </li>
            <li>
              <CheckCircle2 size={16} />
              <span>Localized weather & soil moisture insights</span>
            </li>
          </ul>

          <button
            onClick={handleFarmerEntry}
            disabled={isLoading}
            className="btn-gov-primary"
            id="continue-farmer-btn"
            style={{ width: '100%' }}
          >
            <span>{isLoading ? 'Preparing Session...' : t('farmerCardBtn')}</span>
            <ArrowRight size={16} />
          </button>
        </div>

        {/* Card B: Agricultural Expert Access */}
        <div className="role-card role-card-expert" id="role-card-expert">
          <div className="role-card-header">
            <div className="role-icon-box role-icon-expert">
              <ShieldCheck size={28} />
            </div>
            <div>
              <span className="role-badge badge-expert">{t('expertCardBadge')}</span>
              <h2 className="role-title">{t('expertCardTitle')}</h2>
            </div>
          </div>

          <p className="role-desc">{t('expertCardDesc')}</p>

          <ul className="role-features-list expert-features">
            <li>
              <CheckCircle2 size={16} />
              <span>Multi-agent dispute mediation and concession tracking</span>
            </li>
            <li>
              <CheckCircle2 size={16} />
              <span>Linear programming (LP) optimal water allocation</span>
            </li>
            <li>
              <CheckCircle2 size={16} />
              <span>Verified production XGBoost regressor (R² = 0.9699)</span>
            </li>
            <li>
              <CheckCircle2 size={16} />
              <span>SHAP game-theoretic explainability & audit export</span>
            </li>
          </ul>

          <button
            onClick={handleExpertEntry}
            className="btn-gov-navy"
            id="login-expert-btn"
            style={{ width: '100%' }}
          >
            <Lock size={16} />
            <span>{t('expertCardBtn')}</span>
          </button>
        </div>
      </div>

      {/* Trust & Scientific Architecture Row */}
      <div className="welcome-trust-row">
        <div className="trust-pillar">
          <Cpu size={22} className="trust-pillar-icon" />
          <div className="trust-pillar-text">
            <h4>Verified ML Engine</h4>
            <p>Production XGBoost Regressor with FAO-56 dual crop coefficients.</p>
          </div>
        </div>

        <div className="trust-pillar">
          <BarChart3 size={22} className="trust-pillar-icon" />
          <div className="trust-pillar-text">
            <h4>Fair Multi-Agent Mediation</h4>
            <p>Iterative utility-based concessions ensuring no farmer falls below critical minimums.</p>
          </div>
        </div>

        <div className="trust-pillar">
          <Droplets size={22} className="trust-pillar-icon" />
          <div className="trust-pillar-text">
            <h4>Physical Threshold Clamping</h4>
            <p>Inference bounded by physical soil water capacity and plant physiology.</p>
          </div>
        </div>

        <div className="trust-pillar">
          <Lock size={22} className="trust-pillar-icon" />
          <div className="trust-pillar-text">
            <h4>Server-Side RBAC</h4>
            <p>Cryptographically signed session tokens and brute-force lockout defense.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
