import React, { useState } from 'react';
import { Plus, Edit, Settings, Eye, EyeOff, Download, X, Archive } from 'lucide-react';
import toast from 'react-hot-toast';
import { usePortfolio, Position } from '../contexts/PortfolioContext';
import { marketApi } from '../lib/api';

const PortfolioManagement: React.FC = () => {
  const {
    positions,
    loading,
    error,
    addPosition,
    updatePosition,
    archivePosition,
    getActivePositions,
    getArchivedPositions,
    clearError,
  } = usePortfolio();
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingPosition, setEditingPosition] = useState<Position | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedPositionForConfig, setSelectedPositionForConfig] = useState<Position | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [newPosition, setNewPosition] = useState({
    ticker: '',
    name: '',
    cashAmount: 5000, // Default $5000 cash
    assetAmount: 0,
    units: 0,
    dollarValue: 0,
    currentPrice: 0,
    inputMode: 'dollar' as 'qty' | 'dollar', // 'qty' or 'dollar'
    // Trade configuration defaults as per your spec
    buyTrigger: -0.03, // -3%
    sellTrigger: 0.03, // +3%
    lowGuardrail: 0.25, // 25%
    highGuardrail: 0.75, // 75%
    rebalanceRatio: 1.66667,
    minQuantity: 1,
    commission: 0.0001, // 0.0001%
    dividendTax: 0.25, // 25%
    tradeAfterHours: true,
  });

  // Mock company name lookup - in real app, this would call an API
  const getCompanyName = (ticker: string): string => {
    const companyNames: { [key: string]: string } = {
      // Major Tech Stocks
      AAPL: 'Apple Inc.',
      MSFT: 'Microsoft Corporation',
      GOOGL: 'Alphabet Inc.',
      AMZN: 'Amazon.com Inc.',
      TSLA: 'Tesla Inc.',
      META: 'Meta Platforms Inc.',
      NVDA: 'NVIDIA Corporation',
      NFLX: 'Netflix Inc.',
      ADBE: 'Adobe Inc.',
      CRM: 'Salesforce Inc.',

      // Financial Stocks
      JPM: 'JPMorgan Chase & Co.',
      BAC: 'Bank of America Corp.',
      WFC: 'Wells Fargo & Co.',
      GS: 'Goldman Sachs Group Inc.',
      C: 'Citigroup Inc.',

      // Healthcare & Biotech
      JNJ: 'Johnson & Johnson',
      PFE: 'Pfizer Inc.',
      UNH: 'UnitedHealth Group Inc.',
      ABBV: 'AbbVie Inc.',
      MRK: 'Merck & Co. Inc.',

      // Consumer & Retail
      WMT: 'Walmart Inc.',
      PG: 'Procter & Gamble Co.',
      KO: 'The Coca-Cola Company',
      PEP: 'PepsiCo Inc.',
      MCD: "McDonald's Corporation",

      // Industrial & Energy
      BA: 'The Boeing Company',
      CAT: 'Caterpillar Inc.',
      XOM: 'Exxon Mobil Corporation',
      CVX: 'Chevron Corporation',
      COP: 'ConocoPhillips',

      // Shipping & Transportation
      ZIM: 'ZIM Integrated Shipping Services Ltd.',
      FDX: 'FedEx Corporation',
      UPS: 'United Parcel Service Inc.',

      // ETFs
      SPY: 'SPDR S&P 500 ETF Trust',
      QQQ: 'Invesco QQQ Trust',
      IWM: 'iShares Russell 2000 ETF',
      VTI: 'Vanguard Total Stock Market ETF',
      VOO: 'Vanguard S&P 500 ETF',
      ARKK: 'ARK Innovation ETF',
      TQQQ: 'ProShares UltraPro QQQ',
      SQQQ: 'ProShares UltraPro Short QQQ',
      UPRO: 'ProShares UltraPro S&P 500',
      SPXU: 'ProShares UltraPro Short S&P 500',
      TMF: 'Direxion Daily 20+ Year Treasury Bull 3X Shares',
      TBT: 'ProShares UltraShort 20+ Year Treasury',
    };
    return companyNames[ticker.toUpperCase()] || `${ticker.toUpperCase()} Corporation`;
  };

  // Get current positions to display
  const currentPositions = showArchived ? getArchivedPositions() : getActivePositions();

  const handleAddPosition = async () => {
    // Validate required fields
    if (!newPosition.ticker) {
      toast.error('Please enter a ticker symbol');
      return;
    }

    if (newPosition.cashAmount <= 0) {
      toast.error('Please enter a cash amount');
      return;
    }

    if (
      (newPosition.inputMode === 'dollar' && newPosition.dollarValue <= 0) ||
      (newPosition.inputMode === 'qty' && newPosition.units <= 0)
    ) {
      toast.error(
        `Please enter ${
          newPosition.inputMode === 'dollar' ? 'a dollar value' : 'a quantity'
        } for the asset`,
      );
      return;
    }

    try {
      // Calculate values based on input mode
      const cashAmount = newPosition.cashAmount;
      const assetAmount = newPosition.assetAmount;

      // Fetch current market price for the ticker
      let currentPrice = 0;
      try {
        const priceData = await marketApi.getPrice(newPosition.ticker.toUpperCase());
        currentPrice = priceData.price;
        console.log(`Fetched market price for ${newPosition.ticker}: $${currentPrice}`);
      } catch (error) {
        console.error(`Failed to fetch market price for ${newPosition.ticker}:`, error);
        // Fallback to editing position's price or show error
        if (editingPosition?.currentPrice) {
          currentPrice = editingPosition.currentPrice;
          console.warn(`Using existing position price: $${currentPrice}`);
        } else {
          toast.error(
            `Failed to fetch market price for ${newPosition.ticker}. Please check the ticker symbol and try again.`,
          );
          return;
        }
      }

      // Calculate units and price based on input mode
      let units = 0;
      let finalAssetAmount = 0;

      if (newPosition.inputMode === 'dollar' && newPosition.dollarValue > 0) {
        // User entered dollar value - calculate quantity
        if (currentPrice > 0) {
          units = newPosition.dollarValue / currentPrice;
          finalAssetAmount = newPosition.dollarValue;
        } else {
          toast.error('Market price not available. Please ensure ticker is valid.');
          return;
        }
      } else if (newPosition.inputMode === 'qty' && newPosition.units > 0) {
        // User entered quantity - calculate dollar value
        units = newPosition.units;
        if (currentPrice > 0) {
          finalAssetAmount = units * currentPrice;
        } else {
          toast.error('Market price not available. Please ensure ticker is valid.');
          return;
        }
      } else {
        toast.error(
          `Please enter ${
            newPosition.inputMode === 'dollar' ? 'a dollar value' : 'a quantity'
          } for the asset`,
        );
        return;
      }

      if (editingPosition) {
        // Update existing position
        const updatedPosition: Position = {
          ...editingPosition,
          ticker: newPosition.ticker.toUpperCase(),
          name: newPosition.name,
          cashAmount,
          assetAmount: finalAssetAmount,
          units,
          currentPrice,
          anchorPrice: currentPrice,
          marketValue: finalAssetAmount,
          config: {
            buyTrigger: newPosition.buyTrigger,
            sellTrigger: newPosition.sellTrigger,
            lowGuardrail: newPosition.lowGuardrail,
            highGuardrail: newPosition.highGuardrail,
            rebalanceRatio: newPosition.rebalanceRatio,
            minQuantity: newPosition.minQuantity,
            commission: newPosition.commission,
            dividendTax: newPosition.dividendTax,
            tradeAfterHours: newPosition.tradeAfterHours,
          },
        };
        await handleUpdatePosition(updatedPosition);
      } else {
        // Add new position
        const positionData = {
          ticker: newPosition.ticker.toUpperCase(),
          name: newPosition.name,
          cashAmount,
          assetAmount: finalAssetAmount,
          units,
          currentPrice,
          anchorPrice: currentPrice,
          marketValue: finalAssetAmount,
          pnl: 0,
          pnlPercent: 0,
          isActive: true,
          isArchived: false,
          lastTrade: new Date().toLocaleString(),
          config: {
            buyTrigger: newPosition.buyTrigger,
            sellTrigger: newPosition.sellTrigger,
            lowGuardrail: newPosition.lowGuardrail,
            highGuardrail: newPosition.highGuardrail,
            rebalanceRatio: newPosition.rebalanceRatio,
            minQuantity: newPosition.minQuantity,
            commission: newPosition.commission,
            dividendTax: newPosition.dividendTax,
            tradeAfterHours: newPosition.tradeAfterHours,
          },
        };
        await addPosition(positionData);
      }
      setNewPosition({
        ticker: '',
        name: '',
        cashAmount: 5000, // Default $5000 cash
        assetAmount: 0,
        units: 0,
        dollarValue: 0,
        currentPrice: 0,
        inputMode: 'dollar',
        buyTrigger: -0.03,
        sellTrigger: 0.03,
        lowGuardrail: 0.25,
        highGuardrail: 0.75,
        rebalanceRatio: 1.66667,
        minQuantity: 1,
        commission: 0.0001,
        dividendTax: 0.25,
        tradeAfterHours: true,
      });
      setShowAddForm(false);
      setEditingPosition(null);
    } catch (err) {
      console.error('Failed to add position:', err);
      // Error is already handled by the context
    }
  };

  const handleEditPosition = async (position: Position) => {
    setEditingPosition(position);

    // Fetch current market price
    let currentPrice = position.currentPrice;
    try {
      const priceData = await marketApi.getPrice(position.ticker);
      currentPrice = priceData.price;
    } catch (error) {
      console.error(`Failed to fetch market price for ${position.ticker}:`, error);
      // Use existing price if fetch fails
    }

    setNewPosition({
      ticker: position.ticker,
      name: position.name,
      cashAmount: position.cashAmount,
      assetAmount: position.assetAmount,
      units: position.units,
      dollarValue: position.assetAmount,
      currentPrice,
      inputMode: 'dollar' as 'qty' | 'dollar', // Default to dollar mode for editing
      buyTrigger: position.config.buyTrigger,
      sellTrigger: position.config.sellTrigger,
      lowGuardrail: position.config.lowGuardrail,
      highGuardrail: position.config.highGuardrail,
      rebalanceRatio: position.config.rebalanceRatio,
      minQuantity: position.config.minQuantity,
      commission: position.config.commission,
      dividendTax: position.config.dividendTax,
      tradeAfterHours: position.config.tradeAfterHours,
    });
    setShowAddForm(true);
  };

  const handleUpdatePosition = async (updatedPosition: Position) => {
    try {
      await updatePosition(updatedPosition.id, updatedPosition);
      setEditingPosition(null);
      setShowAddForm(false);
    } catch (error) {
      console.error('Failed to update position:', error);
    }
  };

  const handleDeletePosition = async (id: string) => {
    try {
      await archivePosition(id);
    } catch (err) {
      console.error('Failed to archive position:', err);
    }
  };

  const handleToggleActive = async (id: string) => {
    try {
      const position = positions.find((p) => p.id === id);
      if (position) {
        await updatePosition(id, { isActive: !position.isActive });
      }
    } catch (err) {
      console.error('Failed to toggle position:', err);
    }
  };

  const handleConfigPosition = (position: Position) => {
    setSelectedPositionForConfig(position);
    setShowConfigModal(true);
  };

  const handleExportPortfolio = () => {
    // Export portfolio data as Excel via backend API
    window.open(`/api/excel/positions/export?format=xlsx`, '_blank');
  };

  const totalValue = currentPositions.reduce((sum, p) => sum + p.marketValue, 0);
  const totalPnl = currentPositions.reduce((sum, p) => sum + p.pnl, 0);
  const totalPnlPercent = totalValue > 0 ? (totalPnl / (totalValue - totalPnl)) * 100 : 0;

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Portfolio Management</h1>
        <p className="text-gray-600">Create and manage your trading positions and configurations</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <X className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={clearError}
                  className="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-sm text-blue-800">Loading positions...</span>
          </div>
        </div>
      )}

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Value</h3>
          <p className="text-2xl font-bold text-gray-900">${totalValue.toLocaleString()}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
          <p className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${totalPnl.toLocaleString()}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Return</h3>
          <p
            className={`text-2xl font-bold ${
              totalPnlPercent >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {totalPnlPercent.toFixed(2)}%
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Active Positions</h3>
          <p className="text-2xl font-bold text-gray-900">{getActivePositions().length}</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Add Position
        </button>
        <button
          onClick={handleExportPortfolio}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
        >
          <Download className="h-5 w-5" />
          Export Portfolio
        </button>
        <button
          onClick={() => setShowArchived(!showArchived)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
            showArchived
              ? 'bg-gray-600 text-white hover:bg-gray-700'
              : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
          }`}
        >
          <Archive className="h-5 w-5" />
          {showArchived ? 'Show Active' : 'Show Archived'}
        </button>
      </div>

      {/* Add Position Form */}
      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingPosition ? `Edit ${editingPosition.ticker} Position` : 'Add New Position'}
          </h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAddPosition();
            }}
          >
            {/* Basic Position Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ticker Symbol
                </label>
                <input
                  type="text"
                  value={newPosition.ticker}
                  onChange={async (e) => {
                    const ticker = e.target.value.toUpperCase();
                    const companyName = getCompanyName(ticker);
                    let currentPrice = 0;

                    // Fetch market price when ticker changes
                    if (ticker) {
                      try {
                        const priceData = await marketApi.getPrice(ticker);
                        currentPrice = priceData.price;
                      } catch (error) {
                        console.error(`Failed to fetch market price for ${ticker}:`, error);
                        // Continue without price - user can still enter values
                      }
                    }

                    setNewPosition({
                      ...newPosition,
                      ticker: ticker,
                      name: companyName,
                      currentPrice,
                    });
                  }}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., AAPL, MSFT, ZIM"
                />
                {newPosition.ticker && (
                  <p className="text-xs text-green-600 mt-1">✓ Company name auto-populated</p>
                )}
                {!newPosition.ticker && (
                  <p className="text-xs text-gray-500 mt-1">
                    Try: AAPL, MSFT, GOOGL, AMZN, TSLA, ZIM, SPY, QQQ
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                <input
                  type="text"
                  value={newPosition.name}
                  readOnly
                  className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-700"
                  placeholder="Auto-populated from ticker"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {newPosition.ticker
                    ? `Automatically derived from ${newPosition.ticker}`
                    : 'Enter a ticker symbol above'}
                </p>
              </div>
            </div>

            {/* Asset Input Mode */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Asset Input Mode
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="assetInputMode"
                    value="dollar"
                    checked={newPosition.inputMode === 'dollar'}
                    onChange={(e) =>
                      setNewPosition({
                        ...newPosition,
                        inputMode: e.target.value as 'qty' | 'dollar',
                      })
                    }
                    className="mr-2"
                  />
                  Dollar Value ($)
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="assetInputMode"
                    value="qty"
                    checked={newPosition.inputMode === 'qty'}
                    onChange={(e) =>
                      setNewPosition({
                        ...newPosition,
                        inputMode: e.target.value as 'qty' | 'dollar',
                      })
                    }
                    className="mr-2"
                  />
                  Quantity (shares)
                </label>
              </div>
            </div>

            {/* Cash Amount */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cash Amount ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={newPosition.cashAmount === 0 ? '' : newPosition.cashAmount}
                onChange={(e) =>
                  setNewPosition({
                    ...newPosition,
                    cashAmount: e.target.value === '' ? 0 : Number(e.target.value),
                  })
                }
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="5000"
              />
              <p className="text-xs text-gray-500 mt-1">Initial cash balance for this position</p>
            </div>

            {/* Asset Value/Quantity Input */}
            {newPosition.ticker && newPosition.currentPrice > 0 && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900">Current Market Price</span>
                  <span className="text-lg font-bold text-blue-600">
                    ${newPosition.currentPrice.toFixed(2)}
                  </span>
                </div>
                {newPosition.inputMode === 'dollar' && newPosition.dollarValue > 0 && (
                  <div className="text-xs text-blue-700 mt-1">
                    Calculated quantity:{' '}
                    {(newPosition.dollarValue / newPosition.currentPrice).toFixed(4)} shares
                  </div>
                )}
                {newPosition.inputMode === 'qty' && newPosition.units > 0 && (
                  <div className="text-xs text-blue-700 mt-1">
                    Calculated value: ${(newPosition.units * newPosition.currentPrice).toFixed(2)}
                  </div>
                )}
              </div>
            )}

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {newPosition.inputMode === 'dollar' ? 'Asset Value ($)' : 'Quantity (shares)'}
              </label>
              {newPosition.inputMode === 'dollar' ? (
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    value={newPosition.dollarValue === 0 ? '' : newPosition.dollarValue}
                    onChange={(e) => {
                      const dollarValue = e.target.value === '' ? 0 : Number(e.target.value);
                      const units =
                        newPosition.currentPrice > 0 ? dollarValue / newPosition.currentPrice : 0;
                      setNewPosition({
                        ...newPosition,
                        dollarValue,
                        units,
                        assetAmount: dollarValue,
                      });
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 pl-8"
                    placeholder="10000"
                  />
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                </div>
              ) : (
                <input
                  type="number"
                  step="0.01"
                  value={newPosition.units === 0 ? '' : newPosition.units}
                  onChange={(e) => {
                    const units = e.target.value === '' ? 0 : Number(e.target.value);
                    const dollarValue =
                      newPosition.currentPrice > 0 ? units * newPosition.currentPrice : 0;
                    setNewPosition({
                      ...newPosition,
                      units,
                      dollarValue,
                      assetAmount: dollarValue,
                    });
                  }}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="100"
                />
              )}
              <p className="text-xs text-gray-500 mt-1">
                {newPosition.inputMode === 'dollar'
                  ? 'Enter the dollar value - quantity will be calculated automatically'
                  : 'Enter the number of shares - dollar value will be calculated automatically'}
              </p>
            </div>

            {/* Trade Configuration */}
            <div className="border-t pt-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4">
                Trade Configuration (Defaults)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Buy Trigger (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newPosition.buyTrigger * 100}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, buyTrigger: Number(e.target.value) / 100 })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="-3"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sell Trigger (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newPosition.sellTrigger * 100}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, sellTrigger: Number(e.target.value) / 100 })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="3"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Low Guardrail (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newPosition.lowGuardrail * 100}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, lowGuardrail: Number(e.target.value) / 100 })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    High Guardrail (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newPosition.highGuardrail * 100}
                    onChange={(e) =>
                      setNewPosition({
                        ...newPosition,
                        highGuardrail: Number(e.target.value) / 100,
                      })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="75"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rebalance Ratio
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={newPosition.rebalanceRatio}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, rebalanceRatio: Number(e.target.value) })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="1.66667"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Min Quantity
                  </label>
                  <input
                    type="number"
                    value={newPosition.minQuantity}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, minQuantity: Number(e.target.value) })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Commission (%)
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={newPosition.commission * 100}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, commission: Number(e.target.value) / 100 })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="0.0001"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dividend Tax (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newPosition.dividendTax * 100}
                    onChange={(e) =>
                      setNewPosition({ ...newPosition, dividendTax: Number(e.target.value) / 100 })
                    }
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="25"
                  />
                </div>
                <div className="flex items-center">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newPosition.tradeAfterHours}
                      onChange={(e) =>
                        setNewPosition({ ...newPosition, tradeAfterHours: e.target.checked })
                      }
                      className="mr-2"
                    />
                    Trade After Hours
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                {editingPosition ? 'Update Position' : 'Add Position'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">
            {showArchived ? 'Archived Positions' : 'Active Positions'}
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Position
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cash/Asset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Units
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Value
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
              {currentPositions.map((position) => (
                <tr key={position.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{position.ticker}</div>
                      <div className="text-sm text-gray-500">{position.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>Cash: ${position.cashAmount.toLocaleString()}</div>
                    <div>Asset: ${position.assetAmount.toLocaleString()}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {position.units.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${position.currentPrice.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${position.marketValue.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div
                      className={`text-sm ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}
                    >
                      ${position.pnl.toLocaleString()} ({position.pnlPercent.toFixed(2)}%)
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        position.isActive
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {position.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleConfigPosition(position)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Configure"
                      >
                        <Settings className="h-4 w-4" />
                      </button>
                      {!showArchived && (
                        <>
                          <button
                            onClick={() => handleToggleActive(position.id)}
                            className="text-gray-400 hover:text-gray-600"
                            title={position.isActive ? 'Deactivate' : 'Activate'}
                          >
                            {position.isActive ? (
                              <EyeOff className="h-4 w-4" />
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </button>
                          <button
                            onClick={() => handleEditPosition(position)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeletePosition(position.id)}
                            className="text-orange-600 hover:text-orange-900"
                            title="Archive"
                          >
                            <Archive className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {showArchived && (
                        <button
                          onClick={() =>
                            updatePosition(position.id, { isArchived: false, isActive: true })
                          }
                          className="text-green-600 hover:text-green-900"
                          title="Restore"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

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

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Buy Trigger (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={selectedPositionForConfig.config.buyTrigger * 100}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          buyTrigger: Number(e.target.value) / 100,
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sell Trigger (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={selectedPositionForConfig.config.sellTrigger * 100}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          sellTrigger: Number(e.target.value) / 100,
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Low Guardrail (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={selectedPositionForConfig.config.lowGuardrail * 100}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          lowGuardrail: Number(e.target.value) / 100,
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    High Guardrail (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={selectedPositionForConfig.config.highGuardrail * 100}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          highGuardrail: Number(e.target.value) / 100,
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rebalance Ratio
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={selectedPositionForConfig.config.rebalanceRatio}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          rebalanceRatio: Number(e.target.value),
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Min Quantity
                  </label>
                  <input
                    type="number"
                    value={selectedPositionForConfig.config.minQuantity}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          minQuantity: Number(e.target.value),
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Commission (%)
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={selectedPositionForConfig.config.commission * 100}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          commission: Number(e.target.value) / 100,
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dividend Tax (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={selectedPositionForConfig.config.dividendTax * 100}
                    onChange={(e) => {
                      const updatedPosition = {
                        ...selectedPositionForConfig,
                        config: {
                          ...selectedPositionForConfig.config,
                          dividendTax: Number(e.target.value) / 100,
                        },
                      };
                      setSelectedPositionForConfig(updatedPosition);
                    }}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div className="flex items-center">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedPositionForConfig.config.tradeAfterHours}
                      onChange={(e) => {
                        const updatedPosition = {
                          ...selectedPositionForConfig,
                          config: {
                            ...selectedPositionForConfig.config,
                            tradeAfterHours: e.target.checked,
                          },
                        };
                        setSelectedPositionForConfig(updatedPosition);
                      }}
                      className="mr-2"
                    />
                    Trade After Hours
                  </label>
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => {
                    updatePosition(selectedPositionForConfig.id, selectedPositionForConfig);
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

export default PortfolioManagement;
