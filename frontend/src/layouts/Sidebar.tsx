import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sliders,
  TrendingUp,
  AlertTriangle,
  Scale,
  Handshake,
  Lightbulb,
  FileCheck2,
  Code2,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';

export const Sidebar: React.FC = () => {
  const { scenarioResult } = useScenario();

  const navItems = [
    { to: '/overview', label: '1. Overview', icon: <LayoutDashboard size={17} /> },
    { to: '/scenario', label: '2. Scenario Config', icon: <Sliders size={17} /> },
    { to: '/predictions', label: '3. ML Predictions', icon: <TrendingUp size={17} /> },
    { to: '/conflicts', label: '4. Conflict Engine', icon: <AlertTriangle size={17} /> },
    { to: '/allocation', label: '5. LP Allocation', icon: <Scale size={17} /> },
    { to: '/negotiation', label: '6. Negotiation', icon: <Handshake size={17} /> },
    { to: '/explainability', label: '7. Explainability', icon: <Lightbulb size={17} /> },
    { to: '/agreement', label: '8. Final Agreement', icon: <FileCheck2 size={17} /> },
    { to: '/debug', label: 'Raw API Payload', icon: <Code2 size={17} /> },
  ];

  return (
    <aside className="app-sidebar">
      <div className="sidebar-brand">
        <div className="brand-title-wrap">
          <div className="brand-logo">A</div>
          <div>
            <div className="brand-title">AquaMediAI</div>
            <div className="brand-tagline">AI-Powered Water Mediation</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link-item ${isActive ? 'active' : ''}`}
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="scenario-pill">
          <span>Active Scenario:</span>
          <span className="scenario-pill-id">
            {scenarioResult ? scenarioResult.scenario_id.slice(0, 13) : 'None Loaded'}
          </span>
        </div>
      </div>
    </aside>
  );
};
