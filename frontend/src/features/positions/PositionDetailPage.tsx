import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Settings,
  DollarSign,
  TrendingUp,
  TrendingDown,
  PieChart,
  Activity,
  Clock,
  Play,
  Pause,
  Download,
  Edit,
  Anchor,
} from 'lucide-react';
import { portfolioApi, marketApi } from '../../lib/api';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import EmptyState from '../../components/shared/EmptyState';
import PositionCellCard from '../../components/positions/PositionCellCard';
import PositionActions from './PositionActions';

interface Position {
  id: string;
  asset?: string;
  ticker?: string;
  qty: number;
  cash: number;
  anchor_price: number | null;
  avg_cost?: number | null;
  status?: string;
  total_commission_paid?: number;
  total_dividends_received?: number;
}

interface MarketData {
  price: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  bid?: number;
  ask?: number;
  is_market_hours?: boolean;
}

interface Baseline {
  baseline_price: number;
  baseline_qty: number;
  baseline_cash: number;
  baseline_total_value: number;
  baseline_stock_value: number;
  baseline_timestamp: string;
}

interface PositionEvent {
  id: string;
  event_type?: string;
  evaluation_type?: string;
  timestamp: string;
  effective_price?: number;
  market_price_raw?: number;
  anchor_price?: number;
  action?: string;
  action_taken?: string;
  action_reason?: string;
  evaluation_summary?: string;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  close_price?: number;
  position_qty_before?: number;
  position_qty_after?: number;
  position_cash_before?: number;
  position_cash_after?: number;
  position_total_value_after?: number;
  details?: any;
}

interface EffectiveConfig {
  trigger_up_pct: number;
  trigger_down_pct: number;
  min_stock_pct: number;
  max_stock_pct: number;
  max_trade_pct_of_position: number;
  commission_rate_pct: number;
}

