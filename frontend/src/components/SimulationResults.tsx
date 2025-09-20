import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  ReferenceLine,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart,
  Legend,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Target,
  AlertCircle,
  CheckCircle,
  Clock,
  BarChart3,
} from 'lucide-react';

export interface SimulationResult {
  ticker: string;
  start_date: string;
  end_date: string;
  total_trading_days: number;

  // Algorithm performance
  algorithm: {
    trades: number;
    pnl: number;
    return_pct: number;
    volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };

  // Buy & Hold performance
  buy_hold: {
    pnl: number;
    return_pct: number;
    volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };

  // Comparison metrics
  comparison: {
    excess_return: number;
    alpha: number;
    beta: number;
    information_ratio: number;
  };

  // Trade details
  trade_log: Array<{
    timestamp: string;
    side: 'BUY' | 'SELL';
    qty: number;
    price: number;
    commission: number;
    cash_after: number;
    shares_after: number;
  }>;
  daily_returns: Array<{
    date: string;
    return: number;
    portfolio_value: number;
  }>;

  // Dividend analysis
  dividend_analysis: {
    total_dividends: number;
    dividend_yield: number;
    dividend_count: number;
    total_dividend_amount: number;
    total_dividends_received: number;
    net_dividends_received: number;
    withholding_tax_amount: number;
    dividends: Array<{
      ex_date: string;
      pay_date: string;
      dps: number;
      currency: string;
      withholding_tax_rate: number;
    }>;
    message: string;
  };
}

interface SimulationResultsProps {
  result: SimulationResult | null;
  isLoading: boolean;
  className?: string;
}

