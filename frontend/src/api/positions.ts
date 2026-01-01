/**
 * Position API Service
 *
 * Provides functions for position operations including tick execution.
 * Decoupled from UI components for reusability.
 */

const API_BASE = '/api/v1';

export interface CycleResult {
  position_snapshot: {
    position_id: string;
    symbol: string;
    qty: number;
    cash: number;
    stock_value: number;
    total_value: number;
    allocation_pct: number;
    anchor_price: number | null;
    current_price: number;
  };
  baseline_deltas: {
    position_vs_baseline: {
      pct: number | null;
      abs: number | null;
    };
    stock_vs_baseline: {
      pct: number | null;
      abs: number | null;
    };
  };
  allocation_vs_guardrails: {
    current_allocation_pct: number;
    min_stock_pct: number | null;
    max_stock_pct: number | null;
    within_guardrails: boolean;
  };
  last_event: {
    event_id: string | null;
    timestamp: string | null;
    event_type: string | null;
    action: string | null;
    action_reason: string | null;
  } | null;
  cycle_result: {
    action: string;
    action_reason: string;
    order_id: string | null;
    trade_id: string | null;
    evaluation_timestamp: string;
  };
}

export interface CockpitData {
  position: {
    id: string;
    asset_symbol: string;
    qty: number;
    cash: number;
    anchor_price: number | null;
    avg_cost: number | null;
    total_commission_paid: number;
    total_dividends_received: number;
  };
  baseline: {
    baseline_price: number;
    baseline_qty: number;
    baseline_cash: number;
    baseline_total_value: number;
    baseline_stock_value: number;
    baseline_timestamp: string;
  } | null;
  current_market_data: {
    price: number;
    source: string;
    timestamp: string;
    is_market_hours: boolean;
  } | null;
  trading_status: 'RUNNING' | 'PAUSED';
  position_vs_baseline: {
    pct: number | null;
    abs: number | null;
  };
  stock_vs_baseline: {
    pct: number | null;
    abs: number | null;
  };
  stock_allocation?: {
    stock_value: number | null;
    total_position_value: number | null;
    stock_allocation_pct: number | null;
  };
  guardrails?: {
    min_stock_pct: number | null;
    max_stock_pct: number | null;
  };
  allocation_within_guardrails?: boolean | null;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  evaluation_type?: string;
  effective_price?: number;
  market_price_raw?: number;
  anchor_price?: number;
  action?: string;
  action_taken?: string;
  action_reason?: string;
  evaluation_summary?: string;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  close_price?: number;
  position_qty_before?: number;
  position_qty_after?: number;
  qty_before?: number;
  qty_after?: number;
  position_cash_before?: number;
  position_cash_after?: number;
  cash_before?: number;
  cash_after?: number;
  position_total_value_after?: number;
  total_value_after?: number;
  [key: string]: any;
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

/**
 * Execute a single deterministic tick for a position.
 *
 * @param positionId - The position ID to tick
 * @returns CycleResult with position snapshot, baseline deltas, allocation%, and last event
 */
export async function tickPosition(positionId: string): Promise<CycleResult> {
  return request<CycleResult>(`/positions/${positionId}/tick`, {
    method: 'POST',
  });
}

/**
 * Get position cockpit summary data.
 *
 * @param tenantId - Tenant ID
 * @param portfolioId - Portfolio ID
 * @param positionId - Position ID
 * @returns CockpitData with position state, baseline, market data, and deltas
 */
export async function getPositionCockpit(
  tenantId: string,
  portfolioId: string,
  positionId: string,
): Promise<CockpitData> {
  return request<CockpitData>(
    `/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/cockpit`,
  );
}

/**
 * Get position events (timeline).
 *
 * @param tenantId - Tenant ID
 * @param portfolioId - Portfolio ID
 * @param positionId - Position ID
 * @param limit - Maximum number of events to return (default: 500)
 * @returns Array of timeline events
 */
export async function getPositionEvents(
  tenantId: string,
  portfolioId: string,
  positionId: string,
  limit: number = 100, // Reduced default limit to prevent loading too much data
): Promise<TimelineEvent[]> {
  try {
    // Add timeout to prevent hanging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    const data = await request<TimelineEvent[]>(
      `/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/timeline?limit=${limit}`,
      { signal: controller.signal } as any,
    );
    clearTimeout(timeoutId);
    return Array.isArray(data) ? data : [];
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.error('Timeline request timed out after 10 seconds');
      return [];
    }
    throw error;
  }
}





