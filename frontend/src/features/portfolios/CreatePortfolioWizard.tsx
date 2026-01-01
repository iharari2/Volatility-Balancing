import { useState, useMemo, useEffect } from 'react';
import { X, Upload, Trash2, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { portfolioApi, marketApi } from '../../lib/api';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface CreatePortfolioWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (portfolioId: string) => void;
}

interface PortfolioData {
  name: string;
  description: string;
  portfolioType: 'live' | 'simulation' | 'sandbox';
  startingCash: {
    currency: string;
    amount: number;
  };
  holdings: Array<{
    symbol: string;
    qty: number;
    dollarValue?: number;
    inputMode: 'qty' | 'dollar';
    currentPrice?: number;
    avgCost?: number;
    anchorPrice?: number;
  }>;
  strategyTemplate: 'default' | 'conservative' | 'aggressive' | 'custom';
  marketHoursPolicy: 'market-open-only' | 'allow-after-hours';
}

// Template configurations
const TEMPLATE_CONFIGS: Record<
  'default' | 'conservative' | 'aggressive' | 'custom',
  {
    triggerUp: number;
    triggerDown: number;
    minStockPct: number;
    maxStockPct: number;
    maxTradePctOfPosition: number;
    commission: number;
    description: string;
  }
> = {
  default: {
    triggerUp: 3.0,
    triggerDown: -3.0,
    minStockPct: 20,
    maxStockPct: 60,
    maxTradePctOfPosition: 10,
    commission: 0.1,
    description: 'Balanced trading frequency and risk limits.',
  },
  conservative: {
    triggerUp: 4.0,
    triggerDown: -4.0,
    minStockPct: 15,
    maxStockPct: 50,
    maxTradePctOfPosition: 5,
    commission: 0.1,
    description: 'Fewer trades, tighter exposure, smaller trade sizes.',
  },
  aggressive: {
    triggerUp: 2.0,
    triggerDown: -2.0,
    minStockPct: 25,
    maxStockPct: 75,
    maxTradePctOfPosition: 15,
    commission: 0.1,
    description: 'More trades, larger trade sizes, broader exposure allowed.',
  },
  custom: {
    triggerUp: 3.0,
    triggerDown: -3.0,
    minStockPct: 20,
    maxStockPct: 60,
    maxTradePctOfPosition: 10,
    commission: 0.1,
    description: 'Start from Default then edit parameters immediately after creation.',
  },
};

