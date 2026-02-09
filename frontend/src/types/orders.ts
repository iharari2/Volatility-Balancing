export type OrderStatus =
  | 'created'
  | 'submitted'
  | 'pending'
  | 'working'
  | 'partial'
  | 'filled'
  | 'rejected'
  | 'cancelled';

export const PENDING_STATUSES: OrderStatus[] = [
  'created',
  'submitted',
  'pending',
  'working',
  'partial',
];

export interface OrderRow {
  id: string;
  tenant_id: string;
  portfolio_id: string;
  position_id: string;
  side: 'BUY' | 'SELL';
  qty: number;
  status: OrderStatus;
  idempotency_key: string | null;
  commission_rate_snapshot: number | null;
  commission_estimated: number | null;
  created_at: string;
  updated_at: string;
  // Broker fields
  broker_order_id: string | null;
  broker_status: string | null;
  submitted_to_broker_at: string | null;
  filled_qty: number;
  avg_fill_price: number | null;
  total_commission: number;
  last_broker_update: string | null;
  rejection_reason: string | null;
}

export interface TradeRow {
  id: string;
  order_id: string;
  position_id: string;
  side: string;
  qty: number;
  price: number;
  commission: number;
  executed_at: string;
  broker_execution_id: string | null;
}
