// API Types
export interface Position {
  id: string;
  ticker: string;
  qty: number;
  cash: number;
  anchor_price?: number;
  dividend_receivable?: number;
  withholding_tax_rate?: number;
  order_policy?: OrderPolicy;
  guardrails?: Guardrails;
}

export interface Order {
  id: string;
  position_id: string;
  side: 'BUY' | 'SELL';
  qty: number;
  price: number;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  created_at: string;
  filled_at?: string;
  commission?: number;
}

export interface Event {
  id: string;
  position_id: string;
  type: string;
  message: string;
  ts: string;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
}

export interface EvaluationResult {
  position_id: string;
  current_price: number;
  anchor_price: number;
  trigger_detected: boolean;
  trigger_type?: 'BUY' | 'SELL';
  reasoning: string;
  order_proposal?: {
    side: 'BUY' | 'SELL';
    raw_qty: number;
    trimmed_qty: number;
    notional: number;
    commission: number;
    trimming_reason?: string;
    post_trade_asset_pct: number;
    validation: {
      valid: boolean;
      rejections: string[];
    };
  };
}

export interface CreatePositionRequest {
  ticker: string;
  qty: number;
  cash: number;
  anchor_price?: number;
  order_policy?: OrderPolicy;
  guardrails?: Guardrails;
  withholding_tax_rate?: number;
}

export interface OrderPolicy {
  min_qty: number;
  min_notional: number;
  lot_size: number;
  qty_step: number;
  action_below_min: 'hold' | 'reject' | 'clip';
  trigger_threshold_pct: number;
  rebalance_ratio: number;
  commission_rate: number;
  allow_after_hours: boolean;
}

export interface Guardrails {
  min_stock_alloc_pct: number;
  max_stock_alloc_pct: number;
  max_orders_per_day: number;
}

export interface CreateOrderRequest {
  side: 'BUY' | 'SELL';
  qty: number;
  price: number;
}

export interface FillOrderRequest {
  qty: number;
  price: number;
  commission: number;
}

// UI State Types
export interface TradingState {
  selectedPosition: Position | null;
  currentPrice: number;
  evaluation: EvaluationResult | null;
  isEvaluating: boolean;
}

export interface AppState {
  positions: Position[];
  orders: Order[];
  events: Event[];
  isLoading: boolean;
  error: string | null;
}

// Chart Types
export interface PriceData {
  timestamp: string;
  price: number;
  volume?: number;
}

export interface VolatilityData {
  timestamp: string;
  volatility: number;
  price: number;
  trigger_zone: 'buy' | 'sell' | 'neutral';
}

// Market Data Types
export interface MarketData {
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
}

export interface MarketStatus {
  is_market_open: boolean;
  is_after_hours: boolean;
  next_open: string;
  next_close: string;
}

export interface HistoricalPriceData {
  timestamp: string;
  price: number;
  volume?: number;
  is_market_hours: boolean;
}

// Dividend Types
export interface Dividend {
  id: string;
  ticker: string;
  ex_date: string;
  pay_date: string;
  dps: number;
  currency: string;
  withholding_tax_rate: number;
  status: string;
}

export interface DividendReceivable {
  id: string;
  ticker: string;
  ex_date: string;
  pay_date: string;
  gross_amount: number;
  net_amount: number;
  status: string;
}

export interface DividendPositionStatus {
  position_id: string;
  pending_receivables: DividendReceivable[];
  recent_dividends: Dividend[];
}

export interface DividendMarketInfo {
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
}

export interface UpcomingDividend {
  ex_date: string;
  pay_date: string;
  dps: number;
  currency: string;
}

// Enhanced Evaluation Result with Market Data
export interface EnhancedEvaluationResult extends EvaluationResult {
  market_data: MarketData;
}
