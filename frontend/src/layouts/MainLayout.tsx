import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { FarmerViewPage } from '../pages/FarmerViewPage';
import { AlertBox } from '../components/common/AlertBox';

export const MainLayout: React.FC = () => {
  const { healthStatus, error, clearError } = useScenario();
  const { viewMode } = useViewMode();
  const location = useLocation();

  // Farmer view applies when viewMode is farmer OR on /farmer route
  const isFarmer = viewMode === 'farmer' || location.pathname === '/farmer';
  const showFarmerPage = isFarmer && location.pathname !== '/scenario' && location.pathname !== '/explainability';

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

            {/* In Farmer View on /scenario, render ScenarioPage; otherwise render FarmerViewPage or Expert Outlet */}
            {showFarmerPage ? <FarmerViewPage /> : <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
};