export default function CreatePortfolioWizard({
  isOpen,
  onClose,
  onComplete,
}: CreatePortfolioWizardProps) {
  const navigate = useNavigate();
  const { selectedTenantId, setSelectedPortfolioId, refreshPortfolios, portfolios } =
    useTenantPortfolio();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<PortfolioData>({
    name: '',
    description: '',
    portfolioType: 'live',
    startingCash: {
      currency: 'USD',
      amount: 100000,
    },
    holdings: [],
    strategyTemplate: 'default',
    marketHoursPolicy: 'market-open-only',
  });

  const currentTemplate = useMemo(() => {
    try {
      const template = TEMPLATE_CONFIGS[formData.strategyTemplate];
      // Fallback to default if template not found
      if (!template) {
        console.warn(`Template "${formData.strategyTemplate}" not found, using default`);
        return TEMPLATE_CONFIGS.default;
      }
      return template;
    } catch (error) {
      console.error('Error loading template config:', error);
      return TEMPLATE_CONFIGS.default;
    }
  }, [formData.strategyTemplate]);

  const totalValue = useMemo(() => {
    let value = formData.startingCash.amount;
    formData.holdings.forEach((holding) => {
      const price = holding.anchorPrice || holding.avgCost || 0;
      value += holding.qty * price;
    });
    return value;
  }, [formData.startingCash.amount, formData.holdings]);

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate required fields
      if (!formData.name.trim() || formData.name.length < 3) {
        setError('Portfolio name must be at least 3 characters');
        setLoading(false);
        return;
      }

      // Check for duplicate portfolio name
      const normalizedName = formData.name.trim().toLowerCase();
      const duplicate = portfolios.find((p) => p.name.trim().toLowerCase() === normalizedName);
      if (duplicate) {
        setError(
          `Portfolio with name "${formData.name}" already exists. Please choose a different name.`,
        );
        setLoading(false);
        return;
      }

      if (formData.startingCash.amount <= 0) {
        setError('Starting cash must be greater than 0');
        setLoading(false);
        return;
      }

      // Validate holdings
      for (const holding of formData.holdings) {
        if (!holding.symbol.trim()) {
          setError('All holdings must have a symbol');
          setLoading(false);
          return;
        }
        if (holding.qty <= 0) {
          setError('All holdings must have quantity > 0');
          setLoading(false);
          return;
        }
        if (holding.avgCost !== undefined && holding.avgCost < 0) {
          setError('Average cost cannot be negative');
          setLoading(false);
          return;
        }
        if (holding.anchorPrice !== undefined && holding.anchorPrice < 0) {
          setError('Anchor price cannot be negative');
          setLoading(false);
          return;
        }
      }

      if (!selectedTenantId) {
        setError('No tenant selected. Please select a tenant first.');
        setLoading(false);
        return;
      }

      // Prepare holdings for API
      // Calculate cash allocation per position based on dollar value or distribute starting cash
      const holdingsWithValues = formData.holdings
        .filter((h) => h.symbol && h.qty > 0)
        .map((holding) => {
          // Determine anchor price: use provided, else avg cost, else current price
          let anchorPrice = holding.anchorPrice;
          if (!anchorPrice && holding.avgCost) {
            anchorPrice = holding.avgCost;
          }
          if (!anchorPrice && holding.currentPrice) {
            anchorPrice = holding.currentPrice;
          }

          // Calculate position value
          const positionValue =
            holding.dollarValue || (anchorPrice ? holding.qty * anchorPrice : 0);

          return {
            asset: holding.symbol.toUpperCase(),
            qty: holding.qty,
            avg_cost: holding.avgCost,
            anchor_price: anchorPrice,
            positionValue, // For cash allocation calculation
          };
        });

      // Calculate total position value
      const totalPositionValue = holdingsWithValues.reduce((sum, h) => sum + h.positionValue, 0);

      // Allocate cash proportionally based on position values, or equally if no values
      const holdings = holdingsWithValues.map((holding) => {
        let cash: number | undefined = undefined;

        if (totalPositionValue > 0 && formData.startingCash.amount > 0) {
          // Allocate cash proportionally based on position value
          const allocationRatio = holding.positionValue / totalPositionValue;
          cash = formData.startingCash.amount * allocationRatio;
        } else if (holdingsWithValues.length > 0 && formData.startingCash.amount > 0) {
          // If no position values, distribute equally
          cash = formData.startingCash.amount / holdingsWithValues.length;
        }
        // If cash is 0 or negative, don't include it (let backend handle it)

        return {
          asset: holding.asset,
          qty: holding.qty,
          avg_cost: holding.avg_cost,
          anchor_price: holding.anchor_price,
          cash: cash && cash > 0 ? cash : undefined, // Only include if positive
        };
      });

      // Create portfolio via API with cash, positions, and config in one call
      const result = await portfolioApi.create(selectedTenantId, {
        name: formData.name,
        description: formData.description || undefined,
        type: formData.portfolioType.toUpperCase(), // LIVE, SIMULATION, SANDBOX
        starting_cash: {
          currency: formData.startingCash.currency,
          amount: formData.startingCash.amount,
        },
        holdings: holdings,
        template: formData.strategyTemplate.toUpperCase(), // DEFAULT, CONSERVATIVE, AGGRESSIVE, CUSTOM
        hours_policy:
          formData.marketHoursPolicy === 'market-open-only' ? 'OPEN_ONLY' : 'OPEN_PLUS_AFTER_HOURS',
      });

      const portfolioId = result.portfolio_id;

      // Reset form
      setFormData({
        name: '',
        description: '',
        portfolioType: 'live',
        startingCash: {
          currency: 'USD',
          amount: 100000,
        },
        holdings: [],
        strategyTemplate: 'default',
        marketHoursPolicy: 'market-open-only',
      });
      setStep(1);
      onClose();

      // Refresh portfolios list and set the new portfolio as selected
      await refreshPortfolios();
      setSelectedPortfolioId(portfolioId);

      // Redirect to portfolio overview
      if (onComplete) {
        onComplete(portfolioId);
      } else {
        // Navigate to portfolio overview page
        navigate(`/portfolios/${portfolioId}`);
      }
    } catch (err: any) {
      // Handle validation errors from backend (e.g., duplicate name)
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to create portfolio';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const addHolding = () => {
    setFormData({
      ...formData,
      holdings: [...formData.holdings, { symbol: '', qty: 0, inputMode: 'dollar', dollarValue: 0 }],
    });
  };

  const removeHolding = (index: number) => {
    setFormData({
      ...formData,
      holdings: formData.holdings.filter((_, i) => i !== index),
    });
  };

  // Fetch price for a specific holding (called on blur or button click)
  const fetchHoldingPrice = async (index: number) => {
    const holding = formData.holdings[index];
    if (!holding.symbol || !holding.symbol.trim()) {
      return;
    }

    const updated = [...formData.holdings];
    const symbol = holding.symbol.toUpperCase().trim();

    try {
      const priceData = await marketApi.getPrice(symbol);
      updated[index] = {
        ...holding,
        symbol,
        currentPrice: priceData.price,
      };
      // Recalculate qty or dollarValue based on current input mode
      if (holding.inputMode === 'dollar' && holding.dollarValue && priceData.price > 0) {
        updated[index].qty = holding.dollarValue / priceData.price;
      } else if (holding.inputMode === 'qty' && holding.qty && priceData.price > 0) {
        updated[index].dollarValue = holding.qty * priceData.price;
      }
      setFormData({ ...formData, holdings: updated });
    } catch (error) {
      console.error('Failed to fetch price for', symbol, error);
      // Still update symbol even if price fetch fails
      updated[index] = { ...holding, symbol };
      setFormData({ ...formData, holdings: updated });
    }
  };

  const updateHolding = async (
    index: number,
    field: string,
    value: string | number | undefined,
  ) => {
    const updated = [...formData.holdings];
    const holding = updated[index];

    if (field === 'symbol' && typeof value === 'string') {
      // Update symbol immediately WITHOUT fetching price
      // Price will be fetched on blur or button click
      const symbol = value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      updated[index] = { ...holding, symbol };
      setFormData({ ...formData, holdings: updated });
      // Don't fetch price here - it will be fetched on blur
    } else if (field === 'inputMode') {
      // Switch between qty and dollar input mode
      updated[index] = {
        ...holding,
        inputMode: value as 'qty' | 'dollar',
      };
    } else if (field === 'qty' && holding.currentPrice) {
      // User entered quantity - calculate dollar value
      const qty = typeof value === 'number' ? value : 0;
      updated[index] = {
        ...holding,
        qty,
        dollarValue: qty * holding.currentPrice,
      };
    } else if (field === 'dollarValue' && holding.currentPrice) {
      // User entered dollar value - calculate quantity
      const dollarValue = typeof value === 'number' ? value : 0;
      updated[index] = {
        ...holding,
        dollarValue,
        qty: holding.currentPrice > 0 ? dollarValue / holding.currentPrice : 0,
      };
    } else {
      // Other fields (avgCost, anchorPrice)
      updated[index] = { ...holding, [field]: value };
    }

    setFormData({ ...formData, holdings: updated });
  };

  const refreshHoldingPrice = async (index: number) => {
    const holding = formData.holdings[index];
    if (!holding.symbol) return;

    try {
      const priceData = await marketApi.getPrice(holding.symbol);
      const updated = [...formData.holdings];
      updated[index] = {
        ...holding,
        currentPrice: priceData.price,
      };
      // Recalculate based on current input mode
      if (holding.inputMode === 'dollar' && holding.dollarValue && priceData.price > 0) {
        updated[index].qty = holding.dollarValue / priceData.price;
      } else if (holding.inputMode === 'qty' && holding.qty && priceData.price > 0) {
        updated[index].dollarValue = holding.qty * priceData.price;
      }
      setFormData({ ...formData, holdings: updated });
    } catch (error) {
      console.error('Failed to refresh price:', error);
      alert(`Failed to fetch price for ${holding.symbol}`);
    }
  };

  const handleCSVImport = () => {
    // TODO: Implement CSV import
    alert('CSV import coming soon');
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.name.trim().length >= 3;
      case 2:
        return formData.startingCash.amount > 0;
      case 3:
        // Optional step, always can proceed
        return true;
      case 4:
        return true;
      default:
        return false;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">Create Portfolio</h3>
                <p className="text-sm text-gray-500 mt-1">Step {step} of 4</p>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Form */}
              <div className="lg:col-span-2 space-y-6 overflow-x-auto">
                {/* Step 1: Basics */}
                {step === 1 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">Basics</h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Portfolio Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., Blue Chips – Semi Passive"
                          />
                          {formData.name.length > 0 && formData.name.length < 3 && (
                            <p className="text-xs text-red-600 mt-1">
                              Name must be at least 3 characters
                            </p>
                          )}
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Description
                          </label>
                          <textarea
                            value={formData.description}
                            onChange={(e) =>
                              setFormData({ ...formData, description: e.target.value })
                            }
                            rows={3}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Optional description"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Portfolio Type <span className="text-red-500">*</span>
                          </label>
                          <div className="space-y-2">
                            <label className="flex items-start">
                              <input
                                type="radio"
                                name="portfolioType"
                                value="live"
                                checked={formData.portfolioType === 'live'}
                                onChange={(e) =>
                                  setFormData({
                                    ...formData,
                                    portfolioType: e.target.value as PortfolioData['portfolioType'],
                                  })
                                }
                                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                              />
                              <div className="ml-3">
                                <span className="text-sm font-medium text-gray-700">Live</span>
                                <p className="text-xs text-gray-500">(connect to broker later)</p>
                              </div>
                            </label>
                            <label className="flex items-start">
                              <input
                                type="radio"
                                name="portfolioType"
                                value="simulation"
                                checked={formData.portfolioType === 'simulation'}
                                onChange={(e) =>
                                  setFormData({
                                    ...formData,
                                    portfolioType: e.target.value as PortfolioData['portfolioType'],
                                  })
                                }
                                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                              />
                              <div className="ml-3">
                                <span className="text-sm font-medium text-gray-700">
                                  Simulation
                                </span>
                                <p className="text-xs text-gray-500">(historical backtests)</p>
                              </div>
                            </label>
                            <label className="flex items-start">
                              <input
                                type="radio"
                                name="portfolioType"
                                value="sandbox"
                                checked={formData.portfolioType === 'sandbox'}
                                onChange={(e) =>
                                  setFormData({
                                    ...formData,
                                    portfolioType: e.target.value as PortfolioData['portfolioType'],
                                  })
                                }
                                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                              />
                              <div className="ml-3">
                                <span className="text-sm font-medium text-gray-700">Sandbox</span>
                                <p className="text-xs text-gray-500">(paper trading)</p>
                              </div>
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Starting Cash */}
                {step === 2 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">Starting Cash</h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Starting Cash <span className="text-red-500">*</span>
                          </label>
                          <div className="flex gap-2">
                            <select
                              value={formData.startingCash.currency}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  startingCash: {
                                    ...formData.startingCash,
                                    currency: e.target.value,
                                  },
                                })
                              }
                              className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                              <option value="USD">USD</option>
                              <option value="EUR">EUR</option>
                              <option value="GBP">GBP</option>
                            </select>
                            <input
                              type="number"
                              step="0.01"
                              value={formData.startingCash.amount}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  startingCash: {
                                    ...formData.startingCash,
                                    amount: Number(e.target.value),
                                  },
                                })
                              }
                              className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              placeholder="100000.00"
                            />
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            This is the initial liquid balance used for buys and commissions. You
                            can deposit/withdraw later from Positions & Config.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Existing Holdings */}
                {step === 3 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">
                        Existing Holdings (Optional)
                      </h4>
                      <p className="text-sm text-gray-600 mb-4">
                        Use this if you already own shares (live broker) or want the simulation to
                        start with holdings. Leave empty for cash-only portfolios.
                      </p>

                      {formData.holdings.length > 0 && (
                        <div className="overflow-x-auto mb-4 border border-gray-200 rounded-lg">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[120px]">
                                  Symbol*
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[130px]">
                                  Input Mode
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[140px]">
                                  Qty / $ Value*
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[120px]">
                                  Market Price
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[120px]">
                                  Calculated
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[130px]">
                                  Avg Cost (opt)
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[130px]">
                                  Anchor (opt)
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 uppercase min-w-[80px]">
                                  Actions
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {formData.holdings.map((holding, index) => (
                                <tr key={index} className="hover:bg-gray-50">
                                  <td className="px-4 py-3">
                                    <input
                                      type="text"
                                      value={holding.symbol}
                                      onChange={(e) => {
                                        const value = e.target.value
                                          .toUpperCase()
                                          .replace(/[^A-Z0-9]/g, '');
                                        updateHolding(index, 'symbol', value);
                                      }}
                                      onBlur={() => {
                                        // Fetch price when user leaves the input field
                                        if (holding.symbol && holding.symbol.trim()) {
                                          fetchHoldingPrice(index);
                                        }
                                      }}
                                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                      placeholder="AAPL"
                                      autoComplete="off"
                                      maxLength={10}
                                    />
                                  </td>
                                  <td className="px-4 py-3">
                                    <select
                                      value={holding.inputMode}
                                      onChange={(e) =>
                                        updateHolding(index, 'inputMode', e.target.value)
                                      }
                                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                      <option value="qty">Quantity</option>
                                      <option value="dollar">$ Value</option>
                                    </select>
                                  </td>
                                  <td className="px-4 py-3">
                                    {holding.inputMode === 'qty' ? (
                                      <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        value={holding.qty || ''}
                                        onChange={(e) =>
                                          updateHolding(index, 'qty', Number(e.target.value))
                                        }
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        placeholder="100"
                                      />
                                    ) : (
                                      <div className="relative">
                                        <input
                                          type="number"
                                          step="0.01"
                                          min="0"
                                          value={holding.dollarValue || ''}
                                          onChange={(e) =>
                                            updateHolding(
                                              index,
                                              'dollarValue',
                                              Number(e.target.value),
                                            )
                                          }
                                          className="w-full border border-gray-300 rounded-md px-3 py-2 text-base pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                          placeholder="10000"
                                        />
                                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500 font-medium">
                                          $
                                        </span>
                                      </div>
                                    )}
                                  </td>
                                  <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                      {holding.currentPrice ? (
                                        <span className="text-base font-medium text-gray-900">
                                          ${holding.currentPrice.toFixed(2)}
                                        </span>
                                      ) : (
                                        <span className="text-sm text-gray-400">—</span>
                                      )}
                                      {holding.symbol && (
                                        <button
                                          onClick={() => refreshHoldingPrice(index)}
                                          className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-50 transition-colors"
                                          title="Refresh price"
                                        >
                                          <RefreshCw className="h-4 w-4" />
                                        </button>
                                      )}
                                    </div>
                                  </td>
                                  <td className="px-4 py-3 text-sm text-gray-700">
                                    {holding.inputMode === 'qty' && holding.currentPrice ? (
                                      <div className="font-medium">
                                        ${((holding.qty || 0) * holding.currentPrice).toFixed(2)}
                                      </div>
                                    ) : (
                                      <div>{(holding.qty || 0).toFixed(4)} shares</div>
                                    )}
                                  </td>
                                  <td className="px-4 py-3">
                                    <input
                                      type="number"
                                      step="0.01"
                                      min="0"
                                      value={holding.avgCost || ''}
                                      onChange={(e) =>
                                        updateHolding(
                                          index,
                                          'avgCost',
                                          e.target.value ? Number(e.target.value) : undefined,
                                        )
                                      }
                                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                      placeholder="190.00"
                                    />
                                  </td>
                                  <td className="px-4 py-3">
                                    <input
                                      type="number"
                                      step="0.01"
                                      min="0"
                                      value={holding.anchorPrice || ''}
                                      onChange={(e) =>
                                        updateHolding(
                                          index,
                                          'anchorPrice',
                                          e.target.value ? Number(e.target.value) : undefined,
                                        )
                                      }
                                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                      placeholder="(auto)"
                                    />
                                  </td>
                                  <td className="px-4 py-3">
                                    <button
                                      onClick={() => removeHolding(index)}
                                      className="text-red-600 hover:text-red-800 p-2 rounded hover:bg-red-50 transition-colors"
                                      title="Remove holding"
                                    >
                                      <Trash2 className="h-5 w-5" />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      <div className="flex gap-2">
                        <button
                          onClick={addHolding}
                          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                        >
                          + Add Row
                        </button>
                        <button
                          onClick={handleCSVImport}
                          className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 flex items-center gap-2"
                        >
                          <Upload className="h-4 w-4" />
                          Import CSV
                        </button>
                      </div>

                      <p className="text-xs text-gray-500 mt-2">
                        <strong>Anchor rule (default):</strong> If Anchor provided: use it. Else if
                        Avg Cost provided: anchor = avg cost. Else anchor = first known market
                        price.
                      </p>
                    </div>
                  </div>
                )}

                {/* Step 4: Strategy Configuration */}
                {step === 4 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">
                        Strategy Configuration
                      </h4>
                      {!currentTemplate && (
                        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-md p-3">
                          <p className="text-sm text-yellow-800">
                            Warning: Template configuration not found. Using default settings.
                          </p>
                        </div>
                      )}
                      <div className="space-y-3">
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="default"
                            checked={formData.strategyTemplate === 'default'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Default</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.default.description}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="conservative"
                            checked={formData.strategyTemplate === 'conservative'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Conservative</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.conservative.description}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="aggressive"
                            checked={formData.strategyTemplate === 'aggressive'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Aggressive</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.aggressive.description}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="custom"
                            checked={formData.strategyTemplate === 'custom'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Custom</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.custom.description}
                            </p>
                          </div>
                        </label>
                      </div>

                      <div className="mt-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Market Hours Policy
                        </label>
                        <div className="space-y-2">
                          <label className="flex items-center">
                            <input
                              type="radio"
                              name="marketHoursPolicy"
                              value="market-open-only"
                              checked={formData.marketHoursPolicy === 'market-open-only'}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  marketHoursPolicy: e.target
                                    .value as PortfolioData['marketHoursPolicy'],
                                })
                              }
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <span className="ml-2 text-sm text-gray-700">Market open only</span>
                          </label>
                          <label className="flex items-center">
                            <input
                              type="radio"
                              name="marketHoursPolicy"
                              value="allow-after-hours"
                              checked={formData.marketHoursPolicy === 'allow-after-hours'}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  marketHoursPolicy: e.target
                                    .value as PortfolioData['marketHoursPolicy'],
                                })
                              }
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <span className="ml-2 text-sm text-gray-700">Allow after-hours</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column - Helper/Preview */}
              <div className="lg:col-span-1">
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  {step === 1 && (
                    <div className="space-y-3">
                      <h5 className="text-sm font-semibold text-gray-900">What is a Portfolio?</h5>
                      <ul className="text-xs text-gray-600 space-y-2">
                        <li>• A portfolio belongs to a Tenant and holds cash + positions.</li>
                        <li>
                          • It also has a strategy configuration (triggers, guardrails,
                          commissions).
                        </li>
                      </ul>
                      <div className="mt-4">
                        <h6 className="text-xs font-semibold text-gray-900 mb-2">Type guide:</h6>
                        <ul className="text-xs text-gray-600 space-y-1">
                          <li>
                            <strong>Live:</strong> Use for real-time trading cycles (engine runs in
                            backend).
                          </li>
                          <li>
                            <strong>Simulation:</strong> Use for backtesting on historical data.
                          </li>
                          <li>
                            <strong>Sandbox:</strong> Like live, but no real broker execution.
                          </li>
                        </ul>
                      </div>
                    </div>
                  )}

                  {step === 2 && (
                    <div className="space-y-3">
                      <h5 className="text-sm font-semibold text-gray-900">Initial State Preview</h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Cash:</span>
                          <span className="font-medium text-gray-900">
                            {formData.startingCash.currency}{' '}
                            {formData.startingCash.amount.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Positions:</span>
                          <span className="font-medium text-gray-900">
                            {formData.holdings.length === 0
                              ? 'none'
                              : `${formData.holdings.length}`}
                          </span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span className="text-gray-600 font-medium">Total Value:</span>
                          <span className="font-bold text-gray-900">
                            {formData.startingCash.currency}{' '}
                            {totalValue.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {step === 3 && (
                    <div className="space-y-3">
                      <h5 className="text-sm font-semibold text-gray-900">
                        What are Existing Holdings?
                      </h5>
                      <ul className="text-xs text-gray-600 space-y-2">
                        <li>• Your portfolio's initial shares per asset.</li>
                        <li>
                          • Useful for mirroring a broker account or starting simulations
                          realistically.
                        </li>
                      </ul>
                      <div className="mt-4">
                        <h6 className="text-xs font-semibold text-gray-900 mb-2">
                          Validation tips:
                        </h6>
                        <ul className="text-xs text-gray-600 space-y-1">
                          <li>• Qty must be &gt; 0</li>
                          <li>• Symbol must be valid</li>
                          <li>• Avg cost optional but recommended (P&L accuracy)</li>
                        </ul>
                      </div>
                    </div>
                  )}

                  {step === 4 && currentTemplate && (
                    <div className="space-y-4">
                      <h5 className="text-sm font-semibold text-gray-900">
                        Effective Config Preview
                      </h5>
                      <div className="space-y-3 text-xs">
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Trigger thresholds</h6>
                          <div className="space-y-1 text-gray-600">
                            <div>
                              Up: {currentTemplate.triggerUp > 0 ? '+' : ''}
                              {currentTemplate.triggerUp}%
                            </div>
                            <div>Down: {currentTemplate.triggerDown}%</div>
                          </div>
                        </div>
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Guardrails</h6>
                          <div className="space-y-1 text-gray-600">
                            <div>Min stock %: {currentTemplate.minStockPct}%</div>
                            <div>Max stock %: {currentTemplate.maxStockPct}%</div>
                            <div>
                              Max trade % of position: {currentTemplate.maxTradePctOfPosition}%
                            </div>
                          </div>
                        </div>
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Commission</h6>
                          <div className="text-gray-600">
                            Base rate: {currentTemplate.commission}%
                          </div>
                        </div>
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Market Hours Policy</h6>
                          <div className="text-gray-600">
                            {formData.marketHoursPolicy === 'market-open-only'
                              ? 'Market open only'
                              : 'Allow after-hours'}
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-3 pt-3 border-t">
                          Note: You can edit these later in Positions & Config.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="mt-6 flex items-center justify-between border-t pt-4">
              <div>
                {step > 1 && (
                  <button
                    onClick={handleBack}
                    disabled={loading}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    ← Back
                  </button>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={onClose}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                {step < 4 ? (
                  <button
                    onClick={handleNext}
                    disabled={!canProceed() || loading}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next →
                  </button>
                ) : (
                  <button
                    onClick={handleSubmit}
                    disabled={loading || !canProceed()}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Creating...' : 'Create Portfolio'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
