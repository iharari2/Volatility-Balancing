import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Edit,
  Settings,
  Play,
  Pause,
  Power,
  PowerOff,
  FileText,
  Download,
  Copy,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { portfolioApi } from '../../lib/api';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface PortfolioOverview {
  portfolio_id: string;
  portfolio_name: string;
  description: string | null;
  portfolio_type: 'live' | 'simulation' | 'sandbox';
  tenant_id: string;
  engine_state: 'NOT_CONFIGURED' | 'READY' | 'RUNNING' | 'PAUSED' | 'ERROR';
  market_hours_policy: 'market-open-only' | 'allow-after-hours';
  last_cycle_time: string | null;
  last_cycle_result: string | null;
  last_cycle_trace_id: string | null;
  kpis: {
    total_value: number;
    cash: number;
    stock_value: number;
    stock_percentage: number;
    pnl: number;
    pnl_percent: number;
  };
  positions: Array<{
    ticker: string;
    qty: number;
    price: number;
    value: number;
    weight_percent: number;
    pnl: number;
    pnl_percent: number;
  }>;
  config: {
    trigger_up: number;
    trigger_down: number;
    min_stock_pct: number;
    max_stock_pct: number;
    max_trade_pct_of_position: number;
    commission_base_rate: number;
    commission_overrides_count: number;
    market_hours_policy: string;
    last_updated: string;
  };
}

interface Cycle {
  time: string;
  asset: string;
  price: number;
  pct_change_from_anchor: number;
  trigger_signal: string;
  guardrail_allowed: string;
  action: string;
  order_status: string;
  trace_id: string;
}

