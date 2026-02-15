import { useEffect, useState, useCallback, useMemo } from 'react';
import {
  RefreshCw,
  ShoppingCart,
  Check,
  X,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Zap,
  Filter,
} from 'lucide-react';
import { ordersApi } from '../../lib/api';
import { OrderRow, TradeRow, OrderStatus, PENDING_STATUSES } from '../../types/orders';

interface OrdersTableProps {
  tenantId: string;
  portfolioId: string;
  positionId: string;
}

type StatusFilter = 'all' | 'filled' | 'rejected' | 'cancelled' | 'pending';

const PAGE_SIZE = 50;
const PENDING_REFRESH_MS = 15_000;

const STATUS_BADGE: Record<string, { color: string; label: string }> = {
  created: { color: 'bg-gray-100 text-gray-700', label: 'Created' },
  submitted: { color: 'bg-blue-100 text-blue-700', label: 'Submitted' },
  pending: { color: 'bg-blue-100 text-blue-700', label: 'Pending' },
  working: { color: 'bg-yellow-100 text-yellow-700', label: 'Working' },
  partial: { color: 'bg-orange-100 text-orange-700', label: 'Partial' },
  filled: { color: 'bg-green-100 text-green-700', label: 'Filled' },
  rejected: { color: 'bg-red-100 text-red-700', label: 'Rejected' },
  cancelled: { color: 'bg-gray-100 text-gray-500', label: 'Cancelled' },
};

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
}

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toFixed(2)}`;
}

function formatQty(value: number | null): string {
  if (value === null || value === undefined) return '-';
  return value.toFixed(4);
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '-';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function OrdersTable({ tenantId, portfolioId, positionId }: OrdersTableProps) {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(0);
  const [pendingOpen, setPendingOpen] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadOrders = useCallback(async (silent = false) => {
    if (!portfolioId || !positionId) return;
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);
      setError(null);
      const data = await ordersApi.listOrders(tenantId, portfolioId, positionId);
      setOrders(data.orders);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load orders');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [tenantId, portfolioId, positionId]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  // Derived data
  const pendingOrders = useMemo(
    () => orders.filter((o) => PENDING_STATUSES.includes(o.status)),
    [orders],
  );

  const hasPending = pendingOrders.length > 0;

  // Auto-refresh when there are pending orders
  useEffect(() => {
    if (!hasPending) return;
    const interval = setInterval(() => loadOrders(true), PENDING_REFRESH_MS);
    return () => clearInterval(interval);
  }, [hasPending, loadOrders]);

  // Filtered + paginated history
  const filteredOrders = useMemo(() => {
    let list = orders;
    if (statusFilter === 'filled') list = list.filter((o) => o.status === 'filled');
    else if (statusFilter === 'rejected') list = list.filter((o) => o.status === 'rejected');
    else if (statusFilter === 'cancelled') list = list.filter((o) => o.status === 'cancelled');
    else if (statusFilter === 'pending') list = list.filter((o) => PENDING_STATUSES.includes(o.status));
    // Sort newest first
    return [...list].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }, [orders, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredOrders.length / PAGE_SIZE));
  const pagedOrders = filteredOrders.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // Reset page when filter changes
  useEffect(() => {
    setPage(0);
  }, [statusFilter]);

  if (loading && orders.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-500">
        <RefreshCw className="h-5 w-5 animate-spin mr-2" />
        Loading orders...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12 text-red-500">
        <AlertTriangle className="h-5 w-5 mr-2" />
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">Orders</h3>
        <div className="flex items-center gap-3">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="text-xs border border-gray-200 rounded-md px-2 py-1 text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="all">All ({orders.length})</option>
              <option value="pending">
                Pending ({orders.filter((o) => PENDING_STATUSES.includes(o.status)).length})
              </option>
              <option value="filled">
                Filled ({orders.filter((o) => o.status === 'filled').length})
              </option>
              <option value="rejected">
                Rejected ({orders.filter((o) => o.status === 'rejected').length})
              </option>
              <option value="cancelled">
                Cancelled ({orders.filter((o) => o.status === 'cancelled').length})
              </option>
            </select>
          </div>

          {/* Refresh */}
          <button
            onClick={() => loadOrders(true)}
            className="p-1.5 rounded bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Refresh orders"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Pending Orders Section */}
      {hasPending && (
        <div className="border border-blue-200 bg-blue-50 rounded-lg overflow-hidden">
          <button
            onClick={() => setPendingOpen(!pendingOpen)}
            className="w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-blue-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-semibold text-blue-800">
                Pending Orders ({pendingOrders.length})
              </span>
              {refreshing && <RefreshCw className="h-3 w-3 text-blue-400 animate-spin" />}
            </div>
            {pendingOpen ? (
              <ChevronDown className="h-4 w-4 text-blue-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-blue-500" />
            )}
          </button>

          {pendingOpen && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-t border-blue-200 bg-blue-100/50 text-left text-xs text-blue-700">
                    <th className="px-4 py-2 font-medium">Side</th>
                    <th className="px-4 py-2 font-medium">Qty</th>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 font-medium">Filled</th>
                    <th className="px-4 py-2 font-medium">Broker ID</th>
                    <th className="px-4 py-2 font-medium">Since</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-blue-100">
                  {pendingOrders.map((order) => (
                    <tr key={order.id} className="bg-blue-50/50">
                      <td className="px-4 py-2">
                        <SideBadge side={order.side} />
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">{formatQty(order.qty)}</td>
                      <td className="px-4 py-2">
                        <StatusBadge status={order.status} />
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {order.filled_qty != null && order.filled_qty !== 0
                          ? `${formatQty(order.filled_qty)} @ ${formatCurrency(order.avg_fill_price)}`
                          : '-'}
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-600 font-mono truncate max-w-[120px]" title={order.broker_order_id || ''}>
                        {order.broker_order_id
                          ? `${order.broker_order_id.substring(0, 12)}...`
                          : '-'}
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-600">
                        {timeAgo(order.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Order History Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          <span className="text-xs font-medium text-gray-600">
            Order History — showing {pagedOrders.length} of {filteredOrders.length}
          </span>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1 rounded text-gray-500 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs text-gray-600">
                {page + 1} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1 rounded text-gray-500 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {pagedOrders.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <ShoppingCart className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">No orders{statusFilter !== 'all' ? ' matching filter' : ''}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-xs text-gray-500">
                  <th className="px-4 py-2 font-medium">Created</th>
                  <th className="px-4 py-2 font-medium">Side</th>
                  <th className="px-4 py-2 font-medium">Qty</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Filled Qty</th>
                  <th className="px-4 py-2 font-medium">Avg Fill Price</th>
                  <th className="px-4 py-2 font-medium">Commission</th>
                  <th className="px-4 py-2 font-medium">Broker Order ID</th>
                  <th className="px-4 py-2 font-medium">Last Update</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pagedOrders.map((order) => (
                  <OrderHistoryRow key={order.id} order={order} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function OrderHistoryRow({ order }: { order: OrderRow }) {
  const isPending = PENDING_STATUSES.includes(order.status);
  const isRejected = order.status === 'rejected';

  const rowBg = isPending
    ? 'bg-blue-50/40'
    : isRejected
      ? 'bg-red-50/40'
      : '';

  return (
    <>
      <tr className={`${rowBg} hover:bg-gray-50`}>
        <td className="px-4 py-2 text-xs text-gray-700 whitespace-nowrap">
          {formatDateTime(order.created_at)}
        </td>
        <td className="px-4 py-2">
          <SideBadge side={order.side} />
        </td>
        <td className="px-4 py-2 font-mono text-xs">{formatQty(order.qty)}</td>
        <td className="px-4 py-2">
          <StatusBadge status={order.status} />
        </td>
        <td className="px-4 py-2 font-mono text-xs">
          {order.filled_qty != null && order.filled_qty !== 0 ? formatQty(order.filled_qty) : '-'}
        </td>
        <td className="px-4 py-2 font-mono text-xs">{formatCurrency(order.avg_fill_price)}</td>
        <td className="px-4 py-2 font-mono text-xs">
          {order.total_commission > 0 ? formatCurrency(order.total_commission) : '-'}
        </td>
        <td
          className="px-4 py-2 text-xs text-gray-600 font-mono truncate max-w-[140px]"
          title={order.broker_order_id || ''}
        >
          {order.broker_order_id ? `${order.broker_order_id.substring(0, 12)}...` : '-'}
        </td>
        <td className="px-4 py-2 text-xs text-gray-500 whitespace-nowrap">
          {formatDateTime(order.last_broker_update || order.updated_at)}
        </td>
      </tr>
      {order.rejection_reason && (
        <tr className={rowBg}>
          <td colSpan={9} className="px-4 pb-2 pt-0">
            <div className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
              {order.rejection_reason}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function StatusBadge({ status }: { status: OrderStatus }) {
  const config = STATUS_BADGE[status] || { color: 'bg-gray-100 text-gray-600', label: status };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.color}`}
    >
      {config.label}
    </span>
  );
}

function SideBadge({ side }: { side: string }) {
  const isBuy = side === 'BUY';
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
        isBuy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}
    >
      {isBuy ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {side}
    </span>
  );
}
