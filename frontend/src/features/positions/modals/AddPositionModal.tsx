import { useState, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import { marketApi } from '../../../lib/api';
import toast from 'react-hot-toast';

interface AddPositionModalProps {
  onClose: () => void;
  onSave: (data: {
    ticker: string;
    qty: number;
    dollarValue: number;
    inputMode: 'qty' | 'dollar';
    currentPrice: number;
    cash: number;
  }) => Promise<void>;
}

// Helper function to sanitize ticker symbols
function sanitizeTicker(ticker: string | null | undefined): string | null {
  if (!ticker) return null;
  const sanitized = ticker
    .replace(/[\\\n\r\t]/g, '')
    .trim()
    .toUpperCase();
  return sanitized.length > 0 ? sanitized : null;
}

export default function AddPositionModal({ onClose, onSave }: AddPositionModalProps) {
  const [inputMode, setInputMode] = useState<'qty' | 'dollar'>('dollar');
  const [qty, setQty] = useState(0);
  const [dollarValue, setDollarValue] = useState(0);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [cash, setCash] = useState(0);
  const [loading, setLoading] = useState(false);
  // Store ticker in ref to avoid React re-renders during typing
  const tickerRef = useRef('');
  const tickerInputRef = useRef<HTMLInputElement>(null);

  // Set up native DOM event listener to completely bypass React
  useEffect(() => {
    const input = tickerInputRef.current;
    if (!input) return;

    const handleInput = (e: Event) => {
      const target = e.target as HTMLInputElement;
      tickerRef.current = target.value;
      console.log('[AddPositionModal] Input changed, value:', target.value, '- NO FETCH TRIGGERED');
    };

    const handleBlur = (e: Event) => {
      const target = e.target as HTMLInputElement;
      const upperValue = target.value.toUpperCase().trim();
      target.value = upperValue;
      tickerRef.current = upperValue;
    };

    // Prevent Enter key from submitting form
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
      }
    };

    input.addEventListener('input', handleInput);
    input.addEventListener('blur', handleBlur);
    input.addEventListener('keydown', handleKeyDown);

    return () => {
      input.removeEventListener('input', handleInput);
      input.removeEventListener('blur', handleBlur);
      input.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Only fetch price when user explicitly requests it (button click)
  const fetchPrice = async (source: string = 'unknown') => {
    const callId = `[AddPositionModal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}]`;
    console.log(
      `${callId} fetchPrice called from: ${source} - this should ONLY happen on button click`,
    );

    const tickerValue = tickerRef.current.trim();
    if (!tickerValue) {
      setCurrentPrice(0);
      return;
    }

    const sanitizedTicker = sanitizeTicker(tickerValue);
    if (sanitizedTicker) {
      // Update the input to show sanitized value
      if (tickerInputRef.current) {
        tickerInputRef.current.value = sanitizedTicker;
        tickerRef.current = sanitizedTicker;
      }
      setLoading(true);
      try {
        console.log(`${callId} Fetching price for:`, sanitizedTicker);
        const data = await marketApi.getPrice(sanitizedTicker);
        console.log(`${callId} Price fetched successfully:`, data.price);
        setCurrentPrice(data.price);
      } catch (err: any) {
        console.error(`${callId} Price fetch failed:`, err);
        if (err.message && !err.message.includes('ticker_not_found')) {
          console.warn(`Failed to fetch price:`, err.message);
        }
        setCurrentPrice(0);
      } finally {
        setLoading(false);
      }
    } else {
      setCurrentPrice(0);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const tickerUpper = tickerRef.current.trim().toUpperCase();

    // Validate ticker
    if (!tickerUpper) {
      toast.error('Please enter a valid ticker symbol');
      return;
    }

    // Validate price
    if (!currentPrice || currentPrice <= 0) {
      toast.error('Please fetch the current price first by clicking "Get Price"');
      return;
    }

    // Validate quantity or dollar value based on input mode
    if (inputMode === 'qty') {
      if (!qty || qty <= 0 || !isFinite(qty)) {
        toast.error('Please enter a valid quantity greater than 0');
        return;
      }
    } else {
      if (!dollarValue || dollarValue <= 0 || !isFinite(dollarValue)) {
        toast.error('Please enter a valid dollar value greater than 0');
        return;
      }
    }

    setLoading(true);
    try {
      await onSave({
        ticker: tickerUpper,
        qty: qty || 0,
        dollarValue: dollarValue || 0,
        inputMode,
        currentPrice,
        cash,
      });
    } catch (error) {
      // Error is already handled in parent component
      console.error('Error in handleSubmit:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Add Position</h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ticker <span className="text-red-500">*</span>
                  </label>
                  <div className="flex gap-2">
                    <input
                      ref={tickerInputRef}
                      type="text"
                      className="mt-1 flex-1 block rounded-md border border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2"
                      placeholder="Enter ticker symbol"
                      autoComplete="off"
                      spellCheck="false"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => fetchPrice('button-click')}
                      className="mt-1 ml-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      disabled={loading}
                    >
                      {loading ? 'Loading...' : 'Get Price'}
                    </button>
                  </div>
                  {currentPrice > 0 && (
                    <p className="mt-1 text-sm text-gray-500">
                      Current price: ${currentPrice.toFixed(2)}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Input Mode</label>
                  <div className="flex gap-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="dollar"
                        checked={inputMode === 'dollar'}
                        onChange={(e) => setInputMode(e.target.value as 'qty' | 'dollar')}
                        className="mr-2"
                      />
                      $ Value
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="qty"
                        checked={inputMode === 'qty'}
                        onChange={(e) => setInputMode(e.target.value as 'qty' | 'dollar')}
                        className="mr-2"
                      />
                      Quantity
                    </label>
                  </div>
                </div>

                {inputMode === 'dollar' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Dollar Value <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.01"
                        value={dollarValue || ''}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setDollarValue(val);
                          if (currentPrice > 0) {
                            setQty(val / currentPrice);
                          }
                        }}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm pl-8 px-3 py-2"
                        placeholder="0.00"
                        required
                      />
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 mt-1">
                        $
                      </span>
                    </div>
                    {currentPrice > 0 && dollarValue > 0 && (
                      <p className="mt-1 text-xs text-gray-500">
                        Calculated quantity: {(dollarValue / currentPrice).toFixed(4)} shares
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={qty || ''}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setQty(val);
                        if (currentPrice > 0) {
                          setDollarValue(val * currentPrice);
                        }
                      }}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2"
                      placeholder="0.00"
                      required
                    />
                    {currentPrice > 0 && qty > 0 && (
                      <p className="mt-1 text-xs text-gray-500">
                        Calculated value: ${(qty * currentPrice).toFixed(2)}
                      </p>
                    )}
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cash</label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      value={cash || ''}
                      onChange={(e) => setCash(e.target.value ? Number(e.target.value) : 0)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm pl-8 px-3 py-2"
                      placeholder="0.00"
                      min={0}
                    />
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 mt-1">
                      $
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Starting cash allocated to this position (can be zero).
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Position'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}







