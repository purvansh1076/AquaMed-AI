/**
 * AquaMediAI — Authentication & Role-Based Access Context
 * =======================================================
 * Manages user authentication, Farmer Guest sessions, Agricultural Expert login,
 * token persistence, and role-based permissions throughout the application.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../services/api';
import type { GuestSessionResponse, UserProfile } from '../types/api';

export type UserRole = 'farmer_guest' | 'expert' | null;

interface AuthContextType {
  role: UserRole;
  user: UserProfile | null;
  guestSession: GuestSessionResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isFarmerGuest: boolean;
  isLoading: boolean;
  authError: string | null;
  clearAuthError: () => void;
  continueAsFarmer: () => Promise<void>;
  loginAsExpert: (usernameOrEmail: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_STORAGE_KEY = 'aquamedi_auth_session';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRole] = useState<UserRole>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSessionResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [authError, setAuthError] = useState<string | null>(null);

  // Rehydrate saved session on load
  useEffect(() => {
    try {
      const savedRaw = localStorage.getItem(AUTH_STORAGE_KEY);
      if (savedRaw) {
        const saved = JSON.parse(savedRaw);
        if (saved.token) {
          api.setAuthToken(saved.token);
          setToken(saved.token);
          setRole(saved.role || null);
          setUser(saved.user || null);
          setGuestSession(saved.guestSession || null);
        }
      }
    } catch {
      // Storage parsing failed, clear
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const persistSession = (
    newRole: UserRole,
    newToken: string | null,
    newUser: UserProfile | null,
    newGuest: GuestSessionResponse | null
  ) => {
    setRole(newRole);
    setToken(newToken);
    setUser(newUser);
    setGuestSession(newGuest);
    api.setAuthToken(newToken);

    try {
      if (newToken) {
        localStorage.setItem(
          AUTH_STORAGE_KEY,
          JSON.stringify({
            role: newRole,
            token: newToken,
            user: newUser,
            guestSession: newGuest,
          })
        );
      } else {
        localStorage.removeItem(AUTH_STORAGE_KEY);
      }
    } catch {
      // Storage unavailable
    }
  };

  const clearAuthError = () => setAuthError(null);

  const continueAsFarmer = async (): Promise<void> => {
    setIsLoading(true);
    setAuthError(null);
    try {
      // Request guest session from backend
      const session = await api.createGuestSession();
      persistSession('farmer_guest', session.access_token, null, session);
    } catch (err: unknown) {
      // Graceful offline fallback: create client-side guest session so farmer is never blocked
      const fallbackToken = `guest_offline_${Date.now()}`;
      const fallbackSession: GuestSessionResponse = {
        access_token: fallbackToken,
        token_type: 'bearer',
        role: 'farmer_guest',
        session_id: `guest_local_${Date.now().toString(36)}`,
        display_name: 'Farmer Guest',
        permissions: ['farmer:read', 'farmer:predict'],
        expires_in_seconds: 86400,
      };
      persistSession('farmer_guest', fallbackToken, null, fallbackSession);
      console.warn('Backend offline; initialized offline guest farmer session');
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsExpert = async (usernameOrEmail: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const response = await api.loginExpert({
        username_or_email: usernameOrEmail,
        password,
      });
      persistSession('expert', response.access_token, response.user, null);
      return true;
    } catch (err: unknown) {
      // Demo credential fallback for prototype in development/test environments only
      const isDevOrTest = import.meta.env.DEV || import.meta.env.MODE === 'test';
      if (isDevOrTest && usernameOrEmail === 'admin123' && password === '12345678') {
        const demoToken = `demo_expert_${Date.now()}`;
        const demoUser = {
          email: 'admin123@aquamedi.gov.in',
          full_name: 'Demo Expert Admin (Development)',
          role: 'expert' as const,
          department: 'Agricultural Intelligence',
        };
        persistSession('expert', demoToken, demoUser, null);
        return true;
      }
      const msg = err instanceof Error ? err.message : 'Invalid expert credentials';
      setAuthError(msg);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      if (token) {
        await api.logout().catch(() => {});
      }
    } finally {
      persistSession(null, null, null, null);
      setIsLoading(false);
    }
  };

  const isAuthenticated = role === 'expert' && !!token;
  const isFarmerGuest = role === 'farmer_guest';

  return (
    <AuthContext.Provider
      value={{
        role,
        user,
        guestSession,
        token,
        isAuthenticated,
        isFarmerGuest,
        isLoading,
        authError,
        clearAuthError,
        continueAsFarmer,
        loginAsExpert,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

