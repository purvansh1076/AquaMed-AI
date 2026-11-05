/**
 * AquaMediAI — Government-Grade Header Component
 * ==============================================
 * Inspired by NSW Government design principles:
 * - Clear organizational identity and trust badges.
 * - Prominent display of the verified production model: XGBoost.
 * - Centralized multilingual switcher (English, Hindi, Gujarati, Marathi).
 * - Clear visual indication of active role (Farmer Guest vs Authenticated Expert).
 */

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Droplets, Shield, User, LogOut, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useViewMode } from '../../context/ViewModeContext';
import type { Language } from '../../i18n/translations';

export const GovernmentHeader: React.FC = () => {
  const { role, user, logout } = useAuth();
  const { language, setLanguage, t } = useViewMode();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="gov-header-wrapper" role="banner">
      {/* Top Official Authority Strip */}
      <div className="gov-top-banner">
        <div className="gov-top-banner-content">
          <span className="gov-emblem-badge">
            <span className="badge-dot" />
            {t('governmentBadge')}
          </span>
          <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
          <span style={{ fontSize: '11px', color: '#cbd5e1' }}>
            Decision Support & Dispute Mediation Platform
          </span>
        </div>

        <div className="gov-top-banner-right">
          {/* Active Model Pill - Locked to XGBoost */}
          <div className="active-model-pill" title="Verified active production regressor">
            <CheckCircle2 size={12} style={{ color: '#34d399' }} />
            <span>Active Model: XGBoost</span>
          </div>

          {/* Centralized Language Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <label htmlFor="gov-lang-select" style={{ fontSize: '11px', color: '#94a3b8' }}>
              Language:
            </label>
            <select
              id="gov-lang-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
                fontSize: '11px',
                padding: '2px 6px',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="en" style={{ color: '#0f172a' }}>English (EN)</option>
              <option value="hi" style={{ color: '#0f172a' }}>हिन्दी (HI)</option>
              <option value="gu" style={{ color: '#0f172a' }}>ગુજરાતી (GU)</option>
              <option value="mr" style={{ color: '#0f172a' }}>मराठी (MR)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Government Header Bar */}
      <div className="gov-header">
        <div className="gov-header-inner">
          <Link to="/" className="gov-branding-block">
            <div className="gov-logo-box">
              <Droplets size={26} strokeWidth={2.2} />
            </div>
            <div className="gov-title-group">
              <h1>AquaMediAI</h1>
              <p>Water-Sharing Dispute Mediation & Agricultural Intelligence</p>
            </div>
          </Link>

          <div className="gov-header-controls">
            {/* Session Indicator Pill */}
            {role === 'expert' && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#eff6ff',
                  border: '1px solid #bfdbfe',
                  padding: '5px 12px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  color: '#1e40af',
                  fontWeight: 600,
                }}
              >
                <Shield size={14} style={{ color: '#2563eb' }} />
                <span>{user?.full_name || t('expertModeActive')}</span>
                <button
                  onClick={handleLogout}
                  className="btn-gov-outline"
                  style={{
                    padding: '2px 8px',
                    fontSize: '11px',
                    marginLeft: '4px',
                    borderRadius: '12px',
                  }}
                  title="Sign out of expert session"
                >
                  <LogOut size={12} />
                  <span>{t('logoutBtn')}</span>
                </button>
              </div>
            )}

            {role === 'farmer_guest' && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  padding: '5px 12px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  color: '#166534',
                  fontWeight: 600,
                }}
              >
                <User size={14} style={{ color: '#16a34a' }} />
                <span>{t('farmerModeActive')}</span>
                <button
                  onClick={handleLogout}
                  className="btn-gov-outline"
                  style={{
                    padding: '2px 8px',
                    fontSize: '11px',
                    marginLeft: '4px',
                    borderRadius: '12px',
                  }}
                  title="Exit farmer guest session"
                >
                  <LogOut size={12} />
                  <span>Exit</span>
                </button>
              </div>
            )}

            {!role && (
              <Link to="/login" className="btn-gov-navy" style={{ padding: '7px 14px', fontSize: '13px' }}>
                <Shield size={14} />
                <span>Expert Sign-In</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
