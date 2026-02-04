/**
 * Portfolio-Scoped API Service
 *
 * All endpoints MUST include tenant_id and portfolio_id.
 * This service ensures strict portfolio scoping as per spec.
 */

const API_BASE = '/api/v1';

interface ApiResponse<T> {
  data?: T;
  trace_id?: string;
  error?: string;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

export interface PortfolioPosition {
  id: string;
  ticker?: string; // Legacy field name
  asset?: string; // New field name from backend
  qty: number;
  cash?: number; // Cash lives in PositionCell
  anchor_price: number | null;
  avg_cost?: number | null;
  last_price?: number;
  total_dividends_received?: number;
  position_value?: number;
  weight_pct?: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
  status?: string; // RUNNING / PAUSED
}

// REMOVED: PortfolioCash interface - Cash is now stored in Position entities
// Calculate total cash by summing position.cash values

export interface EffectiveConfig {
  trigger_threshold_up_pct: number;
  trigger_threshold_down_pct: number;
  min_stock_pct: number;
  max_stock_pct: number;
  max_trade_pct_of_position: number;
  commission_rate: number;
  market_hours_policy: 'market-open-only' | 'market-plus-after-hours';
  last_updated: string;
  version: number;
}

export interface PortfolioConfig {
  trigger_threshold_up_pct: number;
  trigger_threshold_down_pct: number;
  min_stock_pct: number;
  max_stock_pct: number;
  max_trade_pct_of_position: number;
  commission_rate: number;
  market_hours_policy: 'market-open-only' | 'market-plus-after-hours';
}

export interface PerAssetOverride {
  asset: string;
  override_type: 'commission' | 'triggers' | 'guardrails';
  values: Record<string, any>;
}

export interface AddPositionRequest {
  asset: string; // Backend expects 'asset', not 'symbol'
  qty: number;
  anchor_price?: number;
  avg_cost?: number;
  cash?: number;
}

export interface AdjustPositionRequest {
  operation: 'BUY' | 'SELL' | 'SET_QTY';
  qty: number;
  price?: number;
  reason: string;
}

export interface CashTransactionRequest {
  amount: number;
  reason: string;
  position_id?: string; // Optional: deposit/withdraw to/from specific position
}

// Analytics types for ANA-2 through ANA-5
export interface AnalyticsEvent {
  date: string;
  type: 'TRADE' | 'DIVIDEND';
  side?: 'BUY' | 'SELL';
  qty?: number;
  price?: number;
  commission?: number;
  gross_amount?: number;
  net_amount?: number;
  shares_held?: number;
  dps?: number;
  position_id?: string;
  asset_symbol?: string;
}

export interface AnalyticsGuardrails {
  min_stock_pct: number;
  max_stock_pct: number;
}

export interface AnalyticsPerformance {
  alpha: number;
  portfolio_return_pct: number;
  benchmark_return_pct: number;
  spy_return_pct?: number;
  spy_alpha?: number;
}

export interface AnalyticsTimeSeriesPoint {
  date: string;
  value: number;
  stock: number;
  cash: number;
  stock_pct: number;
  cash_pct: number;
}

export interface AnalyticsData {
  time_series: AnalyticsTimeSeriesPoint[];
  events: AnalyticsEvent[];
  guardrails: AnalyticsGuardrails | null;
  performance: AnalyticsPerformance;
  kpis: {
    volatility: number;
    max_drawdown: number;
    sharpe_like: number;
    pnl_pct: number;
    commission_total: number;
    dividend_total: number;
  };
  allocation: Record<string, { value: number; percentage: number }>;
  diversification: {
    num_tickers: number;
    num_positions: number;
  };
}

class PortfolioScopedApi {
  /**
   * Load positions for a portfolio
   */
  async getPositions(tenantId: string, portfolioId: string): Promise<PortfolioPosition[]> {
    return request<PortfolioPosition[]>(`/tenants/${tenantId}/portfolios/${portfolioId}/positions`);
  }

  /**
   * Calculate total cash from positions (cash is stored in Position entities)
   */
  async getTotalCash(tenantId: string, portfolioId: string): Promise<number> {
    const positions = await this.getPositions(tenantId, portfolioId);
    return positions.reduce((total, pos) => total + (pos.cash || 0), 0);
  }

