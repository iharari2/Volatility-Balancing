import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { portfolioApi } from '../lib/api';
import { useAuth } from './AuthContext';

interface Tenant {
  id: string;
  name: string;
}

interface Portfolio {
  id: string;
  name: string;
  description?: string | null;
  tenantId: string;
  userId?: string;
  totalValue?: number;
  positionCount?: number;
  autoTradingEnabled?: boolean;
  state?: string;
  created_at?: string;
  updated_at?: string;
}

interface TenantPortfolioContextType {
  tenants: Tenant[];
  portfolios: Portfolio[];
  selectedTenantId: string | null;
  selectedPortfolioId: string | null;
  selectedTenant: Tenant | null;
  selectedPortfolio: Portfolio | null;
  setSelectedTenantId: (tenantId: string) => void;
  setSelectedPortfolioId: (portfolioId: string) => void;
  refreshPortfolios: () => Promise<void>;
  loading: boolean;
}

const TenantPortfolioContext = createContext<TenantPortfolioContextType | undefined>(undefined);

export const useTenantPortfolio = () => {
  const context = useContext(TenantPortfolioContext);
  if (!context) {
    throw new Error('useTenantPortfolio must be used within TenantPortfolioProvider');
  }
  return context;
};

interface TenantPortfolioProviderProps {
  children: ReactNode;
}

export function TenantPortfolioProvider({ children }: TenantPortfolioProviderProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Derive tenant from authenticated user
  const tenantId = user?.tenant_id || 'default';

  // Load tenants and portfolios when user is available
  useEffect(() => {
    loadInitialData();
  }, [tenantId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load portfolios when tenant changes
  useEffect(() => {
    if (selectedTenantId) {
      loadPortfolios(selectedTenantId);
    }
  }, [selectedTenantId]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const tenant: Tenant = { id: tenantId, name: user?.display_name ? `${user.display_name}'s Tenant` : 'My Tenant' };
      setTenants([tenant]);
      setSelectedTenantId(tenantId);

      // Load portfolios for user's tenant
      await loadPortfolios(tenantId);
    } catch (error) {
      console.error('Error loading initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolios = async (tenantId: string) => {
    try {
      const apiPortfolios = await portfolioApi.list(tenantId);

      // Show portfolios immediately with basic info — don't block on overview calls
      const basicPortfolios: Portfolio[] = apiPortfolios.map((p) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        tenantId: tenantId,
        userId: p.user_id,
        created_at: p.created_at,
        updated_at: p.updated_at,
      }));

      setPortfolios(basicPortfolios);

      // Auto-select first portfolio if none selected
      if (basicPortfolios.length > 0) {
        setSelectedPortfolioId((current) => {
          if (!current) return basicPortfolios[0].id;
          return current;
        });
      } else {
        const noRedirect = ['/onboarding', '/login', '/forgot-password', '/reset-password'];
        if (!noRedirect.includes(location.pathname)) {
          navigate('/onboarding', { replace: true });
        }
      }

      // Enrich with overview data in background (non-blocking)
      apiPortfolios.forEach(async (p) => {
        try {
          const overview = await portfolioApi.getOverview(tenantId, p.id);
          setPortfolios((prev) =>
            prev.map((existing) =>
              existing.id === p.id
                ? {
                    ...existing,
                    totalValue: overview.kpis.total_value,
                    positionCount: overview.positions.length,
                    autoTradingEnabled: overview.portfolio.state === 'RUNNING',
                  }
                : existing,
            ),
          );
        } catch {
          // Overview enrichment is best-effort; ignore failures
        }
      });
    } catch (error) {
      console.error('Error loading portfolios:', error);
      setPortfolios([]);
    }
  };

  const refreshPortfolios = async () => {
    if (selectedTenantId) {
      await loadPortfolios(selectedTenantId);
    }
  };

  const selectedTenant = tenants.find((t) => t.id === selectedTenantId) || null;
  const selectedPortfolio = portfolios.find((p) => p.id === selectedPortfolioId) || null;

  return (
    <TenantPortfolioContext.Provider
      value={{
        tenants,
        portfolios,
        selectedTenantId,
        selectedPortfolioId,
        selectedTenant,
        selectedPortfolio,
        setSelectedTenantId,
        setSelectedPortfolioId,
        refreshPortfolios,
        loading,
      }}
    >
      {children}
    </TenantPortfolioContext.Provider>
  );
}
