import { TrendingUp, TrendingDown, ChevronRight, Settings, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface PositionData {
  id: string;
  asset: string;
  qty: number;
  cash: number;
  anchorPrice: number | null;
  avgCost?: number | null;
  currentPrice: number;
  status?: string;
}

export interface PositionConfig {
  triggerUpPct?: number;
  triggerDownPct?: number;
  minStockPct?: number;
  maxStockPct?: number;
}

interface PositionCardProps {
  position: PositionData;
  portfolioId: string;
  config?: PositionConfig;
  variant?: 'compact' | 'detailed';
  onAction?: (action: 'view' | 'trade' | 'configure', positionId: string) => void;
  className?: string;
}

export default function PositionCard({
  position,
  portfolioId,
  config,
  variant = 'compact',
  onAction,
  className = '',
}: PositionCardProps) {
  const navigate = useNavigate();

  const stockValue = position.qty * position.currentPrice;
  const totalValue = stockValue + position.cash;
  const cashPct = totalValue > 0 ? (position.cash / totalValue) * 100 : 0;
  const stockPct = totalValue > 0 ? (stockValue / totalValue) * 100 : 0;

  const initialPrice = position.anchorPrice || position.avgCost || position.currentPrice;
  const positionReturn =
    initialPrice > 0 ? ((position.currentPrice - initialPrice) / initialPrice) * 100 : 0;

  const priceChange = initialPrice > 0 ? position.currentPrice - initialPrice : 0;
  const priceChangePct = positionReturn;
  const isPositive = priceChange >= 0;

  // Check guardrail status
  const minStockPct = config?.minStockPct ?? 0;
  const maxStockPct = config?.maxStockPct ?? 100;
  const isOutOfGuardrails = stockPct < minStockPct || stockPct > maxStockPct;

  const handleViewDetails = () => {
    if (onAction) {
      onAction('view', position.id);
    } else {
      navigate(`/portfolios/${portfolioId}/positions/${position.id}`);
    }
  };

  const handleTrade = () => {
    if (onAction) {
      onAction('trade', position.id);
    } else {
      navigate(`/trade/${portfolioId}/position/${position.id}`);
    }
  };

  const handleConfigure = () => {
    if (onAction) {
      onAction('configure', position.id);
    } else {
      navigate(`/portfolios/${portfolioId}/positions?tab=config&positionId=${position.id}`);
    }
  };

  // Compact card view
  if (variant === 'compact') {
    return (
      <div
        className={`bg-white rounded-lg shadow-md border border-gray-200 p-4 hover:shadow-lg transition-shadow cursor-pointer ${className}`}
        onClick={handleViewDetails}
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900">{position.asset}</h3>
          <span
            className={`text-xs px-2 py-1 rounded ${
              position.status === 'PAUSED' ? 'bg-gray-100 text-gray-700' : 'bg-green-100 text-green-700'
            }`}
          >
            {position.status || 'ACTIVE'}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-gray-900">
              ${position.currentPrice.toFixed(2)}
            </span>
            <span
              className={`flex items-center text-sm font-medium ${
                isPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {isPositive ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              {Math.abs(priceChangePct).toFixed(2)}%
            </span>
          </div>

          <div className="text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Total Value:</span>
              <span className="font-semibold">
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between mt-1">
              <span>Cash: {cashPct.toFixed(1)}%</span>
              <span className={isOutOfGuardrails ? 'text-danger-600 font-semibold' : ''}>
                Stock: {stockPct.toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-200">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Position Return:</span>
              <span className={`font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}
                {positionReturn.toFixed(2)}%
              </span>
            </div>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleViewDetails();
            }}
            className="w-full mt-2 px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 flex items-center justify-center"
          >
            View Details
            <ChevronRight className="h-4 w-4 ml-1" />
          </button>
        </div>
      </div>
    );
  }

  // Detailed card view
  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{position.asset} Position</h2>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            position.status === 'PAUSED' ? 'bg-gray-100 text-gray-700' : 'bg-green-100 text-green-700'
          }`}
        >
          {position.status || 'ACTIVE'}
        </span>
      </div>

      <div className="space-y-6">
        {/* Current Price */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Current Price:</span>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold text-gray-900">
                ${position.currentPrice.toFixed(2)}
              </span>
              <span
                className={`flex items-center text-sm font-medium ${
                  isPositive ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {isPositive ? (
                  <TrendingUp className="h-4 w-4 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 mr-1" />
                )}
                {isPositive ? '+' : ''}${Math.abs(priceChange).toFixed(2)} ({isPositive ? '+' : ''}
                {priceChangePct.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        {/* Value Breakdown */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">Value Breakdown</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Cash:</span>
              <span className="font-semibold text-gray-900">
                ${position.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${cashPct}%` }} />
            </div>

            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Stock:</span>
              <span className="font-semibold text-gray-900">
                ${stockValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${isOutOfGuardrails ? 'bg-red-500' : 'bg-blue-500'}`}
                style={{ width: `${stockPct}%` }}
              />
            </div>

            <div className="pt-2 border-t border-gray-300 flex justify-between">
              <span className="text-sm font-semibold text-gray-700">Total:</span>
              <span className="text-lg font-bold text-gray-900">
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>

        {/* Strategy Config Summary */}
        {config && (
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <h3 className="font-semibold text-gray-700">Strategy Config</h3>
            <div className="flex justify-between">
              <span className="text-gray-600">Triggers:</span>
              <span className="text-gray-900">
                +{config.triggerUpPct}% / {config.triggerDownPct}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Guardrails:</span>
              <span className="text-gray-900">
                {config.minStockPct}% - {config.maxStockPct}%
              </span>
            </div>
            {isOutOfGuardrails && (
              <div className="text-danger-600 text-xs font-medium mt-1">
                Currently outside guardrail range
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={handleConfigure}
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </button>
          <button
            onClick={handleTrade}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Play className="h-4 w-4 mr-2" />
            Trade
          </button>
          <button
            onClick={handleViewDetails}
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            View Details
            <ChevronRight className="h-4 w-4 ml-2" />
          </button>
        </div>
      </div>
    </div>
  );
}
