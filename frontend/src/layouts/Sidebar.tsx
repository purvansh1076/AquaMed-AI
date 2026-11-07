/**
 * AquaMedi AI — Expert Administrative Sidebar (Government Style)
 * ==============================================================
 * Formal department navigation:
 * - Dashboard Overview
 * - Farmer Management
 * - Crop Water Prediction (ML Predictions)
 * - Crop Health
 * - Irrigation Advisory
 * - Water Allocation
 * - Dispute Mediation
 * - Reports
 * - Settings
 */

import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  TrendingUp,
  Activity,
  CloudSun,
  Sliders,
  Droplets,
  Scale,
  Handshake,
  Lightbulb,
  FileCheck2,
  FileText,
  Settings,
  LogOut,
  User,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { scenarioResult } = useScenario();
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { to: '/overview',            label: 'Dashboard Overview',        icon: <LayoutDashboard size={16} /> },
    { to: '/farmer-portal',       label: 'Farmer Management',         icon: <Users size={16} /> },
    { to: '/predictions',         label: 'ML Predictions',            icon: <TrendingUp size={16} /> },
    { to: '/crop-health',         label: 'Crop Health',               icon: <Activity size={16} /> },
    { to: '/irrigation-advisory', label: 'Irrigation Advisory',       icon: <CloudSun size={16} /> },
    { to: '/scenario',            label: 'Scenario Configuration',    icon: <Sliders size={16} /> },
    { to: '/allocation',          label: 'LP Water Allocation',       icon: <Droplets size={16} /> },
    { to: '/conflicts',           label: 'Water Dispute Mediation',   icon: <Scale size={16} /> },
    { to: '/negotiation',         label: 'Negotiation Engine',        icon: <Handshake size={16} /> },
    { to: '/explainability',      label: 'SHAP Explainability',       icon: <Lightbulb size={16} /> },
    { to: '/agreement',           label: 'Final Agreement',           icon: <FileCheck2 size={16} /> },
    { to: '/reports',             label: 'Reports',                   icon: <FileText size={16} /> },
    { to: '/debug',               label: 'Settings',                  icon: <Settings size={16} /> },
  ];

  const displayName = user?.full_name || 'Agricultural Officer';
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <aside
      className="app-sidebar"
      style={{
        backgroundColor: '#12315B',
        color: '#FFFFFF',
        width: '260px',
        minWidth: '260px',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #0d2342',
      }}
    >
      {/* ── Formal Government Header ── */}
      <div
        className="expert-sidebar-header"
        style={{
          padding: '16px 18px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              backgroundColor: '#176B45',
              padding: '6px',
              borderRadius: '3px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Droplets size={16} color="#FFFFFF" />
          </div>
          <div>
            <div
              style={{
                fontSize: '15px',
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.3px',
              }}
            >
              AquaMedi AI
            </div>
            <div
              style={{
                fontSize: '10px',
                color: '#D9E0E7',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.4px',
              }}
            >
              Agricultural Expert Portal
            </div>
          </div>
        </div>
      </div>

      {/* ── User Profile Badge ── */}
      <div
        className="expert-sidebar-user"
        style={{
          padding: '12px 18px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: 'rgba(0, 0, 0, 0.15)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '3px',
            backgroundColor: '#176B45',
            color: '#FFFFFF',
            fontWeight: 700,
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {initials || <User size={14} />}
        </div>
        <div style={{ overflow: 'hidden' }}>
          <div
            style={{
              fontSize: '12px',
              fontWeight: 700,
              color: '#FFFFFF',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {displayName}
          </div>
          <div style={{ fontSize: '11px', color: '#b0c4de' }}>Command Area Officer</div>
        </div>
      </div>

      {/* ── Section Title ── */}
      <div
        style={{
          padding: '12px 18px 6px',
          fontSize: '10px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.6px',
          color: '#8da5c4',
        }}
      >
        Navigation
      </div>

      {/* ── Navigation Links ── */}
      <nav
        className="sidebar-nav"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 8px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link-item ${isActive ? 'active' : ''}`}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '3px',
              fontSize: '12px',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? '#FFFFFF' : '#d2dfed',
              backgroundColor: isActive ? '#176B45' : 'transparent',
              textDecoration: 'none',
              transition: 'background-color 0.15s ease',
            })}
          >
            <span style={{ opacity: 0.9 }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* ── Footer with Scenario Info & Logout ── */}
      <div
        className="sidebar-footer"
        style={{
          padding: '12px 16px',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            color: '#b0c4de',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <span>Scenario:</span>
          <span style={{ fontWeight: 700, color: '#FFFFFF' }}>
            {scenarioResult ? scenarioResult.scenario_id.slice(0, 13) : 'None Loaded'}
          </span>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          id="sidebar-logout-btn"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            width: '100%',
            padding: '6px',
            borderRadius: '3px',
            backgroundColor: 'transparent',
            border: '1px solid rgba(255, 255, 255, 0.25)',
            color: '#FFFFFF',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <LogOut size={13} />
          <span>Exit Session</span>
        </button>
      </div>
    </aside>
  );
};
