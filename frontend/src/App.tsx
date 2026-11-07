/**
 * AquaMedi AI — Root Application Router
 * ======================================
 * Defines route structure with PrivateExpertRoute guard for expert-only pages.
 * Farmer routes remain publicly accessible (guest session).
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ViewModeProvider, useViewMode } from './context/ViewModeContext';
import { MainLayout } from './layouts/MainLayout';
import { WelcomePage } from './pages/WelcomePage';
import { ExpertLoginPage } from './pages/ExpertLoginPage';
import { FarmerViewPage } from './pages/FarmerViewPage';
import { FarmerPortalPage } from './pages/FarmerPortalPage';
import { OverviewPage } from './pages/OverviewPage';
import { ScenarioPage } from './pages/ScenarioPage';
import { PredictionsPage } from './pages/PredictionsPage';
import { ConflictsPage } from './pages/ConflictsPage';
import { AllocationPage } from './pages/AllocationPage';
import { NegotiationPage } from './pages/NegotiationPage';
import { ExplainabilityPage } from './pages/ExplainabilityPage';
import { AgreementPage } from './pages/AgreementPage';
import { DebugPage } from './pages/DebugPage';
import { ReportsPage } from './pages/ReportsPage';
import { CropHealthPage } from './pages/CropHealthPage';
import { IrrigationAdvisoryPage } from './pages/IrrigationAdvisoryPage';

/**
 * PrivateExpertRoute — guards expert-only routes behind authentication check.
 * Redirects unauthenticated users to /login.
 * Optional allowFarmer flag allows farmer guests to access hybrid routes like /scenario.
 */
interface PrivateRouteProps {
  children: React.ReactNode;
  allowFarmer?: boolean;
}

const PrivateExpertRoute: React.FC<PrivateRouteProps> = ({ children, allowFarmer }) => {
  const { isAuthenticated, isFarmerGuest, isLoading } = useAuth();
  const { viewMode } = useViewMode();

  // While session is rehydrating from localStorage, render nothing (avoid flash)
  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: 'var(--gov-bg, #EEF2F7)',
        }}
      >
        <div className="spinner" />
      </div>
    );
  }

  // Allow farmer access on designated hybrid routes
  if (allowFarmer && (isFarmerGuest || viewMode === 'farmer')) {
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <ViewModeProvider>
        <Routes>
          {/* Government Portal Welcome & Role Selection */}
          <Route path="/" element={<WelcomePage />} />
          <Route path="/welcome" element={<WelcomePage />} />
          <Route path="/login" element={<ExpertLoginPage />} />
          <Route path="/expert-login" element={<ExpertLoginPage />} />

          {/* Main Layout for Dashboards & Workflows */}
          <Route element={<MainLayout />}>
            {/* ── Farmer Routes (open access) ── */}
            <Route path="farmer" element={<FarmerViewPage />} />
            <Route path="farmer/portal" element={<FarmerPortalPage />} />
            <Route path="farmer-portal" element={<FarmerPortalPage />} />

            {/* ── Expert Routes (authentication required) ── */}
            <Route
              path="overview"
              element={
                <PrivateExpertRoute>
                  <OverviewPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="scenario"
              element={
                <PrivateExpertRoute allowFarmer>
                  <ScenarioPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="predictions"
              element={
                <PrivateExpertRoute>
                  <PredictionsPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="conflicts"
              element={
                <PrivateExpertRoute>
                  <ConflictsPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="allocation"
              element={
                <PrivateExpertRoute>
                  <AllocationPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="negotiation"
              element={
                <PrivateExpertRoute>
                  <NegotiationPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="explainability"
              element={
                <PrivateExpertRoute>
                  <ExplainabilityPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="agreement"
              element={
                <PrivateExpertRoute>
                  <AgreementPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="reports"
              element={
                <PrivateExpertRoute>
                  <ReportsPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="crop-health"
              element={
                <PrivateExpertRoute>
                  <CropHealthPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="irrigation-advisory"
              element={
                <PrivateExpertRoute>
                  <IrrigationAdvisoryPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="settings"
              element={
                <PrivateExpertRoute>
                  <DebugPage />
                </PrivateExpertRoute>
              }
            />
            <Route
              path="debug"
              element={
                <PrivateExpertRoute>
                  <DebugPage />
                </PrivateExpertRoute>
              }
            />
          </Route>

          {/* Fallback to Welcome */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ViewModeProvider>
    </AuthProvider>
  );
};
