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
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart,
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

  // Use price_data for chart if available, otherwise fall back to daily_returns
  const chartData =
    result.price_data && result.price_data.length > 0
      ? result.price_data.map((pricePoint, index) => ({
          date: new Date(pricePoint.timestamp).toLocaleDateString(),
          algorithm: pricePoint.price, // Use raw price for now
          buyHold: pricePoint.price, // Same as algorithm for now
          return: 0, // Will be calculated if needed
        }))
      : result.daily_returns.map((day, index) => ({
          date: new Date(day.date).toLocaleDateString(),
          algorithm: day.portfolio_value,
          buyHold: result.daily_returns[index]?.portfolio_value || 0,
          return: day.return * 100,
        }));

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
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Value Over Time</h3>
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
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Value']} />
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
                    <Tooltip formatter={(value) => [formatPercent(Number(value)), 'Return']} />
                    <Bar dataKey="return" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
