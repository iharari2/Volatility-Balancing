import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Pause,
  Play,
  Download,
  Filter,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Anchor,
  BarChart3,
} from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioScopedApi, PortfolioPosition } from '../../services/portfolioScopedApi';
import {
  getPositionCockpit,
  getPositionEvents,
  CockpitData,
  TimelineEvent,
} from '../../api/positions';
import PositionActions from '../positions/PositionActions';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import EmptyState from '../../components/shared/EmptyState';
import toast from 'react-hot-toast';

interface MarketDataPoint {
  timestamp: string;
  session?: string;
  effective_price?: number;
  price?: number;
  close?: number;
  bid?: number;
  ask?: number;
  open?: number;
  high?: number;
  low?: number;
  volume?: number;
}

interface MarketDataResponse {
  position_id: string;
  asset_symbol: string;
  latest: {
    session?: string;
    effective_price?: number;
    price?: number;
    price_policy_effective?: string;
    best_bid?: number;
    best_ask?: number;
    open_price?: number;
    high_price?: number;
    low_price?: number;
    close_price?: number;
    volume?: number;
    timestamp?: string;
  } | null;
  recent: MarketDataPoint[];
}

export default function PositionCockpitPage() {
  const { portfolioId, positionId } = useParams<{ portfolioId: string; positionId: string }>();
  const navigate = useNavigate();
  const { selectedTenantId, portfolios } = useTenantPortfolio();

  const tenantId = selectedTenantId || 'default';
  const [cockpitData, setCockpitData] = useState<CockpitData | null>(null);
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [portfolioConfig, setPortfolioConfig] = useState<{
    market_hours_policy: string;
    min_stock_pct?: number;
    max_stock_pct?: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [eventFilter, setEventFilter] = useState<string>('all');
  const [verboseMode, setVerboseMode] = useState(false);
  const [marketDataTab, setMarketDataTab] = useState<'latest' | 'recent'>('latest');
  const [mode] = useState<'LIVE' | 'SIM'>('LIVE'); // TODO: Get from context/config
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());
  const [previousPrice, setPreviousPrice] = useState<number | null>(null);
  const [priceUpdateFlash, setPriceUpdateFlash] = useState(false);
  const [workerStatus, setWorkerStatus] = useState<{
    running: boolean;
    enabled: boolean;
    interval_seconds: number;
  } | null>(null);

  // Refetch function for PositionActions to call after tick
  // Refreshes cockpit, market data, and events
  const refetchCockpitData = useCallback(async () => {
    if (!portfolioId || !positionId) return;

    try {
      const [cockpit, events, marketRes] = await Promise.all([
        getPositionCockpit(tenantId, portfolioId, positionId),
        getPositionEvents(tenantId, portfolioId, positionId, 500),
        fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/marketdata?limit=50`,
        ),
      ]);
      setCockpitData(cockpit);
      setEvents(events);
      if (marketRes.ok) {
        const market = await marketRes.json();
        setMarketData(market);
      }
      setLastUpdateTime(new Date());
    } catch (error) {
      console.error('Error refreshing cockpit data:', error);
    }
  }, [tenantId, portfolioId, positionId]);

  // Load cockpit data
  useEffect(() => {
    if (!portfolioId || !positionId) return;

    const loadCockpitData = async () => {
      try {
        const data = await getPositionCockpit(tenantId, portfolioId, positionId);
        setCockpitData(data);
      } catch (error) {
        console.error('Error loading cockpit data:', error);
      }
    };

    loadCockpitData();
    const interval = setInterval(loadCockpitData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [tenantId, portfolioId, positionId]);

  // Load market data
  useEffect(() => {
    if (!portfolioId || !positionId) return;

    const loadMarketData = async () => {
      try {
        const response = await fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/marketdata?limit=50`,
        );
        if (response.ok) {
          const data = await response.json();
          setMarketData(data);
          setLastUpdateTime(new Date());
        }
      } catch (error) {
        console.error('Error loading market data:', error);
      }
    };

    loadMarketData();
    // Poll market data every 5 seconds for real-time updates
    const interval = setInterval(loadMarketData, 5000);
    return () => clearInterval(interval);
  }, [tenantId, portfolioId, positionId]);

  // Track price changes for visual feedback
  useEffect(() => {
    if (marketData?.latest?.price && previousPrice !== null) {
      if (marketData.latest.price !== previousPrice) {
        setPriceUpdateFlash(true);
        setTimeout(() => setPriceUpdateFlash(false), 1000);
      }
    }
    if (marketData?.latest?.price) {
      setPreviousPrice(marketData.latest.price);
    }
  }, [marketData?.latest?.price, previousPrice]);

  // Load worker status
  useEffect(() => {
    const loadWorkerStatus = async () => {
      try {
        const response = await fetch('/api/v1/trading/worker/status');
        if (response.ok) {
          const data = await response.json();
          setWorkerStatus(data);
        }
      } catch (error) {
        console.error('Error loading worker status:', error);
      }
    };
    loadWorkerStatus();
    const interval = setInterval(loadWorkerStatus, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Load events (Evaluation Timeline)
  useEffect(() => {
    if (!portfolioId || !positionId) return;

    let isMounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const loadEvents = async () => {
      if (!isMounted) return;
      
      try {
        // Reduce limit to prevent loading too much data at once
        const newEvents = await getPositionEvents(tenantId, portfolioId, positionId, 100);
        if (!isMounted) return;
        
        // Check if we have new events (compare by timestamp)
        setEvents((prevEvents) => {
          if (prevEvents.length > 0 && newEvents.length > 0) {
            const latestNewEvent = newEvents[0];
            const latestOldEvent = prevEvents[0];
            if (latestNewEvent.timestamp !== latestOldEvent.timestamp) {
              // New event detected - could show a notification
              toast.success('New trading activity detected!', { duration: 2000 });
            }
          }
          return newEvents;
        });
        setLastUpdateTime(new Date());
      } catch (error) {
        console.error('Error loading events:', error);
        // Don't show error toast on every failed request, just log it
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Initial load with a small delay to prevent blocking
    timeoutId = setTimeout(() => {
      loadEvents();
    }, 100);

    // Poll events every 10 seconds instead of 3 to reduce load
    const interval = setInterval(() => {
      if (isMounted) {
        loadEvents();
      }
    }, 10000);
    
    return () => {
      isMounted = false;
      if (timeoutId) clearTimeout(timeoutId);
      clearInterval(interval);
    };
  }, [tenantId, portfolioId, positionId]); // Removed 'events' from dependencies to prevent infinite loop

  // Load positions for selector
  useEffect(() => {
    if (!portfolioId) return;

    const loadPositions = async () => {
      try {
        const posData = await portfolioScopedApi.getPositions(tenantId, portfolioId);
        setPositions(posData);
      } catch (error) {
        console.error('Error loading positions:', error);
      }
    };

    loadPositions();
  }, [tenantId, portfolioId]);

  // Load portfolio config for market hours policy and guardrails
  useEffect(() => {
    if (!portfolioId) return;

    const loadConfig = async () => {
      try {
        const config = await portfolioScopedApi.getEffectiveConfig(tenantId, portfolioId);
        setPortfolioConfig({
          market_hours_policy: config.market_hours_policy,
          min_stock_pct: config.min_stock_pct,
          max_stock_pct: config.max_stock_pct,
        });
      } catch (error) {
        console.error('Error loading portfolio config:', error);
      }
    };

    loadConfig();
  }, [tenantId, portfolioId]);

  const handleStartPause = async () => {
    if (!portfolioId || !positionId) return;

    const isRunning = cockpitData?.trading_status === 'RUNNING';
    const endpoint = isRunning ? 'pause' : 'start';

    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/${endpoint}`,
        { method: 'POST' },
      );
      if (response.ok) {
        toast.success(`Position ${isRunning ? 'paused' : 'started'} successfully`);
        // Reload cockpit data
        const cockpitResponse = await fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/cockpit`,
        );
        if (cockpitResponse.ok) {
          const data = await cockpitResponse.json();
          setCockpitData(data);
        }
      } else {
        toast.error(`Failed to ${isRunning ? 'pause' : 'start'} position`);
      }
    } catch (error) {
      toast.error(`Error ${isRunning ? 'pausing' : 'starting'} position`);
    }
  };

  const handleMarketHoursToggle = async () => {
    if (!portfolioId || !portfolioConfig) return;

    const newPolicy =
      portfolioConfig.market_hours_policy === 'market-open-only'
        ? 'market-plus-after-hours'
        : 'market-open-only';

    try {
      const currentConfig = await portfolioScopedApi.getConfig(tenantId, portfolioId);
      await portfolioScopedApi.updateConfig(tenantId, portfolioId, {
        ...currentConfig,
        market_hours_policy: newPolicy as 'market-open-only' | 'market-plus-after-hours',
      });
      setPortfolioConfig({ market_hours_policy: newPolicy });
      toast.success(
        `Market hours policy updated to ${
          newPolicy === 'market-open-only' ? 'Regular only' : 'Allow extended'
        }`,
      );
    } catch (error) {
      console.error('Error updating market hours policy:', error);
      toast.error('Failed to update market hours policy');
    }
  };

  const handleResetBaseline = async () => {
    if (!portfolioId || !positionId) return;

    if (
      !window.confirm(
        'Are you sure you want to reset the baseline? This will set the baseline to the current price and qty, resetting all performance deltas.',
      )
    ) {
      return;
    }

    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/baseline/reset`,
        { method: 'POST' },
      );
      if (response.ok) {
        toast.success('Baseline reset successfully');
        // Reload cockpit data
        const cockpitResponse = await fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/cockpit`,
        );
        if (cockpitResponse.ok) {
          const data = await cockpitResponse.json();
          setCockpitData(data);
        }
      } else {
        const errorData = await response.json();
        toast.error(`Failed to reset baseline: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      toast.error('Error resetting baseline');
    }
  };

  const handleExportExcel = async () => {
    if (!portfolioId || !positionId) return;

    try {
      const response = await fetch(
        `/api/v1/excel/tenants/${tenantId}/portfolios/${portfolioId}/positions/${positionId}/export`,
      );
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `position_cockpit_${positionId}_${
          new Date().toISOString().split('T')[0]
        }.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Excel export started');
      } else {
        toast.error('Failed to export to Excel');
      }
    } catch (error) {
      toast.error('Error exporting to Excel');
    }
  };

  const toggleRowExpansion = (eventId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedRows(newExpanded);
  };

  if (loading && !cockpitData) {
    return <LoadingSpinner message="Loading position cockpit..." />;
  }

  if (!cockpitData) {
    return (
      <EmptyState
        icon={<Activity className="h-16 w-16 text-gray-400" />}
        title="Position Not Found"
        description="The position you're looking for doesn't exist or couldn't be loaded."
      />
    );
  }

  const currentPortfolio = portfolios.find((p) => p.id === portfolioId);
  const currentPosition = positions.find((p) => p.id === positionId);
  const currentPrice =
    cockpitData.current_market_data?.price || cockpitData.position.anchor_price || 0;

  // Use backend allocation data if available, otherwise calculate locally
  const stockValue =
    cockpitData.stock_allocation?.stock_value ?? cockpitData.position.qty * currentPrice;
  const totalValue =
    cockpitData.stock_allocation?.total_position_value ?? stockValue + cockpitData.position.cash;
  const stockPct =
    cockpitData.stock_allocation?.stock_allocation_pct ??
    (totalValue > 0 ? (stockValue / totalValue) * 100 : 0);

  // Guardrail constraints - use backend guardrails if available, otherwise from config
  const minStockPct = cockpitData.guardrails?.min_stock_pct ?? portfolioConfig?.min_stock_pct ?? 0;
  const maxStockPct =
    cockpitData.guardrails?.max_stock_pct ?? portfolioConfig?.max_stock_pct ?? 100;
  // Use backend allocation_within_guardrails if available, otherwise calculate
  const isOutOfGuardrails =
    cockpitData.allocation_within_guardrails === false ||
    (cockpitData.allocation_within_guardrails === null &&
      (stockPct < minStockPct || stockPct > maxStockPct));

  // Helper function to format relative time
  const formatRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffSeconds = Math.floor((now.getTime() - eventTime.getTime()) / 1000);

    if (diffSeconds < 5) return 'Just now';
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return eventTime.toLocaleString();
  };

  // Get recent actions (BUY/SELL) for live activity feed
  const recentActions = events
    .filter((e) => e.action && ['BUY', 'SELL'].includes(e.action))
    .slice(0, 5);

  const filteredEvents = events.filter((event) => {
    // Filter by event type
    if (eventFilter === 'actions_only') {
      const action = event.action || '';
      if (!['BUY', 'SELL'].includes(action)) {
        return false;
      }
    } else if (eventFilter === 'blocked_only') {
      if (!event.guardrail_block_reason && event.action !== 'SKIP') {
        return false;
      }
    } else if (eventFilter === 'dividends_only') {
      if (event.evaluation_type !== 'DIVIDEND' && !event.dividend_applied) {
        return false;
      }
    } else if (eventFilter === 'extended_hours_only') {
      if (event.market_session !== 'EXTENDED') {
        return false;
      }
    } else if (eventFilter !== 'all' && event.evaluation_type !== eventFilter) {
      return false;
    }
    return true;
  });

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="space-y-6 p-6">
        {/* Top Bar - Sticky */}
        <div className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => navigate('/trade')}
                  className="flex items-center text-gray-600 hover:text-gray-900"
                >
                  <ArrowLeft className="h-5 w-5 mr-2" />
                  Back
                </button>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Position Cell Cockpit</h1>
                  <p className="text-sm text-gray-500 mt-1">
                    {currentPortfolio?.name || portfolioId} - {cockpitData.position.asset_symbol}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                {/* Portfolio Selector */}
                <select
                  value={portfolioId || ''}
                  onChange={(e) => {
                    const newPortfolioId = e.target.value;
                    // Find first position in new portfolio or navigate to selection
                    navigate(`/trade/${newPortfolioId}/position/${positionId}`);
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {portfolios.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>

                {/* Position Selector */}
                <select
                  value={positionId || ''}
                  onChange={(e) => navigate(`/trade/${portfolioId}/position/${e.target.value}`)}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {positions.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.asset || p.ticker} - {p.qty.toFixed(2)} shares
                    </option>
                  ))}
                </select>

                {/* Mode Badge */}
                <span
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                    mode === 'LIVE' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {mode}
                </span>

                {/* Market Hours Toggle */}
                <button
                  onClick={handleMarketHoursToggle}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                    portfolioConfig?.market_hours_policy === 'market-plus-after-hours'
                      ? 'bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100'
                      : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                  }`}
                >
                  {portfolioConfig?.market_hours_policy === 'market-plus-after-hours'
                    ? 'Allow Extended'
                    : 'Regular Only'}
                </button>

                {/* Position Actions - Tick execution */}
                {positionId && (
                  <PositionActions positionId={positionId} onAfterAction={refetchCockpitData} />
                )}

                {/* Analytics Button */}
                <button
                  onClick={() =>
                    navigate(
                      `/portfolios/${portfolioId}/positions?tab=analytics&positionId=${positionId}`,
                    )
                  }
                  className="px-3 py-1.5 rounded-lg text-sm font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-colors flex items-center"
                  title="View Position Analytics"
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  ANALYTICS
                </button>

                {/* Start/Pause Button */}
                <button
                  onClick={handleStartPause}
                  className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    cockpitData.trading_status === 'RUNNING'
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {cockpitData.trading_status === 'RUNNING' ? (
                    <>
                      <Pause className="h-4 w-4 mr-2" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Start
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Live Status Banner */}
        <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span
                  className={`w-3 h-3 rounded-full ${
                    workerStatus?.enabled ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                  }`}
                ></span>
                <span className="text-sm font-semibold text-gray-900">
                  {workerStatus?.enabled ? 'Worker Active' : 'Worker Inactive'}
                </span>
              </div>
              {workerStatus && (
                <span className="text-xs text-gray-600">
                  Cycle interval: {workerStatus.interval_seconds}s
                </span>
              )}
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-600" />
                <span className="text-xs text-gray-600">
                  Market data: {formatRelativeTime(lastUpdateTime.toISOString())}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span>Auto-refresh: Market 5s • Events 3s • Cockpit 30s</span>
            </div>
          </div>
        </div>

        {/* Summary Row - 4 Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Holdings Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Cell State</h3>
              <DollarSign className="h-5 w-5 text-gray-400" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Symbol:</span>
                <span className="font-semibold text-gray-900">
                  {cockpitData.position.asset_symbol}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Qty:</span>
                <span className="font-semibold">{cockpitData.position.qty.toFixed(2)} shares</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cash:</span>
                <span className="font-semibold">${cockpitData.position.cash.toFixed(2)}</span>
              </div>
              <div className="pt-2 border-t border-gray-200">
                <div className="flex justify-between">
                  <span className="text-lg font-semibold text-gray-900">Cell Total Value:</span>
                  <span className="text-xl font-bold text-gray-900">${totalValue.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-baseline mt-1">
                  <span className="text-sm text-gray-600">Stock Allocation:</span>
                  <div className="flex flex-col items-end">
                    <span
                      className={`font-bold ${
                        isOutOfGuardrails ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {stockPct.toFixed(1)}%
                    </span>
                    <span className="text-[10px] text-gray-400">
                      Guardrail: {minStockPct}-{maxStockPct}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Baseline Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-medium text-gray-500">Baseline</h3>
              <button
                onClick={handleResetBaseline}
                className="text-[10px] font-bold text-primary-600 bg-primary-50 hover:bg-primary-100 px-2 py-1 rounded transition-colors"
              >
                RESET
              </button>
            </div>
            {cockpitData.baseline ? (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Baseline timestamp:</span>
                  <span>{new Date(cockpitData.baseline.baseline_timestamp).toLocaleString()}</span>
                </div>
                {cockpitData.position_vs_baseline.pct !== null && (
                  <>
                    <div className="pt-2 border-t border-gray-200">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Position Δ vs baseline:</span>
                        <div className="text-right">
                          <div
                            className={`font-semibold ${
                              (cockpitData.position_vs_baseline.pct || 0) >= 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {cockpitData.position_vs_baseline.pct >= 0 ? '+' : ''}
                            {cockpitData.position_vs_baseline.pct.toFixed(2)}%
                          </div>
                          <div className="text-xs text-gray-500">
                            {cockpitData.position_vs_baseline.abs !== null &&
                            cockpitData.position_vs_baseline.abs >= 0
                              ? '+'
                              : ''}
                            ${cockpitData.position_vs_baseline.abs?.toFixed(2) || '0.00'}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="pt-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Stock Δ vs baseline:</span>
                        <div className="text-right">
                          <div
                            className={`font-semibold ${
                              (cockpitData.stock_vs_baseline.pct || 0) >= 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {(cockpitData.stock_vs_baseline.pct ?? 0) >= 0 ? '+' : ''}
                            {(cockpitData.stock_vs_baseline.pct ?? 0).toFixed(2)}%
                          </div>
                          <div className="text-xs text-gray-500">
                            {cockpitData.stock_vs_baseline.abs !== null &&
                            cockpitData.stock_vs_baseline.abs >= 0
                              ? '+'
                              : ''}
                            ${cockpitData.stock_vs_baseline.abs?.toFixed(2) || '0.00'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
                <div className="pt-2 border-t border-gray-200">
                  <button
                    onClick={() => {
                      // TODO: Implement reset baseline
                      toast('Reset baseline functionality coming soon');
                    }}
                    className="w-full px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    Reset Baseline
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">No baseline set</div>
            )}
          </div>

          {/* Anchor & Drift Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Anchor & Drift</h3>
              <Anchor className="h-5 w-5 text-gray-400" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Anchor price:</span>
                <span className="font-semibold">
                  ${cockpitData.position.anchor_price?.toFixed(2) || 'N/A'}
                </span>
              </div>
              {cockpitData.position.anchor_price && (
                <>
                  <div className="pt-2 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">% change from anchor:</span>
                      <span
                        className={`font-semibold flex items-center ${
                          currentPrice >= (cockpitData.position.anchor_price || 0)
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {currentPrice >= (cockpitData.position.anchor_price || 0) ? (
                          <TrendingUp className="h-4 w-4 mr-1" />
                        ) : (
                          <TrendingDown className="h-4 w-4 mr-1" />
                        )}
                        {(
                          ((currentPrice - cockpitData.position.anchor_price) /
                            cockpitData.position.anchor_price) *
                          100
                        ).toFixed(2)}
                        %
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Last anchor update:</span>
                    <span>
                      {cockpitData.baseline?.baseline_timestamp
                        ? new Date(cockpitData.baseline.baseline_timestamp).toLocaleString()
                        : 'N/A'}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Trading Status Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Trading Status</h3>
              <Activity className="h-5 w-5 text-gray-400" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span
                  className={`px-2 py-1 rounded text-sm font-medium ${
                    cockpitData.trading_status === 'RUNNING'
                      ? 'bg-green-100 text-green-700'
                      : cockpitData.trading_status === 'PAUSED'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {cockpitData.trading_status}
                </span>
              </div>
              {/* Block reason - get from most recent event */}
              {events.length > 0 && events[0].guardrail_block_reason && (
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-600 mb-1">Block reason:</div>
                  <div className="text-sm text-red-600">{events[0].guardrail_block_reason}</div>
                </div>
              )}
              {/* Last action + timestamp */}
              {events.length > 0 && events[0].action && events[0].action !== 'HOLD' && (
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-600 mb-1">Last action:</div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-gray-900">{events[0].action}</span>
                    <span className="text-xs text-gray-500">
                      {events.length > 0 ? formatRelativeTime(events[0].timestamp) : 'No events'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Market Data Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200">
            <div className="flex items-center justify-between p-4">
              <h2 className="text-lg font-semibold text-gray-900">Market Data</h2>
              <div className="flex space-x-2">
                <button
                  onClick={() => setMarketDataTab('latest')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg ${
                    marketDataTab === 'latest'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Latest
                </button>
                <button
                  onClick={() => setMarketDataTab('recent')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg ${
                    marketDataTab === 'recent'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Recent
                </button>
              </div>
            </div>
          </div>
          <div className="p-6">
            {marketDataTab === 'latest' ? (
              marketData?.latest ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-gray-500">
                      Last updated:{' '}
                      {formatRelativeTime(marketData.latest.timestamp || new Date().toISOString())}
                    </span>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                      Live
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Session:</span>
                      <span className="font-semibold text-gray-900">
                        {marketData.latest.session || 'REGULAR'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Effective price:</span>
                      <span
                        className={`text-xl font-bold text-gray-900 transition-all duration-300 ${
                          priceUpdateFlash
                            ? 'bg-yellow-200 px-3 py-1 rounded-lg animate-pulse scale-105'
                            : ''
                        }`}
                      >
                        $
                        {(
                          marketData.latest.effective_price ||
                          marketData.latest.price ||
                          0
                        ).toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Policy:</span>
                      <span className="font-semibold text-gray-900">
                        {marketData.latest.price_policy_effective || 'MID'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Bid/Ask:</span>
                      <span className="font-semibold text-gray-900">
                        {marketData.latest.best_bid && marketData.latest.best_ask
                          ? `$${marketData.latest.best_bid.toFixed(
                              2,
                            )} / $${marketData.latest.best_ask.toFixed(2)}`
                          : '—'}
                      </span>
                    </div>
                  </div>
                  {(marketData.latest.open_price ||
                    marketData.latest.high_price ||
                    marketData.latest.low_price ||
                    marketData.latest.close_price) && (
                    <div className="pt-3 border-t border-gray-200">
                      <div className="text-sm font-medium text-gray-700 mb-2">OHLCV:</div>
                      <div className="grid grid-cols-5 gap-2 text-sm">
                        {marketData.latest.open_price !== undefined && (
                          <div>
                            <span className="text-gray-600">Open:</span>
                            <div className="font-semibold">
                              ${marketData.latest.open_price.toFixed(2)}
                            </div>
                          </div>
                        )}
                        {marketData.latest.high_price !== undefined && (
                          <div>
                            <span className="text-gray-600">High:</span>
                            <div className="font-semibold">
                              ${marketData.latest.high_price.toFixed(2)}
                            </div>
                          </div>
                        )}
                        {marketData.latest.low_price !== undefined && (
                          <div>
                            <span className="text-gray-600">Low:</span>
                            <div className="font-semibold">
                              ${marketData.latest.low_price.toFixed(2)}
                            </div>
                          </div>
                        )}
                        {marketData.latest.close_price !== undefined && (
                          <div>
                            <span className="text-gray-600">Close:</span>
                            <div className="font-semibold">
                              ${marketData.latest.close_price.toFixed(2)}
                            </div>
                          </div>
                        )}
                        {marketData.latest.volume !== undefined && (
                          <div>
                            <span className="text-gray-600">Volume:</span>
                            <div className="font-semibold">
                              {(marketData.latest.volume / 1000000).toFixed(2)}M
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No market data available</div>
              )
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Timestamp
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Session
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Effective Price
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Close
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Bid/Ask
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {marketData?.recent && marketData.recent.length > 0 ? (
                      marketData.recent.map((point, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {point.timestamp ? new Date(point.timestamp).toLocaleString() : '—'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {point.session || 'REGULAR'}
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                            ${(point.effective_price || point.price || 0).toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {point.close !== undefined ? `$${point.close.toFixed(2)}` : '—'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {point.bid !== undefined && point.ask !== undefined
                              ? `$${point.bid.toFixed(2)} / $${point.ask.toFixed(2)}`
                              : '—'}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-500">
                          No recent market data available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Live Activity Feed - Always visible when there are events */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-600 animate-pulse" />
                Live Activity Feed
                {recentActions.length > 0 && (
                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                    {recentActions.length} Recent
                  </span>
                )}
              </h2>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">
                  Last update: {formatRelativeTime(lastUpdateTime.toISOString())}
                </span>
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                  Live
                </span>
              </div>
            </div>
          </div>
          <div className="p-4 space-y-2">
            {recentActions.length > 0 ? (
              recentActions.map((action, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border-l-4 ${
                    action.action === 'BUY'
                      ? 'bg-green-50 border-green-500'
                      : action.action === 'SELL'
                      ? 'bg-red-50 border-red-500'
                      : 'bg-gray-50 border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          action.action === 'BUY'
                            ? 'bg-green-600 text-white'
                            : action.action === 'SELL'
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-600 text-white'
                        }`}
                      >
                        {action.action}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {action.action_reason || action.trigger_reason || 'Trading action'}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(action.timestamp)}
                    </span>
                  </div>
                  {action.qty_after !== undefined && (
                    <div className="mt-2 text-xs text-gray-600">
                      Qty: {action.qty_before?.toFixed(2) || '—'} → {action.qty_after.toFixed(2)} |
                      Price: ${action.effective_price?.toFixed(2) || '—'} | Value: $
                      {action.position_total_value_after?.toFixed(2) || '—'}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No trading actions yet</p>
                <p className="text-xs mt-1">Actions will appear here when triggers fire</p>
                {positionId && (
                  <div className="mt-4 flex justify-center">
                    <PositionActions positionId={positionId} onAfterAction={refetchCockpitData} />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Event Timeline Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Event Timeline</h2>
              <span className="text-xs text-gray-500">
                Auto-refreshing every 3s • Last: {formatRelativeTime(lastUpdateTime.toISOString())}
              </span>
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <select
                    value={eventFilter}
                    onChange={(e) => setEventFilter(e.target.value)}
                    className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none text-sm"
                  >
                    <option value="all">All Events</option>
                    <option value="actions_only">Actions Only</option>
                    <option value="blocked_only">Blocked Only</option>
                    <option value="dividends_only">Dividends Only</option>
                    <option value="extended_hours_only">Extended Hours Only</option>
                    <option value="DAILY_CHECK">Daily Check</option>
                    <option value="PRICE_UPDATE">Price Update</option>
                    <option value="TRIGGER_EVALUATED">Trigger Evaluated</option>
                    <option value="EXECUTION">Execution</option>
                  </select>
                </div>
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={verboseMode}
                    onChange={(e) => setVerboseMode(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">Verbose Mode</span>
                </label>
                <button
                  onClick={handleExportExcel}
                  className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export to Excel
                </button>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12"></th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Session
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Effective Price
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Anchor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    % from Anchor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Stock Allocation
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Action
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Reason
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Qty Before → After
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Cash Before → After
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Total Value After
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Position Δ vs Baseline
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Stock Δ vs Baseline
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredEvents.length > 0 ? (
                  filteredEvents.map((event) => (
                    <>
                      <tr
                        key={event.id}
                        className={`hover:bg-gray-50 cursor-pointer ${
                          // Highlight events from last 30 seconds
                          (new Date().getTime() - new Date(event.timestamp).getTime()) / 1000 < 30
                            ? 'bg-yellow-50 border-l-4 border-yellow-400'
                            : ''
                        }`}
                        onClick={() => toggleRowExpansion(event.id)}
                      >
                        <td className="px-4 py-3">
                          {expandedRows.has(event.id) ? (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <div className="flex flex-col">
                            <span className="font-medium">
                              {formatRelativeTime(event.timestamp)}
                            </span>
                            <span className="text-xs text-gray-400">
                              {new Date(event.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {event.evaluation_type || 'EVENT'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {event.market_session || 'REGULAR'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <div className="flex flex-col">
                            <span>
                              {event.effective_price ? `$${event.effective_price.toFixed(2)}` : '—'}
                            </span>
                            {event.pct_change_from_prev !== undefined &&
                              event.pct_change_from_prev !== 0 &&
                              event.pct_change_from_prev !== null && (
                                <span
                                  className={`text-[10px] font-bold ${
                                    event.pct_change_from_prev >= 0
                                      ? 'text-green-600'
                                      : 'text-red-600'
                                  }`}
                                >
                                  {event.pct_change_from_prev >= 0 ? '▲' : '▼'}{' '}
                                  {Math.abs(event.pct_change_from_prev).toFixed(2)}%
                                </span>
                              )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {event.anchor_price ? `$${event.anchor_price.toFixed(2)}` : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {event.pct_change_from_anchor !== null &&
                          event.pct_change_from_anchor !== undefined
                            ? `${
                                event.pct_change_from_anchor >= 0 ? '+' : ''
                              }${event.pct_change_from_anchor.toFixed(2)}%`
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <div className="flex flex-col">
                            {event.stock_pct !== null && event.stock_pct !== undefined ? (
                              <>
                                <span
                                  className={`font-semibold ${
                                    event.guardrail_min_stock_pct !== null &&
                                    event.guardrail_max_stock_pct !== null &&
                                    (event.stock_pct < event.guardrail_min_stock_pct ||
                                      event.stock_pct > event.guardrail_max_stock_pct)
                                      ? 'text-red-600'
                                      : 'text-gray-900'
                                  }`}
                                >
                                  {event.stock_pct.toFixed(1)}%
                                </span>
                                {event.guardrail_min_stock_pct !== null &&
                                  event.guardrail_max_stock_pct !== null && (
                                    <span className="text-[10px] text-gray-400">
                                      [{event.guardrail_min_stock_pct.toFixed(0)}-
                                      {event.guardrail_max_stock_pct.toFixed(0)}%]
                                    </span>
                                  )}
                                {event.guardrail_allowed === false && (
                                  <span className="text-[10px] text-red-600 font-bold">
                                    BLOCKED
                                  </span>
                                )}
                              </>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {event.action && event.action !== 'HOLD' ? (
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                event.action === 'BUY'
                                  ? 'bg-green-100 text-green-800'
                                  : event.action === 'SELL'
                                  ? 'bg-red-100 text-red-800'
                                  : event.action === 'SKIP'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {event.action}
                            </span>
                          ) : (
                            <span className="text-gray-400">HOLD</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                          {event.action_reason || '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {event.position_qty_before !== undefined &&
                          event.position_qty_after !== undefined
                            ? `${event.position_qty_before.toFixed(
                                2,
                              )} → ${event.position_qty_after.toFixed(2)}`
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {event.position_cash_before !== undefined &&
                          event.position_cash_after !== undefined
                            ? `$${event.position_cash_before.toFixed(
                                2,
                              )} → $${event.position_cash_after.toFixed(2)}`
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {event.position_total_value_after !== undefined
                            ? `$${event.position_total_value_after.toFixed(2)}`
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {event.position_delta_vs_baseline_pct !== null &&
                          event.position_delta_vs_baseline_pct !== undefined ? (
                            <span
                              className={`font-semibold ${
                                event.position_delta_vs_baseline_pct >= 0
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {event.position_delta_vs_baseline_pct >= 0 ? '+' : ''}
                              {event.position_delta_vs_baseline_pct.toFixed(2)}%
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {event.stock_delta_vs_baseline_pct !== null &&
                          event.stock_delta_vs_baseline_pct !== undefined ? (
                            <span
                              className={`font-semibold ${
                                event.stock_delta_vs_baseline_pct >= 0
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {event.stock_delta_vs_baseline_pct >= 0 ? '+' : ''}
                              {event.stock_delta_vs_baseline_pct.toFixed(2)}%
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                      {expandedRows.has(event.id) && (
                        <tr className="bg-gray-50">
                          <td colSpan={14} className="px-4 py-4">
                            <div className="text-xs text-gray-600 space-y-2">
                              {verboseMode ? (
                                <pre className="whitespace-pre-wrap font-mono bg-gray-100 p-3 rounded">
                                  {JSON.stringify(event, null, 2)}
                                </pre>
                              ) : (
                                <div className="grid grid-cols-2 gap-4">
                                  {/* OHLCV + Bid/Ask */}
                                  {(event.open_price ||
                                    event.high_price ||
                                    event.low_price ||
                                    event.close_price ||
                                    event.best_bid ||
                                    event.best_ask) && (
                                    <div>
                                      <div className="font-semibold mb-2">Market Data</div>
                                      <div className="space-y-1">
                                        {event.open_price !== undefined && (
                                          <div>Open: ${event.open_price.toFixed(2)}</div>
                                        )}
                                        {event.high_price !== undefined && (
                                          <div>High: ${event.high_price.toFixed(2)}</div>
                                        )}
                                        {event.low_price !== undefined && (
                                          <div>Low: ${event.low_price.toFixed(2)}</div>
                                        )}
                                        {event.close_price !== undefined && (
                                          <div>Close: ${event.close_price.toFixed(2)}</div>
                                        )}
                                        {event.volume !== undefined && (
                                          <div>Volume: {(event.volume / 1000000).toFixed(2)}M</div>
                                        )}
                                        {event.best_bid !== undefined &&
                                          event.best_ask !== undefined && (
                                            <div>
                                              Bid/Ask: ${event.best_bid.toFixed(2)} / $
                                              {event.best_ask.toFixed(2)}
                                            </div>
                                          )}
                                      </div>
                                    </div>
                                  )}
                                  {/* Trigger thresholds + decision */}
                                  {(event.trigger_up_threshold ||
                                    event.trigger_down_threshold ||
                                    event.trigger_fired ||
                                    event.trigger_direction) && (
                                    <div>
                                      <div className="font-semibold mb-2">Trigger Evaluation</div>
                                      <div className="space-y-1">
                                        {event.trigger_up_threshold !== undefined && (
                                          <div>
                                            Up Threshold: {event.trigger_up_threshold.toFixed(2)}%
                                          </div>
                                        )}
                                        {event.trigger_down_threshold !== undefined && (
                                          <div>
                                            Down Threshold:{' '}
                                            {event.trigger_down_threshold.toFixed(2)}%
                                          </div>
                                        )}
                                        {event.trigger_direction && (
                                          <div>Direction: {event.trigger_direction}</div>
                                        )}
                                        <div>Fired: {event.trigger_fired ? 'Yes' : 'No'}</div>
                                        {event.trigger_reason && (
                                          <div>Reason: {event.trigger_reason}</div>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                  {/* Guardrail min/max + allocation calc + allowed/block reason */}
                                  {(event.guardrail_min_stock_pct ||
                                    event.guardrail_max_stock_pct ||
                                    event.guardrail_block_reason ||
                                    event.position_stock_pct_before) && (
                                    <div>
                                      <div className="font-semibold mb-2">Guardrail Evaluation</div>
                                      <div className="space-y-1">
                                        {event.guardrail_min_stock_pct !== undefined && (
                                          <div>
                                            Min Stock %: {event.guardrail_min_stock_pct.toFixed(1)}%
                                          </div>
                                        )}
                                        {event.guardrail_max_stock_pct !== undefined && (
                                          <div>
                                            Max Stock %: {event.guardrail_max_stock_pct.toFixed(1)}%
                                          </div>
                                        )}
                                        {event.position_stock_pct_before !== undefined && (
                                          <div>
                                            Current Allocation:{' '}
                                            {event.position_stock_pct_before.toFixed(1)}%
                                          </div>
                                        )}
                                        {event.guardrail_block_reason && (
                                          <div className="text-red-600">
                                            Blocked: {event.guardrail_block_reason}
                                          </div>
                                        )}
                                        {event.guardrail_allowed !== undefined && (
                                          <div>
                                            Allowed: {event.guardrail_allowed ? 'Yes' : 'No'}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                  {/* Dividend fields if applicable */}
                                  {event.dividend_applied && (
                                    <div>
                                      <div className="font-semibold mb-2">Dividend</div>
                                      <div className="space-y-1">
                                        {event.dividend_rate !== undefined && (
                                          <div>Rate: ${event.dividend_rate.toFixed(4)}/share</div>
                                        )}
                                        {event.dividend_gross_value !== undefined && (
                                          <div>Gross: ${event.dividend_gross_value.toFixed(2)}</div>
                                        )}
                                        {event.dividend_net_value !== undefined && (
                                          <div>Net: ${event.dividend_net_value.toFixed(2)}</div>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                  {/* Order/trade IDs if applicable */}
                                  {(event.order_id || event.trade_id) && (
                                    <div>
                                      <div className="font-semibold mb-2">Execution</div>
                                      <div className="space-y-1">
                                        {event.order_id && <div>Order ID: {event.order_id}</div>}
                                        {event.trade_id && <div>Trade ID: {event.trade_id}</div>}
                                        {event.execution_price !== undefined && (
                                          <div>
                                            Execution Price: ${event.execution_price.toFixed(2)}
                                          </div>
                                        )}
                                        {event.execution_qty !== undefined && (
                                          <div>Execution Qty: {event.execution_qty.toFixed(2)}</div>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                  {/* Pricing notes */}
                                  {event.pricing_notes && (
                                    <div>
                                      <div className="font-semibold mb-2">Pricing Notes</div>
                                      <div className="text-gray-600">{event.pricing_notes}</div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))
                ) : (
                  <tr>
                    <td colSpan={14} className="px-4 py-8 text-center text-sm text-gray-500">
                      No events found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}






