import React from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { Droplet, Sprout, Handshake } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { FarmerViewPage } from '../pages/FarmerViewPage';
import { AlertBox } from '../components/common/AlertBox';

export const MainLayout: React.FC = () => {
  const { healthStatus, error, clearError } = useScenario();
  const { viewMode, t } = useViewMode();
  const location = useLocation();

  // Farmer view applies when viewMode is farmer OR on a farmer-specific route
  const isFarmerRoute =
    location.pathname === '/farmer' ||
    location.pathname.startsWith('/farmer/') ||
    location.pathname === '/farmer-portal';
  const isFarmer = viewMode === 'farmer' || isFarmerRoute;
  const isFarmerExplicitPage =
    location.pathname === '/farmer/portal' || location.pathname === '/farmer-portal';
  const showFarmerPage =
    isFarmer &&
    !isFarmerExplicitPage &&
    location.pathname !== '/scenario' &&
    location.pathname !== '/explainability';

  return (
    <div className={`app-layout ${isFarmer ? 'farmer-layout' : 'expert-layout'}`}>
      {/* Sidebar is exclusively for Expert View */}
      {!isFarmer && <Sidebar />}

      <div className="app-main">
        <Header />
        <main className="app-content">
          <div className={`content-container ${isFarmer ? 'farmer-container' : ''}`}>
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

            {isFarmer && (
              <nav
                className="farmer-nav-tabs"
                aria-label="Farmer View Navigation"
                style={{
                  display: 'flex',
                  gap: '8px',
                  marginBottom: '20px',
                  borderBottom: '1px solid var(--border-default)',
                  paddingBottom: '12px',
                  flexWrap: 'wrap',
                }}
              >
                <Link
                  to="/farmer"
                  id="farmer-nav-sharing"
                  className={`btn btn-sm ${
                    location.pathname === '/farmer' ? 'btn-primary' : 'btn-outline'
                  }`}
                  style={{ textDecoration: 'none', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Droplet size={14} />
                  <span>{t('myWaterSharing')}</span>
                </Link>
                <Link
                  to="/farmer-portal"
                  id="farmer-nav-portal"
                  className={`btn btn-sm ${
                    location.pathname === '/farmer-portal' || location.pathname === '/farmer/portal'
                      ? 'btn-primary'
                      : 'btn-outline'
                  }`}
                  style={{ textDecoration: 'none', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Sprout size={14} />
                  <span>{t('farmerPortalTitle')}</span>
                </Link>
                <Link
                  to="/scenario"
                  id="farmer-nav-scenario"
                  className={`btn btn-sm ${
                    location.pathname === '/scenario' ? 'btn-primary' : 'btn-outline'
                  }`}
                  style={{ textDecoration: 'none', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Handshake size={14} />
                  <span>Water Sharing Scenario</span>
                </Link>
              </nav>
            )}

            {/* In Farmer View on explicit farmer portal or scenario/explainability, render Outlet; otherwise render FarmerViewPage or Expert Outlet */}
            {showFarmerPage ? <FarmerViewPage /> : <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
};