export default function PortfolioOverviewPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  const navigate = useNavigate();
  const { selectedTenantId, setSelectedPortfolioId } = useTenantPortfolio();
  const [overview, setOverview] = useState<PortfolioOverview | null>(null);
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (portfolioId && selectedTenantId) {
      setSelectedPortfolioId(portfolioId);
      loadData();
    }
  }, [portfolioId, selectedTenantId]);

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };
    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    if (!portfolioId || !selectedTenantId) return;

    setLoading(true);
    setError(null);
    try {
      // Use the new overview endpoint
      const overviewResponse = await portfolioApi.getOverview(selectedTenantId, portfolioId);

      // Transform to overview format
      const overviewData: PortfolioOverview = {
        portfolio_id: overviewResponse.portfolio.id,
        portfolio_name: overviewResponse.portfolio.id, // Will be updated from portfolio.name if available
        description: null, // TODO: Add to overview response
        portfolio_type: overviewResponse.portfolio.type.toLowerCase() as
          | 'live'
          | 'simulation'
          | 'sandbox',
        tenant_id: selectedTenantId,
        engine_state: overviewResponse.portfolio.state as
          | 'NOT_CONFIGURED'
          | 'READY'
          | 'RUNNING'
          | 'PAUSED'
          | 'ERROR',
        market_hours_policy:
          overviewResponse.portfolio.hours_policy === 'OPEN_ONLY'
            ? 'market-open-only'
            : 'allow-after-hours',
        last_cycle_time: null, // TODO: Get from API
        last_cycle_result: null, // TODO: Get from API
        last_cycle_trace_id: null, // TODO: Get from API
        kpis: {
          total_value: overviewResponse.kpis.total_value,
          cash: overviewResponse.cash.cash_balance,
          stock_value: overviewResponse.kpis.total_value - overviewResponse.cash.cash_balance,
          stock_percentage: overviewResponse.kpis.stock_pct,
          pnl: 0, // TODO: Calculate from API
          pnl_percent: overviewResponse.kpis.pnl_pct,
        },
        positions: overviewResponse.positions.map((pos) => {
          const price = pos.anchor || pos.avg_cost || 0;
          const stock_value = pos.qty * price;
          const value = stock_value; // Position value is just stock value; cash is at portfolio level
          return {
            ticker: pos.asset,
            qty: pos.qty,
            price: price,
            value: value,
            weight_percent:
              overviewResponse.kpis.total_value > 0
                ? (value / overviewResponse.kpis.total_value) * 100
                : 0,
            pnl: 0, // TODO: Calculate from API
            pnl_percent: 0, // TODO: Calculate from API
          };
        }),
        config: {
          trigger_up: overviewResponse.config_effective.trigger_up_pct,
          trigger_down: overviewResponse.config_effective.trigger_down_pct,
          min_stock_pct: overviewResponse.config_effective.min_stock_pct,
          max_stock_pct: overviewResponse.config_effective.max_stock_pct,
          max_trade_pct_of_position:
            overviewResponse.config_effective.max_trade_pct_of_position || 10,
          commission_base_rate: overviewResponse.config_effective.commission_rate_pct,
          commission_overrides_count: 0, // TODO: Get from API
          market_hours_policy:
            overviewResponse.portfolio.hours_policy === 'OPEN_ONLY'
              ? 'market-open-only'
              : 'allow-after-hours',
          last_updated: new Date().toISOString(), // TODO: Get from API
        },
      };

      setOverview(overviewData);
      setCycles([]); // TODO: Load from API
    } catch (err: any) {
      console.error('Error loading portfolio overview:', err);
      setError(err.message || 'Failed to load portfolio overview');
      // Show error banner in developer mode
      if (import.meta.env.DEV) {
        console.error('Data model broken: overview endpoint returned error', err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRunCycle = async () => {
    if (!portfolioId) return;
    setActionLoading('cycle');
    try {
      // TODO: Call API endpoint
      // await portfolioApi.runCycle(portfolioId);
      toast('Cycle run initiated');
      await loadData();
    } catch (err: any) {
      toast.error(`Failed to run cycle: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleAuto = async () => {
    if (!portfolioId || !overview) return;
    setActionLoading('toggle');
    try {
      if (overview.engine_state === 'RUNNING') {
        // TODO: await portfolioApi.disableAuto(portfolioId);
        toast('Auto trading toggle coming soon');
      } else {
        // TODO: await portfolioApi.enableAuto(portfolioId);
        toast('Auto trading toggle coming soon');
      }
      await loadData();
    } catch (err: any) {
      toast.error(`Failed to toggle auto trading: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const copyPortfolioId = () => {
    if (portfolioId) {
      navigator.clipboard.writeText(portfolioId);
    }
  };

  const getEngineStateColor = (state: string) => {
    switch (state) {
      case 'RUNNING':
        return 'bg-green-100 text-green-800';
      case 'READY':
        return 'bg-blue-100 text-blue-800';
      case 'PAUSED':
        return 'bg-yellow-100 text-yellow-800';
      case 'ERROR':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getMarketStatusColor = (status: MarketStatus) => {
    switch (status) {
      case 'OPEN':
        return 'bg-green-100 text-green-800';
      case 'PRE_MARKET':
      case 'AFTER_HOURS':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading portfolio overview...</p>
        </div>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error || 'Portfolio not found'}</p>
        <button
          onClick={() => navigate('/portfolios')}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Back to Portfolios
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Strip */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{overview.portfolio_name}</h1>
            <button
              onClick={copyPortfolioId}
              className="text-gray-400 hover:text-gray-600"
              title="Copy Portfolio ID"
            >
              <Copy className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-500">({overview.portfolio_id})</span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Market:</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${getMarketStatusColor(
                marketStatus,
              )}`}
            >
              {marketStatus}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Allowed:</span>
            <span className="text-gray-700">
              {overview.market_hours_policy === 'market-open-only'
                ? 'Open-only'
                : 'Open + After-hours'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Engine:</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${getEngineStateColor(
                overview.engine_state,
              )}`}
            >
              {overview.engine_state}
            </span>
            {overview.engine_state === 'RUNNING' && (
              <span className="text-green-600 text-xs">(Auto enabled)</span>
            )}
          </div>
          {overview.last_cycle_time && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Last Cycle:</span>
              <span className="text-gray-700">
                {new Date(overview.last_cycle_time).toLocaleTimeString()}
              </span>
              {overview.last_cycle_result && (
                <span className="text-gray-700">| {overview.last_cycle_result}</span>
              )}
              {overview.last_cycle_trace_id && (
                <Link
                  to={`/audit?trace=${overview.last_cycle_trace_id}`}
                  className="text-blue-600 hover:text-blue-800 text-xs flex items-center gap-1"
                >
                  Trace: {overview.last_cycle_trace_id.substring(0, 8)}...
                  <ExternalLink className="h-3 w-3" />
                </Link>
              )}
            </div>
          )}
        </div>
        {marketStatus === 'CLOSED' && overview.market_hours_policy === 'market-open-only' && (
          <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded p-2 text-sm text-yellow-800">
            Market is closed. Auto trading waits until next open.
          </div>
        )}
        {overview.engine_state === 'ERROR' && (
          <div className="mt-3 bg-red-50 border border-red-200 rounded p-2 text-sm text-red-800">
            Engine error detected. Check audit trail for details.
          </div>
        )}
      </div>

      {/* Actions Bar */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/portfolios/${portfolioId}/positions?tab=positions`}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            Edit Positions
          </Link>
          <Link
            to={`/portfolios/${portfolioId}/positions?tab=config`}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            Edit Config
          </Link>
          <button
            onClick={handleRunCycle}
            disabled={actionLoading === 'cycle'}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Play className="h-4 w-4" />
            {actionLoading === 'cycle' ? 'Running...' : 'Run One Cycle Now'}
          </button>
          <button
            onClick={handleToggleAuto}
            disabled={actionLoading === 'toggle' || overview.engine_state === 'NOT_CONFIGURED'}
            className={`px-4 py-2 rounded hover:opacity-90 disabled:opacity-50 flex items-center gap-2 ${
              overview.engine_state === 'RUNNING'
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {overview.engine_state === 'RUNNING' ? (
              <>
                <PowerOff className="h-4 w-4" />
                Disable Auto
              </>
            ) : (
              <>
                <Power className="h-4 w-4" />
                Enable Auto
              </>
            )}
          </button>
          <Link
            to="/simulation"
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 flex items-center gap-2"
          >
            <FileText className="h-4 w-4" />
            Simulation
          </Link>
          <Link
            to="/audit"
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center gap-2"
          >
            <FileText className="h-4 w-4" />
            Audit Trail
          </Link>
          <div className="relative group">
            <button className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 flex items-center gap-2">
              <Download className="h-4 w-4" />
              Export Excel
              <span className="text-xs">▼</span>
            </button>
            <div className="absolute left-0 mt-1 w-48 bg-white rounded shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <div className="py-1">
                <a
                  href={`/api/portfolios/${portfolioId}/export?type=summary`}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Portfolio Summary
                </a>
                <a
                  href={`/api/portfolios/${portfolioId}/export?type=positions`}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Positions Detail
                </a>
                <a
                  href={`/api/portfolios/${portfolioId}/export?type=trades`}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Trades & Executions
                </a>
                <a
                  href={`/api/portfolios/${portfolioId}/export?type=timeline`}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Verbose Timeline
                </a>
                <a
                  href={`/api/portfolios/${portfolioId}/export?type=full`}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Full Pack (all sheets)
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">Total Value</h3>
            <DollarSign className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            $
            {overview.kpis.total_value.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">Cash</h3>
            <DollarSign className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            $
            {overview.kpis.cash.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">Stock %</h3>
            <PieChart className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {overview.kpis.stock_percentage.toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">P&L</h3>
            {overview.kpis.pnl >= 0 ? (
              <TrendingUp className="h-5 w-5 text-green-500" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-500" />
            )}
          </div>
          <p
            className={`text-2xl font-bold ${
              overview.kpis.pnl >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {overview.kpis.pnl >= 0 ? '+' : ''}
            {overview.kpis.pnl_percent.toFixed(2)}%
          </p>
          <p className="text-sm text-gray-500 mt-1">
            $
            {overview.kpis.pnl.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
      </div>

      {/* Positions and Config Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Positions Panel */}
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Positions (Top Holdings)</h3>
            <Link
              to={`/portfolios/${portfolioId}/positions?tab=positions`}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all positions
            </Link>
          </div>
          <div className="p-6">
            {overview.positions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Asset
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Qty
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Price
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Cash
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Stock Value
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Total Value
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Weight
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {overview.positions.map((pos, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-sm font-medium text-gray-900">
                          {pos.ticker}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-700">
                          {pos.qty.toLocaleString()}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-700">${pos.price.toFixed(2)}</td>
                        <td className="px-3 py-2 text-sm font-medium text-gray-900">
                          $
                          {pos.value.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-700">
                          {pos.weight_percent.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p>No positions yet</p>
                <Link
                  to={`/portfolios/${portfolioId}/positions?tab=positions`}
                  className="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block"
                >
                  Add your first position
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Config Panel */}
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Config (Effective)</h3>
            <Link to="/positions?tab=config" className="text-sm text-blue-600 hover:text-blue-800">
              View/Change Config
            </Link>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Trigger thresholds</h4>
              <div className="text-sm text-gray-600">
                Up: {overview.config.trigger_up > 0 ? '+' : ''}
                {overview.config.trigger_up}% / Down: {overview.config.trigger_down}%
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Guardrails</h4>
              <div className="text-sm text-gray-600">
                Min stock %: {overview.config.min_stock_pct}% | Max stock %:{' '}
                {overview.config.max_stock_pct}% | Max trade % of position:{' '}
                {overview.config.max_trade_pct_of_position}%
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Commission</h4>
              <div className="text-sm text-gray-600">
                Base rate: {overview.config.commission_base_rate}% (overrides:{' '}
                {overview.config.commission_overrides_count})
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Market Hours Policy</h4>
              <div className="text-sm text-gray-600">
                {overview.config.market_hours_policy === 'market-open-only'
                  ? 'Market open only'
                  : 'Allow after-hours'}
              </div>
            </div>
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-500">
                Last updated: {new Date(overview.config.last_updated).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Cycles Table */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Cycles (last 20)</h3>
        </div>
        <div className="p-6">
          {cycles.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Time
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Asset
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Price
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      %ΔAnchor
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Trigger
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Guardrail
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Action
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Order Status
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Trace
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {cycles.map((cycle, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-sm text-gray-900">
                        {new Date(cycle.time).toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-sm font-medium text-gray-900">{cycle.asset}</td>
                      <td className="px-3 py-2 text-sm text-gray-700">${cycle.price.toFixed(2)}</td>
                      <td className="px-3 py-2 text-sm text-gray-700">
                        {cycle.pct_change_from_anchor > 0 ? '+' : ''}
                        {cycle.pct_change_from_anchor.toFixed(2)}%
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-700">{cycle.trigger_signal}</td>
                      <td className="px-3 py-2 text-sm text-gray-700">{cycle.guardrail_allowed}</td>
                      <td className="px-3 py-2 text-sm text-gray-700">{cycle.action}</td>
                      <td className="px-3 py-2 text-sm text-gray-700">{cycle.order_status}</td>
                      <td className="px-3 py-2 text-sm">
                        <Link
                          to={`/audit?trace=${cycle.trace_id}`}
                          className="text-blue-600 hover:text-blue-800 text-xs"
                        >
                          {cycle.trace_id.substring(0, 8)}...
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p>No cycles yet</p>
              <p className="text-sm mt-1">Run a cycle to see trading activity</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}







