import { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  PieChart,
  Pie,
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
  Brush,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { Position } from '../../contexts/PortfolioContext';
import type { AnalyticsData, AnalyticsEvent } from '../../services/portfolioScopedApi';

interface AnalyticsChartsProps {
  positions: Position[];
  analyticsData?: AnalyticsData;
  activeBenchmarks?: string[];
  customTicker?: string;
}

export default function AnalyticsCharts({
  positions,
  analyticsData,
  activeBenchmarks = ['buy_hold', 'spy'],
  customTicker,
}: AnalyticsChartsProps) {
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

        const buyTrade = dateTrades.find((t: AnalyticsEvent) => t.side === 'BUY');
        const sellTrade = dateTrades.find((t: AnalyticsEvent) => t.side === 'SELL');
        const hasDividend = dateDividends.length > 0;

        return {
          date: point.date,
          value: point.value,
          stock: point.stock,
          cash: point.cash,
          buyMarker: buyTrade ? point.value : null,
          sellMarker: sellTrade ? point.value : null,
          dividendMarker: hasDividend ? point.value : null,
          tradeQty: buyTrade?.qty || sellTrade?.qty,
          tradeSide: buyTrade ? 'BUY' : sellTrade ? 'SELL' : null,
          dividendAmount: hasDividend
            ? dateDividends.reduce(
                (sum: number, d: AnalyticsEvent) => sum + (d.net_amount || 0),
                0,
              )
            : null,
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

  // ANA-4: Normalised performance comparison with benchmarks
  const performance = analyticsData?.performance;

  // Build date->normalised-value maps for benchmark series
  const buyHoldByDate = useMemo(() => {
    const data = analyticsData?.benchmarks?.buy_hold;
    if (!data?.series) return new Map<string, number>();
    const map = new Map<string, number>();
    data.series.forEach((p) => map.set(p.date, p.value));
    return map;
  }, [analyticsData]);

  const customBenchmarkByDate = useMemo(() => {
    const customData = analyticsData?.benchmarks?.custom;
    if (!customData?.series) return new Map<string, number>();
    const map = new Map<string, number>();
    customData.series.forEach((p) => map.set(p.date, p.value));
    return map;
  }, [analyticsData]);

  const buyHoldData = useMemo(() => {
    if (!analyticsData?.time_series?.length || portfolioValueData.length === 0) {
      return [];
    }

    const timeSeries = analyticsData.time_series;
    const initialPoint = timeSeries[0];
    const initialStockValue = initialPoint.stock || 0;
    const initialValue = initialPoint.value || 0;

    if (initialValue === 0) return [];

    // Use yfinance-sourced buy_hold series when available; fall back to snapshot-derived
    const useYfinanceBuyHold = buyHoldByDate.size > 0;

    return portfolioValueData.map(
      (
        point: {
          date: string;
          value: number;
          buyMarker: number | null;
          sellMarker: number | null;
          dividendMarker: number | null;
        },
        i: number,
      ) => {
        const currentPoint = timeSeries[i];
        if (!currentPoint) return { date: point.date, portfolioReturn: 0, stockReturn: 0 };

        const portfolioReturn = ((point.value - initialValue) / initialValue) * 100;

        // Buy & Hold: prefer yfinance series (value is normalised to 100 at start)
        let stockReturn: number;
        if (useYfinanceBuyHold) {
          const bhValue = buyHoldByDate.get(point.date);
          stockReturn = bhValue !== undefined ? bhValue - 100 : 0;
        } else {
          stockReturn = initialStockValue > 0
            ? ((currentPoint.stock - initialStockValue) / initialStockValue) * 100
            : 0;
        }

        // Custom benchmark – normalised to 100 at start, converted to % change
        const customBmValue = customBenchmarkByDate.get(point.date);
        const customReturn =
          customBmValue !== undefined ? customBmValue - 100 : null;

        return {
          date: point.date,
          portfolioReturn: Math.round(portfolioReturn * 100) / 100,
          stockReturn: Math.round(stockReturn * 100) / 100,
          customReturn: customReturn !== null ? Math.round(customReturn * 100) / 100 : null,
          buyMarker:
            point.buyMarker !== null ? Math.round(portfolioReturn * 100) / 100 : null,
          sellMarker:
            point.sellMarker !== null ? Math.round(portfolioReturn * 100) / 100 : null,
          dividendMarker:
            point.dividendMarker !== null ? Math.round(portfolioReturn * 100) / 100 : null,
        };
      },
    );
  }, [portfolioValueData, analyticsData, customBenchmarkByDate]);

  // ANA-5: 30-day rolling volatility (annualized)
  const rollingVolatilityData = useMemo(() => {
    if (!analyticsData?.time_series?.length || analyticsData.time_series.length < 31) {
      return [];
    }

    const timeSeries = analyticsData.time_series;
    const result: Array<{ date: string; volatility: number }> = [];

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

    const WINDOW = 30;
    for (let i = WINDOW; i < timeSeries.length; i++) {
      const windowReturns = dailyReturns.slice(i - WINDOW, i);

      if (windowReturns.length === WINDOW) {
        const mean = windowReturns.reduce((a, b) => a + b, 0) / WINDOW;
        const variance =
          windowReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (WINDOW - 1);
        const stdDev = Math.sqrt(variance);
        const annualizedVol = stdDev * Math.sqrt(252) * 100;

        result.push({
          date: timeSeries[i].date,
          volatility: Math.round(annualizedVol * 100) / 100,
        });
      }
    }

    return result;
  }, [analyticsData]);

  // Drawdown curve
  const drawdownData = useMemo(() => {
    if (!analyticsData?.time_series?.length) return [];
    const ts = analyticsData.time_series;
    let peak = ts[0].value;
    return ts.map((point) => {
      if (point.value > peak) peak = point.value;
      const dd = peak > 0 ? ((point.value - peak) / peak) * 100 : 0;
      return { date: point.date, drawdown: Math.round(dd * 100) / 100 };
    });
  }, [analyticsData]);

  // 30-day rolling Sharpe
  const rollingSharpData = useMemo(() => {
    if (!analyticsData?.time_series?.length || analyticsData.time_series.length < 31) return [];
    const ts = analyticsData.time_series;
    const WINDOW = 30;
    const dailyReturns: number[] = [];
    for (let i = 1; i < ts.length; i++) {
      const prev = ts[i - 1].value;
      const curr = ts[i].value;
      dailyReturns.push(prev > 0 ? (curr - prev) / prev : 0);
    }
    const result: Array<{ date: string; sharpe: number }> = [];
    for (let i = WINDOW; i < ts.length; i++) {
      const window = dailyReturns.slice(i - WINDOW, i);
      const mean = window.reduce((a, b) => a + b, 0) / WINDOW;
      const variance = window.reduce((s, r) => s + (r - mean) ** 2, 0) / (WINDOW - 1);
      const std = Math.sqrt(variance);
      const annReturn = mean * 252;
      const annVol = std * Math.sqrt(252);
      result.push({ date: ts[i].date, sharpe: annVol > 0 ? Math.round((annReturn / annVol) * 100) / 100 : 0 });
    }
    return result;
  }, [analyticsData]);

  // P&L attribution waterfall (invisible base + colored delta stacked bars)
  const waterfallData = useMemo(() => {
    const attr = analyticsData?.pnl_attribution;
    if (!attr || !attr.start_value) return [];
    const { start_value, trading_pnl, dividend_income, commission_cost, end_value } = attr;
    let running = 0;
    const fmt = (v: number) => `$${Math.abs(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
    const points = [
      { name: 'Start', base: 0, amount: start_value, fill: '#3b82f6', label: fmt(start_value) },
    ];
    running = start_value;
    const tradingBase = trading_pnl >= 0 ? running : running + trading_pnl;
    points.push({ name: 'Trading P&L', base: tradingBase, amount: Math.abs(trading_pnl), fill: trading_pnl >= 0 ? '#10b981' : '#ef4444', label: `${trading_pnl >= 0 ? '+' : '-'}${fmt(trading_pnl)}` });
    running += trading_pnl;
    points.push({ name: 'Dividends', base: running, amount: dividend_income, fill: '#10b981', label: `+${fmt(dividend_income)}` });
    running += dividend_income;
    points.push({ name: 'Fees', base: running - commission_cost, amount: commission_cost, fill: '#ef4444', label: `-${fmt(commission_cost)}` });
    running -= commission_cost;
    points.push({ name: 'End', base: 0, amount: end_value, fill: '#1f2937', label: fmt(end_value) });
    return points;
  }, [analyticsData]);

  // Trade efficiency data (trades with anchor price)
  const tradeEfficiencyRows = useMemo(() => {
    return events
      .filter((e: AnalyticsEvent) => e.type === 'TRADE' && e.anchor_price && e.price)
      .map((e: AnalyticsEvent) => {
        const spread = ((e.price! - e.anchor_price!) / e.anchor_price!) * 100;
        const intendedDir = e.side === 'BUY' ? spread < 0 : spread > 0;
        return { ...e, spread: Math.round(spread * 100) / 100, intendedDir };
      })
      .sort((a, b) => b.date.localeCompare(a.date));
  }, [events]);

  const hasData = portfolioValueData.length > 0;

  // Determine whether to show chart brush (only useful with > 20 data points)
  const showBrush = portfolioValueData.length > 20;

  if (!hasData) {
    return (
      <div className="card p-8 text-center">
        <BarChart3 className="h-12 w-12 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analytics Data Available</h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto mb-4">
          Analytics data is generated from trading activity. Run simulations or execute trades to
          see performance metrics and charts.
        </p>
        <div className="text-xs text-gray-400 space-y-1">
          <p>• Run a simulation to see projected performance</p>
          <p>• Execute trades to build trading history</p>
          <p>• Enable continuous trading for automated data collection</p>
        </div>
      </div>
    );
  }

  const showBuyHold = activeBenchmarks.includes('buy_hold');
  const showSpy = activeBenchmarks.includes('spy');
  const showCustom = activeBenchmarks.includes('custom') && !!customTicker;

  return (
    <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* ANA-2: Portfolio Value Over Time - Stacked Areas + Event Markers + Brush */}
      <div className="card lg:col-span-2">
        <h3 className="text-sm font-bold text-gray-900 mb-6 uppercase tracking-wider">
          {mainLabel} Over Time
        </h3>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={portfolioValueData} syncId="analytics">
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
            {/* Stacked areas */}
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
            {/* Buy markers */}
            <Scatter dataKey="buyMarker" fill="#22c55e" name="buyMarker">
              {portfolioValueData.map((entry, index) => (
                <Cell
                  key={`buy-${index}`}
                  fill={entry.buyMarker ? '#22c55e' : 'transparent'}
                />
              ))}
            </Scatter>
            {/* Sell markers */}
            <Scatter dataKey="sellMarker" fill="#ef4444" name="sellMarker">
              {portfolioValueData.map((entry, index) => (
                <Cell
                  key={`sell-${index}`}
                  fill={entry.sellMarker ? '#ef4444' : 'transparent'}
                />
              ))}
            </Scatter>
            {/* Dividend markers */}
            <Scatter dataKey="dividendMarker" fill="#8b5cf6" shape="diamond" name="dividendMarker">
              {portfolioValueData.map((entry, index) => (
                <Cell
                  key={`div-${index}`}
                  fill={entry.dividendMarker ? '#8b5cf6' : 'transparent'}
                />
              ))}
            </Scatter>
            {/* Brush — syncs with other charts via syncId="analytics" */}
            {showBrush && (
              <Brush
                dataKey="date"
                height={24}
                stroke="#d1d5db"
                fill="#f9fafb"
                travellerWidth={8}
              />
            )}
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
              Target: {guardrails.min_stock_pct.toFixed(0)}% –{' '}
              {guardrails.max_stock_pct.toFixed(0)}%
            </div>
          )}
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={allocationData} syncId="analytics">
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
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
            <div className="flex items-center gap-3 text-xs flex-wrap">
              <span className={performance.alpha >= 0 ? 'text-green-600' : 'text-red-600'}>
                Alpha: {performance.alpha >= 0 ? '+' : ''}
                {performance.alpha.toFixed(2)}%
              </span>
              {performance.spy_alpha !== undefined && (
                <span
                  className={performance.spy_alpha >= 0 ? 'text-green-600' : 'text-red-600'}
                >
                  vs S&P: {performance.spy_alpha >= 0 ? '+' : ''}
                  {performance.spy_alpha.toFixed(2)}%
                </span>
              )}
              <span className="text-gray-500">
                Portfolio: {performance.portfolio_return_pct >= 0 ? '+' : ''}
                {performance.portfolio_return_pct.toFixed(1)}%
              </span>
              {showBuyHold && (
                <span className="text-gray-500">
                  Buy&Hold: {performance.benchmark_return_pct >= 0 ? '+' : ''}
                  {performance.benchmark_return_pct.toFixed(1)}%
                </span>
              )}
              {showSpy && performance.spy_return_pct !== undefined && (
                <span className="text-gray-400">
                  S&P 500: {performance.spy_return_pct >= 0 ? '+' : ''}
                  {performance.spy_return_pct.toFixed(1)}%
                </span>
              )}
              {showCustom && analyticsData?.benchmarks?.custom && (
                <span className="text-purple-500">
                  {customTicker}: {analyticsData.benchmarks.custom.return_pct >= 0 ? '+' : ''}
                  {analyticsData.benchmarks.custom.return_pct.toFixed(1)}%
                </span>
              )}
            </div>
          )}
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={buyHoldData} syncId="analytics">
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
                return [`${value?.toFixed(2)}%`, name];
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            {/* S&P 500 horizontal reference line (scalar return) */}
            {showSpy && performance?.spy_return_pct !== undefined && (
              <ReferenceLine
                y={performance.spy_return_pct}
                stroke="#6b7280"
                strokeDasharray="3 3"
                strokeWidth={1.5}
                label={{
                  value: `S&P 500: ${performance.spy_return_pct >= 0 ? '+' : ''}${performance.spy_return_pct.toFixed(1)}%`,
                  position: 'right',
                  fill: '#6b7280',
                  fontSize: 9,
                }}
              />
            )}
            {/* Portfolio managed line */}
            <Line
              type="monotone"
              dataKey="portfolioReturn"
              stroke="#2563eb"
              strokeWidth={3}
              dot={false}
              name={isSinglePosition ? 'Managed Strategy' : 'Portfolio'}
            />
            {/* Buy & Hold line */}
            {showBuyHold && (
              <Line
                type="monotone"
                dataKey="stockReturn"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="Buy & Hold"
              />
            )}
            {/* Custom ticker time-series line */}
            {showCustom && (
              <Line
                type="monotone"
                dataKey="customReturn"
                stroke="#8b5cf6"
                strokeWidth={2}
                strokeDasharray="4 2"
                dot={false}
                name={customTicker || 'Custom'}
                connectNulls
              />
            )}
            {/* Event markers on portfolio return line */}
            <Scatter dataKey="buyMarker" fill="#22c55e" name="buyMarker">
              {buyHoldData.map((entry, index) => (
                <Cell
                  key={`buy-${index}`}
                  fill={entry.buyMarker !== null ? '#22c55e' : 'transparent'}
                />
              ))}
            </Scatter>
            <Scatter dataKey="sellMarker" fill="#ef4444" name="sellMarker">
              {buyHoldData.map((entry, index) => (
                <Cell
                  key={`sell-${index}`}
                  fill={entry.sellMarker !== null ? '#ef4444' : 'transparent'}
                />
              ))}
            </Scatter>
            <Scatter dataKey="dividendMarker" fill="#8b5cf6" shape="diamond" name="dividendMarker">
              {buyHoldData.map((entry, index) => (
                <Cell
                  key={`div-${index}`}
                  fill={entry.dividendMarker !== null ? '#8b5cf6' : 'transparent'}
                />
              ))}
            </Scatter>
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ANA-5: 30-Day Rolling Volatility */}
      <div className="card lg:col-span-2">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
            30-Day Rolling Volatility
          </h3>
          <span className="text-xs text-gray-500">Annualized</span>
        </div>
        {rollingVolatilityData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={rollingVolatilityData} syncId="analytics">
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
          <div className="h-[250px] flex items-center justify-center text-gray-400 text-sm">
            Need at least 31 days of data to calculate rolling volatility
          </div>
        )}
      </div>
    </div>

      {/* ── Drawdown Curve + Rolling Sharpe ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Drawdown Curve */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Drawdown Curve</h3>
            {drawdownData.length > 0 && (
              <div className="flex gap-3 text-xs">
                <span className="text-red-600 font-semibold">
                  Max: {Math.min(...drawdownData.map((d) => d.drawdown)).toFixed(1)}%
                </span>
                <span className="text-gray-400">
                  {drawdownData.filter((d) => d.drawdown < -1).length}d underwater
                </span>
              </div>
            )}
          </div>
          {drawdownData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={drawdownData} syncId="analytics">
                <defs>
                  <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine y={0} stroke="#e5e7eb" strokeWidth={1} />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  formatter={(v: number) => [`${v.toFixed(2)}%`, 'Drawdown']}
                />
                <Area type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={2} fill="url(#ddGrad)" name="Drawdown" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center text-gray-400 text-sm">
              Need at least 2 data points
            </div>
          )}
          <p className="text-[10px] text-gray-400 mt-2">How far below its peak the portfolio sat at each point in time.</p>
        </div>

        {/* Rolling Sharpe */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">30-Day Rolling Sharpe</h3>
            {rollingSharpData.length > 0 && (
              <span className="text-xs font-semibold text-gray-900">
                Current: {rollingSharpData[rollingSharpData.length - 1]?.sharpe.toFixed(2)}
              </span>
            )}
          </div>
          {rollingSharpData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <ComposedChart data={rollingSharpData} syncId="analytics">
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                <ReferenceLine y={0} stroke="#e5e7eb" strokeWidth={1} />
                <ReferenceLine y={1} stroke="#10b981" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'Sharpe 1.0', position: 'right', fill: '#10b981', fontSize: 9 }} />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  formatter={(v: number) => [v.toFixed(2), 'Rolling Sharpe']}
                />
                <Line type="monotone" dataKey="sharpe" stroke="#f59e0b" strokeWidth={2.5} dot={false} name="Rolling Sharpe" />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center text-gray-400 text-sm">
              Need at least 31 days of data
            </div>
          )}
          <p className="text-[10px] text-gray-400 mt-2">Annualized return ÷ annualized volatility over trailing 30 days. Green dashed = Sharpe 1.0 target.</p>
        </div>
      </div>

      {/* ── Guardrail Zone Analysis + P&L Attribution ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Guardrail Zone Analysis */}
        {(() => {
          const zoneTime = analyticsData?.kpis?.zone_time;
          const hasZone = !!zoneTime && analyticsData?.time_series?.length > 0;
          return (
            <div className="card">
              <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Guardrail Zone Analysis</h3>
              {hasZone ? (
                <>
                  <div className="flex items-center gap-6 mb-5">
                    <PieChart width={110} height={110}>
                      <Pie
                        data={[
                          { name: 'In Zone', value: zoneTime.in_pct, fill: '#10b981' },
                          { name: 'Over', value: zoneTime.over_pct, fill: '#f59e0b' },
                          { name: 'Under', value: zoneTime.under_pct, fill: '#ef4444' },
                        ]}
                        cx={55} cy={55}
                        innerRadius={30} outerRadius={50}
                        dataKey="value"
                        startAngle={90} endAngle={-270}
                      >
                        <Cell fill="#10b981" />
                        <Cell fill="#f59e0b" />
                        <Cell fill="#ef4444" />
                      </Pie>
                    </PieChart>
                    <div className="space-y-2 text-xs flex-1">
                      {[
                        { label: 'In target band', pct: zoneTime.in_pct, days: zoneTime.in_days, color: 'bg-emerald-500', textColor: 'text-emerald-600' },
                        { label: 'Over-exposed', pct: zoneTime.over_pct, days: zoneTime.over_days, color: 'bg-amber-400', textColor: 'text-amber-600' },
                        { label: 'Under-exposed', pct: zoneTime.under_pct, days: zoneTime.under_days, color: 'bg-red-400', textColor: 'text-red-600' },
                      ].map((row) => (
                        <div key={row.label} className="flex items-center gap-2">
                          <span className={`w-2.5 h-2.5 rounded-sm flex-shrink-0 ${row.color}`} />
                          <span className="text-gray-600 flex-1">{row.label}</span>
                          <span className={`font-bold ${row.textColor}`}>{row.pct.toFixed(0)}%</span>
                          <span className="text-gray-400 w-8 text-right">{row.days}d</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 mb-1.5">Daily zone timeline</p>
                    <div className="flex flex-wrap gap-0.5">
                      {analyticsData!.time_series.map((point, i) => (
                        <div
                          key={i}
                          title={`${point.date}: ${point.zone}`}
                          className={`w-3.5 h-3.5 rounded-sm flex-shrink-0 ${
                            point.zone === 'in' ? 'bg-emerald-500' :
                            point.zone === 'over' ? 'bg-amber-400' :
                            point.zone === 'under' ? 'bg-red-400' : 'bg-gray-200'
                          } opacity-80`}
                        />
                      ))}
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1.5">Each square = 1 period. Hover for date and zone.</p>
                  </div>
                </>
              ) : (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
                  Guardrail config required to compute zone analysis
                </div>
              )}
            </div>
          );
        })()}

        {/* P&L Attribution Waterfall */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">P&L Attribution</h3>
            <span className="text-xs text-gray-400">Where did the return come from?</span>
          </div>
          {waterfallData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={waterfallData} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(_: number, __: string, props: any) => [props.payload.label, props.payload.name]}
                  />
                  {/* Invisible base to position bar at correct height */}
                  <Bar dataKey="base" stackId="wf" fill="transparent" />
                  {/* Colored delta bar */}
                  <Bar dataKey="amount" stackId="wf" radius={[3, 3, 0, 0]}>
                    {waterfallData.map((entry, index) => (
                      <Cell key={index} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-2 text-[10px] flex-wrap">
                {waterfallData.map((d) => (
                  <div key={d.name} className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm inline-block" style={{ background: d.fill }} />
                    <span className="text-gray-500">{d.name}:</span>
                    <span className="font-semibold text-gray-700">{d.label}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-400 text-sm">
              Need at least 2 data points
            </div>
          )}
        </div>
      </div>

      {/* ── Trade Efficiency vs Anchor ── */}
      {tradeEfficiencyRows.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Trade Efficiency vs Anchor</h3>
            <span className="text-xs text-gray-400">Did guardrails fire at the right moments?</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] text-gray-400 uppercase tracking-wider border-b border-gray-100">
                  <th className="text-left py-2 pr-4">Date</th>
                  <th className="text-left pr-4">Symbol</th>
                  <th className="text-right pr-4">Side</th>
                  <th className="text-right pr-4">Anchor $</th>
                  <th className="text-right pr-4">Trade $</th>
                  <th className="text-right pr-4">Spread</th>
                  <th className="text-right">Direction</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {tradeEfficiencyRows.map((trade, i) => (
                  <tr key={i} className="hover:bg-gray-50 text-gray-700">
                    <td className="py-2 pr-4 text-gray-500">{trade.date}</td>
                    <td className="pr-4 font-medium">{trade.asset_symbol || '—'}</td>
                    <td className="pr-4 text-right">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${trade.side === 'BUY' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="pr-4 text-right font-mono">${trade.anchor_price!.toFixed(2)}</td>
                    <td className="pr-4 text-right font-mono">${trade.price!.toFixed(2)}</td>
                    <td className={`pr-4 text-right font-semibold ${trade.spread < 0 ? 'text-red-500' : 'text-green-600'}`}>
                      {trade.spread >= 0 ? '+' : ''}{trade.spread.toFixed(1)}%
                    </td>
                    <td className="text-right">
                      {trade.intendedDir ? (
                        <span className="text-green-600 font-semibold">✓ On target</span>
                      ) : (
                        <span className="text-amber-500">↻ Off target</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-gray-400 mt-3">
            On target = BUY below anchor (stock discounted) or SELL above anchor (stock premium). Spread = (trade price − anchor) ÷ anchor.
          </p>
        </div>
      )}
    </div>
  );
}
