import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { authApi, AuthUser } from '../lib/api';

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  impersonating: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => void;
  startImpersonation: (token: string, user: AuthUser) => void;
  exitImpersonation: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [impersonating, setImpersonating] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem('impersonating_user');
    return saved ? JSON.parse(saved) : null;
  });

  // Validate existing token on mount
  useEffect(() => {
    if (token) {
      authApi
        .me()
        .then((u) => setUser(u))
        .catch(() => {
          localStorage.removeItem('auth_token');
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    localStorage.setItem('auth_token', res.token);
    setToken(res.token);
    setUser(res.user);
  }, []);

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    const res = await authApi.register(email, password, displayName);
    localStorage.setItem('auth_token', res.token);
    setToken(res.token);
    setUser(res.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('admin_token');
    localStorage.removeItem('impersonating_user');
    setToken(null);
    setUser(null);
    setImpersonating(null);
  }, []);

  const startImpersonation = useCallback((impToken: string, impUser: AuthUser) => {
    // Stash current admin token
    const adminToken = localStorage.getItem('auth_token');
    if (adminToken) localStorage.setItem('admin_token', adminToken);
    localStorage.setItem('auth_token', impToken);
    localStorage.setItem('impersonating_user', JSON.stringify(impUser));
    setToken(impToken);
    setUser(impUser);
    setImpersonating(impUser);
  }, []);

  const exitImpersonation = useCallback(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) return;
    localStorage.setItem('auth_token', adminToken);
    localStorage.removeItem('admin_token');
    localStorage.removeItem('impersonating_user');
    setToken(adminToken);
    setImpersonating(null);
    // Re-fetch admin user info
    authApi.me().then(setUser).catch(() => {});
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        impersonating,
        login,
        register,
        logout,
        startImpersonation,
        exitImpersonation,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
