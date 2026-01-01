import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { portfolioApi } from '../lib/api';

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
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load tenants and portfolios on mount
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load portfolios when tenant changes
  useEffect(() => {
    if (selectedTenantId) {
      loadPortfolios(selectedTenantId);
    }
  }, [selectedTenantId]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // TODO: Fetch from API
      // For now, use default tenant
      const defaultTenant: Tenant = { id: 'default', name: 'Default Tenant' };
      setTenants([defaultTenant]);
      setSelectedTenantId('default');

      // Load portfolios for default tenant
      await loadPortfolios('default');
    } catch (error) {
      console.error('Error loading initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolios = async (tenantId: string) => {
    try {
      // Fetch from API
      const apiPortfolios = await portfolioApi.list(tenantId);

      // Fetch overview for each portfolio to get totalValue and positionCount
      const portfoliosWithSummary: Portfolio[] = await Promise.all(
        apiPortfolios.map(async (p) => {
          try {
            const overview = await portfolioApi.getOverview(tenantId, p.id);
            return {
              id: p.id,
              name: p.name,
              description: p.description,
              tenantId: tenantId,
              userId: p.user_id,
              totalValue: overview.kpis.total_value,
              positionCount: overview.positions.length,
              autoTradingEnabled: overview.portfolio.state === 'RUNNING',
              created_at: p.created_at,
              updated_at: p.updated_at,
            };
          } catch (err) {
            // If overview fails, return basic portfolio info
            console.warn(`Failed to load overview for portfolio ${p.id}:`, err);
            return {
              id: p.id,
              name: p.name,
              description: p.description,
              tenantId: tenantId,
              userId: p.user_id,
              totalValue: 0,
              positionCount: 0,
              autoTradingEnabled: false,
              created_at: p.created_at,
              updated_at: p.updated_at,
            };
          }
        }),
      );

      setPortfolios(portfoliosWithSummary);

      // Auto-select first portfolio if none selected
      if (portfoliosWithSummary.length > 0) {
        setSelectedPortfolioId((current) => {
          if (!current && portfoliosWithSummary.length > 0) {
            return portfoliosWithSummary[0].id;
          }
          return current;
        });
      }
    } catch (error) {
      console.error('Error loading portfolios:', error);
      // Fallback to empty array on error
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
