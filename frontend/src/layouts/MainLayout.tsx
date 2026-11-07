/**
 * AquaMedi AI — Main Application Layout (Redesign)
 * =================================================
 * Properly separates Farmer and Expert layouts:
 * - Farmer routes: No sidebar, full-width, farmer-specific header + nav bar
 * - Expert routes: Sidebar + Header (standard app shell)
 */

import React from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { Droplet, Sprout, Handshake, Languages, ArrowLeft } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { useAuth } from '../context/AuthContext';
import { FarmerViewPage } from '../pages/FarmerViewPage';
import { AlertBox } from '../components/common/AlertBox';
import type { Language } from '../i18n/translations';

export const MainLayout: React.FC = () => {
  const { healthStatus, error, clearError } = useScenario();
  const { viewMode, language, setLanguage, t } = useViewMode();
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  // Determine if we're on a farmer-specific route
  const isFarmerRoute =
    location.pathname === '/farmer' ||
    location.pathname.startsWith('/farmer/') ||
    location.pathname === '/farmer-portal';

  // Expert routes
  const isExpertRoute =
    location.pathname === '/overview' ||
    location.pathname === '/conflicts' ||
    location.pathname === '/predictions' ||
    location.pathname === '/allocation' ||
    location.pathname === '/negotiation' ||
    location.pathname === '/explainability' ||
    location.pathname === '/agreement' ||
    location.pathname === '/debug';

  const isFarmer = isFarmerRoute || (!isExpertRoute && viewMode === 'farmer' && !isAuthenticated);

  const isFarmerExplicitPage =
    location.pathname === '/farmer/portal' || location.pathname === '/farmer-portal';

  const showFarmerPage =
    isFarmer &&
    !isFarmerExplicitPage &&
    location.pathname !== '/scenario' &&
    location.pathname !== '/explainability';

  // ── Farmer Layout (no sidebar, full width) ──────────────────────────────
  if (isFarmer) {
    return (
      <div className="farmer-portal-layout">
        {/* Farmer Header Bar */}
        <div className="farmer-dashboard-header">
          <div className="farmer-dashboard-logo">
            <Droplet size={20} />
            <span>AquaMedi AI</span>
            <span
              style={{
                fontSize: '12px',
                fontWeight: 500,
                opacity: 0.75,
                marginLeft: '4px',
              }}
            >
              — Farmer Portal
            </span>
          </div>

          <div className="farmer-header-right">
            {/* Language Selector */}
            <div className="language-selector-wrapper">
              <Languages size={14} className="language-icon" />
              <select
                id="farmer-language-select"
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

            {/* Back to Portal Selection */}
            <Link
              to="/"
              className="farmer-header-home-btn"
              title="Return to Portal Selection"
              id="farmer-exit-portal-btn"
            >
              <ArrowLeft size={13} />
              <span>Portal Selection</span>
            </Link>
          </div>
        </div>

        {/* Farmer Navigation Tabs */}
        <nav className="farmer-nav-bar" aria-label="Farmer View Navigation">
          <Link
            to="/farmer"
            id="farmer-nav-sharing"
            className={`farmer-nav-item ${location.pathname === '/farmer' ? 'active' : ''}`}
          >
            <Droplet size={15} />
            <span>{t('myWaterSharing')}</span>
          </Link>
          <Link
            to="/farmer-portal"
            id="farmer-nav-portal"
            className={`farmer-nav-item ${
              location.pathname === '/farmer-portal' || location.pathname === '/farmer/portal'
                ? 'active'
                : ''
            }`}
          >
            <Sprout size={15} />
            <span>{t('farmerPortalTitle')}</span>
          </Link>
          <Link
            to="/scenario"
            id="farmer-nav-scenario"
            className={`farmer-nav-item ${location.pathname === '/scenario' ? 'active' : ''}`}
          >
            <Handshake size={15} />
            <span>Water Sharing Scenario</span>
          </Link>
        </nav>

        {/* Farmer Content */}
        <main className="app-content">
          <div className="content-container farmer-container">
            {healthStatus === 'offline' && (
              <AlertBox
                type="error"
                title="Backend Disconnected"
                message="FastAPI backend is unavailable. Start the AquaMediAI backend (uvicorn app.main:app on port 8000) and try again."
              />
            )}

            {error && (
              <div style={{ position: 'relative' }}>
                <AlertBox
                  type="error"
                  title="API Error"
                  message={error}
                  onDismiss={clearError}
                />
              </div>
            )}

            {showFarmerPage ? <FarmerViewPage /> : <Outlet />}
          </div>
        </main>
      </div>
    );
  }

  // ── Expert Layout (sidebar + header) ────────────────────────────────────
  return (
    <div className="app-layout expert-layout">
      <Sidebar />

      <div className="app-main">
        <Header />
        <main className="app-content">
          <div className="content-container">
            {healthStatus === 'offline' && (
              <AlertBox
                type="error"
                title="Backend Disconnected"
                message="FastAPI backend is unavailable. Start the AquaMediAI backend (uvicorn app.main:app on port 8000) and try again."
              />
            )}

            {error && (
              <div style={{ position: 'relative' }}>
                <AlertBox
                  type="error"
                  title="API Error"
                  message={error}
                  onDismiss={clearError}
                />
              </div>
            )}

            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
