const API_BASE = '/api/portfolios';

export interface PortfolioListItem {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PositionSummaryItem {
  position_id: string;
  asset_symbol: string;
  qty: number;
  cash: number;
  last_price: number | null;
  stock_value: number;
  total_value: number;
  stock_pct: number | null;
  position_vs_baseline_pct: number | null;
  stock_vs_baseline_pct: number | null;
  status?: string | null;
}

export interface CockpitResponse {
  position_summary: {
    position_id: string;
    asset_symbol: string;
    qty: number;
    cash: number;
    last_price: number | null;
    stock_value: number;
    total_value: number;
    anchor_price: number | null;
    avg_cost: number | null;
  };
  baseline_comparison: {
    baseline_price: number | null;
    baseline_total_value: number | null;
    baseline_stock_value: number | null;
    position_vs_baseline_pct: number | null;
    position_vs_baseline_abs: number | null;
    stock_vs_baseline_pct: number | null;
    stock_vs_baseline_abs: number | null;
  };
  allocation_band: {
    min_stock_pct: number | null;
    max_stock_pct: number | null;
    current_stock_pct: number | null;
    within_band: boolean | null;
  };
  recent_quotes: Array<{
    timestamp?: string | null;
    open?: number | null;
    high?: number | null;
    low?: number | null;
    close?: number | null;
    volume?: number | null;
    effective_price?: number | null;
    session?: string | null;
    price_policy?: string | null;
  }>;
  timeline_rows: Array<Record<string, any>>;
}

async function request<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export function getPortfolios(): Promise<PortfolioListItem[]> {
  return request<PortfolioListItem[]>('');
}

export function getPortfolioPositions(portfolioId: string): Promise<PositionSummaryItem[]> {
  return request<PositionSummaryItem[]>(`/${portfolioId}/positions`);
}

export function getPositionCockpit(
  portfolioId: string,
  positionId: string,
  window: string = '7d',
): Promise<CockpitResponse> {
  return request<CockpitResponse>(`/${portfolioId}/positions/${positionId}/cockpit?window=${window}`);
}
