import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useTenantPortfolio } from './TenantPortfolioContext';

export interface PositionConfig {
  buyTrigger: number;
  sellTrigger: number;
  lowGuardrail: number;
  highGuardrail: number;
  rebalanceRatio: number;
  minQuantity: number;
  commission: number;
  dividendTax: number;
  tradeAfterHours: boolean;
}

export const DEFAULT_CONFIG: PositionConfig = {
  buyTrigger: -0.03,
  sellTrigger: 0.03,
  lowGuardrail: 0.25,
  highGuardrail: 0.75,
  rebalanceRatio: 1.66667,
  minQuantity: 1,
  commission: 0.0001,
  dividendTax: 0.25,
  tradeAfterHours: true,
};

export interface Position {
  id: string;
  ticker: string;
  asset?: string; // Alias for ticker (backward compatibility)
  name: string;
  qty: number;
  units: number;
  cash: number;
  cashAmount: number;
  assetAmount: number;
  currentPrice: number;
  anchorPrice: number;
  anchor_price?: number; // Alias for anchorPrice (backward compatibility)
  marketValue: number;
  pnl: number;
  pnlPercent: number;
  isActive: boolean;
  isArchived: boolean;
  lastTrade: string;
  shares: number;
  config: PositionConfig;
}

// Helper to create a complete position with defaults
export function createPosition(partial: Partial<Position>): Position {
  const qty = partial.qty ?? partial.units ?? 0;
  const currentPrice = partial.currentPrice ?? partial.anchorPrice ?? 0;
  const assetAmount = partial.assetAmount ?? qty * currentPrice;
  const cashAmount = partial.cashAmount ?? partial.cash ?? 0;
  const marketValue = partial.marketValue ?? assetAmount;
  const anchorPrice = partial.anchorPrice ?? currentPrice;

  const ticker = partial.ticker ?? partial.asset ?? '';
  return {
    id: partial.id ?? '',
    ticker,
    asset: ticker, // Alias for backward compatibility
    name: partial.name ?? ticker,
    qty,
    units: qty,
    cash: cashAmount,
    cashAmount,
    assetAmount,
    currentPrice,
    anchorPrice,
    anchor_price: anchorPrice, // Alias for backward compatibility
    marketValue,
    pnl: partial.pnl ?? 0,
    pnlPercent: partial.pnlPercent ?? 0,
    isActive: partial.isActive ?? true,
    isArchived: partial.isArchived ?? false,
    lastTrade: partial.lastTrade ?? '',
    shares: partial.shares ?? qty,
    config: { ...DEFAULT_CONFIG, ...partial.config },
  };
}

interface PortfolioOverview {
  portfolio: {
    id: string;
    name: string;
    state: string;
    type: string;
    hours_policy: string;
  };
  cash: {
    currency: string;
    cash_balance: number;
    reserved_cash: number;
  };
  positions: Array<{
    asset: string;
    qty: number;
    anchor: number | null;
    avg_cost: number | null;
  }>;
  config_effective: {
    trigger_up_pct: number;
    trigger_down_pct: number;
    min_stock_pct: number;
    max_stock_pct: number;
    max_trade_pct_of_position: number | null;
    commission_rate_pct: number;
  };
  kpis: {
    total_value: number;
    stock_pct: number;
    cash_pct: number;
    pnl_pct: number;
    pnl_abs?: number;
  };
}

interface PortfolioContextType {
  positions: Position[];
  overview: PortfolioOverview | null;
  loading: boolean;
  error: string | null;
  addPosition: (position: Partial<Position>) => Promise<void>;
  updatePosition: (id: string, updates: Partial<Position>) => Promise<void>;
  archivePosition: (id: string) => Promise<void>;
  getActivePositions: () => Position[];
  getArchivedPositions: () => Position[];
  clearError: () => void;
  refresh: () => Promise<void>;
}

const PortfolioContext = createContext<PortfolioContextType | undefined>(undefined);

export const usePortfolio = () => {
  const context = useContext(PortfolioContext);
  if (!context) {
    throw new Error('usePortfolio must be used within PortfolioProvider');
  }
  return context;
};

