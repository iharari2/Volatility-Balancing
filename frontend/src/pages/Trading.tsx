import React, { useState, useMemo } from 'react';
import {
  Play,
  Pause,
  Square,
  Settings,
  TrendingUp,
  AlertTriangle,
  Eye,
  EyeOff,
  Download,
  X,
} from 'lucide-react';
import { usePortfolio, Position } from '../contexts/PortfolioContext';
import { useMarketPrice } from '../hooks/useMarketData';

// Component for a single position row that can use hooks
interface PositionRowProps {
  position: Position;
  selectedPosition: string | null;
  onSelect: (id: string | null) => void;
  onConfig: (position: Position) => void;
  onToggle: (id: string) => void;
  ochlData: { open: number; close: number; high: number; low: number };
}

const PositionRow: React.FC<PositionRowProps> = ({
  position,
  selectedPosition,
  onSelect,
  onConfig,
  onToggle,
  ochlData,
}) => {
  // Fetch real market price and OHLC data for this position
  const { data: marketPrice } = useMarketPrice(position.ticker);
  const realCurrentPrice = marketPrice?.price || position.anchorPrice || 0;

  // Use real OHLC data from API if available, otherwise use passed ochlData (fallback)
  // Debug: log what we're receiving from the API
  if (marketPrice) {
    console.log(`[${position.ticker}] Market price data:`, {
      price: marketPrice.price,
      open: marketPrice.open,
      high: marketPrice.high,
      low: marketPrice.low,
      close: marketPrice.close,
      hasAllOHLC:
        marketPrice?.open !== undefined &&
        marketPrice?.high !== undefined &&
        marketPrice?.low !== undefined &&
        marketPrice?.close !== undefined,
    });
  }

  const realOCHLData =
    marketPrice?.open !== undefined &&
    marketPrice?.high !== undefined &&
    marketPrice?.low !== undefined &&
    marketPrice?.close !== undefined
      ? {
          open: marketPrice.open,
          high: marketPrice.high,
          low: marketPrice.low,
          close: marketPrice.close,
        }
      : ochlData;

  // Debug: log which data source we're using
  if (
    marketPrice &&
    (marketPrice.open === undefined ||
      marketPrice.high === undefined ||
      marketPrice.low === undefined ||
      marketPrice.close === undefined)
  ) {
    console.warn(
      `[${position.ticker}] Missing OHLC fields in API response, using fallback ochlData:`,
      ochlData,
    );
  }

  // Recalculate market value with real price
  const realMarketValue = position.units * realCurrentPrice;
  const totalValue = realMarketValue + position.cashAmount;
  const assetPercent = totalValue > 0 ? (realMarketValue / totalValue) * 100 : 0;

  // Use the proper anchor price from the position
  const anchorPrice = position.anchorPrice || realCurrentPrice;
  const buyTriggerPrice = anchorPrice * (1 + position.config.buyTrigger);
  const sellTriggerPrice = anchorPrice * (1 + position.config.sellTrigger);
  const highGuardrailPrice = anchorPrice * (1 + position.config.highGuardrail);
  const lowGuardrailPrice = anchorPrice * (1 - position.config.lowGuardrail);

  // Recalculate P&L with real price
  const realPnl = realMarketValue - position.units * anchorPrice;
  const realPnlPercent = anchorPrice > 0 ? (realPnl / (position.units * anchorPrice)) * 100 : 0;

  return (
    <tr className={selectedPosition === position.id ? 'bg-blue-50' : ''}>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">{position.ticker}</div>
          <div className="text-sm text-gray-500">{position.name}</div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">O:</span>
            <span className="text-xs">${realOCHLData.open.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">C:</span>
            <span className="text-xs">${realOCHLData.close.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">H:</span>
            <span className="text-xs text-green-600">${realOCHLData.high.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">L:</span>
            <span className="text-xs text-red-600">${realOCHLData.low.toFixed(2)}</span>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${anchorPrice.toFixed(2)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        <div className="flex items-center space-x-1">
          <span>${realCurrentPrice.toFixed(2)}</span>
          {marketPrice && (
            <span
              className={`text-xs ${marketPrice.is_fresh ? 'text-green-600' : 'text-yellow-600'}`}
              title={marketPrice.is_fresh ? 'Fresh data' : 'Stale data'}
            >
              {marketPrice.is_fresh ? '●' : '○'}
            </span>
          )}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {position.units.toLocaleString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${realMarketValue.toLocaleString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${position.cashAmount.toLocaleString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${totalValue.toLocaleString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {assetPercent.toFixed(1)}%
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm">
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">Buy:</span>
            <span className="text-xs text-green-600">${buyTriggerPrice.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">Sell:</span>
            <span className="text-xs text-red-600">${sellTriggerPrice.toFixed(2)}</span>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm">
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">H:</span>
            <span className="text-xs text-orange-600">${highGuardrailPrice.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-xs text-gray-500">L:</span>
            <span className="text-xs text-blue-600">${lowGuardrailPrice.toFixed(2)}</span>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className={`text-sm ${realPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          ${realPnl.toLocaleString()}
          <br />
          <span className="text-xs">({realPnlPercent.toFixed(2)}%)</span>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span
          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            position.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}
        >
          {position.isActive ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <div className="flex space-x-2">
          <button
            onClick={() => onConfig(position)}
            className="text-purple-600 hover:text-purple-900"
            title="Configure"
          >
            <Settings className="h-4 w-4" />
          </button>
          <button
            onClick={() => onSelect(selectedPosition === position.id ? null : position.id)}
            className="text-blue-600 hover:text-blue-900"
            title="View Details"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            onClick={() => onToggle(position.id)}
            className="text-gray-400 hover:text-gray-600"
            title={position.isActive ? 'Deactivate' : 'Activate'}
          >
            {position.isActive ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </td>
    </tr>
  );
};

interface TradingStatus {
  isRunning: boolean;
  isPaused: boolean;
  lastUpdate: string;
  activePositions: number;
  totalTrades: number;
  pnl: number;
}

const Trading: React.FC = () => {
  const { getActivePositions, updatePosition } = usePortfolio();
  const [tradingStatus, setTradingStatus] = useState<TradingStatus>({
    isRunning: true, // Trading enabled by default
    isPaused: false,
    lastUpdate: new Date().toISOString(),
    activePositions: 0,
    totalTrades: 0,
    pnl: 0,
  });

  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedPositionForConfig, setSelectedPositionForConfig] = useState<Position | null>(null);
  const [refreshFrequency, setRefreshFrequency] = useState(30); // seconds
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [liveData, setLiveData] = useState({
    marketOpen: true,
    lastUpdate: new Date().toLocaleTimeString(),
    activeTrades: 0,
    pendingOrders: 0,
  });

  // Get positions from shared context
  const positions = getActivePositions();

  // Auto-select first position if none selected and positions exist
  React.useEffect(() => {
    if (!selectedPosition && positions.length > 0) {
      setSelectedPosition(positions[0].id);
    }
  }, [positions, selectedPosition]);

  // Debug logging
  console.log('Trading component - positions:', positions);
  console.log('Trading component - positions length:', positions.length);

  // If no positions and backend is not available, show a helpful message
  if (positions.length === 0) {
    console.log('No positions found - this might be due to backend not running');
  }

  // Get OHLC data from market API for each position
  const ochlDataMap = useMemo(() => {
    const dataMap = new Map();
    positions.forEach((position) => {
      // Try to get OHLC from market price API
      // This will be populated by PositionRow component which fetches market data
      // For now, use fallback mock data if not available
      const basePrice = position.currentPrice;
      dataMap.set(position.id, {
        open: basePrice * 0.99, // Fallback - will be replaced by real data
        close: basePrice,
        high: basePrice * 1.01,
        low: basePrice * 0.98,
      });
    });
    return dataMap;
  }, [positions]);

  // Update trading status based on positions
  React.useEffect(() => {
    const activePositions = positions.filter((p) => p.isActive).length;
    const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0);
    const totalTrades = positions.reduce((sum, p) => sum + (p.lastTrade ? 1 : 0), 0);

    setTradingStatus((prev) => ({
      ...prev,
      activePositions: activePositions,
      totalTrades: totalTrades,
      pnl: totalPnl,
    }));
  }, [positions]);

  const handleStartTrading = () => {
    setTradingStatus((prev) => ({ ...prev, isRunning: true, isPaused: false }));
  };

  const handlePauseTrading = () => {
    setTradingStatus((prev) => ({ ...prev, isPaused: !prev.isPaused }));
  };

  const handleStopTrading = () => {
    setTradingStatus((prev) => ({ ...prev, isRunning: false, isPaused: false }));
  };

  const handleTogglePosition = async (id: string) => {
    try {
      await updatePosition(id, { isActive: !positions.find((p) => p.id === id)?.isActive });
    } catch (error) {
      console.error('Failed to toggle position:', error);
    }
  };

  const handleConfigPosition = (position: Position) => {
    setSelectedPositionForConfig(position);
    setShowConfigModal(true);
  };

  const handleExportTradingData = () => {
    // Export trading data as Excel via backend API
    window.open(`/api/excel/trading/export`, '_blank');
  };

  // Simulate live data updates with configurable frequency
  React.useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setLiveData((prev) => ({
        ...prev,
        lastUpdate: new Date().toLocaleTimeString(),
        activeTrades: Math.floor(Math.random() * 5) + 1,
        pendingOrders: Math.floor(Math.random() * 3),
      }));
    }, refreshFrequency * 1000); // Convert seconds to milliseconds

    return () => clearInterval(interval);
  }, [refreshFrequency, autoRefresh]);

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading</h1>
        <p className="text-gray-600">Start, monitor, and control your automated trading system</p>
      </div>

      {/* Refresh Controls */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Data Refresh Settings</h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="autoRefresh" className="text-sm text-gray-700">
                Auto Refresh
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <label htmlFor="refreshFreq" className="text-sm text-gray-700">
                Frequency:
              </label>
              <select
                id="refreshFreq"
                value={refreshFrequency}
                onChange={(e) => setRefreshFrequency(Number(e.target.value))}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
                disabled={!autoRefresh}
              >
                <option value={5}>5 seconds</option>
                <option value={10}>10 seconds</option>
                <option value={30}>30 seconds</option>
                <option value={60}>1 minute</option>
                <option value={300}>5 minutes</option>
              </select>
            </div>
            <button
              onClick={() =>
                setLiveData((prev) => ({ ...prev, lastUpdate: new Date().toLocaleTimeString() }))
              }
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
            >
              Refresh Now
            </button>
          </div>
        </div>
      </div>

      {/* Position Selector */}
      {positions.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Select Position to View</h3>
            <div className="flex-1 max-w-xs ml-4">
              <select
                value={selectedPosition || ''}
                onChange={(e) => setSelectedPosition(e.target.value || null)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select a position --</option>
                {positions.map((position) => (
                  <option key={position.id} value={position.id}>
                    {position.ticker} - {position.name || position.ticker}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Live Market Data */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Market Data</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center">
            <div
              className={`w-3 h-3 rounded-full mr-3 ${
                liveData.marketOpen ? 'bg-green-500' : 'bg-red-500'
              }`}
            ></div>
            <div>
              <h4 className="text-sm font-medium text-gray-500">Market Status</h4>
              <p className="text-lg font-semibold text-gray-900">
                {liveData.marketOpen ? 'Open' : 'Closed'}
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500">Last Update</h4>
            <p className="text-lg font-semibold text-gray-900">{liveData.lastUpdate}</p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500">Active Trades</h4>
            <p className="text-lg font-semibold text-gray-900">{liveData.activeTrades}</p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500">Pending Orders</h4>
            <p className="text-lg font-semibold text-gray-900">{liveData.pendingOrders}</p>
          </div>
        </div>
      </div>

      {/* Trading Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div
              className={`w-3 h-3 rounded-full mr-3 ${
                tradingStatus.isRunning
                  ? tradingStatus.isPaused
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                  : 'bg-gray-400'
              }`}
            ></div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Trading Status</h3>
              <p className="text-lg font-semibold text-gray-900">
                {tradingStatus.isRunning
                  ? tradingStatus.isPaused
                    ? 'Paused'
                    : 'Running'
                  : 'Stopped'}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Active Positions</h3>
          <p className="text-2xl font-bold text-gray-900">{tradingStatus.activePositions}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Trades</h3>
          <p className="text-2xl font-bold text-gray-900">{tradingStatus.totalTrades}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Today's P&L</h3>
          <p
            className={`text-2xl font-bold ${
              tradingStatus.pnl >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            ${tradingStatus.pnl.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Trading Controls */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Trading Controls</h3>
        <div className="flex items-center space-x-4">
          {!tradingStatus.isRunning ? (
            <button
              onClick={handleStartTrading}
              className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <Play className="h-5 w-5" />
              Start Trading
            </button>
          ) : (
            <>
              <button
                onClick={handlePauseTrading}
                className={`px-6 py-3 rounded-lg flex items-center gap-2 ${
                  tradingStatus.isPaused
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-yellow-600 text-white hover:bg-yellow-700'
                }`}
              >
                {tradingStatus.isPaused ? (
                  <Play className="h-5 w-5" />
                ) : (
                  <Pause className="h-5 w-5" />
                )}
                {tradingStatus.isPaused ? 'Resume' : 'Pause'}
              </button>
              <button
                onClick={handleStopTrading}
                className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 flex items-center gap-2"
              >
                <Square className="h-5 w-5" />
                Stop Trading
              </button>
            </>
          )}
          <button className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Settings
          </button>
          <button
            onClick={handleExportTradingData}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Download className="h-5 w-5" />
            Export Data
          </button>
        </div>
        <div className="mt-4 text-sm text-gray-500">
          Last update: {new Date(tradingStatus.lastUpdate).toLocaleString()}
        </div>
      </div>

      {/* Position Monitoring */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Position Monitoring</h3>
          <p className="text-sm text-gray-500">
            Monitor your active positions and trading activity
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset Ticker
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  OCHL
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Anchor Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Qty
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cash Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % of Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Buy/Sell Triggers
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Guardrails H/L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {positions.length === 0 ? (
                <tr>
                  <td colSpan={14} className="px-6 py-8 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <AlertTriangle className="h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-lg font-medium">No Active Positions</p>
                      <p className="text-sm">
                        Add positions in Portfolio Management to start trading
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                positions.map((position) => {
                  const ochlData = ochlDataMap.get(position.id) || { open: 0, close: 0, high: 0, low: 0 };
                  return (
                    <PositionRow
                      key={position.id}
                      position={position}
                      selectedPosition={selectedPosition}
                      onSelect={setSelectedPosition}
                      onConfig={handleConfigPosition}
                      onToggle={handleTogglePosition}
                      ochlData={ochlData}
                    />
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Position Details */}
      {selectedPosition && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">Trading Activity</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Trade:</span>
                  <span className="text-sm text-gray-900">2 hours ago</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Trade Count:</span>
                  <span className="text-sm text-gray-900">12</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Volume Today:</span>
                  <span className="text-sm text-gray-900">1,250 shares</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">Risk Metrics</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Volatility:</span>
                  <span className="text-sm text-gray-900">18.4%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Beta:</span>
                  <span className="text-sm text-gray-900">1.2</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Sharpe Ratio:</span>
                  <span className="text-sm text-gray-900">0.85</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">Alerts</h4>
              <div className="space-y-2">
                <div className="flex items-center text-sm text-yellow-600">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  High volatility detected
                </div>
                <div className="flex items-center text-sm text-green-600">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Rebalance threshold reached
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Config Modal */}
      {showConfigModal && selectedPositionForConfig && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Configure {selectedPositionForConfig.ticker}
                </h3>
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Position Status
                  </label>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedPositionForConfig.isActive}
                      onChange={(e) => {
                        const updatedPosition = {
                          ...selectedPositionForConfig,
                          isActive: e.target.checked,
                        };
                        setSelectedPositionForConfig(updatedPosition);
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Active</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Current Price
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={selectedPositionForConfig.currentPrice}
                      onChange={(e) => {
                        const updatedPosition = {
                          ...selectedPositionForConfig,
                          currentPrice: Number(e.target.value),
                        };
                        setSelectedPositionForConfig(updatedPosition);
                      }}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Market Value
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={selectedPositionForConfig.marketValue}
                      onChange={(e) => {
                        const updatedPosition = {
                          ...selectedPositionForConfig,
                          marketValue: Number(e.target.value),
                        };
                        setSelectedPositionForConfig(updatedPosition);
                      }}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => {
                    // Update positions array with the modified position
                    setShowConfigModal(false);
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Save Configuration
                </button>
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trading;
