/**
 * AquaMediAI — Agricultural Expert Authentication Page
 * ====================================================
 * Secure login portal with brute-force defense, rate-limiting feedback,
 * and authenticated session establishment.
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Lock, User, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useViewMode } from '../context/ViewModeContext';

export const ExpertLoginPage: React.FC = () => {
  const [identifier, setIdentifier] = useState('expert@aquamedi.gov.in');
  const [password, setPassword] = useState('AquaExpert#2026');
  const [localError, setLocalError] = useState<string | null>(null);
  const { loginAsExpert, isLoading, authError, clearAuthError } = useAuth();
  const { setViewMode, t } = useViewMode();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearAuthError();

    if (!identifier.trim()) {
      setLocalError('Please enter your username or official email.');
      return;
    }
    if (!password) {
      setLocalError('Please enter your password.');
      return;
    }

    const success = await loginAsExpert(identifier.trim(), password);
    if (success) {
      setViewMode('expert');
      navigate('/overview');
    }
  };

  const displayError = localError || authError;

  return (
    <div className="login-screen-wrapper">
      <div className="login-card-container">
        {/* Header */}
        <div className="login-header-group">
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '12px',
              backgroundColor: '#dbeafe',
              color: '#002664',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}
          >
            <ShieldCheck size={32} />
          </div>
          <h2>{t('loginTitle')}</h2>
          <p>{t('loginSubtitle')}</p>
        </div>

        {/* Error Alert Box */}
        {displayError && (
          <div
            style={{
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '6px',
              padding: '12px 14px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              marginBottom: '20px',
              color: '#991b1b',
              fontSize: '13px',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <strong>Authentication Error:</strong>
              <div style={{ marginTop: '2px' }}>{displayError}</div>
            </div>
          </div>
        )}

        {/* Official Setup Credentials Box */}
        <div className="login-credentials-hint">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: '#002664' }}>
            <CheckCircle2 size={14} />
            <span>Official Extension Officer Credentials</span>
          </div>
          <div style={{ marginTop: '4px', fontFamily: 'monospace', fontSize: '11.5px', color: '#334155' }}>
            Email: <strong>expert@aquamedi.gov.in</strong>
            <br />
            Password: <strong>AquaExpert#2026</strong>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="login-form-group">
            <label className="login-label" htmlFor="expert-identifier">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <User size={14} />
                {t('loginEmailLabel')}
              </span>
            </label>
            <input
              id="expert-identifier"
              type="text"
              className="login-input"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="e.g., expert@aquamedi.gov.in"
              autoComplete="username"
              required
            />
          </div>

          <div className="login-form-group">
            <label className="login-label" htmlFor="expert-password">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <Lock size={14} />
                {t('loginPasswordLabel')}
              </span>
            </label>
            <input
              id="expert-password"
              type="password"
              className="login-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-gov-navy"
            style={{ width: '100%', marginTop: '8px' }}
            id="expert-submit-btn"
          >
            <ShieldCheck size={16} />
            <span>{isLoading ? 'Verifying Credentials...' : t('loginSubmitBtn')}</span>
          </button>
        </form>

        {/* Back Link */}
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Link
            to="/"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px',
              color: '#475569',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            <ArrowLeft size={14} />
            <span>{t('loginBackBtn')}</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
