import { Position } from '../types';
import { TrendingUp, TrendingDown, DollarSign, Target, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMarketPrice } from '../hooks/useMarketData';

interface PositionCardProps {
  position: Position;
  onDelete?: (positionId: string) => void;
}

export default function PositionCard({ position, onDelete }: PositionCardProps) {
  // Fetch real market price for this ticker
  const { data: marketPrice } = useMarketPrice(position.ticker);
  const currentPrice = marketPrice?.price || position.anchor_price || 0;
  
  const totalValue = position.qty * currentPrice + position.cash;
  const assetPercentage = position.anchor_price
    ? ((position.qty * position.anchor_price) / totalValue) * 100
    : 0;

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <span className="text-primary-600 font-bold text-lg">{position.ticker.charAt(0)}</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{position.ticker}</h3>
            <p className="text-sm text-gray-500">Position #{position.id.slice(-8)}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Link
            to={`/positions/${position.id}`}
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            View Details →
          </Link>
          {onDelete && (
            <button
              onClick={() => onDelete(position.id)}
              className="text-red-600 hover:text-red-700 p-1 rounded hover:bg-red-50"
              title="Delete position"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-1">
          <div className="flex items-center text-sm text-gray-500">
            <TrendingUp className="w-4 h-4 mr-1" />
            Shares
          </div>
          <div className="text-lg font-semibold text-gray-900">{position.qty.toLocaleString()}</div>
        </div>
        <div className="space-y-1">
          <div className="flex items-center text-sm text-gray-500">
            <DollarSign className="w-4 h-4 mr-1" />
            Cash
          </div>
          <div className="text-lg font-semibold text-gray-900">
            ${position.cash.toLocaleString()}
          </div>
        </div>
      </div>

      {position.anchor_price && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Anchor Price</span>
            <span className="font-medium">${position.anchor_price.toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Current Price</span>
            <span className="font-medium">
              ${currentPrice.toFixed(2)}
              {marketPrice && (
                <span className={`ml-1 text-xs ${marketPrice.is_fresh ? 'text-green-600' : 'text-yellow-600'}`}>
                  {marketPrice.is_fresh ? '●' : '○'}
                </span>
              )}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Asset %</span>
            <span className="font-medium">{assetPercentage.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Total Value</span>
            <span className="font-medium">${totalValue.toLocaleString()}</span>
          </div>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center text-sm text-gray-500">
            <Target className="w-4 h-4 mr-1" />
            Trigger Zones
          </div>
          <div className="text-xs text-gray-400">
            {position.anchor_price ? (
              <>
                Buy: ${(position.anchor_price * 0.97).toFixed(2)} | Sell: $
                {(position.anchor_price * 1.03).toFixed(2)}
              </>
            ) : (
              'Not set'
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
