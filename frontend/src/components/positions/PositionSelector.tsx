import { useMemo } from 'react';
import { TrendingUp, TrendingDown, ChevronDown, Briefcase } from 'lucide-react';

export interface PositionOption {
  id: string;
  asset: string;
  qty: number;
  cash: number;
  totalValue: number;
  stockPct: number;
  status?: string;
  priceChange?: number;
  priceChangePct?: number;
}

interface PositionSelectorProps {
  positions: PositionOption[];
  selectedId: string | null;
  onSelect: (positionId: string) => void;
  variant?: 'dropdown' | 'list' | 'cards';
  showMetrics?: boolean;
  className?: string;
  placeholder?: string;
  emptyMessage?: string;
}

export default function PositionSelector({
  positions,
  selectedId,
  onSelect,
  variant = 'dropdown',
  showMetrics = true,
  className = '',
  placeholder = 'Select a position...',
  emptyMessage = 'No positions available',
}: PositionSelectorProps) {
  const selectedPosition = useMemo(
    () => positions.find((p) => p.id === selectedId) || null,
    [positions, selectedId]
  );

  if (positions.length === 0) {
    return (
      <div className={`text-center py-6 ${className}`}>
        <Briefcase className="h-10 w-10 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  // Dropdown variant
  if (variant === 'dropdown') {
    return (
      <div className={`relative ${className}`}>
        <select
          value={selectedId || ''}
          onChange={(e) => onSelect(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-4 py-3 pr-10 text-sm font-medium focus:ring-2 focus:ring-primary-500 focus:border-primary-500 appearance-none bg-white"
        >
          <option value="">{placeholder}</option>
          {positions.map((pos) => (
            <option key={pos.id} value={pos.id}>
              {pos.asset} - {pos.qty.toLocaleString()} shares ($
              {pos.totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })})
            </option>
          ))}
        </select>
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
          <ChevronDown className="h-5 w-5 text-gray-400" />
        </div>

        {showMetrics && selectedPosition && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500 block text-xs">Quantity</span>
                <span className="font-semibold text-gray-900">
                  {selectedPosition.qty.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500 block text-xs">Stock %</span>
                <span className="font-semibold text-gray-900">
                  {selectedPosition.stockPct.toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-gray-500 block text-xs">Total Value</span>
                <span className="font-semibold text-gray-900">
                  ${selectedPosition.totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Cards variant
  if (variant === 'cards') {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
        {positions.map((pos) => {
          const isSelected = pos.id === selectedId;
          const isPositive = (pos.priceChangePct || 0) >= 0;

          return (
            <button
              key={pos.id}
              onClick={() => onSelect(pos.id)}
              className={`p-4 border rounded-xl text-left transition-all ${
                isSelected
                  ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                  : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold text-gray-900 text-lg">{pos.asset}</span>
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    pos.status === 'PAUSED'
                      ? 'bg-gray-100 text-gray-700'
                      : 'bg-green-100 text-green-700'
                  }`}
                >
                  {pos.status || 'ACTIVE'}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Shares</span>
                  <span className="font-medium text-gray-900">{pos.qty.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total Value</span>
                  <span className="font-medium text-gray-900">
                    ${pos.totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Stock %</span>
                  <span className="font-medium text-gray-900">{pos.stockPct.toFixed(1)}%</span>
                </div>
                {pos.priceChangePct !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Change</span>
                    <span
                      className={`font-medium flex items-center ${
                        isPositive ? 'text-success-600' : 'text-danger-600'
                      }`}
                    >
                      {isPositive ? (
                        <TrendingUp className="h-3 w-3 mr-1" />
                      ) : (
                        <TrendingDown className="h-3 w-3 mr-1" />
                      )}
                      {isPositive ? '+' : ''}
                      {pos.priceChangePct.toFixed(2)}%
                    </span>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    );
  }

  // List variant (default)
  return (
    <div className={`divide-y divide-gray-200 ${className}`}>
      {positions.map((pos) => {
        const isSelected = pos.id === selectedId;
        const isPositive = (pos.priceChangePct || 0) >= 0;

        return (
          <button
            key={pos.id}
            onClick={() => onSelect(pos.id)}
            className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
              isSelected ? 'bg-primary-50 border-l-4 border-primary-500' : ''
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-900">{pos.asset}</span>
              <span
                className={`text-xs px-2 py-1 rounded ${
                  pos.status === 'PAUSED' ? 'bg-gray-100 text-gray-700' : 'bg-green-100 text-green-700'
                }`}
              >
                {pos.status || 'ACTIVE'}
              </span>
            </div>
            {showMetrics && (
              <div className="mt-2 grid grid-cols-4 gap-2 text-xs text-gray-600">
                <div>
                  <span className="text-gray-400">Qty:</span> {pos.qty.toLocaleString()}
                </div>
                <div>
                  <span className="text-gray-400">Cash:</span> $
                  {pos.cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
                <div>
                  <span className="text-gray-400">Total:</span> $
                  {pos.totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
                <div>
                  <span className="text-gray-400">Stock:</span> {pos.stockPct.toFixed(1)}%
                </div>
              </div>
            )}
            {pos.priceChangePct !== undefined && (
              <div className="mt-1 flex items-center text-xs">
                <span
                  className={`flex items-center ${isPositive ? 'text-success-600' : 'text-danger-600'}`}
                >
                  {isPositive ? (
                    <TrendingUp className="h-3 w-3 mr-1" />
                  ) : (
                    <TrendingDown className="h-3 w-3 mr-1" />
                  )}
                  {isPositive ? '+' : ''}
                  {pos.priceChangePct.toFixed(2)}%
                </span>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
