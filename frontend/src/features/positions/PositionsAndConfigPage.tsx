import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
// @ts-ignore react-hot-toast types may be missing in this environment
import toast from 'react-hot-toast';
import {
  Settings,
  DollarSign,
  Copy,
  AlertCircle,
  TrendingUp,
  Briefcase,
  X,
  Activity,
  ArrowRight,
  Play,
  BarChart3,
} from 'lucide-react';
import { portfolioApi, marketApi } from '../../lib/api';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import EmptyState from '../../components/shared/EmptyState';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import PositionsTab from './tabs/PositionsTab';
import CashTab from './tabs/CashTab';
import StrategyConfigTab from './tabs/StrategyConfigTab';
import { portfolioScopedApi, PortfolioConfig } from '../../services/portfolioScopedApi';
import AnalyticsKPIs from '../analytics/AnalyticsKPIs';
import AnalyticsCharts from '../analytics/AnalyticsCharts';
import { Filter } from 'lucide-react';

interface Position {
  id: string;
  ticker?: string; // Legacy field - mapped from asset
  asset?: string; // Backend field name
  qty: number;
  cash: number;
  anchor_price: number | null;
  avg_cost?: number | null;
  total_dividends_received?: number;
  current_price?: number;
  position_value?: number;
  weight_percent?: number;
  pnl?: number;
  pnl_percent?: number;
}

interface PortfolioCash {
  total_cash: number;
  reserved_cash: number;
  available_cash: number;
}

interface EffectiveConfig {
  trigger_up: number;
  trigger_down: number;
  min_stock_pct: number;
  max_stock_pct: number;
  max_trade_pct_of_position: number;
  commission_base_rate: number;
  commission_overrides_count: number;
  market_hours_policy: string;
  last_updated: string;
}

// Helper function to sanitize ticker symbols
function sanitizeTicker(ticker: string | null | undefined): string | null {
  if (!ticker) return null;
  // Remove backslashes, newlines, and other invalid characters
  // Trim whitespace and convert to uppercase
  const sanitized = ticker
    .replace(/[\\\n\r\t]/g, '') // Remove backslashes, newlines, tabs
    .trim()
    .toUpperCase();
  return sanitized.length > 0 ? sanitized : null;
}

