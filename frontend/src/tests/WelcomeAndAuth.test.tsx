/**
 * AquaMediAI — Welcome & Authentication Integration Tests
 * ========================================================
 * Verifies all 10 user flows from STEP 3:
 * 1. Landing page opens correctly with government branding & role options.
 * 2. Clicking Farmer Access opens the Farmer Portal.
 * 3. Farmer Portal does not redirect to Expert Login.
 * 4. Expert Access opens the Expert Login page without demo credentials.
 * 5. Valid credentials authenticate through the backend login endpoint.
 * 6. Incorrect credentials are rejected with structured error feedback.
 * 7. Expert Dashboard opens after successful login.
 * 8. Logout works correctly and clears credentials.
 * 9. Expert-only routes are protected from unauthenticated access.
 * 10. Refreshing the browser preserves a valid, unexpired session.
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
import { makeTestJwt, mockExpertIdentity } from './authTestUtils';

const renderWithProviders = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ScenarioProvider>
        <ViewModeProvider>
          <App />
        </ViewModeProvider>
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

    const farmerBtn = await screen.findByRole('button', { name: /Enter Farmer Portal/i });
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
  it('renders Expert Login form with security notice and no demo credentials', () => {
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
    expect(screen.getByRole('button', { name: /Secure Login/i })).toBeInTheDocument();

    // Prototype credentials must not be advertised in the UI.
    expect(screen.queryByText(/Demo Credentials/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/admin123/)).not.toBeInTheDocument();
    expect(screen.queryByText(/12345678/)).not.toBeInTheDocument();
  });

  // FLOW 5 & 7: Valid credentials authenticate and open the Expert Dashboard
  it('submits credentials to api.loginExpert and handles successful authentication', async () => {
    const user = userEvent.setup();
    const loginSpy = vi.spyOn(api, 'loginExpert').mockResolvedValue({
      access_token: makeTestJwt(),
      token_type: 'bearer',
      role: 'expert',
      user: {
        email: 'expert@aquamedi.gov.in',
        full_name: 'Senior Agricultural Specialist',
        role: 'expert',
        department: 'Department of Agriculture & Water Resources',
      },
      expires_in_seconds: 28800,
      message: 'Authentication successful',
    });

    renderWithProviders(['/login']);

    await user.type(
      await screen.findByLabelText(/Username \/ Official Email/i),
      'expert@aquamedi.gov.in'
    );
    await user.type(await screen.findByPlaceholderText('••••••••'), 'CorrectHorse123!');

    const submitBtn = await screen.findByRole('button', { name: /Secure Login/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        username_or_email: 'expert@aquamedi.gov.in',
        password: 'CorrectHorse123!',
      });
    });

    // Expert dashboard rendered
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard Overview').length).toBeGreaterThan(0);
    }, { timeout: 30000 });
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

    await user.type(await screen.findByLabelText(/Username \/ Official Email/i), 'unknown_user');
    await user.type(await screen.findByPlaceholderText('••••••••'), 'bad_password_999');

    const submitBtn = await screen.findByRole('button', { name: /Secure Login/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Invalid username\/email or password/i)).toBeInTheDocument();
    });
  });

  // FLOW 5 (Offline behavior): No fabricated session when the backend is unreachable
  it('does not create a session when expert login cannot reach the backend', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'loginExpert').mockRejectedValue(new Error('Network error: backend offline'));

    renderWithProviders(['/login']);

    await user.type(
      await screen.findByLabelText(/Username \/ Official Email/i),
      'expert@aquamedi.gov.in'
    );
    await user.type(await screen.findByPlaceholderText('••••••••'), 'CorrectHorse123!');

    const submitBtn = await screen.findByRole('button', { name: /Secure Login/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Network error: backend offline/i)).toBeInTheDocument();
    });

    // Still on the login page and no expert session was persisted.
    expect(screen.getByRole('button', { name: /Secure Login/i })).toBeInTheDocument();
    expect(localStorage.getItem('aquamedi_auth_session')).toBeNull();
  });

  // FLOW 8: Logout works correctly
  it('logout terminates authenticated session and clears storage', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'getIdentity').mockResolvedValue(mockExpertIdentity());
    vi.spyOn(api, 'logout').mockResolvedValue({
      status: 'success',
      message: 'Logged out successfully.',
    });
    localStorage.setItem(
      'aquamedi_auth_session',
      JSON.stringify({
        role: 'expert',
        token: makeTestJwt(),
        user: {
          email: 'expert@aquamedi.gov.in',
          full_name: 'Test Expert',
          role: 'expert',
          department: 'Department of Agriculture & Water Resources',
        },
      })
    );

    renderWithProviders(['/overview']);

    // Expert dashboard loaded
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard Overview').length).toBeGreaterThan(0);
    }, { timeout: 30000 });

    // Click logout
    const logoutBtns = await screen.findAllByRole('button', { name: /Logout/i });
    await user.click(logoutBtns[0]);

    // Redirected to Login / Portal Selection
    await screen.findByRole('button', { name: /Secure Login/i });

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
    vi.spyOn(api, 'getIdentity').mockResolvedValue(mockExpertIdentity());
    localStorage.setItem(
      'aquamedi_auth_session',
      JSON.stringify({
        role: 'expert',
        token: makeTestJwt(),
        user: {
          email: 'expert@aquamedi.gov.in',
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
    }, { timeout: 30000 });
    expect(screen.queryByRole('button', { name: /Secure Login/i })).not.toBeInTheDocument();
  });

  // FLOW 10 (Expired session): Expired tokens are discarded on refresh
  it('discards an expired saved session instead of trusting it', async () => {
    const getIdentitySpy = vi.spyOn(api, 'getIdentity').mockResolvedValue(mockExpertIdentity());
    localStorage.setItem(
      'aquamedi_auth_session',
      JSON.stringify({
        role: 'expert',
        token: makeTestJwt(-60),
        user: {
          email: 'expert@aquamedi.gov.in',
          full_name: 'Senior Agricultural Specialist',
          role: 'expert',
          department: 'Agricultural Intelligence',
        },
      })
    );

    renderWithProviders(['/overview']);

    await screen.findByRole('button', { name: /Secure Login/i });
    expect(localStorage.getItem('aquamedi_auth_session')).toBeNull();
    expect(getIdentitySpy).not.toHaveBeenCalled();
  });

  // FLOW 10 (Tampering): Backend role overrides a tampered localStorage role
  it('uses the backend-resolved role instead of a tampered saved expert role', async () => {
    vi.spyOn(api, 'getIdentity').mockResolvedValue({
      ...mockExpertIdentity(),
      role: 'farmer_guest',
      is_authenticated: false,
    });
    localStorage.setItem(
      'aquamedi_auth_session',
      JSON.stringify({
        role: 'expert',
        token: makeTestJwt(),
        user: {
          email: 'farmer@example.test',
          full_name: 'Guest Farmer',
          role: 'expert',
          department: 'Agricultural Intelligence',
        },
      })
    );

    renderWithProviders(['/overview']);

    await screen.findByRole('button', { name: /Secure Login/i });
    expect(screen.queryByText('Dashboard Overview')).not.toBeInTheDocument();
  });
});
