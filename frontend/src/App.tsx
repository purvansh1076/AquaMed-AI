import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ViewModeProvider } from './context/ViewModeContext';
import { MainLayout } from './layouts/MainLayout';
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
    <ViewModeProvider>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/overview" replace />} />
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
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </ViewModeProvider>
  );
};
