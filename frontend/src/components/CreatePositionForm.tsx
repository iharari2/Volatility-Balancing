import { useState } from 'react';
import { TrendingUp, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { CreatePositionRequest } from '../types';
import { useMarketPrice } from '../hooks/useMarketData';
import { useConfiguration } from '../contexts/ConfigurationContext';

interface CreatePositionFormProps {
  onSubmit: (data: CreatePositionRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function CreatePositionForm({
  onSubmit,
  onCancel,
  isLoading = false,
}: CreatePositionFormProps) {
  const [ticker, setTicker] = useState('AAPL');
  const [investmentAmount, setInvestmentAmount] = useState(10000);
  const [isValidating, setIsValidating] = useState(false);
  const { configuration } = useConfiguration();

  // Use real market data
  const {
    data: marketData,
    isLoading: priceLoading,
    error: priceError,
    refetch,
  } = useMarketPrice(ticker);

  const currentPrice = marketData?.price;
  const calculatedShares = currentPrice ? investmentAmount / currentPrice : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form data
    if (!ticker.trim()) {
      alert('Please enter a ticker symbol');
      return;
    }

    if (!currentPrice) {
      alert('Unable to fetch current market price. Please try again.');
      return;
    }

    if (investmentAmount <= 0) {
      alert('Investment amount must be greater than 0');
      return;
    }

    if (calculatedShares <= 0) {
      alert('Unable to calculate shares. Please check the investment amount.');
      return;
    }

    setIsValidating(true);

    const formData: CreatePositionRequest = {
      ticker: ticker.toUpperCase(),
      qty: calculatedShares,
      cash: investmentAmount,
      anchor_price: currentPrice, // Set anchor price to current market price
      order_policy: {
        min_qty: 0,
        min_notional: configuration.minNotional,
        lot_size: 0,
        qty_step: 0,
        action_below_min: 'hold',
        trigger_threshold_pct: configuration.triggerThresholdPct,
        rebalance_ratio: configuration.rebalanceRatio,
        commission_rate: configuration.commissionRate,
        allow_after_hours: configuration.allowAfterHours,
      },
      guardrails: {
        min_stock_alloc_pct: configuration.guardrails.minStockAllocPct,
        max_stock_alloc_pct: configuration.guardrails.maxStockAllocPct,
        max_orders_per_day: 5,
      },
      withholding_tax_rate: 0.25,
    };

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Failed to create position:', error);
      alert('Failed to create position. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleRefreshPrice = () => {
    refetch();
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Create New Position</h3>
        <p className="text-sm text-gray-600">
          Set up a new volatility balancing position. Simply enter the ticker and investment amount
          - we'll automatically calculate the shares and set the anchor price based on current
          market data.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Ticker Input */}
        <div>
          <label className="label">Ticker Symbol</label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            className="input"
            placeholder="e.g., AAPL"
            required
          />
        </div>

        {/* Current Price Display */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Current Market Price</span>
            </div>
            <div className="flex items-center space-x-2">
              {priceLoading ? (
                <div className="animate-pulse h-4 w-16 bg-gray-200 rounded"></div>
              ) : priceError ? (
                <div className="flex items-center space-x-1 text-danger-600">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">Error</span>
                </div>
              ) : currentPrice ? (
                <div className="flex items-center space-x-2">
                  <span className="text-lg font-semibold text-gray-900">
                    ${currentPrice.toFixed(2)}
                  </span>
                  <button
                    type="button"
                    onClick={handleRefreshPrice}
                    className="p-1 hover:bg-gray-200 rounded"
                    title="Refresh price"
                  >
                    <RefreshCw className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
              ) : (
                <span className="text-sm text-gray-500">N/A</span>
              )}
            </div>
          </div>

          {marketData && (
            <div className="mt-2 text-xs text-gray-500">
              <div className="flex items-center space-x-4">
                <span>Source: {marketData.source}</span>
                <span
                  className={`flex items-center space-x-1 ${
                    marketData.is_fresh ? 'text-success-600' : 'text-warning-600'
                  }`}
                >
                  {marketData.is_fresh ? (
                    <CheckCircle className="w-3 h-3" />
                  ) : (
                    <AlertCircle className="w-3 h-3" />
                  )}
                  {marketData.is_fresh ? 'Fresh' : 'Stale'}
                </span>
                <span
                  className={marketData.is_market_hours ? 'text-success-600' : 'text-warning-600'}
                >
                  {marketData.is_market_hours ? 'Market Hours' : 'After Hours'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Investment Amount Input */}
        <div>
          <label className="label">Investment Amount</label>
          <div className="relative">
            <input
              type="number"
              value={investmentAmount}
              onChange={(e) => setInvestmentAmount(Number(e.target.value))}
              className="input pr-8"
              min="0"
              step="0.01"
              required
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <span className="text-gray-500 text-sm">$</span>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            This will be your initial cash allocation for volatility balancing
          </p>
        </div>

        {/* Calculated Shares Display */}
        {currentPrice && (
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-medium text-blue-900 mb-2">Position Calculation</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-blue-700">Investment Amount:</span>
                <span className="font-medium text-blue-900">
                  $
                  {investmentAmount.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-700">Current Price:</span>
                <span className="font-medium text-blue-900">${currentPrice.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-blue-200 pt-2">
                <span className="text-blue-700 font-medium">Shares to Purchase:</span>
                <span className="font-semibold text-blue-900">
                  {calculatedShares.toFixed(4)} shares
                </span>
              </div>
              <div className="text-xs text-blue-600 mt-2">
                The anchor price will be set to ${currentPrice.toFixed(2)} for volatility balancing
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-4">
          <button type="button" onClick={onCancel} className="btn btn-secondary flex-1">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || isValidating || !currentPrice || priceLoading}
            className="btn btn-primary flex-1"
          >
            {isLoading || isValidating ? 'Creating...' : 'Create Position'}
          </button>
        </div>
      </form>
    </div>
  );
}
