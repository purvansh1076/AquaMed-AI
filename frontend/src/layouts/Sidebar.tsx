/**
 * AquaMedi AI — Expert Administrative Sidebar (Government Style)
 * ==============================================================
 * Formal department navigation with interactive collapse & expand.
 * - Supports Desktop (260px expanded / 72px collapsed rail)
 * - Supports Mobile slide-out drawer with backdrop
 * - Hover tooltips in collapsed mode
 * - English navigation labels
 * - Farmer Management removed from Expert navigation
 */

import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
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
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useAuth } from '../context/AuthContext';

export interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed = false,
  onToggleCollapse,
  mobileOpen = false,
  onCloseMobile,
}) => {
  const { scenarioResult } = useScenario();
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  // Nav items for Expert Mode (Farmer Management removed per directive)
  const navItems = [
    { to: '/overview',            label: 'Dashboard Overview',        icon: <LayoutDashboard size={18} /> },
    { to: '/predictions',         label: 'ML Predictions',            icon: <TrendingUp size={18} /> },
    { to: '/crop-health',         label: 'Crop Health',               icon: <Activity size={18} /> },
    { to: '/irrigation-advisory', label: 'Irrigation Advisory',       icon: <CloudSun size={18} /> },
    { to: '/scenario',            label: 'Scenario Configuration',    icon: <Sliders size={18} /> },
    { to: '/allocation',          label: 'LP Water Allocation',       icon: <Droplets size={18} /> },
    { to: '/conflicts',           label: 'Water Dispute Mediation',   icon: <Scale size={18} /> },
    { to: '/negotiation',         label: 'Negotiation Engine',        icon: <Handshake size={18} /> },
    { to: '/explainability',      label: 'SHAP Explainability',       icon: <Lightbulb size={18} /> },
    { to: '/agreement',           label: 'Final Agreement',           icon: <FileCheck2 size={18} /> },
    { to: '/reports',             label: 'Reports',                   icon: <FileText size={18} /> },
    { to: '/debug',               label: 'Settings',                  icon: <Settings size={18} /> },
  ];

  const displayName = user?.full_name || 'Agricultural Officer';
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const scenarioDisplayId = scenarioResult
    ? scenarioResult.scenario_id.slice(0, 13)
    : 'None Loaded';

  return (
    <aside
      className={`app-sidebar ${collapsed ? 'collapsed' : 'expanded'} ${
        mobileOpen ? 'mobile-open' : ''
      }`}
      aria-label="Expert Mode Navigation Sidebar"
      style={{
        backgroundColor: '#12315B',
        color: '#FFFFFF',
        width: collapsed ? '72px' : '260px',
        minWidth: collapsed ? '72px' : '260px',
        maxWidth: collapsed ? '72px' : '260px',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #0d2342',
        transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1), max-width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        zIndex: 100,
      }}
    >
      {/* ── Sidebar Header ── */}
      <div
        className="expert-sidebar-header"
        style={{
          padding: collapsed ? '14px 10px' : '16px 18px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          minHeight: '60px',
          boxSizing: 'border-box',
        }}
      >
        {collapsed ? (
          /* Collapsed compact brand & expand button */
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <div
              title="AquaMedi AI — Agricultural Expert Portal"
              style={{
                backgroundColor: '#176B45',
                width: '32px',
                height: '32px',
                borderRadius: '3px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
              onClick={onToggleCollapse}
            >
              <Droplets size={18} color="#FFFFFF" />
            </div>

            {onToggleCollapse && (
              <button
                type="button"
                onClick={onToggleCollapse}
                id="sidebar-expand-btn"
                className="sidebar-toggle-btn-compact"
                aria-label="Expand sidebar"
                aria-expanded={false}
                title="Expand sidebar"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#8da5c4',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <PanelLeftOpen size={16} />
              </button>
            )}
          </div>
        ) : (
          /* Expanded full brand header */
          <>
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

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {/* Desktop Collapse Toggle */}
              {onToggleCollapse && (
                <button
                  type="button"
                  onClick={onToggleCollapse}
                  id="sidebar-collapse-btn"
                  className="sidebar-collapse-btn"
                  aria-label="Collapse sidebar"
                  aria-expanded={true}
                  title="Collapse sidebar"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#8da5c4',
                    cursor: 'pointer',
                    padding: '4px',
                    borderRadius: '3px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'color 0.15s ease',
                  }}
                >
                  <PanelLeftClose size={16} />
                </button>
              )}

              {/* Mobile Drawer Close Button */}
              {onCloseMobile && mobileOpen && (
                <button
                  type="button"
                  onClick={onCloseMobile}
                  id="sidebar-mobile-close-btn"
                  className="sidebar-mobile-close-btn"
                  aria-label="Close navigation menu"
                  title="Close navigation menu"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#FFFFFF',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <X size={18} />
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── User Profile Badge ── */}
      <div
        className="expert-sidebar-user"
        title={displayName}
        style={{
          padding: collapsed ? '10px 0' : '12px 18px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: 'rgba(0, 0, 0, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
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
            flexShrink: 0,
          }}
        >
          {initials || <User size={14} />}
        </div>
        {!collapsed && (
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
            <div style={{ fontSize: '11px', color: '#b0c4de' }}>
              Command Area Officer
            </div>
          </div>
        )}
      </div>

      {/* ── Section Title (Expanded Only) ── */}
      {!collapsed && (
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
      )}

      {/* ── Navigation Links ── */}
      <nav
        className="sidebar-nav"
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: collapsed ? '12px 6px' : '0 8px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: collapsed ? '4px' : '2px',
        }}
      >
        {navItems.map((item) => (
          <div key={item.to} className="sidebar-nav-item-wrap">
            <NavLink
              to={item.to}
              onClick={() => onCloseMobile?.()}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `nav-link-item ${isActive ? 'active' : ''}`
              }
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'flex-start',
                gap: collapsed ? '0' : '10px',
                padding: collapsed ? '8px 0' : '8px 12px',
                width: collapsed ? '44px' : '100%',
                margin: collapsed ? '0 auto' : '0',
                borderRadius: '3px',
                fontSize: '12px',
                fontWeight: isActive ? 700 : 500,
                color: isActive ? '#FFFFFF' : '#d2dfed',
                backgroundColor: isActive ? '#176B45' : 'transparent',
                textDecoration: 'none',
                transition: 'background-color 0.15s ease, color 0.15s ease',
                position: 'relative',
              })}
            >
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  opacity: 0.95,
                }}
              >
                {item.icon}
              </span>
              {!collapsed && (
                <span style={{ whiteSpace: 'nowrap' }}>{item.label}</span>
              )}
            </NavLink>

            {/* Custom Tooltip in Collapsed Rail */}
            {collapsed && (
              <span className="sidebar-tooltip" role="tooltip">
                {item.label}
              </span>
            )}
          </div>
        ))}
      </nav>

      {/* ── Footer with Scenario Info & Logout ── */}
      <div
        className="sidebar-footer"
        style={{
          padding: collapsed ? '12px 8px' : '12px 16px',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          alignItems: collapsed ? 'center' : 'stretch',
        }}
      >
        {!collapsed ? (
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
              {scenarioDisplayId}
            </span>
          </div>
        ) : (
          <div
            title={`Active Scenario: ${scenarioDisplayId}`}
            style={{
              fontSize: '10px',
              color: '#176B45',
              backgroundColor: '#eaf5ef',
              padding: '2px 4px',
              borderRadius: '2px',
              fontWeight: 700,
              textAlign: 'center',
              cursor: 'default',
            }}
          >
            SCN
          </div>
        )}

        <button
          type="button"
          onClick={handleLogout}
          id="sidebar-logout-btn"
          title="Exit Session"
          aria-label="Exit Session"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            width: collapsed ? '40px' : '100%',
            height: collapsed ? '32px' : 'auto',
            padding: collapsed ? '0' : '6px',
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
          {!collapsed && <span>Exit Session</span>}
        </button>
      </div>
    </aside>
  );
};
