const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export interface PricePoint { timestamp: string; price: number; }
export interface ValuePoint { timestamp: string; value: number; stock_value?: number | null; }
export interface TradeMarker { timestamp: string; side: 'BUY' | 'SELL'; qty: number; price: number; }

export interface PerformanceAnchor {
  price: number | null;
  trigger_up_pct: number | null;
  trigger_down_pct: number | null;
  trigger_up_price: number | null;
  trigger_down_price: number | null;
}

export interface PerformanceGuardrails {
  min_stock_pct: number | null;
  max_stock_pct: number | null;
  current_stock_pct: number | null;
}

export interface AnchorPoint { timestamp: string; anchor_price: number; }

export interface PerformanceData {
  ticker: string;
  window: string;
  price_series: PricePoint[];
  value_series: ValuePoint[];
  trade_markers: TradeMarker[];
  anchor: PerformanceAnchor;
  anchor_series: AnchorPoint[];
  guardrails: PerformanceGuardrails;
}

export async function getPositionPerformance(
  tenantId: string,
  portfolioId: string,
  positionId: string,
  window = '7d',
): Promise<PerformanceData> {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const url = `${API_BASE}/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/performance?window=${window}`;
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}
