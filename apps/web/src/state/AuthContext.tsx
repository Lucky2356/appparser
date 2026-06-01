import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api } from "../api/client";
import type { User } from "../types";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const STORAGE_KEY = "appsparcer.token";

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      if (!token) {
        setIsLoading(false);
        setUser(null);
        return;
      }

      try {
        const currentUser = await api.me(token);
        if (!cancelled) {
          setUser(currentUser);
        }
      } catch {
        if (!cancelled) {
          localStorage.removeItem(STORAGE_KEY);
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadUser();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const saveSession = useCallback((nextToken: string, nextUser: User) => {
    localStorage.setItem(STORAGE_KEY, nextToken);
    setToken(nextToken);
    setUser(nextUser);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.login(email, password);
      saveSession(response.accessToken, response.user);
    },
    [saveSession]
  );

  const register = useCallback(
    async (email: string, password: string) => {
      const response = await api.register(email, password);
      saveSession(response.accessToken, response.user);
    },
    [saveSession]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ token, user, isLoading, login, register, logout }),
    [token, user, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
