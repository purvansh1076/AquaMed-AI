/**
 * AquaMedi AI — Premium Government-Grade Welcome & Role-Selection Page
 * =====================================================================
 * Official government-grade landing portal with two distinct access paths:
 * A. Farmer Portal: Frictionless guest entry with no credentials required.
 * B. Expert Portal: Authenticated access for government agricultural specialists.
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
  Scale,
  Languages,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useViewMode } from '../context/ViewModeContext';
import type { Language } from '../i18n/translations';

export const WelcomePage: React.FC = () => {
  const { continueAsFarmer, isLoading } = useAuth();
  const { setViewMode, language, setLanguage } = useViewMode();
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
    <div className="welcome-page-layout">
      {/* Government Department Research Banner */}
      <div className="gov-top-banner-navy">
        <span>Department of Agriculture &amp; Farmers Welfare — Research Reference System (Ministry of Agriculture &amp; Farmers Welfare Guidelines)</span>
        <span style={{ opacity: 0.8, fontSize: '11px' }}>
          Decision Support System — Not an Official Government Portal
        </span>
      </div>

      {/* Premium Government Header */}
      <header className="welcome-gov-header">
        <div className="welcome-gov-header-inner">
          <div className="welcome-logo-block">
            <div className="welcome-logo-icon-box">
              <Droplets size={24} />
            </div>
            <div className="welcome-logo-text">
              <h1>AquaMedi AI</h1>
              <p>Agricultural Intelligence &amp; Dispute Mediation System</p>
            </div>
          </div>

          <div className="welcome-header-right">
            {/* Language Selector */}
            <div className="language-selector-wrapper">
              <Languages size={14} className="language-icon" />
              <select
                className="language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
                aria-label="Interface Language"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="gu">ગુજરાતી</option>
                <option value="mr">मराठी</option>
              </select>
            </div>
            <span className="prototype-badge">
              <Award size={10} />
              Prototype Platform
            </span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="welcome-hero-section">
        <div className="welcome-hero-inner">
          <div className="hero-system-badge">
            <Droplets size={12} />
            AGRICULTURAL INTELLIGENCE &amp; DISPUTE MEDIATION SYSTEM
          </div>
          <h1 className="welcome-hero-title">
            Empowering Agriculture Through<br />Artificial Intelligence
          </h1>
          <p className="welcome-hero-subtitle">
            Intelligent Water Allocation, Crop Health Monitoring &amp; Agricultural Dispute Resolution
            powered by XGBoost ML, Linear Programming &amp; Multi-Agent Negotiation.
          </p>
          <div className="hero-icon-row">
            <Droplets size={28} color="rgba(255,255,255,0.7)" />
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '20px' }}>·</span>
            <Sprout size={28} color="rgba(255,255,255,0.7)" />
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '20px' }}>·</span>
            <Scale size={28} color="rgba(255,255,255,0.7)" />
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '20px' }}>·</span>
            <BarChart3 size={28} color="rgba(255,255,255,0.7)" />
          </div>
        </div>
      </section>

      {/* Role Cards Section */}
      <section className="welcome-cards-section">
        <div className="welcome-cards-inner">
          <p className="welcome-section-label">Select Your Access Portal</p>

          <div className="welcome-role-grid">
            {/* Farmer Card */}
            <div className="role-card-v2 farmer-card" id="role-card-farmer">
              <div className="role-card-v2-header">
                <div className="role-icon-v2 green">
                  <Sprout size={28} />
                </div>
                <div className="role-card-v2-meta">
                  <span className="role-card-v2-badge green">Free Access</span>
                  <div className="role-card-v2-title">Farmer Portal</div>
                </div>
              </div>

              <p className="role-card-v2-desc">
                Access your personalised water demand calculator, crop health insights, and
                water-sharing status — no login required.
              </p>

              <ul className="role-features-v2">
                <li>
                  <CheckCircle2 size={16} className="check-green" />
                  <span>Instant access — no username or password needed</span>
                </li>
                <li>
                  <CheckCircle2 size={16} className="check-green" />
                  <span>Calculates today's exact crop water requirement (m³)</span>
                </li>
                <li>
                  <CheckCircle2 size={16} className="check-green" />
                  <span>Simple, plain-language agricultural recommendations</span>
                </li>
                <li>
                  <CheckCircle2 size={16} className="check-green" />
                  <span>Localized weather &amp; soil moisture insights</span>
                </li>
              </ul>

              <button
                onClick={handleFarmerEntry}
                disabled={isLoading}
                className="btn-gov-primary"
                id="continue-farmer-btn"
                style={{ width: '100%' }}
              >
                <span>{isLoading ? 'Preparing Session...' : 'Enter Farmer Portal'}</span>
                <ArrowRight size={16} />
              </button>
            </div>

            {/* Expert Card */}
            <div className="role-card-v2 expert-card" id="role-card-expert">
              <div className="role-card-v2-header">
                <div className="role-icon-v2 navy">
                  <ShieldCheck size={28} />
                </div>
                <div className="role-card-v2-meta">
                  <span className="role-card-v2-badge navy">Authorized Personnel</span>
                  <div className="role-card-v2-title">Expert Portal</div>
                </div>
              </div>

              <p className="role-card-v2-desc">
                Full analytical suite for agricultural experts, irrigation engineers, and
                government mediators — secured with role-based access control.
              </p>

              <ul className="role-features-v2">
                <li>
                  <CheckCircle2 size={16} className="check-navy" />
                  <span>Multi-agent dispute mediation &amp; concession tracking</span>
                </li>
                <li>
                  <CheckCircle2 size={16} className="check-navy" />
                  <span>Linear programming (LP) optimal water allocation</span>
                </li>
                <li>
                  <CheckCircle2 size={16} className="check-navy" />
                  <span>Verified production XGBoost regressor (R² = 0.9699)</span>
                </li>
                <li>
                  <CheckCircle2 size={16} className="check-navy" />
                  <span>SHAP game-theoretic explainability &amp; audit export</span>
                </li>
              </ul>

              <button
                onClick={handleExpertEntry}
                className="btn-gov-navy"
                id="login-expert-btn"
                style={{ width: '100%' }}
              >
                <Lock size={16} />
                <span>Expert Login</span>
              </button>
            </div>
          </div>

          {/* Trust Pillars */}
          <div className="welcome-trust-section" style={{ margin: '0 -28px -48px', padding: '36px 28px' }}>
            <div className="welcome-trust-inner">
              <div className="trust-pillar-v2">
                <div className="trust-pillar-v2-icon">
                  <Cpu size={20} />
                </div>
                <div className="trust-pillar-v2-text">
                  <h4>Verified ML Engine</h4>
                  <p>Production XGBoost Regressor with FAO-56 dual crop coefficients.</p>
                </div>
              </div>
              <div className="trust-pillar-v2">
                <div className="trust-pillar-v2-icon">
                  <BarChart3 size={20} />
                </div>
                <div className="trust-pillar-v2-text">
                  <h4>Fair Multi-Agent Mediation</h4>
                  <p>Iterative utility-based concessions ensuring no farmer falls below minimums.</p>
                </div>
              </div>
              <div className="trust-pillar-v2">
                <div className="trust-pillar-v2-icon">
                  <Droplets size={20} />
                </div>
                <div className="trust-pillar-v2-text">
                  <h4>Physical Threshold Clamping</h4>
                  <p>Inference bounded by physical soil water capacity and plant physiology.</p>
                </div>
              </div>
              <div className="trust-pillar-v2">
                <div className="trust-pillar-v2-icon">
                  <Lock size={20} />
                </div>
                <div className="trust-pillar-v2-text">
                  <h4>Server-Side RBAC</h4>
                  <p>Cryptographically signed session tokens and brute-force lockout defense.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Government Footer */}
      <footer className="gov-footer">
        <div className="gov-footer-inner">
          <div className="gov-footer-brand">AquaMedi AI — Agricultural Intelligence Platform</div>
          <div>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.65)' }}>
              Prototype Research Platform — Ministry of Agriculture Reference Project
            </div>
            <div className="gov-footer-disclaimer">
              Not an official Government of India portal
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
