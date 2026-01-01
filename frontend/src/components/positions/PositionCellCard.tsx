import { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  Settings,
  Play,
  Pause,
  ChevronRight,
  Activity,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { marketApi } from '../../lib/api';
import { useNavigate } from 'react-router-dom';
import { getPositionEvents, TimelineEvent } from '../../api/positions';

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

interface PositionCellCardProps {
  position: {
    id: string;
    asset?: string;
    ticker?: string;
    qty: number;
    cash: number;
    anchor_price: number | null;
    avg_cost?: number | null;
    status?: string;
  };
  portfolioId: string;
  tenantId: string;
  config?: {
    trigger_up_pct?: number;
    trigger_down_pct?: number;
    min_stock_pct?: number;
    max_stock_pct?: number;
  };
  initialPrice?: number;
  compact?: boolean;
  onViewDetails?: () => void;
}

export default function PositionCellCard({
  position,
  portfolioId,
  tenantId,
  config,
  initialPrice,
  compact = false,
  onViewDetails,
}: PositionCellCardProps) {
  const navigate = useNavigate();
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);

  const asset = position.asset || position.ticker || 'UNKNOWN';
  const currentPrice = marketData?.price || initialPrice || position.anchor_price || 0;
  const stockValue = position.qty * currentPrice;
  const totalValue = stockValue + (position.cash || 0);
  const cashPct = totalValue > 0 ? ((position.cash || 0) / totalValue) * 100 : 0;
  const stockPct = totalValue > 0 ? (stockValue / totalValue) * 100 : 0;

  // Calculate performance metrics
  const initialPriceForReturn = position.anchor_price || position.avg_cost || currentPrice;
  const positionReturn =
    initialPriceForReturn > 0
      ? ((currentPrice - initialPriceForReturn) / initialPriceForReturn) * 100
      : 0;
  const stockReturn = positionReturn; // Both measured from same initial point
  const alpha = 0; // Alpha would be calculated from actual trading performance

  const priceChange = marketData?.close
    ? currentPrice - marketData.close
    : initialPriceForReturn > 0
    ? currentPrice - initialPriceForReturn
    : 0;
  const priceChangePct =
    marketData?.close && marketData.close > 0
      ? ((currentPrice - marketData.close) / marketData.close) * 100
      : positionReturn;

  useEffect(() => {
    const loadMarketData = async () => {
      if (!asset || asset === 'UNKNOWN') {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await marketApi.getPrice(asset);
        setMarketData({
          price: data.price,
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          is_market_hours: data.is_market_hours,
        });
      } catch (error) {
        console.warn(`Failed to fetch market data for ${asset}:`, error);
      } finally {
        setLoading(false);
      }
    };

    loadMarketData();
    // Refresh every 30 seconds
    const interval = setInterval(loadMarketData, 30000);
    return () => clearInterval(interval);
  }, [asset]);

  useEffect(() => {
    const loadTimelineEvents = async () => {
      if (!position.id || !portfolioId || !tenantId) {
        return;
      }

      try {
        setLoadingEvents(true);
        // Limit to 10 most recent events for better performance
        const events = await getPositionEvents(tenantId, portfolioId, position.id, 10);
        console.log(`[PositionCellCard] Loaded ${events.length} timeline events:`, events);
        setTimelineEvents(events);
      } catch (error) {
        console.warn(`Failed to fetch timeline events for position ${position.id}:`, error);
      } finally {
        setLoadingEvents(false);
      }
    };

    loadTimelineEvents();
    // Refresh every 60 seconds
    const interval = setInterval(loadTimelineEvents, 60000);
    return () => clearInterval(interval);
  }, [position.id, portfolioId, tenantId]);

  const handleViewDetails = () => {
    if (onViewDetails) {
      onViewDetails();
    } else {
      navigate(`/portfolios/${portfolioId}/positions/${position.id}`);
    }
  };

  if (compact) {
    // Compact grid card view
    return (
      <div
        className="bg-white rounded-lg shadow-md border border-gray-200 p-4 hover:shadow-lg transition-shadow cursor-pointer"
        onClick={handleViewDetails}
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900">{asset}</h3>
          <span
            className={`text-xs px-2 py-1 rounded ${
              position.status === 'PAUSED'
                ? 'bg-gray-100 text-gray-700'
                : 'bg-green-100 text-green-700'
            }`}
          >
            {position.status || 'ACTIVE'}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">${currentPrice.toFixed(2)}</span>
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
              {Math.abs(priceChangePct).toFixed(2)}%
            </span>
          </div>

          <div className="text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Total Value:</span>
              <span className="font-semibold">
                $
                {totalValue.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="flex justify-between mt-1">
              <span>Cash: {cashPct.toFixed(1)}%</span>
              <span>Stock: {stockPct.toFixed(1)}%</span>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-200">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Position Return:</span>
              <span
                className={`font-semibold ${
                  positionReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {positionReturn >= 0 ? '+' : ''}
                {positionReturn.toFixed(2)}%
              </span>
            </div>
            {alpha !== 0 && (
              <div className="flex justify-between text-sm mt-1">
                <span className="text-gray-600">Alpha:</span>
                <span className={`font-semibold ${alpha >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {alpha >= 0 ? '+' : ''}
                  {alpha.toFixed(2)}%
                </span>
              </div>
            )}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleViewDetails();
            }}
            className="w-full mt-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center justify-center"
          >
            View Details
            <ChevronRight className="h-4 w-4 ml-1" />
          </button>
        </div>
      </div>
    );
  }

  // Full detailed cell card layout
  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{asset} Position Cell</h2>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            position.status === 'PAUSED'
              ? 'bg-gray-100 text-gray-700'
              : 'bg-green-100 text-green-700'
          }`}
        >
          {position.status || 'ACTIVE'}
        </span>
      </div>

      <div className="space-y-6">
        {/* Current Market Data */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Current Market Data</h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Price:</span>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-gray-900">${currentPrice.toFixed(2)}</span>
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
            {marketData && (
              <>
                {marketData.open !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Open:</span>
                    <span className="text-gray-900">${marketData.open.toFixed(2)}</span>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {marketData.high !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">High:</span>
                      <span className="text-gray-900">${marketData.high.toFixed(2)}</span>
                    </div>
                  )}
                  {marketData.low !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Low:</span>
                      <span className="text-gray-900">${marketData.low.toFixed(2)}</span>
                    </div>
                  )}
                </div>
                {marketData.close !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Close:</span>
                    <span className="text-gray-900">${marketData.close.toFixed(2)}</span>
                  </div>
                )}
                {marketData.volume !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Volume:</span>
                    <span className="text-gray-900">
                      {(marketData.volume / 1000000).toFixed(1)}M
                    </span>
                  </div>
                )}
                {marketData.bid !== undefined && marketData.ask !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Bid/Ask:</span>
                    <span className="text-gray-900">
                      ${marketData.bid.toFixed(2)} / ${marketData.ask.toFixed(2)}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Market:</span>
                  <span
                    className={`font-medium ${
                      marketData.is_market_hours ? 'text-green-600' : 'text-gray-600'
                    }`}
                  >
                    {marketData.is_market_hours ? 'Open ✓' : 'Closed'}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Value Breakdown */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Value Breakdown</h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Cash:</span>
                <span className="font-semibold text-gray-900">
                  $
                  {(position.cash || 0).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: `${cashPct}%` }} />
              </div>
              <div className="text-xs text-gray-500 text-right">{cashPct.toFixed(1)}%</div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Stock:</span>
                <span className="font-semibold text-gray-900">
                  $
                  {stockValue.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${stockPct}%` }} />
              </div>
              <div className="text-xs text-gray-500 text-right">{stockPct.toFixed(1)}%</div>
            </div>
            <div className="pt-2 border-t border-gray-300">
              <div className="flex justify-between">
                <span className="text-sm font-semibold text-gray-700">Total:</span>
                <span className="text-lg font-bold text-gray-900">
                  $
                  {totalValue.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Performance vs Stock */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Performance vs Stock</h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Position Return:</span>
              <span
                className={`text-lg font-bold flex items-center ${
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
                className={`text-lg font-bold flex items-center ${
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
            {alpha !== 0 && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Alpha:</span>
                <span
                  className={`text-lg font-bold ${alpha >= 0 ? 'text-green-600' : 'text-red-600'}`}
                >
                  {alpha >= 0 ? '✓' : '✗'} {alpha >= 0 ? '+' : ''}
                  {alpha.toFixed(2)}%
                </span>
              </div>
            )}
            <div className="pt-2 border-t border-gray-300">
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

        {/* Strategy */}
        {config && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Strategy: Volatility Trading
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Triggers:</span>
                <span className="text-gray-900">
                  {config.trigger_up_pct !== undefined ? `+${config.trigger_up_pct}%` : 'N/A'} /{' '}
                  {config.trigger_down_pct !== undefined ? `${config.trigger_down_pct}%` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Guardrails:</span>
                <span className="text-gray-900">
                  {config.min_stock_pct !== undefined ? `${config.min_stock_pct}%` : 'N/A'} -{' '}
                  {config.max_stock_pct !== undefined ? `${config.max_stock_pct}%` : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Recent Activity - Table Format */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Activity</h3>
          <div className="bg-gray-50 rounded-lg p-4 border-2 border-blue-500">
            {/* DEBUG: Force visible indicator */}
            <div className="bg-yellow-200 p-2 mb-2 text-xs font-bold">
              DEBUG: Table Mode Active - {timelineEvents.length} events loaded
            </div>
            {loadingEvents ? (
              <div className="text-sm text-gray-500 text-center py-4">Loading events...</div>
            ) : timelineEvents.length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-4">No recent activity</div>
            ) : (
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200 border-2 border-red-500">
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
                    {timelineEvents.map((event) => {
                      const eventDate = new Date(event.timestamp);
                      const effectivePrice = event.effective_price || event.market_price_raw;
                      const anchorPrice = event.anchor_price;
                      const priceChange =
                        effectivePrice && anchorPrice ? effectivePrice - anchorPrice : null;
                      const priceChangePct =
                        effectivePrice && anchorPrice && anchorPrice > 0
                          ? ((effectivePrice - anchorPrice) / anchorPrice) * 100
                          : null;

                      // Get action - check multiple possible field names
                      const action =
                        event.action || event.action_taken || event.evaluation_type || 'HOLD';
                      const actionReason = event.action_reason || event.evaluation_summary;

                      // Get position changes (result) - check multiple possible field names
                      const qtyBefore = event.position_qty_before || event.qty_before;
                      const qtyAfter = event.position_qty_after || event.qty_after;
                      const cashBefore = event.position_cash_before || event.cash_before;
                      const cashAfter = event.position_cash_after || event.cash_after;
                      const totalValueAfter =
                        event.position_total_value_after || event.total_value_after;

                      // Get OHLC data
                      const openPrice = event.open_price;
                      const highPrice = event.high_price;
                      const lowPrice = event.low_price;
                      const closePrice = event.close_price;

                      return (
                        <tr key={event.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 whitespace-nowrap text-xs">
                            <div className="text-gray-900 font-medium">
                              {eventDate.toLocaleTimeString()}
                            </div>
                            <div className="text-[10px] text-gray-400 mt-0.5">
                              {eventDate.toLocaleDateString()}
                            </div>
                            {event.evaluation_type && (
                              <div className="text-[10px] text-gray-500 mt-0.5 uppercase">
                                {event.evaluation_type}
                              </div>
                            )}
                          </td>
                          <td className="px-3 py-2 text-xs">
                            {effectivePrice ? (
                              <div className="space-y-0.5">
                                <div className="font-medium text-gray-900">
                                  ${effectivePrice.toFixed(2)}
                                </div>
                                {(openPrice || highPrice || lowPrice || closePrice) && (
                                  <div className="text-gray-500 text-[10px] space-y-0.5">
                                    {openPrice && <div>O: ${openPrice.toFixed(2)}</div>}
                                    {highPrice && lowPrice && (
                                      <div>
                                        H: ${highPrice.toFixed(2)} / L: ${lowPrice.toFixed(2)}
                                      </div>
                                    )}
                                    {closePrice && <div>C: ${closePrice.toFixed(2)}</div>}
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
                                  Anchor: ${anchorPrice.toFixed(2)}
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
                                <div
                                  className="text-gray-600 text-[10px] mt-1 max-w-[200px] truncate"
                                  title={actionReason}
                                >
                                  {actionReason}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2 text-xs">
                            {qtyBefore !== undefined ||
                            qtyAfter !== undefined ||
                            cashBefore !== undefined ||
                            cashAfter !== undefined ||
                            totalValueAfter !== undefined ? (
                              <div className="space-y-0.5">
                                {qtyBefore !== undefined && qtyAfter !== undefined && (
                                  <div
                                    className={`text-gray-600 ${
                                      qtyBefore !== qtyAfter ? 'font-medium' : ''
                                    }`}
                                  >
                                    Qty: {qtyBefore.toFixed(2)}{' '}
                                    {qtyBefore !== qtyAfter ? `→ ${qtyAfter.toFixed(2)}` : ''}
                                  </div>
                                )}
                                {cashBefore !== undefined && cashAfter !== undefined && (
                                  <div
                                    className={`text-gray-600 ${
                                      cashBefore !== cashAfter ? 'font-medium' : ''
                                    }`}
                                  >
                                    Cash: ${cashBefore.toFixed(2)}{' '}
                                    {cashBefore !== cashAfter ? `→ ${cashAfter.toFixed(2)}` : ''}
                                  </div>
                                )}
                                {totalValueAfter !== undefined && (
                                  <div className="font-medium text-gray-900">
                                    Total: ${totalValueAfter.toFixed(2)}
                                  </div>
                                )}
                                {qtyBefore === qtyAfter &&
                                  cashBefore === cashAfter &&
                                  qtyBefore !== undefined && (
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
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={() => navigate(`/portfolios/${portfolioId}/positions?tab=strategy`)}
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </button>
          <button
            onClick={() => navigate(`/portfolios/${portfolioId}/trading`)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Play className="h-4 w-4 mr-2" />
            Trade
          </button>
          <button
            onClick={handleViewDetails}
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            View Details
            <ChevronRight className="h-4 w-4 ml-2" />
          </button>
        </div>
      </div>
    </div>
  );
}
