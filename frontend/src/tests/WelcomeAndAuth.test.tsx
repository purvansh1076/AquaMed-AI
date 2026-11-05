/**
 * AquaMediAI — Welcome & Authentication Integration Tests
 * ========================================================
 * Verifies:
 * 1. Government-Grade Welcome Page rendering and authority branding.
 * 2. Frictionless Farmer Access flow (guest session establishment without credentials).
 * 3. Agricultural Expert Access flow and login credentials validation.
 * 4. Locked XGBoost production model display.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ViewModeProvider } from '../context/ViewModeContext';
import { WelcomePage } from '../pages/WelcomePage';
import { ExpertLoginPage } from '../pages/ExpertLoginPage';
import { api } from '../services/api';

describe('Government Entry & Role Selection Flow', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

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

    // Title and portal prompt
    expect(screen.getByText('Agricultural Decision Support System')).toBeInTheDocument();
    expect(screen.getByText(/Select your portal access level to continue/i)).toBeInTheDocument();

    // Two role cards
    expect(screen.getByText('Farmer Access')).toBeInTheDocument();
    expect(screen.getByText('Agricultural Expert Access')).toBeInTheDocument();

    // Badges
    expect(screen.getByText(/No Credentials Required/i)).toBeInTheDocument();
    expect(screen.getByText(/Official Government Authentication Required/i)).toBeInTheDocument();

    // Buttons
    expect(screen.getByRole('button', { name: /Continue as Farmer/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In as Agricultural Expert/i })).toBeInTheDocument();

    // Verified model pillar
    expect(screen.getByText('Verified ML Engine')).toBeInTheDocument();
    expect(screen.getAllByText(/Production XGBoost Regressor/i)[0]).toBeInTheDocument();
  });

  it('clicking Continue as Farmer creates guest session and triggers navigation', async () => {
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

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <ViewModeProvider>
            <WelcomePage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    const farmerBtn = screen.getByRole('button', { name: /Continue as Farmer/i });
    await user.click(farmerBtn);

    await waitFor(() => {
      expect(guestSpy).toHaveBeenCalled();
    });
  });

  it('renders Expert Login form with default extension officer credentials hint', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <ViewModeProvider>
            <ExpertLoginPage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Agricultural Expert Sign-In')).toBeInTheDocument();
    expect(screen.getByLabelText(/Username or Official Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByText(/expert@aquamedi.gov.in/i)).toBeInTheDocument();
    expect(screen.getByText(/AquaExpert#2026/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Authenticate & Enter/i })).toBeInTheDocument();
  });

  it('submits expert login form to api.loginExpert and handles successful authentication', async () => {
    const user = userEvent.setup();
    const loginSpy = vi.spyOn(api, 'loginExpert').mockResolvedValue({
      access_token: 'mock_expert_jwt_token',
      token_type: 'bearer',
      role: 'expert',
      user: {
        email: 'expert@aquamedi.gov.in',
        full_name: 'Senior Agricultural Specialist',
        role: 'expert',
        department: 'Department of Agriculture',
      },
      expires_in_seconds: 28800,
      message: 'Authentication successful',
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <ViewModeProvider>
            <ExpertLoginPage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /Authenticate & Enter/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        username_or_email: 'expert@aquamedi.gov.in',
        password: 'AquaExpert#2026',
      });
    });
  });

  it('displays authentication error alert when login fails', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'loginExpert').mockRejectedValue(new Error('Invalid username/email or password. 4 attempt(s) remaining.'));

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <ViewModeProvider>
            <ExpertLoginPage />
          </ViewModeProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /Authenticate & Enter/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Invalid username\/email or password/i)).toBeInTheDocument();
    });
  });
});
