/**
 * TypeScript types for the Explainability Table feature.
 *
 * Supports the unified trade tracking view showing the complete trade lifecycle:
 * market data → trigger evaluation → guardrail checks → order submission →
 * execution → position impact.
 */

/**
 * A single row in the explainability timeline.
 * Represents one evaluation point with all data needed to understand
 * why a trading decision was made.
 */
export interface ExplainabilityRow {
  // Group 1: Time & Identity
  timestamp: string;
  date: string; // YYYY-MM-DD format
  trace_id: string | null;

  // Group 2: Market Data
  price: number;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;

  // Group 3: Trigger Evaluation
  anchor_price: number | null;
  delta_pct: number | null; // (price - anchor) / anchor * 100
  trigger_up_threshold: number | null;
  trigger_down_threshold: number | null;
  trigger_fired: boolean;
  trigger_direction: 'UP' | 'DOWN' | 'NONE' | null;
  trigger_reason: string | null;

  // Group 4: Guardrails
  min_stock_pct: number | null;
  max_stock_pct: number | null;
  current_stock_pct: number | null;
  guardrail_allowed: boolean;
  guardrail_block_reason: string | null;

  // Group 5: Action Decision
  action: 'BUY' | 'SELL' | 'HOLD' | 'SKIP';
  action_reason: string | null;
  intended_qty: number | null;
  intended_value: number | null;

  // Group 6: Order Status
  order_id: string | null;
  order_status: 'created' | 'submitted' | 'pending' | 'working' | 'partial' | 'filled' | 'rejected' | 'cancelled' | null;
  broker_order_id: string | null;
  broker_status: string | null;

  // Group 7: Execution Details
  execution_price: number | null;
  execution_qty: number | null;
  execution_value: number | null;
  commission: number | null;
  execution_status: 'FILLED' | 'PARTIAL' | 'NONE' | null;

  // Group 8: Position Impact (Before → After)
  qty_before: number | null;
  qty_after: number | null;
  cash_before: number | null;
  cash_after: number | null;
  stock_value_before: number | null;
  stock_value_after: number | null;
  total_value_before: number | null;
  total_value_after: number | null;
  stock_pct_before: number | null;
  stock_pct_after: number | null;

  // Group 9: Dividends
  dividend_declared: boolean;
  dividend_ex_date: string | null;
  dividend_pay_date: string | null;
  dividend_rate: number | null;
  dividend_gross: number | null;
  dividend_tax: number | null;
  dividend_net: number | null;
  dividend_applied: boolean;

  // Group 10: Anchor Tracking
  anchor_reset: boolean;
  anchor_old_value: number | null;
  anchor_reset_reason: string | null;

  // Legacy/Convenience fields (for backward compatibility)
  qty: number;
  stock_value: number;
  cash: number;
  total_value: number;
  stock_pct: number | null;

  // Metadata
  mode: 'LIVE' | 'SIMULATION';
  simulation_run_id: string | null;
  position_id: string | null;
  portfolio_id: string | null;
  symbol: string | null;
  evaluation_id: string | null;
}

/**
 * Response from explainability API endpoints.
 */
export interface ExplainabilityTimeline {
  rows: ExplainabilityRow[];
  total_rows: number;
  filtered_rows: number;

  // Pagination metadata
  offset: number;
  limit: number;

  // Query metadata
  position_id: string | null;
  portfolio_id: string | null;
  simulation_run_id: string | null;
  symbol: string | null;
  mode: 'LIVE' | 'SIMULATION' | null;

  // Filter metadata
  start_date: string | null;
  end_date: string | null;
  actions_filter: string[] | null;
  order_status_filter: string[] | null;
  aggregation: 'daily' | 'all';
}

/**
 * Request parameters for explainability API.
 */
export interface ExplainabilityParams {
  start_date?: string;
  end_date?: string;
  action?: string; // comma-separated: "BUY,SELL,HOLD,SKIP"
  order_status?: string; // comma-separated: "filled,rejected,cancelled,pending,working"
  aggregation?: 'daily' | 'all';
  offset?: number;
  limit?: number;
}

/**
 * Column group definitions for the explainability table.
 */
export interface ColumnGroup {
  id: string;
  label: string;
  color: string;
  columns: ColumnDef[];
}

/**
 * Column definition for explainability table.
 */
export interface ColumnDef {
  key: keyof ExplainabilityRow;
  label: string;
  format?: 'currency' | 'percent' | 'number' | 'datetime' | 'date' | 'boolean' | 'text';
  width?: string;
}

/**
 * Default column groups configuration - comprehensive view for verbose mode.
 */