export default function SimulationResults({
  result,
  isLoading,
  className = '',
}: SimulationResultsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'trades' | 'charts'>(
    'overview',
  );

  if (isLoading) {
    return (
      <div className={`card ${className}`}>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Running Simulation</h3>
            <p className="text-gray-500">Processing historical data and calculating results...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className={`card ${className}`}>
        <div className="text-center py-12">
          <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Simulation Results</h3>
          <p className="text-gray-500">
            Run a simulation to see detailed results and performance metrics.
          </p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) =>
    `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const formatPercent = (value: number) => `${value.toFixed(2)}%`;
  const formatNumber = (value: number, decimals: number = 0) =>
    value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });

  const performanceData = [
    {
      metric: 'Total Return',
      algorithm: result.algorithm.return_pct,
      buyHold: result.buy_hold.return_pct,
      excess: result.comparison.excess_return,
    },
    {
      metric: 'Volatility',
      algorithm: result.algorithm.volatility,
      buyHold: result.buy_hold.volatility,
      excess: result.algorithm.volatility - result.buy_hold.volatility,
    },
    {
      metric: 'Sharpe Ratio',
      algorithm: result.algorithm.sharpe_ratio,
      buyHold: result.buy_hold.sharpe_ratio,
      excess: result.algorithm.sharpe_ratio - result.buy_hold.sharpe_ratio,
    },
    {
      metric: 'Max Drawdown',
      algorithm: result.algorithm.max_drawdown,
      buyHold: result.buy_hold.max_drawdown,
      excess: result.algorithm.max_drawdown - result.buy_hold.max_drawdown,
    },
  ];

  // Debug: Log dividend data
  if (result.dividend_analysis?.dividends?.length > 0) {
    console.log('Dividend data available:', result.dividend_analysis.dividends);
    console.log('Daily returns dates:', result.daily_returns.map((d) => d.date).slice(0, 5));
  }

  // Create meaningful portfolio performance chart data
  const chartData = result.daily_returns.map((day, index) => {
    // Calculate buy & hold performance (assuming we started with the same initial value)
    const initialValue = result.daily_returns[0]?.portfolio_value || 10000;
    const buyHoldValue = initialValue * (1 + (day.return * index) / result.daily_returns.length);

    // Check if there's a dividend event on this day
    const dayDate = new Date(day.date);
    const dividendOnThisDay = result.dividend_analysis?.dividends?.find((div) => {
      const exDate = new Date(div.ex_date);
      // More flexible date matching - check if dates are within 1 day of each other
      const timeDiff = Math.abs(dayDate.getTime() - exDate.getTime());
      const daysDiff = timeDiff / (1000 * 60 * 60 * 24);
      const isMatch = daysDiff <= 1; // Allow 1 day tolerance

      // Debug logging
      if (isMatch) {
        console.log(
          `Dividend match found: ${dayDate.toDateString()} matches ${exDate.toDateString()}, amount: $${
            div.dps
          }`,
        );
      }

      return isMatch;
    });

    return {
      date: new Date(day.date).toLocaleDateString(),
      algorithm: day.portfolio_value,
      buyHold: buyHoldValue,
      return: day.return * 100,
      day: index + 1,
      hasDividend: !!dividendOnThisDay,
      dividendAmount: dividendOnThisDay ? dividendOnThisDay.dps : 0,
    };
  });

  const tradeSideData = [
    {
      side: 'BUY',
      count: result.trade_log.filter((t) => t.side === 'BUY').length,
      color: '#10b981',
    },
    {
      side: 'SELL',
      count: result.trade_log.filter((t) => t.side === 'SELL').length,
      color: '#ef4444',
    },
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Simulation Results</h2>
            <div className="mt-2 space-y-1">
              <p className="text-gray-600">
                <span className="font-medium">{result.ticker}</span> • {result.total_trading_days}{' '}
                trading days
              </p>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  <span>{new Date(result.start_date).toLocaleDateString()}</span>
                </div>
                <span>→</span>
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  <span>{new Date(result.end_date).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {formatPercent(result.algorithm.return_pct)}
            </div>
            <div className="text-sm text-gray-500">Algorithm Return</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'performance', name: 'Performance', icon: TrendingUp },
              { id: 'trades', name: 'Trades', icon: Activity },
              { id: 'charts', name: 'Charts', icon: Target },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Key Metrics */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Trades</span>
                <span className="font-semibold">{result.algorithm.trades}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Algorithm P&L</span>
                <span
                  className={`font-semibold ${
                    result.algorithm.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}
                >
                  {formatCurrency(result.algorithm.pnl)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Buy & Hold P&L</span>
                <span
                  className={`font-semibold ${
                    result.buy_hold.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}
                >
                  {formatCurrency(result.buy_hold.pnl)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Excess Return</span>
                <span
                  className={`font-semibold ${
                    result.comparison.excess_return >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}
                >
                  {formatPercent(result.comparison.excess_return)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Alpha</span>
                <span
                  className={`font-semibold ${
                    result.comparison.alpha >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}
                >
                  {formatPercent(result.comparison.alpha)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Information Ratio</span>
                <span className="font-semibold">
                  {formatNumber(result.comparison.information_ratio, 2)}
                </span>
              </div>
            </div>
          </div>

          {/* Performance Comparison */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Comparison</h3>
            <div className="space-y-3">
              {performanceData.map((item) => (
                <div key={item.metric} className="flex items-center justify-between">
                  <span className="text-gray-600">{item.metric}</span>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {item.metric === 'Total Return' ||
                        item.metric === 'Volatility' ||
                        item.metric === 'Max Drawdown'
                          ? formatPercent(item.algorithm)
                          : formatNumber(item.algorithm, 2)}
                      </div>
                      <div className="text-xs text-gray-500">Algorithm</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {item.metric === 'Total Return' ||
                        item.metric === 'Volatility' ||
                        item.metric === 'Max Drawdown'
                          ? formatPercent(item.buyHold)
                          : formatNumber(item.buyHold, 2)}
                      </div>
                      <div className="text-xs text-gray-500">Buy & Hold</div>
                    </div>
                    <div
                      className={`text-right ${
                        item.excess >= 0 ? 'text-success-600' : 'text-danger-600'
                      }`}
                    >
                      <div className="text-sm font-medium">
                        {item.metric === 'Total Return' ||
                        item.metric === 'Volatility' ||
                        item.metric === 'Max Drawdown'
                          ? formatPercent(item.excess)
                          : formatNumber(item.excess, 2)}
                      </div>
                      <div className="text-xs">Excess</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          {/* Performance Chart */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Algorithm vs Buy & Hold Performance
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Compare the volatility balancing algorithm performance against a simple buy & hold
              strategy
            </p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Value']} />
                  <Area
                    type="monotone"
                    dataKey="algorithm"
                    stackId="1"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.6}
                    name="Algorithm"
                  />
                  <Area
                    type="monotone"
                    dataKey="buyHold"
                    stackId="2"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.6}
                    name="Buy & Hold"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <h4 className="font-medium text-gray-900 mb-3">Risk Metrics</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Algorithm Volatility</span>
                  <span className="text-sm font-medium">
                    {formatPercent(result.algorithm.volatility)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Buy & Hold Volatility</span>
                  <span className="text-sm font-medium">
                    {formatPercent(result.buy_hold.volatility)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Algorithm Max DD</span>
                  <span className="text-sm font-medium text-danger-600">
                    {formatPercent(result.algorithm.max_drawdown)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Buy & Hold Max DD</span>
                  <span className="text-sm font-medium text-danger-600">
                    {formatPercent(result.buy_hold.max_drawdown)}
                  </span>
                </div>
              </div>
            </div>

            <div className="card">
              <h4 className="font-medium text-gray-900 mb-3">Return Metrics</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Algorithm Return</span>
                  <span
                    className={`text-sm font-medium ${
                      result.algorithm.return_pct >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}
                  >
                    {formatPercent(result.algorithm.return_pct)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Buy & Hold Return</span>
                  <span
                    className={`text-sm font-medium ${
                      result.buy_hold.return_pct >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}
                  >
                    {formatPercent(result.buy_hold.return_pct)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Excess Return</span>
                  <span
                    className={`text-sm font-medium ${
                      result.comparison.excess_return >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}
                  >
                    {formatPercent(result.comparison.excess_return)}
                  </span>
                </div>
              </div>
            </div>

            <div className="card">
              <h4 className="font-medium text-gray-900 mb-3">Risk-Adjusted Returns</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Algorithm Sharpe</span>
                  <span className="text-sm font-medium">
                    {formatNumber(result.algorithm.sharpe_ratio, 2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Buy & Hold Sharpe</span>
                  <span className="text-sm font-medium">
                    {formatNumber(result.buy_hold.sharpe_ratio, 2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Information Ratio</span>
                  <span className="text-sm font-medium">
                    {formatNumber(result.comparison.information_ratio, 2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Alpha</span>
                  <span
                    className={`text-sm font-medium ${
                      result.comparison.alpha >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}
                  >
                    {formatPercent(result.comparison.alpha)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trades Tab */}
      {activeTab === 'trades' && (
        <div className="space-y-6">
          {/* Trade Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="flex items-center">
                <Activity className="h-8 w-8 text-primary-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Trades</p>
                  <p className="text-2xl font-semibold text-gray-900">{result.algorithm.trades}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-success-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Buy Trades</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {result.trade_log.filter((t) => t.side === 'BUY').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <TrendingDown className="h-8 w-8 text-danger-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Sell Trades</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {result.trade_log.filter((t) => t.side === 'SELL').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-warning-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Commission</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(result.trade_log.reduce((sum, t) => sum + t.commission, 0))}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Trade Log */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Log</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Side
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Asset $ Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Change Qty
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Commission
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cash After
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Shares After
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.trade_log.map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(trade.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`badge ${
                            trade.side === 'BUY' ? 'badge-success' : 'badge-danger'
                          }`}
                        >
                          {trade.side}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(Math.abs(trade.qty), 2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(trade.price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(Math.abs(trade.qty) * trade.price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(trade.qty, 2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(trade.commission)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(trade.cash_after)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(trade.shares_after, 2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Charts Tab */}
      {activeTab === 'charts' && (
        <div className="space-y-6">
          {/* Portfolio Value Chart */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Value Comparison</h3>
            <p className="text-sm text-gray-600 mb-4">
              Shows how the volatility balancing algorithm performs compared to a simple buy & hold
              strategy over time
            </p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Value']} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="algorithm"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Algorithm"
                  />
                  <Line
                    type="monotone"
                    dataKey="buyHold"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Buy & Hold"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={tradeSideData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ side, count }) => `${side}: ${count}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {tradeSideData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Returns</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.slice(-30)}>
                    {' '}
                    {/* Last 30 days */}
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip
                      formatter={(value, name, props) => {
                        if (name === 'return') {
                          return [formatPercent(Number(value)), 'Return'];
                        }
                        return [value, name];
                      }}
                      labelFormatter={(label, payload) => {
                        const data = payload?.[0]?.payload;
                        if (data?.hasDividend) {
                          return `${label} (Dividend: $${data.dividendAmount.toFixed(4)})`;
                        }
                        return label;
                      }}
                    />
                    <Bar dataKey="return" fill="#3b82f6" />
                    {/* Add dividend markers */}
                    {chartData
                      .slice(-30)
                      .map((entry, index) =>
                        entry.hasDividend ? (
                          <ReferenceLine
                            key={index}
                            x={entry.date}
                            stroke="#10b981"
                            strokeWidth={2}
                            strokeDasharray="5 5"
                          />
                        ) : null,
                      )}
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {result.dividend_analysis?.dividend_count > 0 && (
                <div className="mt-2 text-sm text-gray-600">
                  <span className="inline-flex items-center">
                    <div
                      className="w-3 h-3 bg-green-500 mr-2"
                      style={{ borderRadius: '50%' }}
                    ></div>
                    Green dashed lines indicate dividend ex-dates
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Dividend Analysis */}
      {result.dividend_analysis && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Dividend Analysis</h3>
          <div className="space-y-4">
            {/* Dividend Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm font-medium text-blue-600">Per Share</div>
                <div className="text-2xl font-bold text-blue-900">
                  ${result.dividend_analysis.total_dividend_amount.toFixed(4)}
                </div>
                <div className="text-xs text-blue-700">total per share</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm font-medium text-green-600">Net Received</div>
                <div className="text-2xl font-bold text-green-900">
                  ${result.dividend_analysis.net_dividends_received.toFixed(2)}
                </div>
                <div className="text-xs text-green-700">after tax (25%)</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm font-medium text-purple-600">Dividend Yield</div>
                <div className="text-2xl font-bold text-purple-900">
                  {result.dividend_analysis.dividend_yield.toFixed(2)}%
                </div>
                <div className="text-xs text-purple-700">annualized</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-sm font-medium text-orange-600">Count</div>
                <div className="text-2xl font-bold text-orange-900">
                  {result.dividend_analysis.dividend_count}
                </div>
                <div className="text-xs text-orange-700">payments</div>
              </div>
            </div>

            {/* Additional Dividend Details */}
            {result.dividend_analysis.dividend_count > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-gray-600">Gross Total</div>
                  <div className="text-lg font-bold text-gray-900">
                    ${result.dividend_analysis.total_dividends_received.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-700">before tax</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-red-600">Tax Withheld</div>
                  <div className="text-lg font-bold text-red-900">
                    ${result.dividend_analysis.withholding_tax_amount.toFixed(2)}
                  </div>
                  <div className="text-xs text-red-700">25% withholding</div>
                </div>
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-indigo-600">Cash Impact</div>
                  <div className="text-lg font-bold text-indigo-900">
                    +${result.dividend_analysis.net_dividends_received.toFixed(2)}
                  </div>
                  <div className="text-xs text-indigo-700">added to cash</div>
                </div>
              </div>
            )}

            {/* Dividend Details */}
            {result.dividend_analysis.dividends.length > 0 ? (
              <div>
                <h4 className="text-md font-semibold text-gray-800 mb-3">Dividend History</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Ex-Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Pay Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Currency
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tax Rate
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {result.dividend_analysis.dividends.map((dividend, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(dividend.ex_date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(dividend.pay_date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${dividend.dps.toFixed(4)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {dividend.currency}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {(dividend.withholding_tax_rate * 100).toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-500">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No Dividends</h3>
                  <p className="mt-1 text-sm text-gray-500">{result.dividend_analysis.message}</p>
                </div>
              </div>
            )}

            {/* Dividend Impact Message */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Dividend Impact</h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>
                      Dividends are not included in the simulation performance calculations. The
                      algorithm focuses on price volatility trading and does not account for
                      dividend payments or ex-dividend date adjustments to anchor prices.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
