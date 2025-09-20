import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
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
  BarChart3,
  PieChart as PieChartIcon,
} from 'lucide-react';

interface EnhancedSimulationAnalyticsProps {
  data: {
    simulationResult?: {
      ticker: string;
      algorithm: {
        trades: number;
        pnl: number;
        return_pct: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
      };
      buy_hold: {
        pnl: number;
        return_pct: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
      };
      comparison: {
        excess_return: number;
        alpha: number;
        beta: number;
        information_ratio: number;
      };
      daily_returns: Array<{
        date: string;
        algorithm_return: number;
        buy_hold_return: number;
        portfolio_value: number;
        price: number;
      }>;
      trade_log: Array<{
        timestamp: string;
        side: string;
        qty: number;
        price: number;
        commission: number;
      }>;
    };
  };
}

export default function EnhancedSimulationAnalytics({ data }: EnhancedSimulationAnalyticsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'trades' | 'risk'>(
    'overview',
  );

  const analytics = useMemo(() => {
    if (!data?.simulationResult) return null;

    const result = data.simulationResult;
    const dailyReturns = result.daily_returns || [];
    const tradeLog = result.trade_log || [];

    // Calculate additional metrics
    const totalTrades = tradeLog.length;
    const buyTrades = tradeLog.filter((t) => t.side === 'BUY').length;
    const sellTrades = tradeLog.filter((t) => t.side === 'SELL').length;
    const totalCommission = tradeLog.reduce((sum, t) => sum + t.commission, 0);
    const avgTradeSize =
      tradeLog.length > 0
        ? tradeLog.reduce((sum, t) => sum + Math.abs(t.qty * t.price), 0) / tradeLog.length
        : 0;

    // Calculate win rate
    const profitableTrades = tradeLog.filter((t) => {
      const nextTrade = tradeLog.find((nt) => nt.timestamp > t.timestamp);
      if (!nextTrade) return false;
      return (
        (t.side === 'BUY' && nextTrade.price > t.price) ||
        (t.side === 'SELL' && nextTrade.price < t.price)
      );
    }).length;
    const winRate = totalTrades > 0 ? (profitableTrades / totalTrades) * 100 : 0;

    // Calculate drawdown periods
    const portfolioValues = dailyReturns.map((d) => d.portfolio_value);
    let maxDrawdown = 0;
    let currentDrawdown = 0;
    let peak = portfolioValues[0];

    for (const value of portfolioValues) {
      if (value > peak) {
        peak = value;
        currentDrawdown = 0;
      } else {
        currentDrawdown = (peak - value) / peak;
        maxDrawdown = Math.max(maxDrawdown, currentDrawdown);
      }
    }

    return {
      ...result,
      metrics: {
        totalTrades,
        buyTrades,
        sellTrades,
        totalCommission,
        avgTradeSize,
        winRate,
        maxDrawdown: maxDrawdown * 100,
      },
    };
  }, [data?.simulationResult]);

  if (!analytics) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No simulation data available</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'performance', label: 'Performance', icon: TrendingUp },
    { id: 'trades', label: 'Trades', icon: DollarSign },
    { id: 'risk', label: 'Risk Analysis', icon: TrendingDown },
  ];

  const performanceData =
    analytics.daily_returns?.map((d) => ({
      date: new Date(d.date).toLocaleDateString(),
      algorithm: d.algorithm_return * 100,
      buyHold: d.buy_hold_return * 100,
      portfolioValue: d.portfolio_value,
      price: d.price,
    })) || [];

  const tradeData =
    analytics.trade_log?.map((t) => ({
      time: new Date(t.timestamp).toLocaleTimeString(),
      side: t.side,
      qty: Math.abs(t.qty),
      price: t.price,
      value: Math.abs(t.qty * t.price),
      commission: t.commission,
    })) || [];

  const pieData = [
    { name: 'Buy Trades', value: analytics.metrics.buyTrades, color: '#10b981' },
    { name: 'Sell Trades', value: analytics.metrics.sellTrades, color: '#ef4444' },
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Enhanced Analytics - {analytics.ticker}
            </h2>
            <p className="text-gray-600">Comprehensive performance analysis and insights</p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span>{analytics.daily_returns?.length || 0} trading days</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-600">Algorithm Return</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {analytics.algorithm.return_pct.toFixed(2)}%
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-blue-500" />
                </div>
              </div>

              <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-600">Buy & Hold Return</p>
                    <p className="text-2xl font-bold text-green-900">
                      {analytics.buy_hold.return_pct.toFixed(2)}%
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-green-500" />
                </div>
              </div>

              <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-purple-600">Excess Return</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {analytics.comparison.excess_return.toFixed(2)}%
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-purple-500" />
                </div>
              </div>

              <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-orange-600">Sharpe Ratio</p>
                    <p className="text-2xl font-bold text-orange-900">
                      {analytics.algorithm.sharpe_ratio.toFixed(2)}
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-orange-500" />
                </div>
              </div>
            </div>

            {/* Performance Comparison Chart */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [`${value.toFixed(2)}%`, name]} />
                  <Legend />
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
        )}

        {activeTab === 'performance' && (
          <div className="space-y-6">
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Algorithm Performance</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total P&L:</span>
                    <span className="font-semibold">${analytics.algorithm.pnl.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Return:</span>
                    <span className="font-semibold">
                      {analytics.algorithm.return_pct.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Volatility:</span>
                    <span className="font-semibold">
                      {analytics.algorithm.volatility.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sharpe Ratio:</span>
                    <span className="font-semibold">
                      {analytics.algorithm.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Drawdown:</span>
                    <span className="font-semibold text-red-600">
                      {analytics.algorithm.max_drawdown.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Buy & Hold Performance</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total P&L:</span>
                    <span className="font-semibold">${analytics.buy_hold.pnl.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Return:</span>
                    <span className="font-semibold">
                      {analytics.buy_hold.return_pct.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Volatility:</span>
                    <span className="font-semibold">
                      {analytics.buy_hold.volatility.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sharpe Ratio:</span>
                    <span className="font-semibold">
                      {analytics.buy_hold.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Drawdown:</span>
                    <span className="font-semibold text-red-600">
                      {analytics.buy_hold.max_drawdown.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Cumulative Returns Chart */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cumulative Returns</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [`${value.toFixed(2)}%`, name]} />
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
        )}

        {activeTab === 'trades' && (
          <div className="space-y-6">
            {/* Trade Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-600">Total Trades</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {analytics.metrics.totalTrades}
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-blue-500" />
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-600">Win Rate</p>
                    <p className="text-2xl font-bold text-green-900">
                      {analytics.metrics.winRate.toFixed(1)}%
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-500" />
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-purple-600">Avg Trade Size</p>
                    <p className="text-2xl font-bold text-purple-900">
                      ${analytics.metrics.avgTradeSize.toFixed(0)}
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-purple-500" />
                </div>
              </div>
            </div>

            {/* Trade Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Distribution</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Details</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Buy Trades:</span>
                    <span className="font-semibold">{analytics.metrics.buyTrades}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sell Trades:</span>
                    <span className="font-semibold">{analytics.metrics.sellTrades}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Commission:</span>
                    <span className="font-semibold">
                      ${analytics.metrics.totalCommission.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Trades Table */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Trades</h3>
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
                        Value
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tradeData.slice(0, 10).map((trade, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {trade.time}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              trade.side === 'BUY'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {trade.side}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {trade.qty.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ${trade.price.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ${trade.value.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="space-y-6">
            {/* Risk Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-red-600">Max Drawdown</p>
                    <p className="text-2xl font-bold text-red-900">
                      {analytics.metrics.maxDrawdown.toFixed(2)}%
                    </p>
                  </div>
                  <TrendingDown className="w-8 h-8 text-red-500" />
                </div>
              </div>

              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-orange-600">Volatility</p>
                    <p className="text-2xl font-bold text-orange-900">
                      {analytics.algorithm.volatility.toFixed(2)}%
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-orange-500" />
                </div>
              </div>
            </div>

            {/* Risk Analysis */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Algorithm Risk Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sharpe Ratio:</span>
                      <span className="font-semibold">
                        {analytics.algorithm.sharpe_ratio.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Max Drawdown:</span>
                      <span className="font-semibold text-red-600">
                        {analytics.algorithm.max_drawdown.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Volatility:</span>
                      <span className="font-semibold">
                        {analytics.algorithm.volatility.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Buy & Hold Risk Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sharpe Ratio:</span>
                      <span className="font-semibold">
                        {analytics.buy_hold.sharpe_ratio.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Max Drawdown:</span>
                      <span className="font-semibold text-red-600">
                        {analytics.buy_hold.max_drawdown.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Volatility:</span>
                      <span className="font-semibold">
                        {analytics.buy_hold.volatility.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
