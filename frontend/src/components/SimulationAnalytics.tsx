import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ComposedChart,
  Legend,
  Scatter,
} from 'recharts';
import TriggerAnalysisTable from './TriggerAnalysisTable';
import {
  TrendingUp,
  DollarSign,
  Activity,
  Target,
  BarChart3,
  PieChart as PieChartIcon,
  Calendar,
  Zap,
  TrendingDown,
} from 'lucide-react';

export interface SimulationAnalyticsData {
  simulationResult: any; // The simulation result from the API
  dailyReturns: Array<{
    date: string;
    return: number;
    portfolio_value: number;
  }>;
  priceData: Array<{
    timestamp: string;
    price: number;
    volume: number;
    is_market_hours: boolean;
  }>;
  tradeLog?: Array<{
    timestamp: string;
    side: string;
    qty: number;
    price: number;
    commission: number;
    cash_after: number;
    shares_after: number;
  }>;
  triggerAnalysis?: Array<{
    timestamp: string;
    price: number;
    anchor_price: number;
    price_change_pct: number;
    trigger_threshold: number;
    triggered: boolean;
    side: string | null;
    qty: number;
    reason: string;
    executed: boolean;
    execution_error?: string;
    commission?: number;
    cash_after?: number;
    shares_after?: number;
  }>;
}

interface SimulationAnalyticsProps {
  data: SimulationAnalyticsData | null;
  isLoading?: boolean;
}

