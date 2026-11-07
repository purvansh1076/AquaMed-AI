/**
 * AquaMedi AI — Agricultural Expert Authentication Page (Premium Redesign)
 * =========================================================================
 * Secure login portal with government-grade visual identity, demo credentials
 * display, and offline fallback authentication.
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ShieldCheck,
  Lock,
  User,
  AlertCircle,
  ArrowLeft,
  Eye,
  EyeOff,
  Droplets,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useViewMode } from '../context/ViewModeContext';

export const ExpertLoginPage: React.FC = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const { loginAsExpert, isLoading, authError, clearAuthError } = useAuth();
  const { setViewMode } = useViewMode();
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
    <div className="login-page-wrapper">
      {/* Government Department Research Banner */}
      <div className="gov-top-banner-navy">
        <span>Department of Agriculture &amp; Farmers Welfare — Research Reference System (Ministry of Agriculture &amp; Farmers Welfare Guidelines)</span>
        <span style={{ opacity: 0.8, fontSize: '11px' }}>
          Decision Support System — Not an Official Government Portal
        </span>
      </div>

      {/* Gov Header */}
      <header className="welcome-gov-header">
        <div className="welcome-gov-header-inner">
          <div className="welcome-logo-block">
            <div className="welcome-logo-icon-box">
              <Droplets size={22} />
            </div>
            <div className="welcome-logo-text">
              <h1>AquaMedi AI</h1>
              <p>Agricultural Intelligence &amp; Dispute Mediation System</p>
            </div>
          </div>
        </div>
      </header>

      {/* Login Body */}
      <div className="login-page-body">
        <div className="login-card-v2">
          {/* Icon */}
          <div className="login-icon-box-v2">
            <ShieldCheck size={30} />
          </div>

          <h2 className="login-card-v2-title">Agricultural Expert Portal</h2>
          <p className="login-card-v2-subtitle">Authorized Personnel Only</p>

          {/* Error */}
          {displayError && (
            <div className="login-error-box">
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '1px' }} />
              <div>
                <strong>Authentication Error:</strong>
                <div style={{ marginTop: '2px' }}>{displayError}</div>
              </div>
            </div>
          )}

          {/* Security Notice */}
          <div className="login-security-box">
            <div className="login-security-box-title">
              <ShieldCheck size={14} />
              <span>Authorized Agricultural Personnel Only</span>
            </div>
            <div>
              Access is restricted to verified extension officers and state irrigation engineers.
              Authenticate with your assigned government credentials.
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="login-form-group">
              <label className="login-label" htmlFor="expert-identifier">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <User size={13} />
                  Username / Official Email
                </span>
              </label>
              <div className="login-input-group">
                <div className="login-input-icon">
                  <User size={15} />
                </div>
                <input
                  id="expert-identifier"
                  type="text"
                  className="login-input-v2"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="admin123"
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="login-form-group">
              <label className="login-label" htmlFor="expert-password">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={13} />
                  Password
                </span>
              </label>
              <div className="login-input-group">
                <div className="login-input-icon">
                  <Lock size={15} />
                </div>
                <input
                  id="expert-password"
                  type={showPassword ? 'text' : 'password'}
                  className="login-input-v2"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  style={{ paddingRight: '44px' }}
                  required
                />
                <button
                  type="button"
                  className="login-password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Demo Credentials */}
            <div className="login-demo-box">
              <div className="login-demo-box-title">🔑 Demo Credentials (Prototype)</div>
              <div className="login-demo-creds">
                Username: <strong>admin123</strong> &nbsp;|&nbsp; Password: <strong>12345678</strong>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-gov-navy"
              style={{ width: '100%', marginTop: '4px' }}
              id="expert-submit-btn"
            >
              <ShieldCheck size={16} />
              <span>{isLoading ? 'Verifying Credentials...' : 'Secure Login'}</span>
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
                color: '#64748b',
                textDecoration: 'none',
                fontWeight: 600,
              }}
            >
              <ArrowLeft size={14} />
              <span>Back to Portal Selection</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="gov-footer">
        <div className="gov-footer-inner">
          <div className="gov-footer-brand">AquaMedi AI — Expert Portal</div>
          <div className="gov-footer-disclaimer">
            Not an official Government of India portal
          </div>
        </div>
      </footer>
    </div>
  );
};
