import { usePortfolio } from '../../contexts/PortfolioContext';
import { useState } from 'react';

export default function AssetAllocationChart() {
  const { positions } = usePortfolio();
  const [viewMode, setViewMode] = useState<'pie' | 'bar'>('pie');

  // Calculate allocations
  const totalCash = positions.reduce((sum, pos) => sum + pos.cashAmount, 0);
  const totalStock = positions.reduce((sum, pos) => sum + pos.marketValue, 0);
  const total = totalCash + totalStock;

  const cashPercent = total > 0 ? (totalCash / total) * 100 : 0;
  const stockPercent = total > 0 ? (totalStock / total) * 100 : 0;

  // Calculate per-asset breakdown
  const assetBreakdown = positions
    .filter((pos) => (pos.shares || pos.units || 0) > 0)
    .map((pos) => ({
      symbol: pos.ticker,
      value: pos.marketValue || 0,
      percent: total > 0 ? ((pos.marketValue || 0) / total) * 100 : 0,
    }));

  if (viewMode === 'pie') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">Asset Allocation</h3>
          <button
            onClick={() => setViewMode('bar')}
            className="text-xs text-primary-600 hover:text-primary-900"
          >
            Switch to Bar Chart
          </button>
        </div>

        {/* Simple pie chart representation */}
        <div className="flex items-center justify-center">
          <div className="relative w-64 h-64">
            {/* Pie chart using SVG */}
            <svg viewBox="0 0 100 100" className="transform -rotate-90">
              {/* Cash slice */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#10b981"
                strokeWidth="20"
                strokeDasharray={`${cashPercent * 2.513} 251.3`}
              />
              {/* Stock slice */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#3b82f6"
                strokeWidth="20"
                strokeDasharray={`${stockPercent * 2.513} 251.3`}
                strokeDashoffset={-cashPercent * 2.513}
              />
            </svg>
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-center space-x-6">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
            <span className="text-sm text-gray-700">
              Cash: {cashPercent.toFixed(1)}% (${totalCash.toLocaleString()})
            </span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
            <span className="text-sm text-gray-700">
              Stocks: {stockPercent.toFixed(1)}% (${totalStock.toLocaleString()})
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Bar chart view
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">Asset Allocation by Asset</h3>
        <button
          onClick={() => setViewMode('pie')}
          className="text-xs text-primary-600 hover:text-primary-900"
        >
          Switch to Pie Chart
        </button>
      </div>

      <div className="space-y-2">
        {/* Cash bar */}
        <div>
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Cash</span>
            <span>
              {cashPercent.toFixed(1)}% (${totalCash.toLocaleString()})
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-green-500 h-4 rounded-full"
              style={{ width: `${cashPercent}%` }}
            ></div>
          </div>
        </div>

        {/* Stock bars by asset */}
        {assetBreakdown.map((asset) => (
          <div key={asset.symbol}>
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>{asset.symbol}</span>
              <span>
                {asset.percent.toFixed(1)}% (${asset.value.toLocaleString()})
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-500 h-4 rounded-full"
                style={{ width: `${asset.percent}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
















