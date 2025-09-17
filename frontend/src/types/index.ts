// API Types
export interface Position {
  id: string;
  ticker: string;
  qty: number;
  cash: number;
  anchor_price?: number;
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
  order_policy?: OrderPolicy;
}

export interface OrderPolicy {
  min_qty: number;
  min_notional: number;
  lot_size: number;
  qty_step: number;
  action_below_min: 'hold' | 'reject' | 'clip';
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