// Main page for managing positions and strategy configuration for a specific portfolio
export default function PositionsAndConfigPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { selectedTenantId, selectedPortfolioId, portfolios, selectedTenant } =
    useTenantPortfolio();
  const activeTab = searchParams.get('tab') || 'positions';
  const selectedPositionId = searchParams.get('positionId');

  // Use portfolioId from URL or context
  const currentPortfolioId = portfolioId || selectedPortfolioId;
  const currentPortfolio = portfolios.find((p) => p.id === currentPortfolioId);

  // Ensure selectedTenantId has a default value
  const tenantId = selectedTenantId || 'default';
  const tenantName = selectedTenant?.name || 'Default Tenant';

  const [positions, setPositions] = useState<Position[]>([]);
  // Cash is calculated from positions
  const totalCash = positions.reduce((sum, pos) => sum + (pos.cash || 0), 0);
  const [effectiveConfig, setEffectiveConfig] = useState<EffectiveConfig | null>(null);
  const [editableConfig, setEditableConfig] = useState<PortfolioConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [copiedTraceId, setCopiedTraceId] = useState<string | null>(null);

  useEffect(() => {
    if (!currentPortfolioId) {
      setError('No portfolio selected');
      setLoading(false);
      return;
    }
    loadData();
  }, [currentPortfolioId]);

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };
    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Only navigate to detail page if positionId is explicitly in URL path, not just search params
    // This prevents auto-redirect when user wants to see the list
    if (activeTab === 'positions' && selectedPositionId && currentPortfolioId) {
      // Check if we're already on the detail page route
      const currentPath = window.location.pathname;
      const detailPath = `/portfolios/${currentPortfolioId}/positions/${selectedPositionId}`;

      // Only navigate if we're NOT already on the detail page
      if (!currentPath.includes(`/positions/${selectedPositionId}`)) {
        navigate(detailPath, {
          replace: true,
        });
      }
    }
  }, [activeTab, selectedPositionId, currentPortfolioId, navigate]);

  const loadData = async () => {
    if (!currentPortfolioId) return;

    setLoading(true);
    setError(null);
    try {
      // Load positions, cash, and config in parallel
      const [positionsData, summary] = await Promise.all([
        portfolioApi.getPositions(tenantId, currentPortfolioId).catch(() => []),
        portfolioApi.getSummary(tenantId, currentPortfolioId).catch(() => null),
      ]);

      // Fetch current prices for positions (with error handling)
      const positionsWithPrices = await Promise.all(
        positionsData.map(async (pos: any) => {
          // Backend returns 'asset', map it to 'ticker' for frontend compatibility
          const tickerValue = pos.asset || pos.ticker || '';
          // Sanitize ticker before making API call
          const sanitizedTicker = sanitizeTicker(tickerValue);

          // Skip price fetch if ticker is invalid
          if (!sanitizedTicker) {
            console.warn(`Invalid ticker symbol: "${tickerValue}" - skipping price fetch`);
            return {
              ...pos,
              ticker: tickerValue, // Map asset to ticker for frontend
              asset: tickerValue, // Keep asset field too
              current_price: pos.anchor_price || 0,
              position_value: pos.qty * (pos.anchor_price || 0),
              weight_percent: 0,
            };
          }

          try {
            const priceData = await marketApi.getPrice(sanitizedTicker);
            const currentPrice = priceData.price;
            const positionValue = pos.qty * currentPrice;
            const totalValue = summary?.total_value || 0;
            return {
              ...pos,
              ticker: sanitizedTicker, // Map asset to ticker for frontend
              asset: sanitizedTicker, // Keep asset field too
              cash: pos.cash || 0, // Include cash from backend
              current_price: currentPrice,
              position_value: positionValue,
              weight_percent: totalValue > 0 ? (positionValue / totalValue) * 100 : 0,
            };
          } catch (err: any) {
            // Silently handle price fetch failures - use anchor price or 0 as fallback
            // Only log if it's not a "ticker_not_found" error (which is expected for invalid tickers)
            if (err.message && !err.message.includes('ticker_not_found')) {
              console.warn(`Failed to fetch price for ${sanitizedTicker}:`, err.message);
            }
            return {
              ...pos,
              ticker: sanitizedTicker, // Map asset to ticker for frontend
              asset: sanitizedTicker, // Keep asset field too
              current_price: pos.anchor_price || 0,
              position_value: pos.qty * (pos.anchor_price || 0),
              weight_percent: 0,
            };
          }
        }),
      );

      setPositions(positionsWithPrices);

      // Don't auto-select first position - let user see the list
      // Auto-selection was causing issues when navigating back from detail page

      // Cash is now calculated from positions - no separate cash state needed

      // Load effective and editable config from API
      try {
        const [effective, editable] = await Promise.all([
          portfolioScopedApi.getEffectiveConfig(tenantId, currentPortfolioId),
          portfolioScopedApi.getConfig(tenantId, currentPortfolioId),
        ]);

        setEffectiveConfig({
          trigger_up: effective.trigger_threshold_up_pct,
          trigger_down: effective.trigger_threshold_down_pct,
          min_stock_pct: effective.min_stock_pct,
          max_stock_pct: effective.max_stock_pct,
          max_trade_pct_of_position: effective.max_trade_pct_of_position,
          commission_base_rate: effective.commission_rate,
          commission_overrides_count: 0,
          market_hours_policy: effective.market_hours_policy,
          last_updated: effective.last_updated,
        });

        setEditableConfig(editable);
      } catch (err: any) {
        console.warn('Failed to load config:', err);
        // Use defaults if API fails
        setEffectiveConfig({
          trigger_up: 3.0,
          trigger_down: -3.0,
          min_stock_pct: 20,
          max_stock_pct: 60,
          max_trade_pct_of_position: 10,
          commission_base_rate: 0.1,
          commission_overrides_count: 0,
          market_hours_policy: 'market-open-only',
          last_updated: new Date().toISOString(),
        });
        // Set default editable config so StrategyConfigTab can render
        // Use consistent values matching effectiveConfig defaults above
        setEditableConfig({
          trigger_threshold_up_pct: 3.0,
          trigger_threshold_down_pct: -3.0,
          min_stock_pct: 20.0,
          max_stock_pct: 60.0,
          max_trade_pct_of_position: 10.0,
          commission_rate: 0.1,
          market_hours_policy: 'market-open-only',
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load portfolio data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddPosition = async (positionData: {
    ticker: string;
    qty: number;
    dollarValue: number;
    inputMode: 'qty' | 'dollar';
    currentPrice: number;
    startingCash: {
      currency: string;
      amount: number;
    };
  }) => {
    if (!currentPortfolioId) {
      toast.error('No portfolio selected');
      return;
    }

    try {
      // Validate inputs
      if (!positionData.ticker || !positionData.ticker.trim()) {
        toast.error('Ticker symbol is required');
        return;
      }

      // Determine final qty
      const finalQty =
        positionData.inputMode === 'qty'
          ? positionData.qty
          : positionData.dollarValue / positionData.currentPrice;

      if (finalQty <= 0 || !isFinite(finalQty)) {
        toast.error('Invalid quantity. Please check your input values.');
        return;
      }

      const positionPayload = {
        asset: positionData.ticker.trim().toUpperCase(),
        qty: finalQty,
        // Anchor/avg cost are derived from current price on the backend.
        anchor_price: positionData.currentPrice,
        avg_cost: positionData.currentPrice,
        starting_cash: {
          currency: positionData.startingCash.currency,
          amount: positionData.startingCash.amount,
        },
      };

      console.log('Creating position with data:', {
        tenantId,
        portfolioId: currentPortfolioId,
        payload: positionPayload,
      });

      // Create position directly in the portfolio
      const result = await portfolioApi.createPosition(
        tenantId,
        currentPortfolioId,
        positionPayload,
      );

      console.log('Position created successfully:', result);

      await loadData();
      // After creating a position, move user to the Strategy Config tab
      navigate(`/portfolios/${currentPortfolioId}/positions?tab=config`);
      toast.success(`Position ${positionData.ticker} added successfully`);
    } catch (err: any) {
      // Extract error message from various possible sources
      let errorMessage = 'Unknown error occurred';

      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.detail) {
        errorMessage = err.detail;
      } else if (err?.message) {
        errorMessage = err.message;
      }

      console.error('Error adding position:', {
        error: err,
        message: errorMessage,
        stack: err?.stack,
        response: err?.response,
      });

      toast.error(`Failed to add position: ${errorMessage}`);
    }
  };

  if (!currentPortfolioId || !currentPortfolio) {
    return (
      <EmptyState
        icon={<Briefcase className="h-16 w-16 text-gray-400" />}
        title="No Portfolio Selected"
        description="Please select a portfolio from the top bar or create a new one to manage positions and configuration"
        action={{
          label: 'Go to Portfolios',
          to: '/portfolios',
        }}
      />
    );
  }

  if (loading) {
    return <LoadingSpinner message="Loading positions and config..." />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold text-gray-900">Position Cells & Config</h1>
          <button
            onClick={() => {
              if (currentPortfolioId) {
                navigator.clipboard.writeText(currentPortfolioId);
              }
            }}
            className="text-gray-400 hover:text-gray-600"
            title="Copy Portfolio ID"
          >
            <Copy className="h-4 w-4" />
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Tenant:</span>
            <span className="text-gray-700">{tenantName}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Portfolio:</span>
            <span className="text-gray-700 font-medium">
              {currentPortfolio.name} ({currentPortfolioId})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Engine:</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${getEngineStateColor('READY')}`}
            >
              READY
            </span>
          </div>
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
            <span className="text-gray-500">Hours:</span>
            <span className="text-gray-700">
              {effectiveConfig?.market_hours_policy === 'market-open-only'
                ? 'Open-only'
                : 'Open+After-hours'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {[
              { id: 'positions', label: 'Position Cells', icon: TrendingUp },
              { id: 'trade', label: 'Trade', icon: Activity },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 },
              { id: 'cash', label: 'Cash', icon: DollarSign },
              { id: 'config', label: 'Strategy Config', icon: Settings },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() =>
                  navigate(`/portfolios/${currentPortfolioId}/positions?tab=${tab.id}`)
                }
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Positions Tab */}
          {activeTab === 'positions' && (
            <>
              {selectedPositionId ? (
                <LoadingSpinner message="Loading position details..." />
              ) : (
                // Show positions list/grid
                <PositionsTab
                  tenantId={tenantId}
                  portfolioId={currentPortfolioId!}
                  effectiveConfig={
                    effectiveConfig
                      ? {
                          trigger_threshold_up_pct: effectiveConfig.trigger_up,
                          trigger_threshold_down_pct: effectiveConfig.trigger_down,
                          min_stock_pct: effectiveConfig.min_stock_pct,
                          max_stock_pct: effectiveConfig.max_stock_pct,
                          max_trade_pct_of_position: effectiveConfig.max_trade_pct_of_position,
                          commission_rate: effectiveConfig.commission_base_rate,
                          market_hours_policy: effectiveConfig.market_hours_policy as
                            | 'market-open-only'
                            | 'market-plus-after-hours',
                          last_updated: effectiveConfig.last_updated,
                          version: 1,
                        }
                      : null
                  }
                  positions={positions.map((pos) => ({
                    id: pos.id,
                    ticker: pos.asset || pos.ticker,
                    asset: pos.asset || pos.ticker,
                    qty: pos.qty,
                    cash: pos.cash || 0, // Include cash from position
                    anchor_price: pos.anchor_price,
                    avg_cost: pos.avg_cost,
                    total_dividends_received: pos.total_dividends_received,
                    last_price: pos.current_price,
                    position_value: pos.position_value,
                    weight_pct: pos.weight_percent,
                    unrealized_pnl: pos.pnl,
                    unrealized_pnl_pct: pos.pnl_percent,
                  }))}
                  onRefresh={loadData}
                  onCopyTraceId={setCopiedTraceId}
                  onPositionClick={(positionId) => {
                    navigate(`/portfolios/${currentPortfolioId}/positions/${positionId}`);
                  }}
                />
              )}
            </>
          )}

          {/* Trade Tab */}
          {activeTab === 'trade' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg p-6 border border-gray-100 shadow-sm">
                <h2 className="text-xl font-bold text-gray-900 mb-2">Cell Cockpit Selection</h2>
                <p className="text-sm text-gray-500 mb-6">
                  Select a position cell below to open its trading cockpit
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {positions.map((position) => {
                    const currentPrice = position.current_price || position.anchor_price || 0;
                    const stockValue = position.qty * currentPrice;
                    const totalValue = (position.cash || 0) + stockValue;
                    const stockPct = totalValue > 0 ? (stockValue / totalValue) * 100 : 0;

                    // Guardrail constraints
                    const minStockPct = effectiveConfig?.min_stock_pct ?? 0;
                    const maxStockPct = effectiveConfig?.max_stock_pct ?? 100;
                    const isOutOfGuardrails = stockPct < minStockPct || stockPct > maxStockPct;

                    return (
                      <div
                        key={position.id}
                        className="p-4 border border-gray-200 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition-all group relative"
                      >
                        <div className="flex items-center justify-between">
                          <div
                            className="flex flex-col text-left cursor-pointer flex-grow"
                            onClick={() =>
                              navigate(`/trade/${currentPortfolioId}/position/${position.id}`)
                            }
                          >
                            <span className="text-sm font-black text-gray-900 uppercase tracking-tight group-hover:text-primary-700">
                              {position.asset || position.ticker}
                            </span>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-gray-500">
                                {position.qty.toLocaleString()} shares
                              </span>
                              <span className="text-[10px] text-gray-300">•</span>
                              <span
                                className={`text-xs font-bold ${
                                  isOutOfGuardrails ? 'text-danger-600' : 'text-primary-600'
                                }`}
                              >
                                {stockPct.toFixed(1)}% Stock
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() =>
                                navigate(
                                  `/portfolios/${currentPortfolioId}/positions?tab=analytics&positionId=${position.id}`,
                                )
                              }
                              className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors"
                              title="Analytics"
                            >
                              <BarChart3 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() =>
                                navigate(`/trade/${currentPortfolioId}/position/${position.id}`)
                              }
                              className="p-2 text-primary-600 hover:bg-primary-100 rounded-lg transition-colors"
                              title="Open Cockpit"
                            >
                              <ArrowRight className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {positions.length === 0 && (
                    <div className="col-span-full py-12 text-center">
                      <Briefcase className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">No positions found in this portfolio</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Portfolio Analytics</h2>
                  <p className="text-sm text-gray-500">
                    Performance metrics and trends for{' '}
                    {selectedPositionId === 'all' || !selectedPositionId
                      ? 'all positions'
                      : positions.find((p) => p.id === selectedPositionId)?.ticker ||
                        'selected position'}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <select
                      value={selectedPositionId || 'all'}
                      onChange={(e) => {
                        const newParams = new URLSearchParams(searchParams);
                        newParams.set('positionId', e.target.value);
                        setSearchParams(newParams);
                      }}
                      className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none text-sm bg-white min-w-[160px]"
                    >
                      <option value="all">All Positions</option>
                      {positions.map((pos) => (
                        <option key={pos.id} value={pos.id}>
                          {pos.asset || pos.ticker}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <AnalyticsKPIs
                positions={
                  (!selectedPositionId || selectedPositionId === 'all'
                    ? positions.map((p) => ({
                        ...p,
                        anchorPrice: p.anchor_price || 0,
                        currentPrice: p.current_price || 0,
                        marketValue: p.position_value || 0,
                        cashAmount: p.cash || 0,
                        ticker: p.asset || p.ticker || 'UNKNOWN',
                      }))
                    : positions
                        .filter((p) => p.id === selectedPositionId)
                        .map((p) => ({
                          ...p,
                          anchorPrice: p.anchor_price || 0,
                          currentPrice: p.current_price || 0,
                          marketValue: p.position_value || 0,
                          cashAmount: p.cash || 0,
                          ticker: p.asset || p.ticker || 'UNKNOWN',
                        }))) as any
                }
              />

              <AnalyticsCharts
                positions={
                  (!selectedPositionId || selectedPositionId === 'all'
                    ? positions.map((p) => ({
                        ...p,
                        anchorPrice: p.anchor_price || 0,
                        currentPrice: p.current_price || 0,
                        marketValue: p.position_value || 0,
                        cashAmount: p.cash || 0,
                        ticker: p.asset || p.ticker || 'UNKNOWN',
                      }))
                    : positions
                        .filter((p) => p.id === selectedPositionId)
                        .map((p) => ({
                          ...p,
                          anchorPrice: p.anchor_price || 0,
                          currentPrice: p.current_price || 0,
                          marketValue: p.position_value || 0,
                          cashAmount: p.cash || 0,
                          ticker: p.asset || p.ticker || 'UNKNOWN',
                        }))) as any
                }
              />
            </div>
          )}

          {/* Cash Tab */}
          {activeTab === 'cash' && (
            <CashTab
              tenantId={tenantId}
              portfolioId={currentPortfolioId!}
              cash={{
                cash_balance: totalCash,
                reserved_cash: 0, // Reserved cash not implemented in position-level model
                available_cash: totalCash,
              }}
              positions={positions.map((pos) => ({
                id: pos.id,
                ticker: pos.asset || pos.ticker,
                asset: pos.asset || pos.ticker,
                qty: pos.qty,
                cash: pos.cash || 0,
                anchor_price: pos.anchor_price,
                avg_cost: pos.avg_cost,
                last_price: pos.current_price,
              }))}
              onRefresh={loadData}
              onCopyTraceId={setCopiedTraceId}
              copiedTraceId={copiedTraceId}
            />
          )}

          {/* Strategy Config Tab */}
          {activeTab === 'config' && effectiveConfig && (
            <StrategyConfigTab
              tenantId={tenantId}
              portfolioId={currentPortfolioId!}
              positionId={
                selectedPositionId && selectedPositionId !== 'all' ? selectedPositionId : undefined
              }
              positionName={
                selectedPositionId && selectedPositionId !== 'all'
                  ? positions.find((p) => p.id === selectedPositionId)?.asset ||
                    positions.find((p) => p.id === selectedPositionId)?.ticker ||
                    undefined
                  : undefined
              }
              effectiveConfig={{
                trigger_threshold_up_pct: effectiveConfig.trigger_up,
                trigger_threshold_down_pct: effectiveConfig.trigger_down,
                min_stock_pct: effectiveConfig.min_stock_pct,
                max_stock_pct: effectiveConfig.max_stock_pct,
                max_trade_pct_of_position: effectiveConfig.max_trade_pct_of_position,
                commission_rate: effectiveConfig.commission_base_rate,
                market_hours_policy: effectiveConfig.market_hours_policy as
                  | 'market-open-only'
                  | 'market-plus-after-hours',
                last_updated: effectiveConfig.last_updated,
                version: 1,
              }}
              editableConfig={editableConfig}
              marketStatus={marketStatus}
              onConfigChange={(config) => setEditableConfig(config)}
              onSave={async (config) => {
                try {
                  // If editing position-specific config, this will be handled by StrategyConfigTab
                  // Otherwise, save portfolio-level config
                  if (!selectedPositionId || selectedPositionId === 'all') {
                    await portfolioScopedApi.updateConfig(tenantId, currentPortfolioId!, config);
                    toast.success('Config saved successfully');
                    await loadData();
                  }
                } catch (err: any) {
                  toast.error(`Failed to save config: ${err.message}`);
                  throw err;
                }
              }}
              onReload={loadData}
              onCopyTraceId={setCopiedTraceId}
              copiedTraceId={copiedTraceId}
            />
          )}
        </div>
      </div>
    </div>
  );
}




