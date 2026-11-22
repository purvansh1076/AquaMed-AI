/**
 * AquaMedi AI — Root Application Router
 * ======================================
 * Defines route structure with PrivateExpertRoute guard for expert-only pages.
 * Farmer routes remain publicly accessible (guest session).
 */

import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useViewMode } from './context/ViewModeContext';
import { MainLayout } from './layouts/MainLayout';
import { ErrorBoundary } from './components/common/ErrorBoundary';

const WelcomePage = lazy(() => import('./pages/WelcomePage').then((m) => ({ default: m.WelcomePage })));
const ExpertLoginPage = lazy(() => import('./pages/ExpertLoginPage').then((m) => ({ default: m.ExpertLoginPage })));
const FarmerViewPage = lazy(() => import('./pages/FarmerViewPage').then((m) => ({ default: m.FarmerViewPage })));
const FarmerPortalPage = lazy(() => import('./pages/FarmerPortalPage').then((m) => ({ default: m.FarmerPortalPage })));
const OverviewPage = lazy(() => import('./pages/OverviewPage').then((m) => ({ default: m.OverviewPage })));
const ScenarioPage = lazy(() => import('./pages/ScenarioPage').then((m) => ({ default: m.ScenarioPage })));
const PredictionsPage = lazy(() => import('./pages/PredictionsPage').then((m) => ({ default: m.PredictionsPage })));
const ConflictsPage = lazy(() => import('./pages/ConflictsPage').then((m) => ({ default: m.ConflictsPage })));
const AllocationPage = lazy(() => import('./pages/AllocationPage').then((m) => ({ default: m.AllocationPage })));
const NegotiationPage = lazy(() => import('./pages/NegotiationPage').then((m) => ({ default: m.NegotiationPage })));
const ExplainabilityPage = lazy(() => import('./pages/ExplainabilityPage').then((m) => ({ default: m.ExplainabilityPage })));
const AgreementPage = lazy(() => import('./pages/AgreementPage').then((m) => ({ default: m.AgreementPage })));
const DebugPage = lazy(() => import('./pages/DebugPage').then((m) => ({ default: m.DebugPage })));
const ReportsPage = lazy(() => import('./pages/ReportsPage').then((m) => ({ default: m.ReportsPage })));
const CropHealthPage = lazy(() => import('./pages/CropHealthPage').then((m) => ({ default: m.CropHealthPage })));
const IrrigationAdvisoryPage = lazy(() => import('./pages/IrrigationAdvisoryPage').then((m) => ({ default: m.IrrigationAdvisoryPage })));

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
      <ErrorBoundary>
      <Suspense fallback={<div>Loading...</div>}>
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
                import.meta.env.DEV ? (
                  <PrivateExpertRoute>
                    <DebugPage />
                  </PrivateExpertRoute>
                ) : (
                  <Navigate to="/overview" replace />
                )
              }
            />
            <Route
              path="debug"
              element={
                import.meta.env.DEV ? (
                  <PrivateExpertRoute>
                    <DebugPage />
                  </PrivateExpertRoute>
                ) : (
                  <Navigate to="/overview" replace />
                )
              }
            />
          </Route>

          {/* Fallback to Welcome */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
    </AuthProvider>
  );
};