export default function SimulationAnalytics({ data, isLoading }: SimulationAnalyticsProps) {
  // Trade triggers data for overlay chart
  const tradeTriggersData = useMemo(() => {
    if (!data?.tradeLog || !data?.dailyReturns?.length) {
      console.log('No trade log or daily returns:', {
        tradeLog: data?.tradeLog?.length,
        dailyReturns: data?.dailyReturns?.length,
      });
      return [];
    }

    // Map trade log to chart data points
    const result = data.tradeLog.map((trade) => {
      // Find the corresponding day in dailyReturns
      const tradeDate = new Date(trade.timestamp).toISOString().split('T')[0];
      const dayData = data.dailyReturns.find((day) => day.date === tradeDate);

      return {
        x: tradeDate, // Use actual date string for x-axis
        y: trade.price, // Price for y-axis
        date: tradeDate, // Also include date for Scatter component
        timestamp: trade.timestamp,
        side: trade.side,
        qty: trade.qty,
        price: trade.price,
        commission: trade.commission,
        cash_after: trade.cash_after,
        shares_after: trade.shares_after,
      };
    });

    // Debug logging
    console.log('Trade triggers:', result.length, 'total');
    console.log('Buy:', result.filter((t) => t.side?.toLowerCase() === 'buy').length);
    console.log('Sell:', result.filter((t) => t.side?.toLowerCase() === 'sell').length);
    console.log('Sample trigger data:', result[0]);
    console.log('Chart data sample:', data?.dailyReturns?.[0]);
    console.log(
      'All trigger dates:',
      result.map((t) => t.x),
    );
    console.log(
      'Chart dates:',
      data?.dailyReturns?.map((d) => d.date),
    );
    return result;
  }, [data?.tradeLog, data?.dailyReturns]);

  const analytics = useMemo(() => {
    if (!data?.simulationResult || !data?.dailyReturns?.length) {
      return null;
    }

    const result = data.simulationResult;
    const dailyReturns = data.dailyReturns;
    const priceData = data.priceData || [];

    // Debug logging
    console.log('Simulation result keys:', Object.keys(result));
    console.log('Daily returns sample:', dailyReturns[0]);
    console.log('Price data sample:', priceData[0]);

    // Calculate key metrics
    const totalTrades = result.algorithm?.trades || 0;
    const totalPnL = result.algorithm?.pnl || 0;
    const finalValue = (result.algorithm?.pnl || 0) + (result.initial_cash || 10000);
    const initialValue = result.initial_cash || 10000;
    const totalReturn = result.algorithm?.return_pct || 0;

    // Buy & Hold comparison
    const buyHoldValue = (result.buy_hold?.pnl || 0) + (result.initial_cash || 10000);
    const buyHoldReturn = result.buy_hold?.return_pct || 0;

    // Calculate daily metrics from dailyReturns
    const dailyMetrics = dailyReturns.map((day, index) => {
      // Use actual simulation data
      const actualCash = day.cash || 0;
      const actualStockValue = day.stock_value || 0;
      const actualShares = day.shares || 0;
      const actualPrice = day.price || 0;

      // Calculate asset return from price data
      const firstPrice = priceData.length > 0 ? priceData[0].price : actualPrice;
      const assetReturn = firstPrice > 0 ? ((actualPrice - firstPrice) / firstPrice) * 100 : 0;

      return {
        date: new Date(day.date).toLocaleDateString(),
        portfolioValue: day.portfolio_value,
        cash: actualCash,
        stockValue: actualStockValue,
        dailyReturn: day.return * 100, // Convert to percentage
        price: actualPrice,
        shares: actualShares,
        assetReturn: assetReturn,
      };
    });

    // Calculate volatility metrics
    const returns = dailyMetrics.map((d) => d.dailyReturn).filter((r) => !isNaN(r));
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const volatility = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length,
    );

    // Calculate Sharpe ratio (assuming risk-free rate of 0)
    const sharpeRatio = volatility > 0 ? avgReturn / volatility : 0;

    // Calculate max drawdown
    let maxDrawdown = 0;
    let peak = initialValue;
    for (const day of dailyMetrics) {
      if (day.portfolioValue > peak) {
        peak = day.portfolioValue;
      }
      const drawdown = ((peak - day.portfolioValue) / peak) * 100;
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown;
      }
    }

    // Trade frequency analysis
    const tradingDays = priceData.length;
    const tradesPerDay = tradingDays > 0 ? totalTrades / tradingDays : 0;

    // Asset allocation over time
    const allocationData = dailyMetrics.map((day) => ({
      date: day.date,
      cash: (day.cash / day.portfolioValue) * 100,
      stock: (day.stockValue / day.portfolioValue) * 100,
    }));

    return {
      totalTrades,
      totalPnL,
      finalValue,
      initialValue,
      totalReturn,
      buyHoldValue,
      buyHoldReturn,
      dailyMetrics,
      volatility,
      sharpeRatio,
      maxDrawdown,
      tradesPerDay,
      allocationData,
      returns,
    };
  }, [data]);

  // Create combined chart data with trade triggers
  const chartDataWithTriggers = useMemo(() => {
    if (!analytics?.dailyMetrics) return [];

    // Create a combined dataset that includes trade triggers as separate data points
    const baseData = analytics.dailyMetrics.map((day, index) => ({
      ...day,
      dayIndex: index + 1,
      hasTrade: false,
      tradeSide: null,
      tradePrice: null,
    }));

    // Add trade triggers as separate data points
    const tradeData = tradeTriggersData.map((trigger) => ({
      dayIndex: trigger.x,
      price: trigger.y,
      portfolioValue: null, // Will be interpolated
      hasTrade: true,
      tradeSide: trigger.side,
      tradePrice: trigger.price,
      date: trigger.date,
    }));

    // Combine and sort by day index
    const combined = [...baseData, ...tradeData].sort((a, b) => a.dayIndex - b.dayIndex);

    console.log('Chart data with triggers:', combined);
    return combined;
  }, [analytics?.dailyMetrics, tradeTriggersData]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Simulation Data</h3>
        <p className="text-gray-500">Run a simulation to see analytics and performance metrics.</p>
      </div>
    );
  }

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Simulation Analytics</h2>
          <p className="text-gray-600">
            Performance analysis for{' '}
            <span className="font-semibold text-blue-600">
              {data?.simulationResult?.ticker || 'Unknown Asset'}
            </span>
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Calendar className="w-4 h-4" />
          <span>{analytics.dailyMetrics.length} trading days</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Return</p>
              <p
                className={`text-2xl font-bold ${
                  analytics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {analytics.totalReturn.toFixed(2)}%
              </p>
            </div>
            <TrendingUp
              className={`w-8 h-8 ${
                analytics.totalReturn >= 0 ? 'text-green-500' : 'text-red-500'
              }`}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            vs Buy & Hold: {analytics.buyHoldReturn.toFixed(2)}%
          </p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Final Value</p>
              <p className="text-2xl font-bold text-gray-900">
                ${analytics.finalValue.toLocaleString()}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-500" />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            From ${analytics.initialValue.toLocaleString()}
          </p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Trades</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.totalTrades}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {analytics.tradesPerDay.toFixed(1)} trades/day
          </p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Volatility</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.volatility.toFixed(2)}%</p>
            </div>
            <Zap className="w-8 h-8 text-yellow-500" />
          </div>
          <p className="text-xs text-gray-500 mt-1">Sharpe: {analytics.sharpeRatio.toFixed(2)}</p>
        </div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Value Over Time */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Portfolio Value Over Time ({data?.simulationResult?.ticker || 'Asset'})
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={analytics.dailyMetrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value, name) => [
                    typeof value === 'number' ? `$${value.toLocaleString()}` : value,
                    name,
                  ]}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="cash"
                  stackId="1"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.6}
                  name="Cash"
                />
                <Area
                  type="monotone"
                  dataKey="stockValue"
                  stackId="1"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.6}
                  name="Stock Value"
                />
                <Line
                  type="monotone"
                  dataKey="assetReturn"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="Asset Performance (%)"
                  yAxisId="right"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trade Triggers Over Asset Price */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Trade Triggers Over {data?.simulationResult?.ticker || 'Asset'} Price
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={analytics?.dailyMetrics || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" tickFormatter={(value) => `$${value.toFixed(2)}`} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === 'price') {
                      return [`$${value.toFixed(2)}`, 'Asset Price'];
                    }
                    return [`$${value.toLocaleString()}`, 'Portfolio Value'];
                  }}
                  labelFormatter={(label) => label}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name={`${data?.simulationResult?.ticker || 'Asset'} Price`}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="portfolioValue"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Portfolio Value"
                />
                {/* Buy trade markers */}
                <Scatter
                  yAxisId="left"
                  data={tradeTriggersData.filter(
                    (trigger) => trigger.side?.toLowerCase() === 'buy',
                  )}
                  fill="#ef4444"
                  name="Buy Triggers"
                  r={8}
                  stroke="#dc2626"
                  strokeWidth={2}
                />
                {/* Sell trade markers */}
                <Scatter
                  yAxisId="left"
                  data={tradeTriggersData.filter(
                    (trigger) => trigger.side?.toLowerCase() === 'sell',
                  )}
                  fill="#f59e0b"
                  name="Sell Triggers"
                  r={8}
                  stroke="#d97706"
                  strokeWidth={2}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            <div className="mb-2 text-xs text-gray-500">
              Debug: {tradeTriggersData.length} trade triggers found (
              {tradeTriggersData.filter((t) => t.side?.toLowerCase() === 'buy').length} buy,{' '}
              {tradeTriggersData.filter((t) => t.side?.toLowerCase() === 'sell').length} sell)
              <br />
              Sides: {[...new Set(tradeTriggersData.map((t) => t.side))].join(', ')}
            </div>
            {tradeTriggersData.length > 0 ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span>Buy Triggers</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span>Sell Triggers</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span>{data?.simulationResult?.ticker || 'Asset'} Price</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span>Portfolio Value</span>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500">
                No trade triggers found. Trade markers will appear here when trades are executed.
              </div>
            )}
          </div>
        </div>

        {/* Daily Returns Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Returns Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.dailyMetrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value.toFixed(2)}%`, 'Daily Return']} />
                <Bar dataKey="dailyReturn" fill="#3B82F6" name="Daily Return (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Asset Allocation Over Time */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Allocation</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.allocationData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Allocation']} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="cash"
                  stackId="1"
                  stroke="#10B981"
                  fill="#10B981"
                  name="Cash %"
                />
                <Area
                  type="monotone"
                  dataKey="stock"
                  stackId="1"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  name="Stock %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Metrics Summary */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Metrics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Max Drawdown</span>
              <span className="text-lg font-semibold text-red-600">
                -{analytics.maxDrawdown.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Volatility</span>
              <span className="text-lg font-semibold text-gray-900">
                {analytics.volatility.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Sharpe Ratio</span>
              <span className="text-lg font-semibold text-gray-900">
                {analytics.sharpeRatio.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Trades per Day</span>
              <span className="text-lg font-semibold text-gray-900">
                {analytics.tradesPerDay.toFixed(1)}
              </span>
            </div>
          </div>
        </div>

        {/* Performance Comparison */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Comparison</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Volatility Strategy</span>
              <span
                className={`text-lg font-semibold ${
                  analytics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {analytics.totalReturn.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Buy & Hold</span>
              <span
                className={`text-lg font-semibold ${
                  analytics.buyHoldReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {analytics.buyHoldReturn.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center border-t pt-2">
              <span className="text-sm font-medium text-gray-900">Outperformance</span>
              <span
                className={`text-lg font-bold ${
                  analytics.totalReturn - analytics.buyHoldReturn >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {(analytics.totalReturn - analytics.buyHoldReturn).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Trigger Analysis Table - Full Width */}
      {data?.triggerAnalysis && data.triggerAnalysis.length > 0 && (
        <div className="mt-6">
          <TriggerAnalysisTable data={data.triggerAnalysis} />
        </div>
      )}
    </div>
  );
}
