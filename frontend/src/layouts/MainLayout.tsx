/**
 * AquaMedi AI — Main Application Layout (Redesign)
 * =================================================
 * Properly separates Farmer and Expert layouts:
 * - Farmer routes: No sidebar, full-width, farmer-specific header + nav bar
 * - Expert routes: Sidebar + Header (standard app shell)
 */

import React, { useState, useEffect } from 'react';
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
  const { viewMode, setViewMode, language, setLanguage, t } = useViewMode();
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  // Sidebar interactive state (persisted across sessions)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('aquamedi_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false);

  // Toggle handlers supporting Desktop (collapse rail) and Mobile (off-canvas drawer)
  const handleToggleSidebar = () => {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      setIsMobileOpen((prev) => !prev);
    } else {
      setIsSidebarCollapsed((prev) => {
        const next = !prev;
        try {
          localStorage.setItem('aquamedi_sidebar_collapsed', String(next));
        } catch {
          // ignore
        }
        return next;
      });
    }
  };

  const handleCloseMobile = () => {
    setIsMobileOpen(false);
  };

  // Keyboard accessibility: Escape key closes mobile drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileOpen) {
        setIsMobileOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileOpen]);

  // Route change automatically dismisses mobile navigation drawer
  useEffect(() => {
    setIsMobileOpen(false);
  }, [location.pathname]);

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
    location.pathname === '/crop-health' ||
    location.pathname === '/irrigation-advisory' ||
    location.pathname === '/reports' ||
    location.pathname === '/debug';

  // Ensure Expert Mode strictly defaults to English when navigating to expert routes
  useEffect(() => {
    if (isExpertRoute && viewMode !== 'expert') {
      setViewMode('expert');
    }
  }, [isExpertRoute, viewMode, setViewMode]);

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
    <div className={`app-layout expert-layout ${isSidebarCollapsed ? 'sidebar-collapsed' : 'sidebar-expanded'}`}>
      {/* Mobile Drawer Backdrop */}
      {isMobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={handleCloseMobile}
          aria-hidden="true"
        />
      )}

      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={handleToggleSidebar}
        mobileOpen={isMobileOpen}
        onCloseMobile={handleCloseMobile}
      />

      <div className="app-main">
        <Header
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={handleToggleSidebar}
        />
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
