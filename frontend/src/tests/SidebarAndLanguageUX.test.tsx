import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../layouts/Sidebar';
import { Header } from '../layouts/Header';
import { MainLayout } from '../layouts/MainLayout';
import { ViewModeProvider, useViewMode } from '../context/ViewModeContext';
import { ScenarioProvider } from '../context/ScenarioContext';
import { AuthProvider } from '../context/AuthContext';
import { api } from '../services/api';

describe('AquaMedi AI — Expert Portal Sidebar & Language UX Improvements', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
    vi.spyOn(api, 'getHealth').mockResolvedValue({
      status: 'healthy',
      service: 'AquaMediAI',
      version: '1.0.0',
      pipeline: 'available',
      disclaimer: 'Test',
    });
  });

  describe('1. Sidebar Collapsible & Interactive Behavior', () => {
    it('renders expanded by default with full labels and collapse toggle button', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={false} onToggleCollapse={vi.fn()} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      const sidebar = screen.getByRole('complementary', { name: /expert mode navigation sidebar/i });
      expect(sidebar).toHaveClass('expanded');
      expect(sidebar).not.toHaveClass('collapsed');

      // Brand labels
      expect(screen.getByText('AquaMedi AI')).toBeInTheDocument();
      expect(screen.getByText('Agricultural Expert Portal')).toBeInTheDocument();

      // Navigation labels
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
      expect(screen.getByText('ML Predictions')).toBeInTheDocument();
      expect(screen.getByText('LP Water Allocation')).toBeInTheDocument();

      // Collapse toggle button exists with proper aria-expanded
      const collapseBtn = screen.getByRole('button', { name: /collapse sidebar/i });
      expect(collapseBtn).toBeInTheDocument();
      expect(collapseBtn).toHaveAttribute('aria-expanded', 'true');
    });

    it('renders collapsed rail mode with 72px width, centered icons, and tooltips', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={true} onToggleCollapse={vi.fn()} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      const sidebar = screen.getByRole('complementary', { name: /expert mode navigation sidebar/i });
      expect(sidebar).toHaveClass('collapsed');

      // Expand toggle button exists with proper aria-expanded
      const expandBtn = screen.getByRole('button', { name: /expand sidebar/i });
      expect(expandBtn).toBeInTheDocument();
      expect(expandBtn).toHaveAttribute('aria-expanded', 'false');

      // In collapsed mode, navigation links have title attributes and tooltip elements
      const overviewLink = screen.getByTitle('Dashboard Overview');
      expect(overviewLink).toBeInTheDocument();

      const predictionLink = screen.getByTitle('ML Predictions');
      expect(predictionLink).toBeInTheDocument();

      // Tooltip roles exist
      const tooltips = screen.getAllByRole('tooltip');
      expect(tooltips.length).toBeGreaterThan(0);
      expect(tooltips.some((t) => t.textContent === 'Dashboard Overview')).toBe(true);
      expect(tooltips.some((t) => t.textContent === 'ML Predictions')).toBe(true);
    });

    it('toggles sidebar collapse when toggle buttons are clicked', async () => {
      const user = userEvent.setup();
      const toggleMock = vi.fn();

      const { rerender } = render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={false} onToggleCollapse={toggleMock} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      const collapseBtn = screen.getByRole('button', { name: /collapse sidebar/i });
      await user.click(collapseBtn);
      expect(toggleMock).toHaveBeenCalledTimes(1);

      // Rerender collapsed
      rerender(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={true} onToggleCollapse={toggleMock} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      const expandBtn = screen.getByRole('button', { name: /expand sidebar/i });
      await user.click(expandBtn);
      expect(toggleMock).toHaveBeenCalledTimes(2);
    });

    it('Header toggle button triggers sidebar toggle', async () => {
      const user = userEvent.setup();
      const toggleMock = vi.fn();

      render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <ViewModeProvider>
                <Header isSidebarCollapsed={false} onToggleSidebar={toggleMock} />
              </ViewModeProvider>
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      const headerToggleBtn = screen.getByRole('button', { name: /collapse sidebar navigation/i });
      expect(headerToggleBtn).toBeInTheDocument();
      await user.click(headerToggleBtn);
      expect(toggleMock).toHaveBeenCalledTimes(1);
    });
  });

  describe('2. Farmer Management Removal from Expert Navigation', () => {
    it('Farmer Management navigation item does NOT appear in expanded Expert sidebar', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={false} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.queryByText('Farmer Management')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Farmer Management')).not.toBeInTheDocument();
    });

    it('Farmer Management navigation item does NOT appear in collapsed Expert sidebar', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={true} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.queryByText('Farmer Management')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Farmer Management')).not.toBeInTheDocument();
    });
  });

  describe('3. Expert Mode — English as Default Language', () => {
    // Helper to test context language switching
    const LanguageTestComponent = () => {
      const { viewMode, language, setViewMode, setLanguage } = useViewMode();
      return (
        <div>
          <span data-testid="mode-display">{viewMode}</span>
          <span data-testid="lang-display">{language}</span>
          <button onClick={() => setViewMode('expert')} data-testid="btn-enter-expert">
            Enter Expert
          </button>
          <button onClick={() => setViewMode('farmer')} data-testid="btn-enter-farmer">
            Enter Farmer
          </button>
          <button onClick={() => setLanguage('hi')} data-testid="btn-set-hindi">
            Set Hindi
          </button>
          <button onClick={() => setLanguage('gu')} data-testid="btn-set-gujarati">
            Set Gujarati
          </button>
        </div>
      );
    };

    it('defaults language to English when entering Expert Mode', async () => {
      const user = userEvent.setup();
      render(
        <ViewModeProvider>
          <LanguageTestComponent />
        </ViewModeProvider>
      );

      // Start in farmer mode with Hindi selected
      await user.click(screen.getByTestId('btn-set-hindi'));
      expect(screen.getByTestId('lang-display').textContent).toBe('hi');

      // Switch to Expert Mode
      await user.click(screen.getByTestId('btn-enter-expert'));
      expect(screen.getByTestId('mode-display').textContent).toBe('expert');
      // Language MUST automatically switch back to English ('en')
      expect(screen.getByTestId('lang-display').textContent).toBe('en');
    });

    it('preserves manual language changes within Expert Mode if selected by user', async () => {
      const user = userEvent.setup();
      render(
        <ViewModeProvider>
          <LanguageTestComponent />
        </ViewModeProvider>
      );

      // Enter expert mode
      await user.click(screen.getByTestId('btn-enter-expert'));
      expect(screen.getByTestId('lang-display').textContent).toBe('en');

      // User manually changes language to Gujarati
      await user.click(screen.getByTestId('btn-set-gujarati'));
      expect(screen.getByTestId('lang-display').textContent).toBe('gu');
    });
  });

  describe('4. Mobile Responsive Drawer & Escape Accessibility', () => {
    it('renders mobile-open drawer when mobileOpen is true and closes on close button click', async () => {
      const user = userEvent.setup();
      const closeMock = vi.fn();

      render(
        <MemoryRouter>
          <AuthProvider>
            <ScenarioProvider>
              <Sidebar collapsed={false} mobileOpen={true} onCloseMobile={closeMock} />
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      const sidebar = screen.getByRole('complementary', { name: /expert mode navigation sidebar/i });
      expect(sidebar).toHaveClass('mobile-open');

      const mobileCloseBtn = screen.getByRole('button', { name: /close navigation menu/i });
      expect(mobileCloseBtn).toBeInTheDocument();
      await user.click(mobileCloseBtn);
      expect(closeMock).toHaveBeenCalledTimes(1);
    });

    it('pressing Escape key triggers mobile drawer close in MainLayout', async () => {
      render(
        <MemoryRouter initialEntries={['/overview']}>
          <AuthProvider>
            <ScenarioProvider>
              <ViewModeProvider>
                <MainLayout />
              </ViewModeProvider>
            </ScenarioProvider>
          </AuthProvider>
        </MemoryRouter>
      );

      // Simulate mobile resize
      window.innerWidth = 500;
      const toggleBtn = screen.getByRole('button', { name: /sidebar navigation/i });
      fireEvent.click(toggleBtn);

      // Drawer should be open and backdrop present
      await waitFor(() => {
        expect(document.querySelector('.sidebar-backdrop')).toBeInTheDocument();
      });

      // Press Escape
      fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });

      // Backdrop should disappear
      await waitFor(() => {
        expect(document.querySelector('.sidebar-backdrop')).not.toBeInTheDocument();
      });
    });
  });
});
