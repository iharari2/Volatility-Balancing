import {
  Position,
  Order,
  Event,
  EvaluationResult,
  CreatePositionRequest,
  CreateOrderRequest,
  FillOrderRequest,
} from '../types';

const API_BASE = '/api'; // This will use the Vite proxy
// const API_BASE = 'http://localhost:8001/v1'; // Direct connection

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
    let errorMessage = 'Request failed';
    let errorData: any = null;
    try {
      errorData = await response.json();
      errorMessage =
        errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
    } catch {
      // If response is not JSON, use status text
      errorMessage =
        response.status === 404
          ? 'Not Found'
          : `HTTP ${response.status}: ${response.statusText || 'Unknown error'}`;
    }

    // Log error details for debugging
    console.error('API Error:', {
      url,
      status: response.status,
      statusText: response.statusText,
      errorData,
      errorMessage,
    });

    throw new ApiError(response.status, errorMessage);
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

  delete: (id: string) =>
    request<{ message: string; position_id: string }>(`/positions/${id}`, {
      method: 'DELETE',
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
  getVerboseTimeline: (simulationId: string) =>
    request<{
      simulation_id: string;
      ticker: string;
      start_date: string;
      end_date: string;
      rows: Array<Record<string, any>>;
      total_rows: number;
    }>(`/v1/simulations/${simulationId}/verbose-timeline`),

  runSimulation: (config: any) => {
    // Handle dates - SimulationLabPage sends start_date and end_date as ISO strings
    // Legacy code might send startDate/endDate as strings
    let startDate: string;
    let endDate: string;

    if (config.start_date && config.end_date) {
      // Dates are already formatted as ISO strings (from SimulationLabPage)
      startDate = config.start_date;
      endDate = config.end_date;
    } else if (config.startDate && config.endDate) {
      // Legacy format - parse and format
      try {
        // Check if already ISO format (contains T and Z)
        const startIsISO =
          typeof config.startDate === 'string' &&
          config.startDate.includes('T') &&
          (config.startDate.includes('Z') || config.startDate.includes('+'));
        const endIsISO =
          typeof config.endDate === 'string' &&
          config.endDate.includes('T') &&
          (config.endDate.includes('Z') || config.endDate.includes('+'));

        if (startIsISO) {
          startDate = config.startDate;
        } else {
          // Parse date string (could be YYYY-MM-DD or MM/DD/YYYY)
          const startDateObj = new Date(config.startDate);
          if (isNaN(startDateObj.getTime())) {
            throw new Error(`Invalid start date: ${config.startDate}`);
          }
          startDate = startDateObj.toISOString();
        }

        if (endIsISO) {
          endDate = config.endDate;
        } else {
          // Parse date string and set to end of day
          const endDateObj = new Date(config.endDate);
          if (isNaN(endDateObj.getTime())) {
            throw new Error(`Invalid end date: ${config.endDate}`);
          }
          // Set to end of day in UTC
          endDateObj.setUTCHours(23, 59, 59, 999);
          endDate = endDateObj.toISOString();
        }
      } catch (error: any) {
        throw new Error(`Date parsing error: ${error.message || 'Invalid time value'}`);
      }
    } else {
      throw new Error('Missing required dates: start_date/end_date or startDate/endDate');
    }

    // Convert resolution to intraday_interval_minutes if provided
    const resolutionToMinutes: Record<string, number> = {
      '1min': 1,
      '5min': 5,
      '15min': 15,
      '30min': 30,
      '1hour': 60,
      daily: 1440, // 24 hours
    };
    const intradayIntervalMinutes =
      resolutionToMinutes[config.resolution as string] || config.intraday_interval_minutes || 30;

    const requestData = {
      ticker: config.ticker || config.asset,
      start_date: startDate,
      end_date: endDate,
      initial_cash: config.initialCash ?? 10000,
      initial_asset_value: config.initialAssetValue,
      initial_asset_units: config.initialAssetUnits,
      include_after_hours: config.allowAfterHours ?? true,
      intraday_interval_minutes: intradayIntervalMinutes,
      position_config: config.position_config || {
        trigger_threshold_pct: config.triggerThresholdPct ?? 0.03,
        rebalance_ratio: config.rebalanceRatio ?? 1.6667,
        commission_rate: config.commissionRate ?? 0.0001,
        min_notional: config.minNotional ?? 100,
        allow_after_hours: config.allowAfterHours ?? true,
        guardrails: {
          min_stock_alloc_pct: config.guardrails?.minStockAllocPct ?? 0.25,
          max_stock_alloc_pct: config.guardrails?.maxStockAllocPct ?? 0.75,
        },
      },
    };

    return request<any>('/v1/simulation/run', {
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
      open?: number;
      high?: number;
      low?: number;
      close?: number;
      validation: {
        valid: boolean;
        warnings: string[];
        rejections: string[];
      };
    }>(`/market/price/${ticker}?force_refresh=true&_t=${Date.now()}`), // Add cache-busting timestamp

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

// Audit Trail API
export const auditTrailApi = {
  getTraces: (params?: {
    tenant_id?: string;
    portfolio_id?: string;
    asset?: string;
    trace_id?: string;
    start_date?: string;
    end_date?: string;
    source?: string;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.tenant_id) queryParams.append('tenant_id', params.tenant_id);
    if (params?.portfolio_id) queryParams.append('portfolio_id', params.portfolio_id);
    if (params?.asset) queryParams.append('asset', params.asset);
    if (params?.trace_id) queryParams.append('trace_id', params.trace_id);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.source) queryParams.append('source', params.source);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return request<{
      traces: Array<{
        trace_id: string;
        tenant_id: string;
        portfolio_id: string;
        asset: string;
        source: string;
        created_at: string;
        event_count: number;
        summary: string;
      }>;
      total: number;
    }>(`/v1/audit/traces${query ? `?${query}` : ''}`);
  },

  getTraceEvents: (traceId: string) =>
    request<{
      trace_id: string;
      events: Array<{
        event_id: string;
        event_type: string;
        trace_id: string;
        parent_event_id?: string;
        tenant_id: string;
        portfolio_id: string;
        asset_id?: string;
        payload: any;
        created_at: string;
      }>;
    }>(`/v1/audit/traces/${traceId}/events`),

  getEvents: (params?: {
    tenant_id?: string;
    portfolio_id?: string;
    asset?: string;
    trace_id?: string;
    event_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.tenant_id) queryParams.append('tenant_id', params.tenant_id);
    if (params?.portfolio_id) queryParams.append('portfolio_id', params.portfolio_id);
    if (params?.asset) queryParams.append('asset', params.asset);
    if (params?.trace_id) queryParams.append('trace_id', params.trace_id);
    if (params?.event_type) queryParams.append('event_type', params.event_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString();
    return request<{
      events: Array<{
        event_id: string;
        event_type: string;
        trace_id: string;
        parent_event_id?: string;
        tenant_id: string;
        portfolio_id: string;
        asset_id?: string;
        payload: any;
        created_at: string;
      }>;
      total: number;
    }>(`/v1/audit/events${query ? `?${query}` : ''}`);
  },
};

// Portfolio API - All methods require tenantId and portfolioId
export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  type?: string;
  template?: string;
  hours_policy?: string;
}

export const portfolioApi = {
  list: (tenantId: string, userId?: string) =>
    request<
      Array<{
        id: string;
        name: string;
        description: string | null;
        user_id: string;
        created_at: string;
        updated_at: string;
      }>
    >(`/v1/tenants/${tenantId}/portfolios${userId ? `?user_id=${userId}` : ''}`),

  get: (tenantId: string, portfolioId: string) =>
    request<{
      id: string;
      name: string;
      description: string | null;
      user_id: string;
      created_at: string;
      updated_at: string;
    }>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}`),

  create: (tenantId: string, data: CreatePortfolioRequest) =>
    request<{
      portfolio_id: string;
    }>(`/v1/tenants/${tenantId}/portfolios`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (tenantId: string, portfolioId: string, data: { name?: string; description?: string }) =>
    request<{
      id: string;
      name: string;
      description: string | null;
      user_id: string;
      created_at: string;
      updated_at: string;
    }>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (tenantId: string, portfolioId: string) =>
    request<void>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}`, {
      method: 'DELETE',
    }),

  getOverview: (tenantId: string, portfolioId: string) =>
    request<{
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
      };
    }>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}/overview`),

  getSummary: (tenantId: string, portfolioId: string) =>
    request<{
      portfolio_id: string;
      portfolio_name: string;
      description: string | null;
      total_positions: number;
      total_cash: number;
      total_value: number;
      positions_by_ticker: Record<string, any>;
      created_at: string;
      updated_at: string;
    }>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}/summary`),

  getPositions: (tenantId: string, portfolioId: string) =>
    request<
      Array<{
        id: string;
        asset: string;
        qty: number;
        anchor_price: number | null;
        avg_cost: number | null;
      }>
    >(`/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions`),

  createPosition: (
    tenantId: string,
    portfolioId: string,
    data: {
      asset: string;
      qty: number;
      starting_cash: { currency: string; amount: number };
      avg_cost?: number;
      anchor_price?: number;
    },
  ) =>
    request<{
      message: string;
      portfolio_id: string;
      position_id: string;
    }>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  addPosition: (tenantId: string, portfolioId: string, positionId: string) =>
    request<{
      message: string;
      portfolio_id: string;
      position_id: string;
    }>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}`, {
      method: 'POST',
    }),

  removePosition: (tenantId: string, portfolioId: string, positionId: string) =>
    request<void>(`/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}`, {
      method: 'DELETE',
    }),
};

// Portfolio State API
export const portfolioStateApi = {
  savePortfolioState: (state: {
    name: string;
    description?: string;
    initial_cash: number;
    initial_asset_value: number;
    initial_asset_units: number;
    current_cash: number;
    current_asset_value: number;
    current_asset_units: number;
    ticker: string;
  }) =>
    request<{
      id: string;
      name: string;
      description?: string;
      initial_cash: number;
      initial_asset_value: number;
      initial_asset_units: number;
      current_cash: number;
      current_asset_value: number;
      current_asset_units: number;
      ticker: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    }>('/portfolio-state/save', {
      method: 'POST',
      body: JSON.stringify(state),
    }),

  getActivePortfolioState: () =>
    request<{
      id: string;
      name: string;
      description?: string;
      initial_cash: number;
      initial_asset_value: number;
      initial_asset_units: number;
      current_cash: number;
      current_asset_value: number;
      current_asset_units: number;
      ticker: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    } | null>('/portfolio-state/active'),

  listPortfolioStates: (limit: number = 10, offset: number = 0) =>
    request<
      Array<{
        id: string;
        name: string;
        description?: string;
        initial_cash: number;
        initial_asset_value: number;
        initial_asset_units: number;
        current_cash: number;
        current_asset_value: number;
        current_asset_units: number;
        ticker: string;
        is_active: boolean;
        created_at: string;
        updated_at: string;
      }>
    >(`/portfolio-state/list?limit=${limit}&offset=${offset}`),
};

// Simulation Progress API
export const simulationProgressApi = {
  getProgress: (simulationId: string) =>
    request<{
      simulation_id: string;
      status: string;
      progress: number;
      message: string;
      current_step: string;
      total_steps: number;
      completed_steps: number;
      start_time?: string;
      end_time?: string;
      error?: string;
    }>(`/simulation/progress/${simulationId}`),

  clearProgress: (simulationId: string) =>
    request<{ message: string }>(`/simulation/progress/${simulationId}`, {
      method: 'DELETE',
    }),
};

export { ApiError };
