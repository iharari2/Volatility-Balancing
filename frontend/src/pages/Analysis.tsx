import React, { useState, useEffect, useMemo } from 'react';
import {
  Download,
  BarChart3,
  TrendingUp,
  PieChart,
  Table,
  Filter,
  RefreshCw,
  Clock,
  CheckCircle,
  AlertCircle,
  DollarSign,
  Activity,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { usePortfolio } from '../contexts/PortfolioContext';

interface AnalysisData {
  date: string;
  portfolioValue: number;
  marketValue: number;
  marketIndexValue: number;
  pnl: number;
  returnPercent: number;
  marketReturnPercent: number;
  indexReturnPercent: number;
}

interface PositionAnalysis {
  ticker: string;
  name: string;
  allocation: number;
  performance: number;
  volatility: number;
  sharpeRatio: number;
  marketPerformance: number;
  indexPerformance: number;
  alpha: number;
  beta: number;
}

interface MarketIndexData {
  name: string;
  symbol: string;
  value: number;
  change: number;
  changePercent: number;
}

interface Event {
  id: string;
  type: 'transaction' | 'pending' | 'dividend';
  timestamp: string;
  ticker: string;
  action: string;
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  reason: string;
  status: 'completed' | 'pending' | 'failed';
}

interface MarketData {
  date: string;
  time: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  bid: number;
  ask: number;
  dividendRate: number;
  dividendValue: number;
}

const Analysis: React.FC = () => {
  const { getActivePositions } = usePortfolio();
  const [activeTab, setActiveTab] = useState('positions');
  const [timeRange, setTimeRange] = useState('1M');
  const [analysisData, setAnalysisData] = useState<AnalysisData[]>([]);
  const [positionAnalysis, setPositionAnalysis] = useState<PositionAnalysis[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isUpdating, setIsUpdating] = useState(false);
  const [marketIndexData, setMarketIndexData] = useState<MarketIndexData[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [marketData, setMarketData] = useState<{ [ticker: string]: MarketData[] }>({});
  const [eventFilter, setEventFilter] = useState<'all' | 'transaction' | 'pending' | 'dividend'>(
    'all',
  );
  const [debugMode, setDebugMode] = useState(false);
  const [exportSuccessfulOnly, setExportSuccessfulOnly] = useState(true);

  // Get positions from shared context
  const positions = getActivePositions();

  // Generate mock data functions
  const generateMarketIndexData = () => {
    // Calculate average portfolio performance
    const avgPortfolioPerformance =
      positions.length > 0
        ? positions.reduce((sum, p) => sum + p.pnlPercent, 0) / positions.length
        : 0;

    return [
      {
        name: 'S&P 500',
        symbol: 'SPY',
        value: 4500 + (Math.random() - 0.5) * 100,
        change: (Math.random() - 0.5) * 50,
        changePercent: (Math.random() - 0.5) * 2,
        portfolioPerformance: avgPortfolioPerformance,
      },
      {
        name: 'NASDAQ',
        symbol: 'QQQ',
        value: 3800 + (Math.random() - 0.5) * 80,
        change: (Math.random() - 0.5) * 40,
        changePercent: (Math.random() - 0.5) * 2.5,
        portfolioPerformance: avgPortfolioPerformance,
      },
      {
        name: 'Russell 2000',
        symbol: 'IWM',
        value: 1800 + (Math.random() - 0.5) * 60,
        change: (Math.random() - 0.5) * 30,
        changePercent: (Math.random() - 0.5) * 3,
        portfolioPerformance: avgPortfolioPerformance,
      },
    ];
  };

  const generateEventsData = (positions: any[]): Event[] => {
    const events: Event[] = [];
    const now = new Date();

    positions.forEach((position, posIndex) => {
      // Generate transactions
      for (let i = 0; i < 3; i++) {
        const isBuy = Math.random() > 0.5;
        const quantity = Math.floor(Math.random() * 50) + 10;
        const price = position.currentPrice * (0.95 + Math.random() * 0.1);
        const amount = quantity * price;
        const commission = amount * 0.0001;

        events.push({
          id: `txn_${posIndex}_${i}`,
          type: 'transaction',
          timestamp: new Date(now.getTime() - (i + 1) * 24 * 60 * 60 * 1000).toISOString(),
          ticker: position.ticker,
          action: isBuy ? 'BUY' : 'SELL',
          quantity: isBuy ? quantity : -quantity,
          price: price,
          amount: amount,
          commission: commission,
          reason: isBuy ? 'Price below buy trigger' : 'Price above sell trigger',
          status: 'completed',
        });
      }

      // Generate pending orders
      if (Math.random() > 0.5) {
        events.push({
          id: `pending_${posIndex}`,
          type: 'pending',
          timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
          ticker: position.ticker,
          action: 'BUY',
          quantity: 25,
          price: position.currentPrice * 0.98,
          amount: 25 * position.currentPrice * 0.98,
          commission: 0,
          reason: 'Limit order below current price',
          status: 'pending',
        });
      }

      // Generate dividends
      if (position.ticker === 'AAPL' || position.ticker === 'MSFT') {
        events.push({
          id: `div_${posIndex}`,
          type: 'dividend',
          timestamp: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          ticker: position.ticker,
          action: 'DIVIDEND',
          quantity: position.units,
          price: 0.25,
          amount: position.units * 0.25,
          commission: 0,
          reason: 'Quarterly dividend payment',
          status: 'completed',
        });
      }
    });

    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  };

  const generateMarketData = (positions: any[]): { [ticker: string]: MarketData[] } => {
    const marketData: { [ticker: string]: MarketData[] } = {};

    positions.forEach((position) => {
      const data: MarketData[] = [];
      const basePrice = position.currentPrice;

      for (let i = 0; i < 30; i++) {
        const date = new Date();
        date.setDate(date.getDate() - (29 - i));

        const variation = (Math.random() - 0.5) * 0.1;
        const open = basePrice * (1 + variation);
        const close = open * (1 + (Math.random() - 0.5) * 0.05);
        const high = Math.max(open, close) * (1 + Math.random() * 0.02);
        const low = Math.min(open, close) * (1 - Math.random() * 0.02);
        const volume = Math.floor(Math.random() * 1000000) + 100000;
        const bid = close * 0.999;
        const ask = close * 1.001;
        const dividendRate = position.ticker === 'AAPL' || position.ticker === 'MSFT' ? 0.25 : 0;
        const dividendValue = position.ticker === 'AAPL' || position.ticker === 'MSFT' ? 0.25 : 0;

        data.push({
          date: date.toISOString().split('T')[0],
          time: date.toTimeString().split(' ')[0],
          open: open,
          close: close,
          high: high,
          low: low,
          volume: volume,
          bid: bid,
          ask: ask,
          dividendRate: dividendRate,
          dividendValue: dividendValue,
        });
      }

      marketData[position.ticker] = data;
    });

    return marketData;
  };

  const generateStableAnalysisData = () => {
    const mockData: AnalysisData[] = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);

    const totalValue = positions.reduce((sum, p) => sum + p.marketValue, 0);
    const baseValue = totalValue > 0 ? totalValue : 100000;

    for (let i = 0; i < 30; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);

      const dayVariation = Math.sin(i / 5) * 0.02;
      const randomNoise = (Math.random() - 0.5) * 0.01;
      const variation = dayVariation + randomNoise;

      const marketVariation = dayVariation * 0.7 + (Math.random() - 0.5) * 0.008;
      const indexVariation = dayVariation * 0.6 + (Math.random() - 0.5) * 0.006;

      mockData.push({
        date: date.toISOString().split('T')[0],
        portfolioValue: baseValue * (1 + variation),
        marketValue: baseValue * (1 + marketVariation),
        marketIndexValue: baseValue * (1 + indexVariation),
        pnl: baseValue * variation,
        returnPercent: variation * 100,
        marketReturnPercent: marketVariation * 100,
        indexReturnPercent: indexVariation * 100,
      });
    }
    return mockData;
  };

  // Memoize position analysis to prevent unnecessary recalculations
  const stablePositionAnalysis = useMemo(() => {
    const totalValue = positions.reduce((sum, p) => sum + p.marketValue, 0);

    if (positions.length === 0) {
      return [];
    }

    return positions.map((position) => {
      const allocation = totalValue > 0 ? (position.marketValue / totalValue) * 100 : 0;
      const performance = position.pnlPercent;
      const volatility = position.ticker === 'ZIM' ? 45 : 25;
      const sharpeRatio = volatility > 0 ? (performance / volatility) * 0.1 : 0;
      const marketPerformance = performance * 0.8;
      const indexPerformance = performance * 0.7;
      const alpha = performance * 0.2;
      const beta = 1.0;

      return {
        ticker: position.ticker,
        name: position.name,
        allocation,
        performance,
        volatility,
        sharpeRatio,
        marketPerformance,
        indexPerformance,
        alpha,
        beta,
      };
    });
  }, [positions]);

  // Update analysis data
  const updateAnalysisData = (forceRefresh = false) => {
    setIsUpdating(true);

    const newAnalysisData = generateStableAnalysisData();
    const newPositionAnalysis = stablePositionAnalysis; // Use memoized version
    const newMarketIndexData = generateMarketIndexData();
    const newEvents = generateEventsData(positions);
    const newMarketData = generateMarketData(positions);

    setAnalysisData(newAnalysisData);
    setPositionAnalysis(newPositionAnalysis);
    setMarketIndexData(newMarketIndexData);
    setEvents(newEvents);
    setMarketData(newMarketData);
    setLastUpdate(new Date());
    setIsUpdating(false);
  };

  // Initial data generation - only when positions change significantly
  useEffect(() => {
    updateAnalysisData();
  }, [positions.length]); // Only trigger when number of positions changes

  // Set up periodic updates (every 30 minutes) - much less frequent
  useEffect(() => {
    const interval = setInterval(() => {
      updateAnalysisData(true);
    }, 1800000); // 30 minutes instead of 10 minutes

    return () => clearInterval(interval);
  }, []); // Remove positions dependency to prevent frequent updates

  const tabs = [
    { id: 'positions', name: 'Position Analysis', icon: Table },
    { id: 'portfolio', name: 'Portfolio Overview', icon: BarChart3 },
    { id: 'market', name: 'Market Comparison', icon: BarChart3 },
  ];

  const handleExportData = () => {
    try {
      // Export to Excel via backend API with debug filtering
      const params = new URLSearchParams({
        format: 'xlsx',
        debug: debugMode.toString(),
        successfulOnly: exportSuccessfulOnly.toString(),
      });
      window.open(`/api/excel/positions/export?${params}`, '_blank');
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  };

  const handleExportPosition = (position: PositionAnalysis) => {
    try {
      // Export individual position data as Excel via backend API
      // Find the actual position to get the ID
      const actualPosition = positions.find((p) => p.ticker === position.ticker);
      if (actualPosition) {
        window.open(
          `/api/excel/positions/${actualPosition.id}/export?ticker=${actualPosition.ticker}`,
          '_blank',
        );
      } else {
        alert('Position not found for export');
      }
    } catch (error) {
      console.error('Position export failed:', error);
      alert('Position export failed. Please try again.');
    }
  };

  const handleComprehensiveExport = () => {
    try {
      // Use the backend comprehensive export API with correct ticker
      const firstPosition = positions[0];
      if (firstPosition) {
        window.open(
          `/api/excel/positions/${firstPosition.id}/comprehensive-export?ticker=${firstPosition.ticker}`,
          '_blank',
        );
      } else {
        alert('No positions available for comprehensive export');
      }
    } catch (error) {
      console.error('Comprehensive export failed:', error);
      alert('Comprehensive export failed. Please try again.');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Analysis</h1>
            <p className="text-gray-600">
              Charts, tables, and analysis of your portfolio and positions
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Last updated: {lastUpdate.toLocaleTimeString()}
              {isUpdating && (
                <span className="ml-2 text-blue-600">
                  <RefreshCw className="inline h-4 w-4 animate-spin" /> Updating...
                </span>
              )}
            </p>
          </div>
          <button
            onClick={() => updateAnalysisData(true)}
            disabled={isUpdating}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isUpdating ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>
      </div>

      {/* Time Range and Export Controls */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label htmlFor="timeRange" className="text-sm font-medium text-gray-700">
              Time Range:
            </label>
            <select
              id="timeRange"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="1D">1 Day</option>
              <option value="1W">1 Week</option>
              <option value="1M">1 Month</option>
              <option value="3M">3 Months</option>
              <option value="6M">6 Months</option>
              <option value="1Y">1 Year</option>
              <option value="ALL">All Time</option>
            </select>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="debugMode"
                checked={debugMode}
                onChange={(e) => setDebugMode(e.target.checked)}
                className="mr-1"
              />
              <label htmlFor="debugMode" className="text-sm text-gray-700">
                Debug Mode
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="successfulOnly"
                checked={exportSuccessfulOnly}
                onChange={(e) => setExportSuccessfulOnly(e.target.checked)}
                className="mr-1"
                disabled={!debugMode}
              />
              <label htmlFor="successfulOnly" className="text-sm text-gray-700">
                Successful Only
              </label>
            </div>
          </div>
          <button
            onClick={() => handleComprehensiveExport()}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export Data to Excel
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'positions' && (
          <div className="space-y-6">
            {/* Position Allocation Chart */}
            {positions.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Position Allocation</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={stablePositionAnalysis.map((pos) => ({
                            name: pos.ticker,
                            value: pos.allocation,
                            color:
                              pos.ticker === 'AAPL'
                                ? '#3B82F6'
                                : pos.ticker === 'ZIM'
                                ? '#10B981'
                                : pos.ticker === 'MSFT'
                                ? '#F59E0B'
                                : pos.ticker === 'GOOGL'
                                ? '#EF4444'
                                : '#6B7280',
                          }))}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                        >
                          {stablePositionAnalysis.map((pos, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={
                                pos.ticker === 'AAPL'
                                  ? '#3B82F6'
                                  : pos.ticker === 'ZIM'
                                  ? '#10B981'
                                  : pos.ticker === 'MSFT'
                                  ? '#F59E0B'
                                  : pos.ticker === 'GOOGL'
                                  ? '#EF4444'
                                  : '#6B7280'
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-900">Allocation Details</h4>
                    {stablePositionAnalysis.map((pos) => (
                      <div key={pos.ticker} className="flex justify-between items-center">
                        <div className="flex items-center">
                          <div
                            className="w-3 h-3 rounded-full mr-2"
                            style={{
                              backgroundColor:
                                pos.ticker === 'AAPL'
                                  ? '#3B82F6'
                                  : pos.ticker === 'ZIM'
                                  ? '#10B981'
                                  : pos.ticker === 'MSFT'
                                  ? '#F59E0B'
                                  : pos.ticker === 'GOOGL'
                                  ? '#EF4444'
                                  : '#6B7280',
                            }}
                          />
                          <span className="text-sm text-gray-700">{pos.ticker}</span>
                        </div>
                        <span className="text-sm font-medium">{pos.allocation.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {positions.length > 0 ? (
              positions.map((position) => (
                <div key={position.id} className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {position.ticker} - {position.name}
                        </h3>
                        <p className="text-sm text-gray-500">Position Analysis & Performance</p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="text-sm text-gray-500">Current Price</div>
                          <div className="text-lg font-semibold">
                            ${position.currentPrice.toFixed(2)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-500">P&L</div>
                          <div
                            className={`text-lg font-semibold ${
                              position.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            ${position.pnl.toFixed(2)} ({position.pnlPercent.toFixed(2)}%)
                          </div>
                        </div>
                        <button
                          onClick={() =>
                            handleExportPosition({
                              ticker: position.ticker,
                              name: position.name,
                              allocation:
                                (position.marketValue /
                                  positions.reduce((sum, p) => sum + p.marketValue, 0)) *
                                100,
                              performance: position.pnlPercent,
                              volatility: position.ticker === 'ZIM' ? 45 : 25,
                              sharpeRatio:
                                (position.pnlPercent / (position.ticker === 'ZIM' ? 45 : 25)) * 0.1,
                              marketPerformance: position.pnlPercent * 0.8,
                              indexPerformance: position.pnlPercent * 0.7,
                              alpha: position.pnlPercent * 0.2,
                              beta: 1.0,
                            })
                          }
                          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
                        >
                          <Download className="h-4 w-4" />
                          Export {position.ticker}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {/* Position Details */}
                      <div className="space-y-4">
                        <h4 className="text-md font-semibold text-gray-900">Position Details</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Units:</span>
                            <span className="text-sm font-medium">
                              {position.units.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Asset Value:</span>
                            <span className="text-sm font-medium">
                              ${position.assetAmount.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Cash:</span>
                            <span className="text-sm font-medium">
                              ${position.cashAmount.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Total Value:</span>
                            <span className="text-sm font-medium">
                              ${(position.marketValue + position.cashAmount).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Anchor Price:</span>
                            <span className="text-sm font-medium">
                              ${position.anchorPrice.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Trading Configuration */}
                      <div className="space-y-4">
                        <h4 className="text-md font-semibold text-gray-900">
                          Trading Configuration
                        </h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Buy Trigger:</span>
                            <span className="text-sm font-medium text-green-600">
                              $
                              {(position.anchorPrice * (1 + position.config.buyTrigger)).toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Sell Trigger:</span>
                            <span className="text-sm font-medium text-red-600">
                              $
                              {(position.anchorPrice * (1 + position.config.sellTrigger)).toFixed(
                                2,
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">High Guardrail:</span>
                            <span className="text-sm font-medium text-orange-600">
                              $
                              {(position.anchorPrice * (1 + position.config.highGuardrail)).toFixed(
                                2,
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Low Guardrail:</span>
                            <span className="text-sm font-medium text-blue-600">
                              $
                              {(position.anchorPrice * (1 - position.config.lowGuardrail)).toFixed(
                                2,
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Rebalance Ratio:</span>
                            <span className="text-sm font-medium">
                              {position.config.rebalanceRatio.toFixed(5)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Performance Metrics */}
                      <div className="space-y-4">
                        <h4 className="text-md font-semibold text-gray-900">Performance Metrics</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">P&L:</span>
                            <span
                              className={`text-sm font-medium ${
                                position.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              ${position.pnl.toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Return %:</span>
                            <span
                              className={`text-sm font-medium ${
                                position.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              {position.pnlPercent.toFixed(2)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Volatility:</span>
                            <span className="text-sm font-medium">
                              {position.ticker === 'ZIM' ? '45.0%' : '25.0%'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Sharpe Ratio:</span>
                            <span className="text-sm font-medium">
                              {(
                                (position.pnlPercent / (position.ticker === 'ZIM' ? 45 : 25)) *
                                0.1
                              ).toFixed(3)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Status:</span>
                            <span
                              className={`text-sm font-medium ${
                                position.isActive ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              {position.isActive ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Market Comparison */}
                    <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                      <h4 className="text-md font-semibold text-gray-900 mb-4">
                        Market Comparison
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {marketIndexData.map((index, idx) => (
                          <div key={idx} className="bg-white p-3 rounded border">
                            <div className="flex justify-between items-center mb-2">
                              <div>
                                <h5 className="font-medium text-gray-900 text-sm">{index.name}</h5>
                                <p className="text-xs text-gray-500">{index.symbol}</p>
                              </div>
                              <span
                                className={`text-sm font-medium ${
                                  index.change >= 0 ? 'text-green-600' : 'text-red-600'
                                }`}
                              >
                                {index.change >= 0 ? '+' : ''}
                                {index.changePercent.toFixed(2)}%
                              </span>
                            </div>
                            <div className="text-lg font-bold text-gray-900">
                              {index.value.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500">
                              vs {position.ticker}:{' '}
                              {position.pnlPercent > index.changePercent ? '+' : ''}
                              {(position.pnlPercent - index.changePercent).toFixed(2)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Events Table */}
                    <div className="mt-6">
                      <div className="flex justify-between items-center mb-4">
                        <h4 className="text-md font-semibold text-gray-900">Recent Events</h4>
                        <div className="flex items-center space-x-2">
                          <Filter className="h-4 w-4 text-gray-500" />
                          <select
                            value={eventFilter}
                            onChange={(e) => setEventFilter(e.target.value as any)}
                            className="text-sm border border-gray-300 rounded-md px-2 py-1"
                          >
                            <option value="all">All Events</option>
                            <option value="transaction">Transactions</option>
                            <option value="pending">Pending Orders</option>
                            <option value="dividend">Dividends</option>
                          </select>
                        </div>
                      </div>
                      <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Type
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Time
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Action
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Qty
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Price
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Amount
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Reason
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Status
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {events
                                .filter(
                                  (event) =>
                                    event.ticker === position.ticker &&
                                    (eventFilter === 'all' || event.type === eventFilter),
                                )
                                .slice(0, 10)
                                .map((event) => (
                                  <tr key={event.id}>
                                    <td className="px-4 py-4 whitespace-nowrap">
                                      <span
                                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                          event.type === 'transaction'
                                            ? 'bg-blue-100 text-blue-800'
                                            : event.type === 'pending'
                                            ? 'bg-yellow-100 text-yellow-800'
                                            : 'bg-green-100 text-green-800'
                                        }`}
                                      >
                                        {event.type === 'transaction' && (
                                          <Activity className="h-3 w-3 mr-1" />
                                        )}
                                        {event.type === 'pending' && (
                                          <Clock className="h-3 w-3 mr-1" />
                                        )}
                                        {event.type === 'dividend' && (
                                          <DollarSign className="h-3 w-3 mr-1" />
                                        )}
                                        {event.type.toUpperCase()}
                                      </span>
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                      {new Date(event.timestamp).toLocaleString()}
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                                      <span
                                        className={
                                          event.action === 'BUY'
                                            ? 'text-green-600'
                                            : event.action === 'SELL'
                                            ? 'text-red-600'
                                            : 'text-blue-600'
                                        }
                                      >
                                        {event.action}
                                      </span>
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                      {event.quantity.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                      ${event.price.toFixed(2)}
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                      ${event.amount.toFixed(2)}
                                    </td>
                                    <td className="px-4 py-4 text-sm text-gray-900 max-w-xs truncate">
                                      {event.reason}
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap">
                                      <span
                                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                          event.status === 'completed'
                                            ? 'bg-green-100 text-green-800'
                                            : event.status === 'pending'
                                            ? 'bg-yellow-100 text-yellow-800'
                                            : 'bg-red-100 text-red-800'
                                        }`}
                                      >
                                        {event.status === 'completed' && (
                                          <CheckCircle className="h-3 w-3 mr-1" />
                                        )}
                                        {event.status === 'pending' && (
                                          <Clock className="h-3 w-3 mr-1" />
                                        )}
                                        {event.status === 'failed' && (
                                          <AlertCircle className="h-3 w-3 mr-1" />
                                        )}
                                        {event.status.toUpperCase()}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                            </tbody>
                          </table>
                          {events.filter(
                            (event) =>
                              event.ticker === position.ticker &&
                              (eventFilter === 'all' || event.type === eventFilter),
                          ).length === 0 && (
                            <div className="text-center py-8 text-gray-500">
                              <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                              <p>No events found for {position.ticker}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Market Data Table */}
                    <div className="mt-6">
                      <h4 className="text-md font-semibold text-gray-900 mb-4">
                        Market Data (Last 10 Days)
                      </h4>
                      <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Date
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Open
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Close
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  High
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Low
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Volume
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Bid/Ask
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Dividend
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {marketData[position.ticker]?.slice(-10).map((data, index) => (
                                <tr key={index}>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {data.date}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${data.open.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${data.close.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${data.high.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${data.low.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {data.volume.toLocaleString()}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    ${data.bid.toFixed(2)} / ${data.ask.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {data.dividendValue > 0
                                      ? `$${data.dividendValue.toFixed(2)}`
                                      : '-'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {(!marketData[position.ticker] ||
                            marketData[position.ticker].length === 0) && (
                            <div className="text-center py-8 text-gray-500">
                              <BarChart3 className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                              <p>No market data available for {position.ticker}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Table className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Positions Available</h3>
                <p className="text-gray-500 mb-4">
                  Add positions in Portfolio Management to see detailed analysis
                </p>
                <button
                  onClick={() => (window.location.href = '/portfolio')}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Go to Portfolio Management
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'portfolio' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Total Portfolio Value</h3>
                <p className="text-2xl font-bold text-gray-900">$125,430</p>
                <p className="text-sm text-green-600">+5.2% from last month</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
                <p className="text-2xl font-bold text-green-600">+$6,230</p>
                <p className="text-sm text-gray-500">+5.2% return</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Volatility</h3>
                <p className="text-2xl font-bold text-gray-900">18.4%</p>
                <p className="text-sm text-gray-500">Annualized</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Sharpe Ratio</h3>
                <p className="text-2xl font-bold text-gray-900">0.85</p>
                <p className="text-sm text-gray-500">Risk-adjusted return</p>
              </div>
            </div>

            {/* Portfolio vs Market Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Portfolio vs Market Performance</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analysisData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip
                      formatter={(value, name) => [
                        typeof value === 'number' ? `$${value.toLocaleString()}` : value,
                        name === 'portfolioValue'
                          ? 'Portfolio Value'
                          : name === 'marketIndexValue'
                          ? 'Market Index'
                          : name,
                      ]}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="portfolioValue"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      name="Portfolio Value"
                    />
                    <Line
                      type="monotone"
                      dataKey="marketIndexValue"
                      stroke="#10B981"
                      strokeWidth={2}
                      name="Market Index"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'market' && (
          <div className="space-y-6">
            {/* Market Index Overview */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Market Index Performance</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {marketIndexData.map((index, idx) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-gray-900">{index.name}</h4>
                        <p className="text-sm text-gray-500">{index.symbol}</p>
                      </div>
                      <span
                        className={`text-sm font-medium ${
                          index.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {index.change >= 0 ? '+' : ''}
                        {index.changePercent.toFixed(2)}%
                      </span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {index.value.toLocaleString()}
                    </div>
                    <div
                      className={`text-sm ${index.change >= 0 ? 'text-green-600' : 'text-red-600'}`}
                    >
                      {index.change >= 0 ? '+' : ''}${index.change.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Comparison Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Portfolio vs Market Indices</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={marketIndexData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="symbol" />
                    <YAxis />
                    <Tooltip
                      formatter={(value, name) => [
                        typeof value === 'number' ? `${value.toFixed(2)}%` : value,
                        name === 'changePercent'
                          ? 'Index Performance'
                          : name === 'portfolioPerformance'
                          ? 'Portfolio Performance'
                          : name,
                      ]}
                    />
                    <Legend />
                    <Bar dataKey="changePercent" fill="#10B981" name="Index Performance" />
                    <Bar
                      dataKey="portfolioPerformance"
                      fill="#3B82F6"
                      name="Portfolio Performance"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Analysis;
