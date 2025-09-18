import {
  Position,
  Order,
  Event,
  EvaluationResult,
  CreatePositionRequest,
  CreateOrderRequest,
  FillOrderRequest,
} from '../types';

// const API_BASE = '/api'; // This will use the Vite proxy
const API_BASE = 'http://localhost:8001/v1'; // Direct connection

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
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
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

// Positions API
export const positionsApi = {
  create: (data: CreatePositionRequest) =>
    request<Position>('/positions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  list: () => request<{ positions: Position[] }>('/positions'),

  get: (id: string) => request<Position>(`/positions/${id}`),

  setAnchor: (id: string, price: number) =>
    request<{ position_id: string; anchor_price: number; message: string }>(
      `/positions/${id}/anchor?price=${price}`,
      { method: 'POST' },
    ),

  evaluate: (id: string, currentPrice: number) =>
    request<EvaluationResult>(`/positions/${id}/evaluate?current_price=${currentPrice}`, {
      method: 'POST',
    }),

  getEvents: (id: string, limit = 100) =>
    request<{ position_id: string; events: Event[] }>(`/positions/${id}/events?limit=${limit}`),

  autoSize: (id: string, currentPrice: number, idempotencyKey?: string) =>
    request<{
      position_id: string;
      current_price: number;
      order_submitted: boolean;
      order_id?: string;
      order_details?: any;
      sizing_details?: any;
      evaluation: EvaluationResult;
      reason?: string;
      rejections?: string[];
    }>(`/positions/${id}/orders/auto-size?current_price=${currentPrice}`, {
      method: 'POST',
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),
};

// Orders API
export const ordersApi = {
  create: (positionId: string, data: CreateOrderRequest, idempotencyKey?: string) =>
    request<{
      order_id: string;
      position_id: string;
      side: string;
      qty: number;
      price: number;
      status: string;
    }>(`/positions/${positionId}/orders`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),

  fill: (orderId: string, data: FillOrderRequest) =>
    request<{ order_id: string; status: string; qty: number; price: number; commission: number }>(
      `/orders/${orderId}/fill`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      },
    ),

  list: (positionId: string, limit = 100) =>
    request<{ position_id: string; orders: Order[] }>(
      `/positions/${positionId}/orders?limit=${limit}`,
    ),

  autoSize: (positionId: string, currentPrice: number, idempotencyKey?: string) =>
    request<{
      position_id: string;
      current_price: number;
      order_submitted: boolean;
      order_id?: string;
      order_details?: any;
      sizing_details?: any;
      evaluation: EvaluationResult;
      reason?: string;
      rejections?: string[];
    }>(`/positions/${positionId}/orders/auto-size?current_price=${currentPrice}`, {
      method: 'POST',
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),
};

// Simulation API
export const simulationApi = {
  runSimulation: (config: any) => {
    // Ensure dates are in ISO format with timezone
    const startDate = new Date(config.startDate + 'T00:00:00.000Z').toISOString();
    const endDate = new Date(config.endDate + 'T23:59:59.999Z').toISOString();

    const requestData = {
      ticker: config.ticker,
      start_date: startDate,
      end_date: endDate,
      initial_cash: config.initialCash,
      include_after_hours: config.allowAfterHours,
      position_config: {
        trigger_threshold_pct: config.triggerThresholdPct,
        rebalance_ratio: config.rebalanceRatio,
        commission_rate: config.commissionRate,
        min_notional: config.minNotional,
        allow_after_hours: config.allowAfterHours,
        guardrails: {
          min_stock_alloc_pct: config.guardrails.minStockAllocPct,
          max_stock_alloc_pct: config.guardrails.maxStockAllocPct,
        },
      },
    };

    return request<any>('/simulation/run', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  },

  getVolatility: (ticker: string, windowMinutes: number = 60) =>
    request<{ ticker: string; volatility: number; window_minutes: number }>(
      `/simulation/volatility/${ticker}?window_minutes=${windowMinutes}`,
    ),

  getHistoricalData: (
    ticker: string,
    startDate: string,
    endDate: string,
    marketHoursOnly: boolean = false,
  ) =>
    request<{
      ticker: string;
      start_date: string;
      end_date: string;
      market_hours_only: boolean;
      data_points: number;
      price_data: Array<{
        timestamp: string;
        price: number;
        volume?: number;
        is_market_hours: boolean;
      }>;
    }>(
      `/market/historical/${ticker}?start_date=${startDate}&end_date=${endDate}&market_hours_only=${marketHoursOnly}`,
    ),
};

// Market Data API
export const marketApi = {
  getPrice: (ticker: string) =>
    request<{
      ticker: string;
      price: number;
      source: string;
      is_market_hours: boolean;
      is_fresh: boolean;
      is_inline: boolean;
      validation: {
        valid: boolean;
        warnings: string[];
        rejections: string[];
      };
    }>(`/market/price/${ticker}`),

  getStatus: () =>
    request<{
      is_market_open: boolean;
      is_after_hours: boolean;
      next_open: string;
      next_close: string;
    }>('/market/status'),

  getHistoricalData: (
    ticker: string,
    startDate: string,
    endDate: string,
    marketHoursOnly = false,
  ) =>
    request<{
      ticker: string;
      start_date: string;
      end_date: string;
      market_hours_only: boolean;
      data_points: number;
      price_data: Array<{
        timestamp: string;
        price: number;
        volume?: number;
        is_market_hours: boolean;
      }>;
    }>(
      `/market/historical/${ticker}?start_date=${startDate}&end_date=${endDate}&market_hours_only=${marketHoursOnly}`,
    ),
};

// Dividend API
export const dividendApi = {
  announce: (data: {
    ticker: string;
    ex_date: string;
    pay_date: string;
    dps: number;
    currency: string;
    withholding_tax_rate: number;
  }) =>
    request<{
      dividend_id: string;
      ticker: string;
      ex_date: string;
      pay_date: string;
      dps: number;
      currency: string;
      withholding_tax_rate: number;
      message: string;
    }>('/dividends/announce', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getPositionStatus: (positionId: string) =>
    request<{
      position_id: string;
      pending_receivables: Array<{
        id: string;
        ticker: string;
        ex_date: string;
        pay_date: string;
        gross_amount: number;
        net_amount: number;
        status: string;
      }>;
      recent_dividends: Array<{
        id: string;
        ticker: string;
        ex_date: string;
        pay_date: string;
        dps: number;
        status: string;
      }>;
    }>(`/dividends/positions/${positionId}/status`),

  getMarketInfo: (ticker: string) =>
    request<{
      ticker: string;
      next_ex_date?: string;
      next_pay_date?: string;
      next_dps?: number;
      dividend_frequency: string;
      last_dividend?: {
        ex_date: string;
        pay_date: string;
        dps: number;
      };
    }>(`/dividends/market/${ticker}/info`),

  getUpcoming: (ticker: string) =>
    request<{
      ticker: string;
      upcoming_dividends: Array<{
        ex_date: string;
        pay_date: string;
        dps: number;
        currency: string;
      }>;
    }>(`/dividends/market/${ticker}/upcoming`),

  processExDividend: (positionId: string) =>
    request<{
      position_id: string;
      processed: boolean;
      dividend_id?: string;
      anchor_adjustment?: {
        old_anchor: number;
        dps: number;
        new_anchor: number;
      };
      receivable_created?: {
        gross_amount: number;
        net_amount: number;
        receivable_id: string;
      };
      message: string;
    }>(`/dividends/positions/${positionId}/process-ex-dividend`, {
      method: 'POST',
    }),

  processPayment: (positionId: string, receivableId: string) =>
    request<{
      position_id: string;
      receivable_id: string;
      amount_received: number;
      cash_updated: number;
      message: string;
    }>(`/dividends/positions/${positionId}/process-payment`, {
      method: 'POST',
      body: JSON.stringify({ receivable_id: receivableId }),
    }),
};

// Enhanced Positions API with market data evaluation
export const enhancedPositionsApi = {
  ...positionsApi,

  evaluateWithMarketData: (id: string) =>
    request<
      EvaluationResult & {
        market_data: {
          price: number;
          source: string;
          is_market_hours: boolean;
          is_fresh: boolean;
          is_inline: boolean;
          validation: {
            valid: boolean;
            warnings: string[];
            rejections: string[];
          };
        };
      }
    >(`/positions/${id}/evaluate/market`, {
      method: 'POST',
    }),

  autoSizeWithMarketData: (id: string, idempotencyKey?: string) =>
    request<{
      position_id: string;
      current_price: number;
      order_submitted: boolean;
      order_id?: string;
      order_details?: any;
      sizing_details?: any;
      evaluation: EvaluationResult;
      market_data: {
        price: number;
        source: string;
        is_market_hours: boolean;
      };
      reason?: string;
      rejections?: string[];
    }>(`/positions/${id}/orders/auto-size/market`, {
      method: 'POST',
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),
};

// Health API
export const healthApi = {
  check: () => request<{ status: string; timestamp: string }>('/healthz'),
};

export { ApiError };