interface PortfolioProviderProps {
  children: ReactNode;
}

export function PortfolioProvider({ children }: PortfolioProviderProps) {
  const { selectedPortfolioId, selectedTenantId } = useTenantPortfolio();
  const [positions, setPositions] = useState<Position[]>([]);
  const [overview, setOverview] = useState<PortfolioOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedPortfolioId && selectedTenantId) {
      loadData();
    } else {
      setPositions([]);
      setOverview(null);
      setLoading(false);
    }
  }, [selectedPortfolioId, selectedTenantId]);

  const loadData = async () => {
    if (!selectedPortfolioId || !selectedTenantId) return;

    setLoading(true);
    setError(null);
    try {
      const { portfolioApi } = await import('../lib/api');

      // Fetch positions and overview in parallel
      const [apiPositions, apiOverview] = await Promise.all([
        portfolioApi.getPositions(selectedTenantId, selectedPortfolioId),
        portfolioApi.getOverview(selectedTenantId, selectedPortfolioId),
      ]);

      // Transform API positions to Position format using createPosition helper
      const transformedPositions: Position[] = apiPositions.map((pos: any) =>
        createPosition({
          id: pos.id,
          ticker: pos.asset,
          name: pos.asset, // Will be updated with company name if available
          qty: pos.qty,
          anchorPrice: pos.anchor_price ?? 0,
          currentPrice: pos.anchor_price ?? 0, // Will be updated with market data
          cashAmount: pos.cash ?? 0,
          marketValue: pos.qty * (pos.anchor_price || 0),
          isActive: true,
          isArchived: false,
        })
      );

      setPositions(transformedPositions);
      setOverview(apiOverview);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio data');
      console.error('Error loading portfolio data:', err);
    } finally {
      setLoading(false);
    }
  };

  const addPosition = async (position: Partial<Position>) => {
    if (!selectedPortfolioId || !selectedTenantId) {
      throw new Error('No portfolio selected');
    }

    try {
      // Call API to create position
      const { positionsApi, portfolioApi } = await import('../lib/api');

      // Create position first
      const createdPosition = await positionsApi.create({
        ticker: position.ticker || '',
        qty: position.qty || position.units || 0,
        cash: position.cashAmount || 0,
        anchor_price: position.anchorPrice || position.currentPrice || undefined,
      });

      // Link to portfolio
      await portfolioApi.addPosition(selectedTenantId, selectedPortfolioId, createdPosition.id);

      // Reload data to get updated data
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add position');
      throw err;
    }
  };

  const updatePosition = async (id: string, updates: Partial<Position>) => {
    if (!selectedPortfolioId || !selectedTenantId) {
      throw new Error('No portfolio selected');
    }

    try {
      // Update position via API
      const { positionsApi } = await import('../lib/api');

      // If anchor price is being updated, use the setAnchor endpoint
      if (updates.anchorPrice !== undefined) {
        await positionsApi.setAnchor(id, updates.anchorPrice);
      }

      // Reload data to get updated data
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update position');
      throw err;
    }
  };

  const archivePosition = async (id: string) => {
    if (!selectedPortfolioId || !selectedTenantId) {
      throw new Error('No portfolio selected');
    }

    try {
      // Remove position from portfolio via API
      const { portfolioApi } = await import('../lib/api');
      await portfolioApi.removePosition(selectedTenantId, selectedPortfolioId, id);

      // Reload data to get updated data
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive position');
      throw err;
    }
  };

  const getActivePositions = () => {
    return positions.filter((pos) => pos.isActive !== false && pos.isArchived !== true);
  };

  const getArchivedPositions = () => {
    return positions.filter((pos) => pos.isArchived === true);
  };

  const clearError = () => {
    setError(null);
  };

  const refresh = async () => {
    await loadData();
  };

  return (
    <PortfolioContext.Provider
      value={{
        positions,
        overview,
        loading,
        error,
        addPosition,
        updatePosition,
        archivePosition,
        getActivePositions,
        getArchivedPositions,
        clearError,
        refresh,
      }}
    >
      {children}
    </PortfolioContext.Provider>
  );
}
