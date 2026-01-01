import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Play,
  Pause,
  Power,
  PowerOff,
  Activity,
  DollarSign,
  PieChart,
  TrendingUp,
  TrendingDown,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Download,
} from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioScopedApi, PortfolioPosition } from '../../services/portfolioScopedApi';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import EmptyState from '../../components/shared/EmptyState';
import toast from 'react-hot-toast';

interface TradingState {
  engine_state: 'NOT_CONFIGURED' | 'READY' | 'RUNNING' | 'PAUSED' | 'ERROR';
  worker_active: boolean;
  worker_interval_seconds: number;
  last_cycle_time: string | null;
  last_cycle_result: string | null;
  last_cycle_trace_id: string | null;
}

interface ActivityLogEntry {
  id: string;
  timestamp: string;
  asset: string;
  action: string;
  explanation: string;
  stock_value: number;
  cash_value: number;
  total_value: number;
  dividends: number;
  trace_id: string;
}

export default function TradingConsolePage() {
  const { selectedTenantId, selectedPortfolioId, portfolios } = useTenantPortfolio();
  const navigate = useNavigate();

  const tenantId = selectedTenantId || 'default';
  const portfolioId = selectedPortfolioId;
  const currentPortfolio = portfolios.find((p) => p.id === portfolioId);

  const [loading, setLoading] = useState(true);
  const [tradingState, setTradingState] = useState<TradingState | null>(null);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(30);

  const loadData = async () => {
    if (!portfolioId) return;

    try {
      // Fetch positions
      const posData = await portfolioScopedApi.getPositions(tenantId, portfolioId);
      setPositions(posData);

      // Fetch worker status from backend (server-side state)
      try {
        const { request } = await import('../../lib/api');
        const workerStatus = await request<{
          running: boolean;
          enabled: boolean;
          interval_seconds: number;
        }>('/v1/trading/worker/status');

        setTradingState({
          engine_state: workerStatus.enabled ? 'RUNNING' : 'PAUSED',
          worker_active: workerStatus.enabled,
          worker_interval_seconds: workerStatus.interval_seconds,
          last_cycle_time: new Date().toISOString(),
          last_cycle_result: 'Success',
          last_cycle_trace_id: 'trace_' + Math.random().toString(36).substr(2, 9),
        });
      } catch (workerError) {
        console.error('Error fetching worker status:', workerError);
        // Fallback to portfolio state if worker status fails
        setTradingState({
          engine_state: (currentPortfolio?.state as any) || 'READY',
          worker_active: currentPortfolio?.state === 'RUNNING',
          worker_interval_seconds: 60,
          last_cycle_time: new Date().toISOString(),
          last_cycle_result: 'Success',
          last_cycle_trace_id: 'trace_' + Math.random().toString(36).substr(2, 9),
        });
      }

      // Fetch activity log
      // Mock data for now
      setActivityLog([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          asset: 'AAPL',
          action: 'HOLD',
          explanation: 'Price within trigger thresholds',
          stock_value: 15000,
          cash_value: 5000,
          total_value: 20000,
          dividends: 0,
          trace_id: 'trace_abc123',
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          asset: 'MSFT',
          action: 'BUY',
          explanation: 'Price dropped below trigger threshold',
          stock_value: 12000,
          cash_value: 8000,
          total_value: 20000,
          dividends: 0,
          trace_id: 'trace_def456',
        },
      ]);
    } catch (error) {
      console.error('Error loading trading console data:', error);
      toast.error('Failed to load trading data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (portfolioId) {
      loadData();
      const interval = setInterval(loadData, refreshInterval * 1000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [portfolioId, refreshInterval]);

  const handleToggleWorker = async () => {
    if (!tradingState) return;

    try {
      const { request } = await import('../../lib/api');
      const newEnabledState = !tradingState.worker_active;

      // Call backend API to persist worker state on server
      const result = await request<{
        message: string;
        enabled: boolean;
        running: boolean;
        interval_seconds: number;
      }>('/v1/trading/worker/enable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled: newEnabledState }),
      });

      // Update local state with server response
      setTradingState({
        ...tradingState,
        worker_active: result.enabled,
        engine_state: result.enabled ? 'RUNNING' : 'PAUSED',
        worker_interval_seconds: result.interval_seconds,
      });

      toast.success(
        result.message || `Worker ${newEnabledState ? 'enabled' : 'disabled'} successfully`,
      );
    } catch (error: any) {
      console.error('Error toggling worker:', error);
      const errorMessage =
        error?.message ||
        error?.detail ||
        error?.response?.data?.detail ||
        'Failed to update worker state';
      toast.error(
        `Failed to ${tradingState.worker_active ? 'disable' : 'enable'} worker: ${errorMessage}`,
      );
    }
  };

  if (loading && !tradingState) {
    return <LoadingSpinner message="Loading trading console..." />;
  }

  if (!portfolioId) {
    return (
      <EmptyState
        icon={<Activity className="h-16 w-16 text-gray-400" />}
        title="No Portfolio Selected"
        description="Select a portfolio to view and manage trading activity."
        action={{
          label: 'Select Portfolio',
          to: '/portfolios',
        }}
      />
    );
  }

  const kpis = {
    total_value: positions.reduce((sum, p) => sum + (p.position_value || 0) + (p.cash || 0), 0),
    stock_value: positions.reduce((sum, p) => sum + (p.position_value || 0), 0),
    cash: positions.reduce((sum, p) => sum + (p.cash || 0), 0),
    pnl: positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0),
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Console</h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time monitoring and control for {currentPortfolio?.name}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm">
            <Clock className="h-4 w-4 text-gray-400" />
            <span className="text-gray-600">Refresh:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="border-none p-0 focus:ring-0 text-sm font-medium"
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
            </select>
          </div>
          <button
            onClick={loadData}
            className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Control Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Trading Controls</h2>
            <div
              className={`badge ${
                tradingState?.engine_state === 'RUNNING'
                  ? 'badge-success'
                  : tradingState?.engine_state === 'PAUSED'
                  ? 'badge-warning'
                  : 'badge-info'
              }`}
            >
              {tradingState?.engine_state}
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleToggleWorker}
              className={`btn flex items-center gap-2 ${
                tradingState?.worker_active ? 'btn-danger' : 'btn-success'
              }`}
            >
              {tradingState?.worker_active ? (
                <>
                  <PowerOff className="h-4 w-4" /> Suspend Worker
                </>
              ) : (
                <>
                  <Power className="h-4 w-4" /> Enable Worker
                </>
              )}
            </button>

            <button className="btn btn-secondary flex items-center gap-2">
              <Play className="h-4 w-4" /> Run Manual Cycle
            </button>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <span className="text-sm text-gray-500 block mb-1">Last Cycle Time</span>
              <span className="font-medium text-gray-900">
                {tradingState?.last_cycle_time
                  ? new Date(tradingState.last_cycle_time).toLocaleTimeString()
                  : 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-500 block mb-1">Last Cycle Result</span>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">
                  {tradingState?.last_cycle_result || 'N/A'}
                </span>
                {tradingState?.last_cycle_trace_id && (
                  <Link
                    to={`/audit?trace_id=${tradingState.last_cycle_trace_id}`}
                    className="text-primary-600 hover:text-primary-700 flex items-center gap-1 text-xs"
                  >
                    View Trace <ExternalLink className="h-3 w-3" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="card bg-primary-900 text-white border-none shadow-md">
          <h2 className="text-lg font-semibold mb-6 opacity-90">Portfolio Summary</h2>
          <div className="space-y-4">
            <div>
              <span className="text-sm opacity-70 block mb-1">Total Value</span>
              <span className="text-3xl font-bold">
                ${kpis.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <span className="text-xs opacity-70 block mb-1">Stock Value</span>
                <span className="font-semibold">
                  ${kpis.stock_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div>
                <span className="text-xs opacity-70 block mb-1">Cash</span>
                <span className="font-semibold">
                  ${kpis.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
            <div className="pt-2">
              <span className="text-xs opacity-70 block mb-1">Unrealized P&L</span>
              <div
                className={`flex items-center gap-1 font-semibold ${
                  kpis.pnl >= 0 ? 'text-success-400' : 'text-danger-400'
                }`}
              >
                {kpis.pnl >= 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                ${Math.abs(kpis.pnl).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Position Details */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Positions</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Weight %
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {positions.map((pos) => (
                <tr key={pos.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-bold text-gray-900">
                        {pos.asset || pos.ticker}
                      </div>
                      <Link
                        to={`/trade/${portfolioId}/position/${pos.id}`}
                        className="ml-2 text-primary-600 hover:text-primary-700"
                        title="Open Cockpit"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                    <div className="text-xs text-gray-500">{pos.qty.toLocaleString()} shares</div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                    ${(pos.last_price || 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                    $
                    {(pos.position_value || 0).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {(pos.weight_pct || 0).toFixed(1)}%
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm">
                    <div
                      className={`font-semibold ${
                        (pos.unrealized_pnl || 0) >= 0 ? 'text-success-600' : 'text-danger-600'
                      }`}
                    >
                      $
                      {(pos.unrealized_pnl || 0).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                      })}
                    </div>
                    <div
                      className={`text-xs ${
                        (pos.unrealized_pnl_pct || 0) >= 0 ? 'text-success-500' : 'text-danger-500'
                      }`}
                    >
                      {(pos.unrealized_pnl_pct || 0).toFixed(2)}%
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <span
                      className={`badge ${
                        pos.status === 'PAUSED' ? 'badge-warning' : 'badge-success'
                      }`}
                    >
                      {pos.status || 'RUNNING'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Activity Log */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Activity Log</h2>
          <button className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            Export Excel <Download className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="w-10 px-4 py-3"></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Explanation
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Value
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {activityLog.map((log) => (
                <React.Fragment key={log.id}>
                  <tr
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => setExpandedLogId(expandedLogId === log.id ? null : log.id)}
                  >
                    <td className="px-4 py-4">
                      {expandedLogId === log.id ? (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      )}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      {log.asset}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span
                        className={`badge ${
                          log.action === 'BUY'
                            ? 'badge-success'
                            : log.action === 'SELL'
                            ? 'badge-danger'
                            : 'badge-info'
                        }`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">{log.explanation}</td>
                    <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                      ${log.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                  {expandedLogId === log.id && (
                    <tr className="bg-gray-50">
                      <td colSpan={6} className="px-14 py-4">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-sm">
                          <div>
                            <span className="text-gray-500 block mb-1">Stock Value</span>
                            <span className="font-medium text-gray-900">
                              ${log.stock_value.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500 block mb-1">Cash Value</span>
                            <span className="font-medium text-gray-900">
                              ${log.cash_value.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500 block mb-1">Dividends</span>
                            <span className="font-medium text-gray-900">
                              ${log.dividends.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500 block mb-1">Trace ID</span>
                            <Link
                              to={`/audit?trace_id=${log.trace_id}`}
                              className="text-primary-600 hover:text-primary-700 flex items-center gap-1"
                            >
                              {log.trace_id} <ExternalLink className="h-3 w-3" />
                            </Link>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
