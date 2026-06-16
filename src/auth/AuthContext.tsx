import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { clearTokens, fetchMe, getAccessToken, login as apiLogin } from '../services/api';
import type { SessionUser, UserProfile } from '../types';

type AuthContextValue = {
  user: SessionUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<SessionUser>;
  logout: () => void;
  reloadUser: () => Promise<SessionUser | null>;
  hasAnyProfile: (profiles: UserProfile[]) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Mantem usuario, tokens e carregamento de sessao disponiveis para toda a aplicacao.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);

  const reloadUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const session = await fetchMe();
      setUser(session);
      return session;
    } catch {
      clearTokens();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reloadUser();
  }, [reloadUser]);

  const handleLogin = useCallback(async (username: string, password: string) => {
    await apiLogin(username, password);
    const session = await fetchMe();
    setUser(session);
    return session;
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login: handleLogin,
      logout,
      reloadUser,
      hasAnyProfile: (profiles) => profiles.includes(user?.profile ?? null),
    }),
    [handleLogin, loading, logout, reloadUser, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Acessa o estado autenticado e falha cedo se usado fora do provider.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider.');
  }
  return context;
}
