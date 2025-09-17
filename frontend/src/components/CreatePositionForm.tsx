import { useState, useEffect } from 'react';
import { DollarSign, Package, TrendingUp, AlertCircle } from 'lucide-react';
import { CreatePositionRequest } from '../types';

interface CreatePositionFormProps {
  onSubmit: (data: CreatePositionRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

type InputMethod = 'dollar' | 'quantity';

export default function CreatePositionForm({ onSubmit, onCancel, isLoading = false }: CreatePositionFormProps) {
  const [inputMethod, setInputMethod] = useState<InputMethod>('dollar');
  const [ticker, setTicker] = useState('AAPL');
  const [dollarAmount, setDollarAmount] = useState(10000);
  const [quantity, setQuantity] = useState(0);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [priceError, setPriceError] = useState<string | null>(null);

  // Mock current price - in real implementation, this would fetch from market data API
  useEffect(() => {
    const fetchCurrentPrice = async () => {
      if (!ticker) return;
      
      setPriceLoading(true);
      setPriceError(null);
      
      try {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock price data - in real implementation, this would be actual market data
        const mockPrices: Record<string, number> = {
          'AAPL': 150.25,
          'MSFT': 350.80,
          'GOOGL': 2800.50,
          'TSLA': 250.75,
          'AMZN': 3200.00,
        };
        
        const price = mockPrices[ticker.toUpperCase()] || 100.00;
        setCurrentPrice(price);
      } catch (error) {
        setPriceError('Failed to fetch current price');
        setCurrentPrice(null);
      } finally {
        setPriceLoading(false);
      }
    };

    fetchCurrentPrice();
  }, [ticker]);

  // Calculate derived values
  const calculatedQuantity = currentPrice ? dollarAmount / currentPrice : 0;
  const calculatedDollarValue = currentPrice ? quantity * currentPrice : 0;
  const totalValue = inputMethod === 'dollar' ? dollarAmount : calculatedDollarValue;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const formData: CreatePositionRequest = {
      ticker: ticker.toUpperCase(),
      qty: inputMethod === 'quantity' ? quantity : calculatedQuantity,
      cash: inputMethod === 'dollar' ? dollarAmount : calculatedDollarValue,
    };

    await onSubmit(formData);
  };

  const handleDollarAmountChange = (value: number) => {
    setDollarAmount(value);
    if (currentPrice) {
      setQuantity(value / currentPrice);
    }
  };

  const handleQuantityChange = (value: number) => {
    setQuantity(value);
    if (currentPrice) {
      setDollarAmount(value * currentPrice);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Create New Position</h3>
        <p className="text-sm text-gray-600">
          Set up a new volatility balancing position. Choose how you want to specify the initial investment.
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
            <div className="text-right">
              {priceLoading ? (
                <div className="animate-pulse h-4 w-16 bg-gray-200 rounded"></div>
              ) : priceError ? (
                <div className="flex items-center space-x-1 text-danger-600">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">Error</span>
                </div>
              ) : currentPrice ? (
                <span className="text-lg font-semibold text-gray-900">
                  ${currentPrice.toFixed(2)}
                </span>
              ) : (
                <span className="text-sm text-gray-500">N/A</span>
              )}
            </div>
          </div>
        </div>

        {/* Input Method Toggle */}
        <div>
          <label className="label">Investment Method</label>
          <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg">
            <button
              type="button"
              onClick={() => setInputMethod('dollar')}
              className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                inputMethod === 'dollar'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <DollarSign className="w-4 h-4" />
              <span>Dollar Amount</span>
            </button>
            <button
              type="button"
              onClick={() => setInputMethod('quantity')}
              className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                inputMethod === 'quantity'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Package className="w-4 h-4" />
              <span>Share Quantity</span>
            </button>
          </div>
        </div>

        {/* Input Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Primary Input */}
          <div>
            <label className="label">
              {inputMethod === 'dollar' ? 'Dollar Amount' : 'Share Quantity'}
            </label>
            <div className="relative">
              <input
                type="number"
                value={inputMethod === 'dollar' ? dollarAmount : quantity}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (inputMethod === 'dollar') {
                    handleDollarAmountChange(value);
                  } else {
                    handleQuantityChange(value);
                  }
                }}
                className="input pr-8"
                min="0"
                step={inputMethod === 'dollar' ? '0.01' : '0.01'}
                required
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <span className="text-gray-500 text-sm">
                  {inputMethod === 'dollar' ? '$' : 'shares'}
                </span>
              </div>
            </div>
          </div>

          {/* Conversion Display */}
          <div>
            <label className="label">
              {inputMethod === 'dollar' ? 'Share Quantity' : 'Dollar Value'}
            </label>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {inputMethod === 'dollar' 
                  ? `${calculatedQuantity.toFixed(4)} shares`
                  : `$${calculatedDollarValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                }
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {inputMethod === 'dollar' 
                  ? 'Calculated from dollar amount'
                  : 'Calculated from share quantity'
                }
              </div>
            </div>
          </div>
        </div>

        {/* Position Preview */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="font-medium text-blue-900 mb-2">Position Preview</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-blue-700">Ticker:</span>
              <span className="font-medium text-blue-900">{ticker.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Shares:</span>
              <span className="font-medium text-blue-900">
                {inputMethod === 'quantity' ? quantity.toFixed(4) : calculatedQuantity.toFixed(4)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Cash:</span>
              <span className="font-medium text-blue-900">
                ${(inputMethod === 'dollar' ? dollarAmount : calculatedDollarValue).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between border-t border-blue-200 pt-1">
              <span className="text-blue-700 font-medium">Total Value:</span>
              <span className="font-semibold text-blue-900">
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="btn btn-secondary flex-1"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || !currentPrice}
            className="btn btn-primary flex-1"
          >
            {isLoading ? 'Creating...' : 'Create Position'}
          </button>
        </div>
      </form>
    </div>
  );
}
