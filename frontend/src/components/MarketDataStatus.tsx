import { useMarketStatus, useMarketPrice } from '../hooks/useMarketData';
import { Clock, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

interface MarketDataStatusProps {
  ticker?: string;
  showPrice?: boolean;
}

export default function MarketDataStatus({ ticker, showPrice = false }: MarketDataStatusProps) {
  const { data: marketStatus, isLoading: statusLoading } = useMarketStatus();
  const { data: priceData, isLoading: priceLoading } = useMarketPrice(ticker || '');

  if (statusLoading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
      </div>
    );
  }

  if (!marketStatus) {
    return (
      <div className="card">
        <div className="flex items-center text-gray-500">
          <AlertTriangle className="w-4 h-4 mr-2" />
          <span className="text-sm">Market data unavailable</span>
        </div>
      </div>
    );
  }

  const getMarketStatusIcon = () => {
    if (marketStatus.is_market_open) {
      return <CheckCircle className="w-4 h-4 text-success-600" />;
    } else if (marketStatus.is_after_hours) {
      return <Clock className="w-4 h-4 text-warning-600" />;
    } else {
      return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getMarketStatusText = () => {
    if (marketStatus.is_market_open) {
      return 'Market Open';
    } else if (marketStatus.is_after_hours) {
      return 'After Hours';
    } else {
      return 'Market Closed';
    }
  };

  const getMarketStatusColor = () => {
    if (marketStatus.is_market_open) {
      return 'text-success-600';
    } else if (marketStatus.is_after_hours) {
      return 'text-warning-600';
    } else {
      return 'text-gray-500';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getMarketStatusIcon()}
          <span className={`text-sm font-medium ${getMarketStatusColor()}`}>
            {getMarketStatusText()}
          </span>
        </div>

        {showPrice && ticker && priceData && (
          <div className="text-right">
            <div className="text-lg font-semibold text-gray-900">${priceData.price.toFixed(2)}</div>
            <div className="text-xs text-gray-500">
              {priceData.source} • {priceData.is_fresh ? 'Fresh' : 'Stale'}
            </div>
          </div>
        )}
      </div>

      {!marketStatus.is_market_open && (
        <div className="mt-2 text-xs text-gray-500">
          {marketStatus.is_after_hours ? (
            <>Next close: {new Date(marketStatus.next_close).toLocaleTimeString()}</>
          ) : (
            <>Next open: {new Date(marketStatus.next_open).toLocaleString()}</>
          )}
        </div>
      )}

      {showPrice && ticker && priceData && priceData.validation && (
        <div className="mt-2">
          {!priceData.validation.valid && (
            <div className="text-xs text-danger-600">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              Price validation failed: {priceData.validation.rejections.join(', ')}
            </div>
          )}
          {priceData.validation.warnings.length > 0 && (
            <div className="text-xs text-warning-600">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              Warnings: {priceData.validation.warnings.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
