/**
 * OrdersPanel - Display orders and trades for a position
 *
 * Shows recent orders with their status and fill details,
 * plus a trades/execution log.
 */

import { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw,
  ShoppingCart,
  Check,
  X,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Receipt,
} from 'lucide-react';

interface Order {
  id: string;
  position_id: string;
  side: string;
  qty: number;
  price?: number;
  status: string;
  broker_order_id?: string;
  broker_status?: string;
  filled_qty?: number;
  avg_fill_price?: number;
  total_commission?: number;
  rejection_reason?: string;
  created_at?: string;
  submitted_to_broker_at?: string;
  last_broker_update?: string;
}

interface Trade {
  id: string;
  order_id: string;
  position_id: string;
  side: string;
  qty: number;
  price: number;
  commission: number;
  executed_at: string;
  broker_execution_id?: string;
}

interface OrdersPanelProps {
  portfolioId: string;
  positionId: string;
  limit?: number;
  refreshInterval?: number; // seconds, 0 to disable auto-refresh
}

const TENANT_ID = 'default';
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export default function OrdersPanel({
  portfolioId,
  positionId,
  limit = 20,
  refreshInterval = 30,
}: OrdersPanelProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [activeTab, setActiveTab] = useState<'orders' | 'trades'>('orders');

  const loadData = useCallback(async () => {
    if (!portfolioId || !positionId) return;

    try {
      setError(null);

      // Fetch orders and trades in parallel
      const [ordersRes, tradesRes] = await Promise.all([
        fetch(`${API_BASE}/api/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/orders?limit=${limit}`),
        fetch(`${API_BASE}/api/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/trades?limit=${limit}`),
      ]);

      if (!ordersRes.ok) {
        throw new Error('Failed to fetch orders');
      }
      if (!tradesRes.ok) {
        throw new Error('Failed to fetch trades');
      }

      const ordersData = await ordersRes.json();
      const tradesData = await tradesRes.json();

      setOrders(ordersData.orders || []);
      setTrades(tradesData.trades || []);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [portfolioId, positionId, limit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!refreshInterval) return;

    const interval = setInterval(loadData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval, loadData]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: typeof Check; label: string }> = {
      filled: { color: 'bg-green-100 text-green-700', icon: Check, label: 'Filled' },
      partially_filled: { color: 'bg-yellow-100 text-yellow-700', icon: Clock, label: 'Partial' },
      pending: { color: 'bg-blue-100 text-blue-700', icon: Clock, label: 'Pending' },
      working: { color: 'bg-blue-100 text-blue-700', icon: Clock, label: 'Working' },
      submitted: { color: 'bg-blue-100 text-blue-700', icon: Clock, label: 'Submitted' },
      rejected: { color: 'bg-red-100 text-red-700', icon: X, label: 'Rejected' },
      cancelled: { color: 'bg-gray-100 text-gray-600', icon: X, label: 'Cancelled' },
      expired: { color: 'bg-gray-100 text-gray-500', icon: Clock, label: 'Expired' },
    };

    const config = statusConfig[status.toLowerCase()] || {
      color: 'bg-gray-100 text-gray-600',
      icon: AlertTriangle,
      label: status,
    };
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </span>
    );
  };

  const getSideBadge = (side: string) => {
    const isBuy = side.toLowerCase() === 'buy';
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
        isBuy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}>
        {isBuy ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        {side.toUpperCase()}
      </span>
    );
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return '-';
    return `$${value.toFixed(2)}`;
  };

  if (loading && orders.length === 0 && trades.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center text-gray-500">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />
          Loading orders & trades...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center text-red-500">
          <AlertTriangle className="h-5 w-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header with Tabs */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveTab('orders')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'orders'
                ? 'bg-purple-100 text-purple-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ShoppingCart className="h-4 w-4" />
            Orders ({orders.length})
          </button>
          <button
            onClick={() => setActiveTab('trades')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'trades'
                ? 'bg-green-100 text-green-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Receipt className="h-4 w-4" />
            Executions ({trades.length})
          </button>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={loadData}
            className="p-1.5 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <>
          {orders.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <ShoppingCart className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p>No orders yet</p>
              <p className="text-sm mt-1">Orders will appear here when triggers fire</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
              {orders.map((order) => (
                <div key={order.id} className="px-4 py-3 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getSideBadge(order.side)}
                      <span className="font-medium text-gray-900">
                        {order.qty.toFixed(4)} shares
                      </span>
                      {order.price && (
                        <span className="text-gray-500">@ {formatCurrency(order.price)}</span>
                      )}
                    </div>
                    {getStatusBadge(order.status)}
                  </div>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-gray-600">
                    <div>
                      <span className="text-gray-400">Created:</span>{' '}
                      {formatDateTime(order.created_at)}
                    </div>
                    {order.filled_qty !== undefined && order.filled_qty > 0 && (
                      <div>
                        <span className="text-gray-400">Filled:</span>{' '}
                        {order.filled_qty.toFixed(4)} @ {formatCurrency(order.avg_fill_price)}
                      </div>
                    )}
                    {order.total_commission !== undefined && order.total_commission > 0 && (
                      <div>
                        <span className="text-gray-400">Commission:</span>{' '}
                        {formatCurrency(order.total_commission)}
                      </div>
                    )}
                    {order.broker_order_id && (
                      <div className="truncate" title={order.broker_order_id}>
                        <span className="text-gray-400">Broker ID:</span>{' '}
                        {order.broker_order_id.substring(0, 12)}...
                      </div>
                    )}
                  </div>

                  {order.rejection_reason && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                      {order.rejection_reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Trades/Executions Tab */}
      {activeTab === 'trades' && (
        <>
          {trades.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Receipt className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p>No executions yet</p>
              <p className="text-sm mt-1">Trade executions will appear here when orders are filled</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
              {trades.map((trade) => (
                <div key={trade.id} className="px-4 py-3 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getSideBadge(trade.side)}
                      <span className="font-medium text-gray-900">
                        {trade.qty.toFixed(4)} shares
                      </span>
                      <span className="text-gray-500">@ {formatCurrency(trade.price)}</span>
                    </div>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                      <Check className="h-3 w-3" />
                      Executed
                    </span>
                  </div>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-gray-600">
                    <div>
                      <span className="text-gray-400">Executed:</span>{' '}
                      {formatDateTime(trade.executed_at)}
                    </div>
                    <div>
                      <span className="text-gray-400">Value:</span>{' '}
                      {formatCurrency(trade.qty * trade.price)}
                    </div>
                    {trade.commission > 0 && (
                      <div>
                        <span className="text-gray-400">Commission:</span>{' '}
                        {formatCurrency(trade.commission)}
                      </div>
                    )}
                    {trade.broker_execution_id && (
                      <div className="truncate" title={trade.broker_execution_id}>
                        <span className="text-gray-400">Exec ID:</span>{' '}
                        {trade.broker_execution_id.substring(0, 12)}...
                      </div>
                    )}
                  </div>

                  <div className="mt-1 text-xs text-gray-400">
                    Order: {trade.order_id.substring(0, 16)}...
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