export const EXPLAINABILITY_COLUMN_GROUPS: ColumnGroup[] = [
  {
    id: 'time',
    label: 'Time',
    color: 'bg-slate-100',
    columns: [
      { key: 'timestamp', label: 'Timestamp', format: 'datetime' },
      { key: 'date', label: 'Date', format: 'date' },
    ],
  },
  {
    id: 'market',
    label: 'Market',
    color: 'bg-green-50',
    columns: [
      { key: 'price', label: 'Price', format: 'currency' },
      { key: 'open', label: 'Open', format: 'currency' },
      { key: 'high', label: 'High', format: 'currency' },
      { key: 'low', label: 'Low', format: 'currency' },
      { key: 'close', label: 'Close', format: 'currency' },
    ],
  },
  {
    id: 'trigger',
    label: 'Trigger',
    color: 'bg-blue-50',
    columns: [
      { key: 'anchor_price', label: 'Anchor', format: 'currency' },
      { key: 'delta_pct', label: 'Delta %', format: 'percent' },
      { key: 'trigger_up_threshold', label: 'Up Thresh', format: 'percent' },
      { key: 'trigger_down_threshold', label: 'Down Thresh', format: 'percent' },
      { key: 'trigger_fired', label: 'Fired', format: 'boolean' },
      { key: 'trigger_direction', label: 'Direction', format: 'text' },
      { key: 'trigger_reason', label: 'Trigger Reason', format: 'text' },
    ],
  },
  {
    id: 'guardrails',
    label: 'Guardrails',
    color: 'bg-orange-50',
    columns: [
      { key: 'min_stock_pct', label: 'Min %', format: 'percent' },
      { key: 'max_stock_pct', label: 'Max %', format: 'percent' },
      { key: 'current_stock_pct', label: 'Current %', format: 'percent' },
      { key: 'guardrail_allowed', label: 'Allowed', format: 'boolean' },
      { key: 'guardrail_block_reason', label: 'Block Reason', format: 'text' },
    ],
  },
  {
    id: 'action',
    label: 'Action',
    color: 'bg-purple-50',
    columns: [
      { key: 'action', label: 'Action', format: 'text' },
      { key: 'action_reason', label: 'Reason', format: 'text' },
      { key: 'intended_qty', label: 'Intent Qty', format: 'number' },
      { key: 'intended_value', label: 'Intent Value', format: 'currency' },
    ],
  },
  {
    id: 'order',
    label: 'Order',
    color: 'bg-cyan-50',
    columns: [
      { key: 'order_id', label: 'Order ID', format: 'text' },
      { key: 'order_status', label: 'Status', format: 'text' },
      { key: 'broker_order_id', label: 'Broker ID', format: 'text' },
      { key: 'broker_status', label: 'Broker Status', format: 'text' },
    ],
  },
  {
    id: 'execution',
    label: 'Execution',
    color: 'bg-indigo-50',
    columns: [
      { key: 'execution_price', label: 'Exec Price', format: 'currency' },
      { key: 'execution_qty', label: 'Exec Qty', format: 'number' },
      { key: 'execution_value', label: 'Exec Value', format: 'currency' },
      { key: 'commission', label: 'Commission', format: 'currency' },
      { key: 'execution_status', label: 'Exec Status', format: 'text' },
    ],
  },
  {
    id: 'position',
    label: 'Position Impact',
    color: 'bg-yellow-50',
    columns: [
      { key: 'qty_before', label: 'Qty Before', format: 'number' },
      { key: 'qty_after', label: 'Qty After', format: 'number' },
      { key: 'cash_before', label: 'Cash Before', format: 'currency' },
      { key: 'cash_after', label: 'Cash After', format: 'currency' },
      { key: 'stock_pct_before', label: '% Before', format: 'percent' },
      { key: 'stock_pct_after', label: '% After', format: 'percent' },
    ],
  },
  {
    id: 'dividends',
    label: 'Dividends',
    color: 'bg-emerald-50',
    columns: [
      { key: 'dividend_declared', label: 'Declared', format: 'boolean' },
      { key: 'dividend_rate', label: 'Rate', format: 'currency' },
      { key: 'dividend_gross', label: 'Gross', format: 'currency' },
      { key: 'dividend_tax', label: 'Tax', format: 'currency' },
      { key: 'dividend_net', label: 'Net', format: 'currency' },
      { key: 'dividend_applied', label: 'Applied', format: 'boolean' },
    ],
  },
  {
    id: 'anchor',
    label: 'Anchor',
    color: 'bg-rose-50',
    columns: [
      { key: 'anchor_reset', label: 'Reset', format: 'boolean' },
      { key: 'anchor_old_value', label: 'Old Anchor', format: 'currency' },
      { key: 'anchor_reset_reason', label: 'Reset Reason', format: 'text' },
    ],
  },
];

/**
 * Default columns to show (subset for standard view).
 */
export const DEFAULT_VISIBLE_COLUMNS: (keyof ExplainabilityRow)[] = [
  'timestamp',
  'price',
  'anchor_price',
  'delta_pct',
  'trigger_fired',
  'guardrail_allowed',
  'action',
  'action_reason',
  'execution_qty',
  'execution_price',
];

/**
 * Default column groups enabled in verbose mode.
 */
export const DEFAULT_ENABLED_GROUPS: string[] = [
  'time',
  'market',
  'trigger',
  'guardrails',
  'action',
  'execution',
];

/**
 * Action types for filtering.
 */
export const ACTION_TYPES = [
  { value: 'BUY', label: 'Buy', color: 'bg-green-100 text-green-800' },
  { value: 'SELL', label: 'Sell', color: 'bg-red-100 text-red-800' },
  { value: 'HOLD', label: 'Hold', color: 'bg-gray-100 text-gray-800' },
  { value: 'SKIP', label: 'Skip', color: 'bg-yellow-100 text-yellow-800' },
];

/**
 * Order status types for filtering.
 */
export const ORDER_STATUS_TYPES = [
  { value: 'filled', label: 'Filled', color: 'bg-green-100 text-green-700' },
  { value: 'partial', label: 'Partial', color: 'bg-orange-100 text-orange-700' },
  { value: 'working', label: 'Working', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'rejected', label: 'Rejected', color: 'bg-red-100 text-red-700' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-gray-100 text-gray-500' },
  { value: 'pending', label: 'Pending', color: 'bg-blue-100 text-blue-700' },
];

/**
 * Order status display configuration.
 */
export const ORDER_STATUS_COLORS: Record<string, string> = {
  created: 'bg-gray-100 text-gray-700',
  submitted: 'bg-blue-100 text-blue-700',
  pending: 'bg-blue-100 text-blue-700',
  working: 'bg-yellow-100 text-yellow-700',
  partial: 'bg-orange-100 text-orange-700',
  filled: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  cancelled: 'bg-gray-100 text-gray-500',
};
