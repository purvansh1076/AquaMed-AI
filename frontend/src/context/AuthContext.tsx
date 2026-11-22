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
  offline: boolean;
  authError: string | null;
  clearAuthError: () => void;
  continueAsFarmer: () => Promise<void>;
  loginAsExpert: (usernameOrEmail: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_STORAGE_KEY = 'aquamedi_auth_session';

/**
 * Decode a JWT payload and determine whether it is expired or malformed.
 * This is only a local convenience check; the backend remains authoritative.
 */
function isTokenExpired(token: string): boolean {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return true;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
    const payload = JSON.parse(atob(padded)) as { exp?: unknown };
    if (typeof payload.exp !== 'number') return true;
    return payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRole] = useState<UserRole>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSessionResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [offline, setOffline] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const clearSession = () => {
    setRole(null);
    setToken(null);
    setUser(null);
    setGuestSession(null);
    api.setAuthToken(null);
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } catch {
      // Storage unavailable
    }
  };

  // Rehydrate saved session on load, rejecting expired or malformed tokens.
  useEffect(() => {
    let cancelled = false;

    const rehydrate = async () => {
      try {
        const savedRaw = localStorage.getItem(AUTH_STORAGE_KEY);
        if (!savedRaw) {
          // Drop any stale token left over from an earlier partial session.
          api.setAuthToken(null);
          return;
        }

        const saved = JSON.parse(savedRaw) as {
          token?: string;
          role?: UserRole;
          user?: UserProfile | null;
          guestSession?: GuestSessionResponse | null;
        };

        if (!saved.token || isTokenExpired(saved.token)) {
          clearSession();
          return;
        }

        api.setAuthToken(saved.token);
        if (cancelled) return;
        setToken(saved.token);
        setRole(saved.role || null);
        setUser(saved.user || null);
        setGuestSession(saved.guestSession || null);

        // Validate the session against the backend (the authority). The
        // backend-resolved role overrides whatever localStorage claimed, so a
        // tampered saved role cannot escalate UI privileges.
        try {
          const identity = await api.getIdentity();
          if (cancelled) return;
          if (identity.role === 'expert' || identity.role === 'admin') {
            setRole('expert');
          } else if (identity.role === 'farmer_guest') {
            setRole('farmer_guest');
          } else {
            clearSession();
          }
        } catch (err: unknown) {
          const statusCode = (err as { statusCode?: number }).statusCode;
          if (statusCode === 401) {
            clearSession();
          } else {
            setOffline(true);
          }
        }
      } catch {
        clearSession();
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    void rehydrate();
    return () => {
      cancelled = true;
    };
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
    setOffline(false);
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
    setOffline(false);
    try {
      const session = await api.createGuestSession();
      persistSession('farmer_guest', session.access_token, null, session);
    } catch (err: unknown) {
      // Do not invent an offline session. Surface the failure and let the
      // existing backend-disconnected banner explain the state.
      const msg = err instanceof Error ? err.message : 'Unable to start a farmer session.';
      setAuthError(msg);
      setOffline(true);
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsExpert = async (usernameOrEmail: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setAuthError(null);
    setOffline(false);
    try {
      const response = await api.loginExpert({
        username_or_email: usernameOrEmail,
        password,
      });
      persistSession('expert', response.access_token, response.user, null);
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid expert credentials';
      setAuthError(msg);
      const statusCode = (err as { statusCode?: number }).statusCode;
      if (!statusCode || statusCode === 0) setOffline(true);
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
      clearSession();
      setOffline(false);
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
        offline,
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
