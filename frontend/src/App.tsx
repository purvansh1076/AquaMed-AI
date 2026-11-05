import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ViewModeProvider } from './context/ViewModeContext';
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
            <Route path="farmer" element={<FarmerViewPage />} />
            <Route path="farmer/portal" element={<FarmerPortalPage />} />
            <Route path="farmer-portal" element={<FarmerPortalPage />} />
            <Route path="overview" element={<OverviewPage />} />
            <Route path="scenario" element={<ScenarioPage />} />
            <Route path="predictions" element={<PredictionsPage />} />
            <Route path="conflicts" element={<ConflictsPage />} />
            <Route path="allocation" element={<AllocationPage />} />
            <Route path="negotiation" element={<NegotiationPage />} />
            <Route path="explainability" element={<ExplainabilityPage />} />
            <Route path="agreement" element={<AgreementPage />} />
            <Route path="debug" element={<DebugPage />} />
          </Route>

          {/* Fallback navigation to Welcome */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ViewModeProvider>
    </AuthProvider>
  );
};
