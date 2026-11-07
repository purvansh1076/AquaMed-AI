/**
 * AquaMedi AI — Application Header (Government Department Style)
 * ==============================================================
 * Formal department-portal layout:
 * - Title: AquaMedi AI
 * - Subtitle: Agricultural Water Management System
 * - Navigation breadcrumb
 * - User login information
 * - Language selection (English, हिन्दी, ગુજરાતી, मराठी)
 * - Backend health status indicator
 * No fake Government of India emblems, official seals, or claims of authorization.
 */

import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { RefreshCw, Languages, LogOut, User } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { useAuth } from '../context/AuthContext';
import type { Language } from '../i18n/translations';

// Map route paths to human-readable names
const ROUTE_LABELS: Record<string, string> = {
  '/overview':       'Dashboard Overview',
  '/scenario':       'Scenario Configuration',
  '/predictions':    'ML Predictions',
  '/conflicts':      'Water Dispute Mediation',
  '/allocation':     'LP Water Allocation',
  '/negotiation':    'Negotiation Engine',
  '/explainability': 'SHAP Explainability',
  '/agreement':      'Final Agreement',
  '/debug':          'Debug / Raw API',
  '/reports':        'Reports & Documentation',
  '/farmer':         'Water Sharing',
  '/farmer-portal':  'Farmer Portal',
  '/farmer/portal':  'Farmer Portal',
};

export const Header: React.FC = () => {
  const { health, healthStatus, checkHealth } = useScenario();
  const { viewMode, language, setLanguage, t } = useViewMode();
  const { logout, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const currentLabel = ROUTE_LABELS[location.pathname] || t('appTitle');
  const userDisplayName = user?.full_name || user?.email || (isAuthenticated ? 'Agricultural Officer' : 'Guest');

  return (
    <header
      className="app-header"
      style={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #D9E0E7',
        height: '60px',
        minHeight: '60px',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'none',
      }}
    >
      {/* ── Left: Portal Identity & Breadcrumb ── */}
      <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '16px',
                fontWeight: 800,
                color: '#12315B',
                letterSpacing: '-0.2px',
              }}
            >
              AquaMedi AI
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: '#176B45',
                backgroundColor: '#eaf5ef',
                border: '1px solid #b8e2cd',
                padding: '1px 6px',
                borderRadius: '2px',
              }}
            >
              PORTAL
            </span>
          </div>
          <span
            style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontWeight: 500,
            }}
          >
            Agricultural Water Management System
          </span>
        </div>

        <div style={{ width: '1px', height: '28px', backgroundColor: '#D9E0E7' }} />

        {/* Breadcrumb Navigation */}
        <nav className="gov-breadcrumb" aria-label="Breadcrumb">
          <span className="gov-breadcrumb-item">AquaMedi AI</span>
          <span className="gov-breadcrumb-sep">›</span>
          <span className="gov-breadcrumb-item active">{currentLabel}</span>
        </nav>
      </div>

      {/* ── Center: View Mode Indicator Badge (Maintains Test Compatibility) ── */}
      <div className="header-center">
        <span
          className={`view-mode-badge ${viewMode === 'farmer' ? 'farmer-mode' : 'expert-mode'}`}
          style={{
            fontSize: '12px',
            fontWeight: 600,
            padding: '4px 10px',
            borderRadius: '3px',
            backgroundColor: viewMode === 'farmer' ? '#eaf5ef' : '#eef3f9',
            color: viewMode === 'farmer' ? '#176B45' : '#12315B',
            border: `1px solid ${viewMode === 'farmer' ? '#b8e2cd' : '#c8d8ec'}`,
          }}
        >
          {viewMode === 'farmer' ? '🌾 Farmer Mode' : '🛡 Expert Mode'}
        </span>
      </div>

      {/* ── Right: Language, Health, User Profile & Actions ── */}
      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Language Selector */}
        <div className="language-selector-wrapper">
          <Languages size={14} className="language-icon" style={{ color: '#12315B' }} />
          <select
            id="app-language-select"
            className="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            aria-label="Interface Language"
            style={{
              border: '1px solid #D9E0E7',
              borderRadius: '3px',
              padding: '4px 8px',
              fontSize: '12px',
              color: '#263445',
              backgroundColor: '#FFFFFF',
            }}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="gu">ગુજરાતી</option>
            <option value="mr">मराठी</option>
          </select>
        </div>

        {/* Backend Health Status */}
        <div
          className={`health-badge ${healthStatus}`}
          onClick={checkHealth}
          title={
            healthStatus === 'connected'
              ? `FastAPI Backend v${health?.version || '1.0.0'} (${health?.pipeline || 'pipeline active'})`
              : 'FastAPI Backend Offline. Click to retry.'
          }
          style={{
            cursor: 'pointer',
            padding: '4px 8px',
            border: '1px solid #D9E0E7',
            borderRadius: '3px',
            backgroundColor: '#F5F7F9',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
          }}
        >
          <div className="health-dot" />
          <span style={{ fontWeight: 600 }}>
            {healthStatus === 'connected' && t('apiConnected')}
            {healthStatus === 'offline'   && t('backendOffline')}
            {healthStatus === 'checking'  && t('checkingApi')}
          </span>
          <RefreshCw size={11} style={{ opacity: 0.6 }} />
        </div>

        {/* User Login Information */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '3px 8px',
            border: '1px solid #D9E0E7',
            borderRadius: '3px',
            backgroundColor: '#F5F7F9',
            fontSize: '12px',
            color: '#12315B',
          }}
        >
          <User size={13} />
          <span style={{ fontWeight: 600 }}>{userDisplayName}</span>
        </div>

        {/* Expert Actions */}
        {(viewMode === 'expert' || isAuthenticated) && (
          <div style={{ display: 'flex', gap: '6px' }}>
            <Link
              to="/scenario"
              className="btn btn-sm"
              style={{
                backgroundColor: '#176B45',
                color: '#FFFFFF',
                border: '1px solid #176B45',
                padding: '4px 10px',
                borderRadius: '3px',
                fontSize: '12px',
                textDecoration: 'none',
                fontWeight: 600,
              }}
            >
              New Scenario
            </Link>

            <button
              type="button"
              onClick={handleLogout}
              className="btn btn-sm"
              style={{
                backgroundColor: '#FFFFFF',
                color: '#B42318',
                borderColor: '#f8c9c7',
                border: '1px solid #f8c9c7',
                padding: '4px 8px',
                borderRadius: '3px',
                fontSize: '12px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <LogOut size={13} />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
