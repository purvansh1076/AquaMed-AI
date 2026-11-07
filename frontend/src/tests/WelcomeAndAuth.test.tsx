/**
 * AquaMediAI — Welcome & Authentication Integration Tests
 * ========================================================
 * Verifies all 10 user flows from STEP 3:
 * 1. Landing page opens correctly with government branding & role options.
 * 2. Clicking Farmer Access opens the Farmer Portal.
 * 3. Farmer Portal does not redirect to Expert Login.
 * 4. Expert Access opens the Expert Login page.
 * 5. Username admin123 and password 12345678 work for prototype login.
 * 6. Incorrect credentials are rejected with structured error feedback.
 * 7. Expert Dashboard opens after successful login.
 * 8. Logout works correctly and clears credentials.
 * 9. Expert-only routes are protected from unauthenticated access.
 * 10. Refreshing the browser preserves authentication state from localStorage.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ViewModeProvider } from '../context/ViewModeContext';
import { ScenarioProvider } from '../context/ScenarioContext';
import { WelcomePage } from '../pages/WelcomePage';
import { ExpertLoginPage } from '../pages/ExpertLoginPage';
import { App } from '../App';
import { api } from '../services/api';

const renderWithProviders = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ScenarioProvider>
        <App />
      </ScenarioProvider>
    </MemoryRouter>
  );
};

describe('Government Entry & Role Selection Flow', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  // FLOW 1: Landing page opens correctly
  it('renders official government-grade portal branding and both access cards', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <ViewModeProvider>
            <WelcomePage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Authority banner and title
    expect(screen.getByText(/Ministry of Agriculture & Farmers Welfare/i)).toBeInTheDocument();
    expect(screen.getAllByText('AquaMedi AI')[0]).toBeInTheDocument();
    expect(screen.getByText('Select Your Access Portal')).toBeInTheDocument();

    // Two role access cards
    expect(screen.getByText('Farmer Portal')).toBeInTheDocument();
    expect(screen.getByText('Expert Portal')).toBeInTheDocument();
    expect(screen.getByText('Free Access')).toBeInTheDocument();
    expect(screen.getByText('Authorized Personnel')).toBeInTheDocument();

    // Portal entry action buttons
    expect(screen.getByRole('button', { name: /Enter Farmer Portal/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Expert Login/i })).toBeInTheDocument();

    // Trust pillars
    expect(screen.getByText('Verified ML Engine')).toBeInTheDocument();
    expect(screen.getByText('Fair Multi-Agent Mediation')).toBeInTheDocument();
    expect(screen.getByText('Physical Threshold Clamping')).toBeInTheDocument();
    expect(screen.getByText('Server-Side RBAC')).toBeInTheDocument();
  });

  // FLOW 2 & 3: Clicking Farmer Access enters Farmer Portal without redirect to login
  it('clicking Enter Farmer Portal establishes guest session and opens Farmer Portal', async () => {
    const user = userEvent.setup();
    const guestSpy = vi.spyOn(api, 'createGuestSession').mockResolvedValue({
      access_token: 'mock_guest_jwt_token',
      token_type: 'bearer',
      role: 'farmer_guest',
      session_id: 'guest_test_123',
      display_name: 'Farmer Guest',
      permissions: ['farmer:read', 'farmer:predict'],
      expires_in_seconds: 86400,
    });

    renderWithProviders(['/']);

    const farmerBtn = screen.getByRole('button', { name: /Enter Farmer Portal/i });
    await user.click(farmerBtn);

    await waitFor(() => {
      expect(guestSpy).toHaveBeenCalled();
    });

    // Confirms user is in Farmer Portal and NOT redirected to Expert Login
    await waitFor(() => {
      expect(screen.queryByText('Agricultural Expert Portal')).not.toBeInTheDocument();
      expect(screen.getAllByText(/Farmer Portal/i).length).toBeGreaterThan(0);
    });
  });

  // FLOW 4: Expert Access opens the Expert Login page
  it('renders Expert Login form with security notice, fields, and demo credentials', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <ViewModeProvider>
            <ExpertLoginPage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Agricultural Expert Portal')).toBeInTheDocument();
    expect(screen.getByText(/Authorized Personnel Only/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Username \/ Official Email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByText(/Demo Credentials \(Prototype\)/i)).toBeInTheDocument();
    expect(screen.getByText(/admin123/)).toBeInTheDocument();
    expect(screen.getByText(/12345678/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Secure Login/i })).toBeInTheDocument();
  });

  // FLOW 5 & 7: Username admin123 and password 12345678 work and open Expert Dashboard
  it('submits admin123 and 12345678 to api.loginExpert and handles successful authentication', async () => {
    const user = userEvent.setup();
    const loginSpy = vi.spyOn(api, 'loginExpert').mockResolvedValue({
      access_token: 'mock_expert_jwt_token',
      token_type: 'bearer',
      role: 'expert',
      user: {
        email: 'admin123@aquamedi.gov.in',
        full_name: 'Senior Agricultural Specialist (Admin)',
        role: 'expert',
        department: 'Agricultural Intelligence',
      },
      expires_in_seconds: 28800,
      message: 'Authentication successful',
    });

    renderWithProviders(['/login']);

    await user.type(screen.getByLabelText(/Username \/ Official Email/i), 'admin123');
    await user.type(screen.getByPlaceholderText('••••••••'), '12345678');

    const submitBtn = screen.getByRole('button', { name: /Secure Login/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        username_or_email: 'admin123',
        password: '12345678',
      });
    });

    // Expert dashboard rendered
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard Overview').length).toBeGreaterThan(0);
    });
  });

  // FLOW 6: Incorrect credentials are rejected
  it('rejects incorrect credentials and displays authentication error alert', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'loginExpert').mockRejectedValue(
      new Error('Invalid username/email or password. 4 attempt(s) remaining.')
    );

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <ViewModeProvider>
            <ExpertLoginPage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Username \/ Official Email/i), 'unknown_user');
    await user.type(screen.getByPlaceholderText('••••••••'), 'bad_password_999');

    const submitBtn = screen.getByRole('button', { name: /Secure Login/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Invalid username\/email or password/i)).toBeInTheDocument();
    });
  });

  // FLOW 5 (Offline fallback): Prototype admin123 works even if backend is unreachable
  it('offline fallback enables admin123 / 12345678 prototype login when backend is offline', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'loginExpert').mockRejectedValue(new Error('Network error: backend offline'));

    renderWithProviders(['/login']);

    await user.type(screen.getByLabelText(/Username \/ Official Email/i), 'admin123');
    await user.type(screen.getByPlaceholderText('••••••••'), '12345678');

    const submitBtn = screen.getByRole('button', { name: /Secure Login/i });
    await user.click(submitBtn);

    // Navigates to overview via demo fallback session
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard Overview').length).toBeGreaterThan(0);
    });

    const saved = JSON.parse(localStorage.getItem('aquamedi_auth_session') || '{}');
    expect(saved.role).toBe('expert');
    expect(saved.token).toMatch(/^demo_expert_/);
  });

  // FLOW 8: Logout works correctly
  it('logout terminates authenticated session and clears storage', async () => {
    const user = userEvent.setup();
    localStorage.setItem(
      'aquamedi_auth_session',
      JSON.stringify({
        role: 'expert',
        token: 'existing_token_abc',
        user: { email: 'admin123@aquamedi.gov.in', full_name: 'Admin User', role: 'expert' },
      })
    );

    renderWithProviders(['/overview']);

    // Expert dashboard loaded
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard Overview').length).toBeGreaterThan(0);
    });

    // Click logout
    const logoutBtns = screen.getAllByRole('button', { name: /Logout/i });
    await user.click(logoutBtns[0]);

    // Redirected to Login / Portal Selection
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Secure Login/i })).toBeInTheDocument();
    });

    expect(localStorage.getItem('aquamedi_auth_session')).toBeNull();
  });

  // FLOW 9: Expert-only routes are protected
  it('protects expert-only routes and redirects unauthenticated users to /login', async () => {
    renderWithProviders(['/overview']);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Secure Login/i })).toBeInTheDocument();
      expect(screen.getByText(/Authorized Personnel Only/i)).toBeInTheDocument();
    });
  });

  // FLOW 10: Refreshing the browser preserves authentication state from localStorage
  it('rehydrates expert authentication session from localStorage on page refresh', async () => {
    localStorage.setItem(
      'aquamedi_auth_session',
      JSON.stringify({
        role: 'expert',
        token: 'active_valid_token_xyz',
        user: {
          email: 'admin123@aquamedi.gov.in',
          full_name: 'Senior Agricultural Specialist',
          role: 'expert',
          department: 'Agricultural Intelligence',
        },
      })
    );

    renderWithProviders(['/overview']);

    // Stays on expert dashboard without redirecting to login
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard Overview').length).toBeGreaterThan(0);
    });
    expect(screen.queryByRole('button', { name: /Secure Login/i })).not.toBeInTheDocument();
  });
});