  /**
   * Load effective config (read-only, what engine uses)
   */
  async getEffectiveConfig(tenantId: string, portfolioId: string): Promise<EffectiveConfig> {
    return request<EffectiveConfig>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/config/effective`,
    );
  }

  /**
   * Load editable config
   */
  async getConfig(tenantId: string, portfolioId: string): Promise<PortfolioConfig> {
    return request<PortfolioConfig>(`/tenants/${tenantId}/portfolios/${portfolioId}/config`);
  }

  /**
   * Update portfolio config
   */
  async updateConfig(
    tenantId: string,
    portfolioId: string,
    config: PortfolioConfig,
  ): Promise<ApiResponse<void>> {
    return request<ApiResponse<void>>(`/tenants/${tenantId}/portfolios/${portfolioId}/config`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  /**
   * Add a position to portfolio
   */
  async addPosition(
    tenantId: string,
    portfolioId: string,
    position: AddPositionRequest,
  ): Promise<ApiResponse<PortfolioPosition>> {
    return request<ApiResponse<PortfolioPosition>>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/positions`,
      {
        method: 'POST',
        body: JSON.stringify(position),
      },
    );
  }

  /**
   * Adjust position (manual correction)
   */
  async adjustPosition(
    tenantId: string,
    portfolioId: string,
    asset: string,
    adjustment: AdjustPositionRequest,
  ): Promise<ApiResponse<void>> {
    return request<ApiResponse<void>>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/positions/${asset}/adjust`,
      {
        method: 'POST',
        body: JSON.stringify(adjustment),
      },
    );
  }

  /**
   * Set anchor price for an asset
   */
  async setAnchor(
    tenantId: string,
    portfolioId: string,
    asset: string,
    anchorPrice: number,
  ): Promise<ApiResponse<void>> {
    return request<ApiResponse<void>>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/positions/${asset}/anchor`,
      {
        method: 'POST',
        body: JSON.stringify({ anchor_price: anchorPrice }),
      },
    );
  }

  /**
   * Deposit cash
   */
  async depositCash(
    tenantId: string,
    portfolioId: string,
    transaction: CashTransactionRequest,
  ): Promise<ApiResponse<void>> {
    // Use /api/v1 prefix for portfolio routes
    const url = `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/cash/deposit`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(transaction),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Withdraw cash
   */
  async withdrawCash(
    tenantId: string,
    portfolioId: string,
    transaction: CashTransactionRequest,
  ): Promise<ApiResponse<void>> {
    // Use /api/v1 prefix for portfolio routes
    const url = `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/cash/withdraw`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(transaction),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Remove a position from portfolio
   */
  async removePosition(tenantId: string, portfolioId: string, positionId: string): Promise<void> {
    const url = `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }
  }

  /**
   * Load per-asset overrides
   */
  async getOverrides(tenantId: string, portfolioId: string): Promise<PerAssetOverride[]> {
    return request<PerAssetOverride[]>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/config/overrides`,
    );
  }

  /**
   * Get position-specific configuration
   */
  async getPositionConfig(
    tenantId: string,
    portfolioId: string,
    positionId: string,
  ): Promise<{
    trigger_threshold_up_pct: number;
    trigger_threshold_down_pct: number;
    min_stock_pct: number;
    max_stock_pct: number;
    max_trade_pct_of_position: number;
    commission_rate: number;
    allow_after_hours: boolean;
    is_position_specific: boolean;
  }> {
    return request(`/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/config`);
  }

  /**
   * Update position-specific configuration
   */
  async updatePositionConfig(
    tenantId: string,
    portfolioId: string,
    positionId: string,
    config: {
      trigger_threshold_up_pct?: number;
      trigger_threshold_down_pct?: number;
      min_stock_pct?: number;
      max_stock_pct?: number;
      max_trade_pct_of_position?: number;
      commission_rate?: number;
    },
  ): Promise<ApiResponse<void>> {
    return request(
      `/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/config`,
      {
        method: 'PUT',
        body: JSON.stringify(config),
      },
    );
  }

  /**
   * Get portfolio analytics
   * @param positionId - Optional position ID to filter analytics to a single position
   */
  async getAnalytics(tenantId: string, portfolioId: string, days: number = 30, positionId?: string): Promise<AnalyticsData> {
    const positionParam = positionId && positionId !== 'all' ? `&position_id=${positionId}` : '';
    return request<AnalyticsData>(`/tenants/${tenantId}/portfolios/${portfolioId}/analytics?days=${days}${positionParam}`);
  }

  /**
   * Update per-asset overrides
   */
  async updateOverrides(
    tenantId: string,
    portfolioId: string,
    overrides: PerAssetOverride[],
  ): Promise<ApiResponse<void>> {
    return request<ApiResponse<void>>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/config/overrides`,
      {
        method: 'PUT',
        body: JSON.stringify({ overrides }),
      },
    );
  }
}

export const portfolioScopedApi = new PortfolioScopedApi();







