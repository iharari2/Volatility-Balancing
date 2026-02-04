import { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
  Scatter,
  Cell,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { Position } from '../../contexts/PortfolioContext';
import type { AnalyticsData, AnalyticsEvent } from '../../services/portfolioScopedApi';

interface AnalyticsChartsProps {
  positions: Position[];
  analyticsData?: AnalyticsData;
}

export default function AnalyticsCharts({ positions, analyticsData }: AnalyticsChartsProps) {
  const isSinglePosition = positions.length === 1;
  const mainLabel = isSinglePosition
    ? `${positions[0].ticker || 'Position'} Value`
    : 'Portfolio Value';

  // Extract events for markers
  const events = analyticsData?.events || [];
  const tradeEvents = events.filter((e: AnalyticsEvent) => e.type === 'TRADE');
  const dividendEvents = events.filter((e: AnalyticsEvent) => e.type === 'DIVIDEND');

  // Create lookup maps for events by date
  const tradesByDate = useMemo(() => {
    const map = new Map<string, AnalyticsEvent[]>();
    tradeEvents.forEach((e: AnalyticsEvent) => {
      const existing = map.get(e.date) || [];
      existing.push(e);
      map.set(e.date, existing);
    });
    return map;
  }, [tradeEvents]);

  const dividendsByDate = useMemo(() => {
    const map = new Map<string, AnalyticsEvent[]>();
    dividendEvents.forEach((e: AnalyticsEvent) => {
      const existing = map.get(e.date) || [];
      existing.push(e);
      map.set(e.date, existing);
    });
    return map;
  }, [dividendEvents]);

  // ANA-2: Portfolio Value with stacked areas (cash + stock) and event markers
  const portfolioValueData = useMemo(() => {
    if (analyticsData?.time_series && analyticsData.time_series.length > 0) {
      return analyticsData.time_series.map((point) => {
        const dateTrades = tradesByDate.get(point.date) || [];
        const dateDividends = dividendsByDate.get(point.date) || [];

        // Find buy/sell trades for this date
        const buyTrade = dateTrades.find((t: AnalyticsEvent) => t.side === 'BUY');
        const sellTrade = dateTrades.find((t: AnalyticsEvent) => t.side === 'SELL');
        const hasDividend = dateDividends.length > 0;

        return {
          date: point.date,
          value: point.value,
          stock: point.stock,
          cash: point.cash,
          // Markers for events
          buyMarker: buyTrade ? point.value : null,
          sellMarker: sellTrade ? point.value : null,
          dividendMarker: hasDividend ? point.value : null,
          // Store event details for tooltip
          tradeQty: buyTrade?.qty || sellTrade?.qty,
          tradeSide: buyTrade ? 'BUY' : sellTrade ? 'SELL' : null,
          dividendAmount: hasDividend ? dateDividends.reduce((sum: number, d: AnalyticsEvent) => sum + (d.net_amount || 0), 0) : null,
        };
      });
    }
    return [];
  }, [analyticsData, tradesByDate, dividendsByDate]);

  // ANA-3: Allocation data with guardrail bands
  const guardrails = analyticsData?.guardrails;

  const allocationData = useMemo(() => {
    if (analyticsData?.time_series && analyticsData.time_series.length > 0) {
      return analyticsData.time_series.map((point) => ({
        date: point.date,
        stock: point.stock_pct,
        cash: point.cash_pct,
      }));
    }
    return [];
  }, [analyticsData]);

  // ANA-4: Normalized performance comparison with event markers
  const performance = analyticsData?.performance;

  const buyHoldData = useMemo(() => {
    if (!analyticsData?.time_series?.length || portfolioValueData.length === 0) {
      return [];
    }

    const timeSeries = analyticsData.time_series;
    const initialPoint = timeSeries[0];
    const initialStockValue = initialPoint.stock || 0;
    const initialValue = initialPoint.value || 0;

    if (initialValue === 0 || initialStockValue === 0) return [];

    // Calculate normalized returns (percentage change from start)
    return portfolioValueData.map((point: { date: string; value: number; buyMarker: number | null; sellMarker: number | null; dividendMarker: number | null }, i: number) => {
      const currentPoint = timeSeries[i];
      if (!currentPoint) return { date: point.date, portfolioReturn: 0, stockReturn: 0 };

      // Portfolio return: percentage change from initial total value
      const portfolioReturn = ((point.value - initialValue) / initialValue) * 100;

      // Stock/Buy-hold return: percentage change in stock value (represents holding stock only)
      const stockReturn = ((currentPoint.stock - initialStockValue) / initialStockValue) * 100;

      // Add markers for trades/dividends on the portfolio return line
      const hasEvent = point.buyMarker !== null || point.sellMarker !== null || point.dividendMarker !== null;

      return {
        date: point.date,
        portfolioReturn: Math.round(portfolioReturn * 100) / 100,
        stockReturn: Math.round(stockReturn * 100) / 100,
        // Marker on portfolio return value when there's an event
        buyMarker: point.buyMarker !== null ? Math.round(portfolioReturn * 100) / 100 : null,
        sellMarker: point.sellMarker !== null ? Math.round(portfolioReturn * 100) / 100 : null,
        dividendMarker: point.dividendMarker !== null ? Math.round(portfolioReturn * 100) / 100 : null,
      };
    });
  }, [portfolioValueData, analyticsData]);

  // ANA-5: 30-day rolling volatility (annualized)
  const rollingVolatilityData = useMemo(() => {
    if (!analyticsData?.time_series?.length || analyticsData.time_series.length < 31) {
      return [];
    }

    const timeSeries = analyticsData.time_series;
    const result: Array<{ date: string; volatility: number }> = [];

    // Calculate daily returns first
    const dailyReturns: number[] = [];
    for (let i = 1; i < timeSeries.length; i++) {
      const prevValue = timeSeries[i - 1].value;
      const currValue = timeSeries[i].value;
      if (prevValue > 0) {
        dailyReturns.push((currValue - prevValue) / prevValue);
      } else {
        dailyReturns.push(0);
      }
    }

    // For each day after day 30, calculate rolling std dev
    const WINDOW = 30;
    for (let i = WINDOW; i < timeSeries.length; i++) {
      // Get the last 30 daily returns (from i-30 to i-1 in dailyReturns, which is offset by 1)
      const windowReturns = dailyReturns.slice(i - WINDOW, i);

      if (windowReturns.length === WINDOW) {
        // Calculate mean
        const mean = windowReturns.reduce((a, b) => a + b, 0) / WINDOW;

        // Calculate variance
        const variance = windowReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (WINDOW - 1);

        // Calculate standard deviation and annualize
        const stdDev = Math.sqrt(variance);
        const annualizedVol = stdDev * Math.sqrt(252) * 100; // Convert to percentage

        result.push({
          date: timeSeries[i].date,
          volatility: Math.round(annualizedVol * 100) / 100,
        });
      }
    }

    return result;
  }, [analyticsData]);

  // Check if we have any data to display
  const hasData = portfolioValueData.length > 0;

  if (!hasData) {
    return (
      <div className="card p-8 text-center">
        <BarChart3 className="h-12 w-12 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analytics Data Available</h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto mb-4">
          Analytics data is generated from trading activity. Run simulations or execute trades to see performance metrics and charts.
        </p>
        <div className="text-xs text-gray-400 space-y-1">
          <p>• Run a simulation to see projected performance</p>
          <p>• Execute trades to build trading history</p>
          <p>• Enable continuous trading for automated data collection</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* ANA-2: Portfolio Value Over Time - Stacked Areas + Event Markers */}
      <div className="card">
        <h3 className="text-sm font-bold text-gray-900 mb-6 uppercase tracking-wider">
          {mainLabel} Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={portfolioValueData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number, name: string) => {
                if (name === 'buyMarker') return [`$${value?.toLocaleString()}`, 'BUY'];
                if (name === 'sellMarker') return [`$${value?.toLocaleString()}`, 'SELL'];
                if (name === 'dividendMarker') return [`$${value?.toLocaleString()}`, 'Dividend'];
                if (name === 'Cash') return [`$${value?.toLocaleString()}`, 'Cash'];
                if (name === 'Stock') return [`$${value?.toLocaleString()}`, 'Stock'];
                if (name === 'Total') return [`$${value?.toLocaleString()}`, 'Total'];
                return [`$${value?.toLocaleString()}`, name];
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            {/* Stacked areas: cash (bottom) + stock (top) */}
            <Area
              type="monotone"
              dataKey="cash"
              stackId="1"
              stroke="#2563eb"
              fill="#2563eb"
              fillOpacity={0.4}
              name="Cash"
            />
            <Area
              type="monotone"
              dataKey="stock"
              stackId="1"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.6}
              name="Stock"
            />
            {/* Total value line overlay */}
            <Line
              type="monotone"
              dataKey="value"
              stroke="#1f2937"
              strokeWidth={2}
              dot={false}
              name="Total"
            />
            {/* Buy markers (green triangles) */}
            <Scatter dataKey="buyMarker" fill="#22c55e" name="buyMarker">
              {portfolioValueData.map((entry, index) => (
                <Cell key={`buy-${index}`} fill={entry.buyMarker ? '#22c55e' : 'transparent'} />
              ))}
            </Scatter>
            {/* Sell markers (red triangles) */}
            <Scatter dataKey="sellMarker" fill="#ef4444" name="sellMarker">
              {portfolioValueData.map((entry, index) => (
                <Cell key={`sell-${index}`} fill={entry.sellMarker ? '#ef4444' : 'transparent'} />
              ))}
            </Scatter>
            {/* Dividend markers (purple diamonds) */}
            <Scatter dataKey="dividendMarker" fill="#8b5cf6" shape="diamond" name="dividendMarker">
              {portfolioValueData.map((entry, index) => (
                <Cell key={`div-${index}`} fill={entry.dividendMarker ? '#8b5cf6' : 'transparent'} />
              ))}
            </Scatter>
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ANA-3: Stock Allocation Over Time with Guardrail Bands */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
            {isSinglePosition ? 'Asset Allocation' : 'Portfolio Allocation'} Trend
          </h3>
          {guardrails && (
            <div className="text-xs text-gray-500">
              Target: {guardrails.min_stock_pct.toFixed(0)}% - {guardrails.max_stock_pct.toFixed(0)}%
            </div>
          )}
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={allocationData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            {/* Guardrail bands - render after grid, before data */}
            {guardrails && (
              <ReferenceArea
                y1={0}
                y2={guardrails.min_stock_pct}
                fill="#fee2e2"
                fillOpacity={0.5}
                ifOverflow="visible"
              />
            )}
            {guardrails && (
              <ReferenceArea
                y1={guardrails.min_stock_pct}
                y2={guardrails.max_stock_pct}
                fill="#dcfce7"
                fillOpacity={0.4}
                ifOverflow="visible"
              />
            )}
            {guardrails && (
              <ReferenceArea
                y1={guardrails.max_stock_pct}
                y2={100}
                fill="#fee2e2"
                fillOpacity={0.5}
                ifOverflow="visible"
              />
            )}
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
              domain={[0, 100]}
              tickCount={6}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number) => [`${value?.toFixed(1)}%`, '']}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            {/* Stock allocation line */}
            <Area
              type="monotone"
              dataKey="stock"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.6}
              name="Stock %"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ANA-4: Benchmark Comparison with Alpha Metrics and Event Markers */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
            {isSinglePosition ? 'Stock' : 'Benchmark'} Comparison
          </h3>
          {performance && (
            <div className="flex items-center gap-4 text-xs flex-wrap">
              <span className={performance.alpha >= 0 ? 'text-green-600' : 'text-red-600'}>
                Alpha: {performance.alpha >= 0 ? '+' : ''}{performance.alpha.toFixed(2)}%
              </span>
              {performance.spy_alpha !== undefined && (
                <span className={performance.spy_alpha >= 0 ? 'text-green-600' : 'text-red-600'}>
                  vs S&P: {performance.spy_alpha >= 0 ? '+' : ''}{performance.spy_alpha.toFixed(2)}%
                </span>
              )}
              <span className="text-gray-500">
                Portfolio: {performance.portfolio_return_pct >= 0 ? '+' : ''}{performance.portfolio_return_pct.toFixed(1)}%
              </span>
              <span className="text-gray-500">
                Stock: {performance.benchmark_return_pct >= 0 ? '+' : ''}{performance.benchmark_return_pct.toFixed(1)}%
              </span>
              {performance.spy_return_pct !== undefined && (
                <span className="text-gray-400">
                  S&P 500: {performance.spy_return_pct >= 0 ? '+' : ''}{performance.spy_return_pct.toFixed(1)}%
                </span>
              )}
            </div>
          )}
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={buyHoldData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number, name: string) => {
                if (name === 'buyMarker') return [`${value?.toFixed(2)}%`, 'BUY'];
                if (name === 'sellMarker') return [`${value?.toFixed(2)}%`, 'SELL'];
                if (name === 'dividendMarker') return [`${value?.toFixed(2)}%`, 'Dividend'];
                if (name === 'S&P 500') return [`${value?.toFixed(2)}%`, 'S&P 500'];
                return [`${value?.toFixed(2)}%`, ''];
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            {/* S&P 500 reference line (if available) */}
            {performance?.spy_return_pct !== undefined && (
              <ReferenceLine
                y={performance.spy_return_pct}
                stroke="#6b7280"
                strokeDasharray="3 3"
                strokeWidth={2}
                label={{
                  value: `S&P 500: ${performance.spy_return_pct >= 0 ? '+' : ''}${performance.spy_return_pct.toFixed(1)}%`,
                  position: 'right',
                  fill: '#6b7280',
                  fontSize: 10,
                }}
              />
            )}
            <Line
              type="monotone"
              dataKey="portfolioReturn"
              stroke="#2563eb"
              strokeWidth={3}
              dot={false}
              name={isSinglePosition ? 'Managed Strategy' : 'Portfolio'}
            />
            <Line
              type="monotone"
              dataKey="stockReturn"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Stock Only (Buy & Hold)"
            />
            {/* Event markers on portfolio return line */}
            <Scatter dataKey="buyMarker" fill="#22c55e" name="buyMarker">
              {buyHoldData.map((entry, index) => (
                <Cell key={`buy-${index}`} fill={entry.buyMarker !== null ? '#22c55e' : 'transparent'} />
              ))}
            </Scatter>
            <Scatter dataKey="sellMarker" fill="#ef4444" name="sellMarker">
              {buyHoldData.map((entry, index) => (
                <Cell key={`sell-${index}`} fill={entry.sellMarker !== null ? '#ef4444' : 'transparent'} />
              ))}
            </Scatter>
            <Scatter dataKey="dividendMarker" fill="#8b5cf6" shape="diamond" name="dividendMarker">
              {buyHoldData.map((entry, index) => (
                <Cell key={`div-${index}`} fill={entry.dividendMarker !== null ? '#8b5cf6' : 'transparent'} />
              ))}
            </Scatter>
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ANA-5: 30-Day Rolling Volatility */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
            30-Day Rolling Volatility
          </h3>
          <span className="text-xs text-gray-500">Annualized</span>
        </div>
        {rollingVolatilityData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={rollingVolatilityData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: '8px',
                  border: 'none',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Volatility']}
              />
              <Legend verticalAlign="top" align="right" height={36} />
              <Line
                type="monotone"
                dataKey="volatility"
                stroke="#8b5cf6"
                strokeWidth={3}
                dot={false}
                name="30-Day Rolling Volatility"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center text-gray-400 text-sm">
            Need at least 31 days of data to calculate rolling volatility
          </div>
        )}
      </div>
    </div>
  );
}
