import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ExternalLink, PlusCircle, RefreshCw, Languages } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useViewMode } from '../context/ViewModeContext';
import { API_BASE_URL } from '../services/api';
import type { Language } from '../i18n/translations';

export const Header: React.FC = () => {
  const { health, healthStatus, checkHealth } = useScenario();
  const { viewMode, setViewMode, language, setLanguage, t } = useViewMode();
  const navigate = useNavigate();
  const location = useLocation();

  const handleModeChange = (mode: 'farmer' | 'expert') => {
    setViewMode(mode);
    if (location.pathname === '/scenario' || location.pathname === '/explainability') {
      return;
    }
    if (mode === 'farmer') {
      navigate('/farmer');
    } else {
      navigate('/overview');
    }
  };

  return (
    <header className="app-header">
      <div className="header-left">
        <span className="header-page-title">{t('appTitle')}</span>
        <span className="header-divider">|</span>
        <span className="header-subtitle">
          {viewMode === 'farmer' ? t('appSubtitle') : 'Explainable Multi-Agent Water Dispute Mediation'}
        </span>
      </div>

      <div className="header-center">
        {/* Exactly TWO presentation modes: Farmer View & Expert View */}
        <div className="mode-toggle-group" role="tablist" aria-label="Presentation Mode">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'farmer'}
            className={`mode-toggle-btn ${viewMode === 'farmer' ? 'active' : ''}`}
            onClick={() => handleModeChange('farmer')}
            id="farmer-view-btn"
          >
            {t('farmerView')}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'expert'}
            className={`mode-toggle-btn ${viewMode === 'expert' ? 'active' : ''}`}
            onClick={() => handleModeChange('expert')}
            id="expert-view-btn"
          >
            {t('expertView')}
          </button>
        </div>
      </div>

      <div className="header-right">
        {/* Language selector: English, Hindi, Gujarati */}
        <div className="language-selector-wrapper">
          <Languages size={15} className="language-icon" />
          <select
            id="app-language-select"
            className="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            aria-label="Interface Language"
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी (Hindi)</option>
            <option value="gu">ગુજરાતી (Gujarati)</option>
          </select>
        </div>

        {/* Backend API Health Status */}
        <div
          className={`health-badge ${healthStatus}`}
          onClick={checkHealth}
          title={
            healthStatus === 'connected'
              ? `FastAPI Backend v${health?.version || '1.0.0'} (${health?.pipeline || 'pipeline active'})`
              : 'FastAPI Backend Offline. Click to retry.'
          }
        >
          <div className="health-dot" />
          <span>
            {healthStatus === 'connected' && t('apiConnected')}
            {healthStatus === 'offline' && t('backendOffline')}
            {healthStatus === 'checking' && t('checkingApi')}
          </span>
          <RefreshCw size={11} style={{ opacity: 0.6 }} />
        </div>

        {/* Expert Quick Actions */}
        {viewMode === 'expert' && (
          <>
            <a
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline btn-sm"
              style={{ textDecoration: 'none' }}
            >
              <ExternalLink size={13} />
              <span>API Docs</span>
            </a>

            <Link to="/scenario" className="btn btn-primary btn-sm">
              <PlusCircle size={14} />
              <span>New Scenario</span>
            </Link>
          </>
        )}
      </div>
    </header>
  );
};