export default function PositionDetailPage() {
  const { portfolioId, positionId } = useParams<{ portfolioId: string; positionId: string }>();
  const navigate = useNavigate();
  const { selectedTenantId, selectedPortfolioId, portfolios } = useTenantPortfolio();

  const currentPortfolioId = portfolioId || selectedPortfolioId;
  const currentPositionId = positionId || useSearchParams()[0].get('positionId');
  const tenantId = selectedTenantId || 'default';

  const [position, setPosition] = useState<Position | null>(null);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [baseline, setBaseline] = useState<Baseline | null>(null);
  const [events, setEvents] = useState<PositionEvent[]>([]);
  const [config, setConfig] = useState<EffectiveConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');

  useEffect(() => {
    if (!currentPortfolioId || !currentPositionId) {
      setError('Portfolio ID and Position ID are required');
      setLoading(false);
      return;
    }
    loadPositionData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPortfolioId, currentPositionId, tenantId]);

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };
    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  // Helper function to create fetch with timeout
  const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeoutMs = 10000): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout: ${url} took longer than ${timeoutMs}ms`);
      }
      throw error;
    }
  };

  const loadPositionData = async (showLoadingSpinner = false) => {
    if (!currentPortfolioId || !currentPositionId) {
      setError('Portfolio ID and Position ID are required');
      setLoading(false);
      return;
    }

    console.log(`[PositionDetailPage] Loading data for position ${currentPositionId} in portfolio ${currentPortfolioId}`);

    // Only show full page loading spinner on initial load or when explicitly requested
    const isInitialLoad = showLoadingSpinner || position === null;
    if (isInitialLoad) {
      setLoading(true);
    } else {
      // Show a subtle refresh indicator for subsequent loads
      setRefreshing(true);
    }
    setError(null);

    // Set a maximum timeout for the entire load operation
    let timeoutFired = false;
    const loadTimeout = setTimeout(() => {
      timeoutFired = true;
      console.warn('[PositionDetailPage] Load timeout - taking longer than 30 seconds');
      setError('Loading is taking longer than expected. Some data may be missing.');
      setLoading(false);
      setRefreshing(false);
    }, 30000); // 30 second max timeout

    try {
      // Load position with individual timeout
      console.log('[PositionDetailPage] Fetching positions...');
      const positionsPromise = portfolioApi.getPositions(tenantId, currentPortfolioId);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Position fetch timeout after 10 seconds')), 10000)
      );
      
      const positions = await Promise.race([positionsPromise, timeoutPromise]) as any[];
      
      if (timeoutFired) {
        clearTimeout(loadTimeout);
        return; // Timeout already handled
      }
      
      console.log(`[PositionDetailPage] Found ${positions.length} positions`);
      const foundPosition = positions.find((p) => p.id === currentPositionId);
      if (!foundPosition) {
        clearTimeout(loadTimeout);
        setError(`Position ${currentPositionId} not found in portfolio`);
        setLoading(false);
        setRefreshing(false);
        return;
      }
      
      console.log('[PositionDetailPage] Position found:', foundPosition.id, foundPosition.asset);

      const positionData: Position = {
        id: foundPosition.id,
        asset: foundPosition.asset,
        ticker: foundPosition.asset,
        qty: foundPosition.qty,
        cash: (foundPosition as any).cash || 0,
        anchor_price: foundPosition.anchor_price,
        avg_cost: foundPosition.avg_cost,
        status: (foundPosition as any).status || 'RUNNING',
      };
      setPosition(positionData);

      // Load market data
      const asset = positionData.asset || positionData.ticker;
      if (asset) {
        try {
          const market = await marketApi.getPrice(asset);
          setMarketData({
            price: market.price,
            open: market.open,
            high: market.high,
            low: market.low,
            close: market.close,
            is_market_hours: market.is_market_hours,
          });
        } catch (err) {
          console.warn('Failed to load market data:', err);
        }
      }

      // Load baseline with timeout
      try {
        const baselineRes = await fetchWithTimeout(
          `/api/v1/tenants/${tenantId}/portfolios/${currentPortfolioId}/positions/${currentPositionId}/baseline`,
          {},
          10000, // 10 second timeout
        );
        if (baselineRes.ok) {
          const baselineData = await baselineRes.json();
          setBaseline(baselineData);
        }
      } catch (err: any) {
        console.warn('Failed to load baseline:', err.message || err);
      }

      // Load events - try timeline first (more detailed), fallback to events if empty
      try {
        // First try timeline endpoint (more detailed data)
        const timelineRes = await fetchWithTimeout(
          `/api/v1/tenants/${tenantId}/portfolios/${currentPortfolioId}/positions/${currentPositionId}/timeline?limit=50&mode=LIVE`,
          {},
          15000, // 15 second timeout for timeline
        );
        if (timelineRes.ok) {
          const timelineData = await timelineRes.json();
          if (Array.isArray(timelineData) && timelineData.length > 0) {
            setEvents(timelineData);
          } else {
            // Timeline is empty, fallback to events endpoint
            console.log('Timeline is empty, falling back to events endpoint');
            const eventsRes = await fetchWithTimeout(
              `/api/v1/tenants/${tenantId}/portfolios/${currentPortfolioId}/positions/${currentPositionId}/events?limit=50`,
              {},
              10000, // 10 second timeout
            );
            if (eventsRes.ok) {
              const eventsData = await eventsRes.json();
              // Events endpoint might return array or object with events array
              const eventsArray = Array.isArray(eventsData) 
                ? eventsData 
                : (eventsData.events || []);
              setEvents(eventsArray);
            }
          }
        } else {
          // Timeline failed, try events endpoint
          const eventsRes = await fetchWithTimeout(
            `/api/v1/tenants/${tenantId}/portfolios/${currentPortfolioId}/positions/${currentPositionId}/events?limit=50`,
            {},
            10000, // 10 second timeout
          );
          if (eventsRes.ok) {
            const eventsData = await eventsRes.json();
            const eventsArray = Array.isArray(eventsData) 
              ? eventsData 
              : (eventsData.events || []);
            setEvents(eventsArray);
          }
        }
      } catch (err: any) {
        console.warn('Failed to load events:', err.message || err);
        // Set empty array so page doesn't hang
        setEvents([]);
      }

      // Load effective config with timeout
      try {
        const configRes = await fetchWithTimeout(
          `/api/v1/tenants/${tenantId}/portfolios/${currentPortfolioId}/config/effective`,
          {},
          10000, // 10 second timeout
        );
        if (configRes.ok) {
          const configData = await configRes.json();
          setConfig({
            trigger_up_pct: configData.trigger_threshold_up_pct || 3.0,
            trigger_down_pct: configData.trigger_threshold_down_pct || -3.0,
            min_stock_pct: configData.min_stock_pct || 25.0,
            max_stock_pct: configData.max_stock_pct || 75.0,
            max_trade_pct_of_position: configData.max_trade_pct_of_position || 15.0,
            commission_rate_pct: configData.commission_rate || 0.1,
          });
        }
      } catch (err: any) {
        console.warn('Failed to load config:', err.message || err);
      }
    } catch (err: any) {
      console.error('[PositionDetailPage] Error loading position data:', err);
      if (!timeoutFired) {
        clearTimeout(loadTimeout);
        setError(err.message || 'Failed to load position data');
        setLoading(false);
        setRefreshing(false);
      }
    } finally {
      if (!timeoutFired) {
        clearTimeout(loadTimeout);
        setLoading(false);
        setRefreshing(false);
      }
      console.log('[PositionDetailPage] Load complete');
    }
  };

  // Refresh market data periodically
  useEffect(() => {
    if (!position?.asset) return;

    const refreshMarketData = async () => {
      try {
        const market = await marketApi.getPrice(position.asset!);
        setMarketData({
          price: market.price,
          open: market.open,
          high: market.high,
          low: market.low,
          close: market.close,
          is_market_hours: market.is_market_hours,
        });
      } catch (err) {
        console.warn('Failed to refresh market data:', err);
      }
    };

    const interval = setInterval(refreshMarketData, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [position?.asset]);

  // Show loading state with timeout warning and debug info
  if (loading) {
    return (
      <div className="space-y-4 p-6">
        <LoadingSpinner message="Loading position details..." />
        <div className="text-center text-sm text-gray-500 mt-4 space-y-2">
          <p>Loading position: <code className="bg-gray-100 px-2 py-1 rounded">{currentPositionId}</code></p>
          <p>Portfolio: <code className="bg-gray-100 px-2 py-1 rounded">{currentPortfolioId}</code></p>
          <p className="mt-4 text-xs">If this takes longer than 30 seconds, check:</p>
          <ul className="text-xs text-left max-w-md mx-auto mt-2 space-y-1">
            <li>• Browser console (F12) for errors</li>
            <li>• Backend server is running on port 8000</li>
            <li>• Network tab shows API requests</li>
          </ul>
          <button
            onClick={() => {
              console.log('Force stopping load...');
              setLoading(false);
              setError('Loading cancelled by user');
            }}
            className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Cancel Loading
          </button>
        </div>
      </div>
    );
  }

  // Show error state or partial data
  if (error && !position) {
    return (
      <div className="space-y-4 p-6">
        <button
          onClick={() => navigate(`/portfolios/${currentPortfolioId}/positions`)}
          className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back to Position Cells</span>
        </button>
        <EmptyState
          icon={<Activity className="h-16 w-16 text-gray-400" />}
          title={error || 'Position not found'}
          description="The position you're looking for doesn't exist or couldn't be loaded. Check the browser console for details."
        />
      </div>
    );
  }

  // If we have an error but also have position data, show a warning but still render
  if (error && position) {
    console.warn('Position loaded with errors:', error);
  }

  const asset = position.asset || position.ticker || 'UNKNOWN';
  const currentPrice = marketData?.price || position.anchor_price || position.avg_cost || 0;
  const stockValue = position.qty * currentPrice;
  const totalValue = stockValue + (position.cash || 0);
  const cashPct = totalValue > 0 ? ((position.cash || 0) / totalValue) * 100 : 0;
  const stockPct = totalValue > 0 ? (stockValue / totalValue) * 100 : 0;

  // Calculate performance metrics
  const initialPrice =
    baseline?.baseline_price || position.anchor_price || position.avg_cost || currentPrice;
  const positionReturn =
    baseline && baseline.baseline_total_value > 0
      ? ((totalValue - baseline.baseline_total_value) / baseline.baseline_total_value) * 100
      : initialPrice > 0
      ? ((currentPrice - initialPrice) / initialPrice) * 100
      : 0;
  const stockReturn = initialPrice > 0 ? ((currentPrice - initialPrice) / initialPrice) * 100 : 0;
  const alpha = positionReturn - stockReturn;

  // Calculate anchor deviation
  const anchorPrice = position.anchor_price || initialPrice;
  const anchorDeviation = anchorPrice > 0 ? ((currentPrice - anchorPrice) / anchorPrice) * 100 : 0;

  // Calculate trigger prices
  const buyTriggerPrice = config
    ? anchorPrice * (1 + config.trigger_down_pct / 100)
    : anchorPrice * 0.97;
  const sellTriggerPrice = config
    ? anchorPrice * (1 + config.trigger_up_pct / 100)
    : anchorPrice * 1.03;

  const priceChange = marketData?.close ? currentPrice - marketData.close : 0;
  const priceChangePct =
    marketData?.close && marketData.close > 0
      ? ((currentPrice - marketData.close) / marketData.close) * 100
      : 0;

  // Get recent trades from events
  const recentTrades = events.filter(
    (e) => e.event_type?.includes('TRADE') || e.event_type?.includes('ORDER'),
  );
  const lastTrade = recentTrades.length > 0 ? recentTrades[0] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {
              // Navigate to positions list and explicitly clear positionId from search params
              const searchParams = new URLSearchParams();
              searchParams.set('tab', 'positions');
              // Don't set positionId - this ensures we see the list, not a detail view
              navigate(`/portfolios/${currentPortfolioId}/positions?${searchParams.toString()}`, {
                replace: true,
              });
            }}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-colors font-medium shadow-sm"
            title="Go back to Position Cells list (where you can Add/Remove positions)"
          >
            <ArrowLeft className="h-5 w-5" />
            <span>Back to Position Cells</span>
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{asset} Position Cell</h1>
            <p className="text-sm text-gray-500 mt-1">Position ID: {position.id}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              position.status === 'PAUSED'
                ? 'bg-gray-100 text-gray-700'
                : 'bg-green-100 text-green-700'
            }`}
          >
            {position.status || 'ACTIVE'}
          </span>
          <button
            onClick={() => navigate(`/portfolios/${currentPortfolioId}/positions?tab=strategy`)}
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Value Breakdown */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Value Breakdown</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cash Balance:</span>
                <span className="text-lg font-semibold text-gray-900">
                  $
                  {(position.cash || 0).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Stock Holdings:</span>
                <span className="text-lg font-semibold text-gray-900">
                  {position.qty.toLocaleString()} shares @ ${currentPrice.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Stock Value:</span>
                <span className="text-lg font-semibold text-gray-900">
                  $
                  {stockValue.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-semibold text-gray-900">Total Value:</span>
                  <span className="text-2xl font-bold text-gray-900">
                    $
                    {totalValue.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>
                </div>
                <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                  <span>
                    Allocation: {cashPct.toFixed(1)}% cash, {stockPct.toFixed(1)}% stock
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Market Data */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Market Data</h2>
            {marketData ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Current Price:</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl font-bold text-gray-900">
                      ${currentPrice.toFixed(2)}
                    </span>
                    <span
                      className={`flex items-center text-sm font-medium ${
                        priceChange >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {priceChange >= 0 ? (
                        <TrendingUp className="h-4 w-4 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 mr-1" />
                      )}
                      {priceChange >= 0 ? '+' : ''}${Math.abs(priceChange).toFixed(2)} (
                      {priceChange >= 0 ? '+' : ''}
                      {priceChangePct.toFixed(2)}%)
                    </span>
                  </div>
                </div>
                {marketData.open != null && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Open:</span>
                      <span className="text-gray-900">${(marketData.open || 0).toFixed(2)}</span>
                    </div>
                    {marketData.high != null && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">High:</span>
                        <span className="text-gray-900">${(marketData.high || 0).toFixed(2)}</span>
                      </div>
                    )}
                    {marketData.low != null && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Low:</span>
                        <span className="text-gray-900">${(marketData.low || 0).toFixed(2)}</span>
                      </div>
                    )}
                    {marketData.close != null && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Close (Prev):</span>
                        <span className="text-gray-900">${(marketData.close || 0).toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                )}
                {marketData.volume != null && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Volume:</span>
                    <span className="text-gray-900">
                      {((marketData.volume || 0) / 1000000).toFixed(1)}M
                    </span>
                  </div>
                )}
                {marketData.bid != null && marketData.ask != null && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Bid/Ask:</span>
                    <span className="text-gray-900">
                      ${(marketData.bid || 0).toFixed(2)} / ${(marketData.ask || 0).toFixed(2)}
                    </span>
                  </div>
                )}
                {marketData.bid != null && marketData.ask != null && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Spread:</span>
                    <span className="text-gray-900">
                      ${((marketData.ask || 0) - (marketData.bid || 0)).toFixed(2)} (
                      {(marketData.bid || 0) > 0
                        ? ((((marketData.ask || 0) - (marketData.bid || 0)) / (marketData.bid || 1)) * 100).toFixed(2)
                        : '0.00'}
                      %)
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm pt-2 border-t border-gray-200">
                  <span className="text-gray-600">Market Status:</span>
                  <span
                    className={`font-medium ${
                      marketData.is_market_hours ? 'text-green-600' : 'text-gray-600'
                    }`}
                  >
                    {marketData.is_market_hours ? 'Open ✓' : 'Closed'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Last Update:</span>
                  <span className="text-gray-900">{new Date().toLocaleTimeString()}</span>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">Market data not available</div>
            )}
          </div>

          {/* Anchor & Triggers */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Anchor & Triggers</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Anchor:</span>
                <span className="text-lg font-semibold text-gray-900">
                  ${(anchorPrice || 0).toFixed(2)}
                </span>
              </div>
              {baseline && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Set:</span>
                  <span className="text-gray-900">
                    {baseline.baseline_timestamp 
                      ? (() => {
                          const date = new Date(baseline.baseline_timestamp);
                          return isNaN(date.getTime()) ? 'Invalid date' : date.toLocaleString();
                        })()
                      : 'N/A'}
                  </span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Deviation:</span>
                <span
                  className={`text-lg font-semibold ${
                    anchorDeviation >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {anchorDeviation >= 0 ? '+' : ''}
                  {anchorDeviation.toFixed(2)}%
                </span>
              </div>
              {config && (
                <>
                  <div className="pt-2 border-t border-gray-200">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Buy Trigger:</span>
                      <span className="text-gray-900">
                        ${buyTriggerPrice.toFixed(2)} ({config.trigger_down_pct >= 0 ? '+' : ''}
                        {config.trigger_down_pct}%)
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span className="text-gray-600">Sell Trigger:</span>
                      <span className="text-gray-900">
                        ${sellTriggerPrice.toFixed(2)} ({config.trigger_up_pct >= 0 ? '+' : ''}
                        {config.trigger_up_pct}%)
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Position Return:</span>
                <span
                  className={`text-xl font-bold flex items-center ${
                    positionReturn >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {positionReturn >= 0 ? (
                    <TrendingUp className="h-5 w-5 mr-1" />
                  ) : (
                    <TrendingDown className="h-5 w-5 mr-1" />
                  )}
                  {positionReturn >= 0 ? '+' : ''}
                  {positionReturn.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Stock Return:</span>
                <span
                  className={`text-xl font-bold flex items-center ${
                    stockReturn >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stockReturn >= 0 ? (
                    <TrendingUp className="h-5 w-5 mr-1" />
                  ) : (
                    <TrendingDown className="h-5 w-5 mr-1" />
                  )}
                  {stockReturn >= 0 ? '+' : ''}
                  {stockReturn.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Alpha:</span>
                <span
                  className={`text-xl font-bold ${alpha >= 0 ? 'text-green-600' : 'text-red-600'}`}
                >
                  {alpha >= 0 ? '✓' : '✗'} {alpha >= 0 ? '+' : ''}
                  {alpha.toFixed(2)}%
                </span>
              </div>
              {baseline && (
                <>
                  <div className="pt-4 border-t border-gray-200 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Initial Value:</span>
                      <span className="text-gray-900">
                        $
                        {baseline.baseline_total_value.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Current Value:</span>
                      <span className="text-gray-900">
                        $
                        {totalValue.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                  </div>
                </>
              )}
              <div className="pt-2 border-t border-gray-200">
                <span className="text-sm text-gray-600">
                  Status:{' '}
                  {positionReturn > stockReturn
                    ? 'Outperforming'
                    : positionReturn < stockReturn
                    ? 'Underperforming'
                    : 'In Line'}
                </span>
              </div>
            </div>
          </div>

          {/* Trading Activity */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Trading Activity</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Trades:</span>
                <span className="text-gray-900">{recentTrades.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Commissions:</span>
                <span className="text-gray-900">
                  $
                  {(position.total_commission_paid || 0).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Dividends:</span>
                <span className="text-gray-900">
                  $
                  {(position.total_dividends_received || 0).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              {lastTrade && (
                <div className="flex justify-between pt-2 border-t border-gray-200">
                  <span className="text-gray-600">Last Trade:</span>
                  <span className="text-gray-900">
                        {lastTrade.timestamp 
                          ? (() => {
                              const date = new Date(lastTrade.timestamp);
                              return isNaN(date.getTime()) ? 'Invalid date' : date.toLocaleString();
                            })()
                          : 'N/A'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Strategy Configuration */}
          {config && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Configuration</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Trigger Up:</span>
                  <span className="text-gray-900">
                    {config.trigger_up_pct >= 0 ? '+' : ''}
                    {config.trigger_up_pct}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Trigger Down:</span>
                  <span className="text-gray-900">
                    {config.trigger_down_pct >= 0 ? '+' : ''}
                    {config.trigger_down_pct}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Min Stock %:</span>
                  <span className="text-gray-900">{config.min_stock_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Stock %:</span>
                  <span className="text-gray-900">{config.max_stock_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Trade % of Position:</span>
                  <span className="text-gray-900">{config.max_trade_pct_of_position}%</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-gray-200">
                  <span className="text-gray-600">Commission Rate:</span>
                  <span className="text-gray-900">{config.commission_rate_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="font-medium text-gray-900">{position.status || 'ACTIVE'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Recent Activities - Table Format */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-gray-900">Recent Activities</h2>
                {refreshing && (
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
                    <span>Refreshing...</span>
                  </div>
                )}
              </div>
              {currentPositionId && (
                <PositionActions
                  positionId={currentPositionId}
                  onAfterAction={() => {
                    console.log('Refreshing position data after tick...');
                    loadPositionData(false);
                  }}
                  showRun10Ticks={true}
                />
              )}
            </div>
            {events.length > 0 ? (
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200 border border-gray-300">
                  <thead className="bg-gray-100 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        Market Data
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        Anchor & Delta
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        Action & Reason
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        Result
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {events.slice(0, 20).map((event) => {
                      const eventDate = event.timestamp ? new Date(event.timestamp) : null;
                      const isValidDate = eventDate && !isNaN(eventDate.getTime());
                      const effectivePrice = event.effective_price || event.market_price_raw;
                      const anchorPrice = event.anchor_price;
                      const priceChange =
                        effectivePrice && anchorPrice ? effectivePrice - anchorPrice : null;
                      const priceChangePct =
                        effectivePrice && anchorPrice && anchorPrice > 0
                          ? ((effectivePrice - anchorPrice) / anchorPrice) * 100
                          : null;

                      // Get action - check multiple possible field names
                      const action = event.action || event.action_taken || event.evaluation_type || event.event_type || 'HOLD';
                      const actionReason = event.action_reason || event.evaluation_summary;

                      // Get position changes (result) - check multiple possible field names
                      const qtyBefore = event.position_qty_before;
                      const qtyAfter = event.position_qty_after;
                      const cashBefore = event.position_cash_before;
                      const cashAfter = event.position_cash_after;
                      const totalValueAfter = event.position_total_value_after;

                      // Get OHLC data
                      const openPrice = event.open_price;
                      const highPrice = event.high_price;
                      const lowPrice = event.low_price;
                      const closePrice = event.close_price;

                      return (
                        <tr key={event.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 whitespace-nowrap text-xs">
                            {isValidDate ? (
                              <>
                                <div className="text-gray-900 font-medium">
                                  {eventDate!.toLocaleTimeString()}
                                </div>
                                <div className="text-[10px] text-gray-400 mt-0.5">
                                  {eventDate!.toLocaleDateString()}
                                </div>
                              </>
                            ) : (
                              <div className="text-gray-400 text-[10px]">No timestamp</div>
                            )}
                            {(event.evaluation_type || event.event_type) && (
                              <div className="text-[10px] text-gray-500 mt-0.5 uppercase">
                                {event.evaluation_type || event.event_type}
                              </div>
                            )}
                          </td>
                          <td className="px-3 py-2 text-xs">
                            {effectivePrice != null ? (
                              <div className="space-y-0.5">
                                <div className="font-medium text-gray-900">
                                  ${(effectivePrice || 0).toFixed(2)}
                                </div>
                                {(openPrice != null || highPrice != null || lowPrice != null || closePrice != null) && (
                                  <div className="text-gray-500 text-[10px] space-y-0.5">
                                    {openPrice != null && (
                                      <div>O: ${(openPrice || 0).toFixed(2)}</div>
                                    )}
                                    {highPrice != null && lowPrice != null && (
                                      <div>H: ${(highPrice || 0).toFixed(2)} / L: ${(lowPrice || 0).toFixed(2)}</div>
                                    )}
                                    {closePrice != null && (
                                      <div>C: ${(closePrice || 0).toFixed(2)}</div>
                                    )}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-xs">
                            {anchorPrice ? (
                              <div className="space-y-0.5">
                                <div className="text-gray-600">
                                  Anchor: ${(anchorPrice || 0).toFixed(2)}
                                </div>
                                {priceChange !== null && priceChangePct !== null && (
                                  <div
                                    className={`font-medium ${
                                      priceChange >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}
                                  >
                                    {priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)} (
                                    {priceChange >= 0 ? '+' : ''}
                                    {priceChangePct.toFixed(2)}%)
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-xs">
                            <div className="space-y-0.5">
                              <span
                                className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                                  action === 'BUY' || action?.toUpperCase() === 'BUY'
                                    ? 'bg-green-100 text-green-800'
                                    : action === 'SELL' || action?.toUpperCase() === 'SELL'
                                    ? 'bg-red-100 text-red-800'
                                    : action === 'HOLD' || action?.toUpperCase() === 'HOLD'
                                    ? 'bg-gray-100 text-gray-800'
                                    : 'bg-blue-100 text-blue-800'
                                }`}
                              >
                                {action}
                              </span>
                              {actionReason && (
                                <div className="text-gray-600 text-[10px] mt-1 max-w-[200px] truncate" title={actionReason}>
                                  {actionReason}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2 text-xs">
                            {(qtyBefore != null || qtyAfter != null || cashBefore != null || cashAfter != null || totalValueAfter != null) ? (
                              <div className="space-y-0.5">
                                {qtyBefore != null && qtyAfter != null && (
                                  <div className={`text-gray-600 ${qtyBefore !== qtyAfter ? 'font-medium' : ''}`}>
                                    Qty: {(qtyBefore || 0).toFixed(2)} {qtyBefore !== qtyAfter ? `→ ${(qtyAfter || 0).toFixed(2)}` : ''}
                                  </div>
                                )}
                                {cashBefore != null && cashAfter != null && (
                                  <div className={`text-gray-600 ${cashBefore !== cashAfter ? 'font-medium' : ''}`}>
                                    Cash: ${(cashBefore || 0).toFixed(2)} {cashBefore !== cashAfter ? `→ ${(cashAfter || 0).toFixed(2)}` : ''}
                                  </div>
                                )}
                                {totalValueAfter != null && (
                                  <div className="font-medium text-gray-900">
                                    Total: ${(totalValueAfter || 0).toFixed(2)}
                                  </div>
                                )}
                                {qtyBefore === qtyAfter && cashBefore === cashAfter && qtyBefore != null && (
                                  <div className="text-gray-400 text-[10px]">No change</div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500 mb-2">No cycles yet</p>
                <p className="text-xs text-gray-400 mb-4">Run a cycle to see trading activity</p>
                {currentPositionId && (
                  <PositionActions
                    positionId={currentPositionId}
                    onAfterAction={() => {
                      console.log('Refreshing position data after tick...');
                      loadPositionData(false);
                    }}
                    showRun10Ticks={true}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Actions & Quick Info */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions</h2>
            <div className="space-y-2">
              <button
                onClick={() =>
                  navigate(
                    `/portfolios/${currentPortfolioId}/positions?tab=config&positionId=${currentPositionId}`,
                  )
                }
                className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit Strategy
              </button>
              <button
                onClick={() => navigate(`/portfolios/${currentPortfolioId}/positions?tab=cash`)}
                className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <DollarSign className="h-4 w-4 mr-2" />
                Deposit/Withdraw Cash
              </button>
              <button
                onClick={() => {
                  // TODO: Implement set anchor functionality
                  alert('Set Anchor functionality coming soon');
                }}
                className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <Anchor className="h-4 w-4 mr-2" />
                Set Anchor
              </button>
              <button
                onClick={() =>
                  navigate(`/trade/${currentPortfolioId}/position/${currentPositionId}`)
                }
                className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Activity className="h-4 w-4 mr-2" />
                View Position Cockpit
              </button>
              <button
                onClick={() => {
                  // TODO: Implement export functionality
                  alert('Export functionality coming soon');
                }}
                className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </button>
            </div>
          </div>

          {/* Position Summary Card */}
          <PositionCellCard
            position={position}
            portfolioId={currentPortfolioId!}
            tenantId={tenantId}
            config={config || undefined}
            initialPrice={currentPrice}
            compact={true}
            onViewDetails={() => {
              // Already on detail page
            }}
          />
        </div>
      </div>
    </div>
  );
}






