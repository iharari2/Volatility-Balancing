import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { ArrowLeft, Target, Settings, DollarSign, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { usePosition, useSetAnchorPrice, usePositionEvents } from '../hooks/usePositions';
import { useMarketPrice } from '../hooks/useMarketData';
import TradingInterface from '../components/TradingInterface';
import EventTimeline from '../components/EventTimeline';
import DividendManagement from '../components/DividendManagement';
import TradingConfigPanel from '../components/TradingConfigPanel';
import { useConfiguration } from '../contexts/ConfigurationContext';

export default function PositionDetail() {
  const { id } = useParams<{ id: string }>();
  const [showAnchorForm, setShowAnchorForm] = useState(false);
  const [anchorPrice, setAnchorPrice] = useState<number>(0);
  const { configuration } = useConfiguration();
  const [activeTab, setActiveTab] = useState<'trading' | 'dividends' | 'config'>('trading');

  const { data: position, isLoading: positionLoading } = usePosition(id!);
  const { data: events, isLoading: eventsLoading } = usePositionEvents(id!);
  const setAnchorPriceMutation = useSetAnchorPrice(id!);

  // Fetch current market price for the position's ticker
  const {
    data: marketData,
    isLoading: priceLoading,
    error: priceError,
    refetch: refetchPrice,
  } = useMarketPrice(position?.ticker || '');

  const handleSetAnchor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!anchorPrice) return;

    try {
      await setAnchorPriceMutation.mutateAsync(anchorPrice);
      setShowAnchorForm(false);
      setAnchorPrice(0);
    } catch (error) {
      console.error('Failed to set anchor price:', error);
    }
  };

  const handleSetCurrentPrice = () => {
    if (marketData?.price) {
      setAnchorPrice(marketData.price);
    }
  };

  if (positionLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="card">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="space-y-2">
              <div className="h-3 bg-gray-200 rounded"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!position) {
    return (
      <div className="space-y-6">
        <Link
          to="/positions"
          className="inline-flex items-center text-primary-600 hover:text-primary-700"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Positions
        </Link>
        <div className="card text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Position Not Found</h3>
          <p className="text-gray-500">
            The position you're looking for doesn't exist or has been deleted.
          </p>
        </div>
      </div>
    );
  }

  const totalValue =
    position.qty * (position.anchor_price || 0) +
    position.cash +
    (position.dividend_receivable || 0);
  const assetPercentage = position.anchor_price
    ? ((position.qty * position.anchor_price) / totalValue) * 100
    : 0;

  const tabs = [
    { id: 'trading', label: 'Trading', icon: Target },
    { id: 'dividends', label: 'Dividends', icon: DollarSign },
    { id: 'config', label: 'Config', icon: Settings },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/positions"
            className="inline-flex items-center text-primary-600 hover:text-primary-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Positions
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{position.ticker}</h1>
            <p className="text-gray-600">Position #{position.id.slice(-8)}</p>
          </div>
        </div>

        <div className="flex space-x-3">
          {!position.anchor_price && (
            <button onClick={() => setShowAnchorForm(true)} className="btn btn-warning">
              <Target className="w-4 h-4 mr-2" />
              Set Anchor Price
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Position Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Position Stats */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-gray-500">Shares</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {position.qty.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Cash</p>
                <p className="text-2xl font-semibold text-gray-900">
                  ${position.cash.toLocaleString()}
                </p>
                {position.dividend_receivable && position.dividend_receivable > 0 && (
                  <p className="text-xs text-primary-600">
                    +${position.dividend_receivable.toFixed(2)} receivable
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-500">Anchor Price</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {position.anchor_price ? `$${position.anchor_price.toFixed(2)}` : 'Not set'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Value</p>
                <p className="text-2xl font-semibold text-gray-900">
                  ${totalValue.toLocaleString()}
                </p>
              </div>
            </div>

            {position.anchor_price && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Asset Allocation</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {assetPercentage.toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Buy Trigger</p>
                    <p className="text-lg font-semibold text-success-600">
                      ${(position.anchor_price * 0.97).toFixed(2)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Sell Trigger</p>
                    <p className="text-lg font-semibold text-danger-600">
                      ${(position.anchor_price * 1.03).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tab Content */}
          {activeTab === 'trading' && (
            <>
              {position.anchor_price ? (
                <TradingInterface position={position} />
              ) : (
                <div className="card text-center py-12">
                  <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Anchor Price Required</h3>
                  <p className="text-gray-500 mb-4">
                    Set an anchor price to enable volatility trading for this position.
                  </p>
                  <button onClick={() => setShowAnchorForm(true)} className="btn btn-primary">
                    <Target className="w-4 h-4 mr-2" />
                    Set Anchor Price
                  </button>
                </div>
              )}
            </>
          )}

          {activeTab === 'dividends' && (
            <DividendManagement positionId={position.id} ticker={position.ticker} />
          )}

          {activeTab === 'config' && (
            <TradingConfigPanel
              orderPolicy={
                position.order_policy || {
                  min_qty: 0,
                  min_notional: configuration.minNotional,
                  lot_size: 0,
                  qty_step: 0,
                  action_below_min: 'hold',
                  trigger_threshold_pct: configuration.triggerThresholdPct,
                  rebalance_ratio: configuration.rebalanceRatio,
                  commission_rate: configuration.commissionRate,
                  allow_after_hours: configuration.allowAfterHours,
                  order_sizing_strategy: 'proportional',
                }
              }
              guardrails={
                position.guardrails || {
                  min_stock_alloc_pct: configuration.guardrails.minStockAllocPct,
                  max_stock_alloc_pct: configuration.guardrails.maxStockAllocPct,
                  max_orders_per_day: 5,
                }
              }
              withholdingTaxRate={position.withholding_tax_rate || 0.25}
              onSave={(config) => {
                // TODO: Implement save configuration
                console.log('Save config:', config);
              }}
              onReset={() => {
                // TODO: Implement reset configuration
                console.log('Reset config');
              }}
            />
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Events Timeline */}
          <EventTimeline events={events?.events || []} />
        </div>
      </div>

      {/* Set Anchor Price Modal */}
      {showAnchorForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setShowAnchorForm(false)}
            />
            <div className="relative bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Set Anchor Price</h3>
              <p className="text-sm text-gray-600 mb-4">
                The anchor price is used as a reference point for volatility calculations. Buy
                triggers occur at 3% below, sell triggers at 3% above.
              </p>

              <form onSubmit={handleSetAnchor} className="space-y-4">
                {/* Current Market Price Info */}
                {marketData && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-blue-900">Current Market Price</h4>
                        <p className="text-2xl font-bold text-blue-900">
                          ${marketData.price.toFixed(2)}
                        </p>
                        <p className="text-sm text-blue-700">
                          {marketData.is_market_hours ? 'Market Open' : 'After Hours'} •
                          {marketData.is_fresh ? ' Live Data' : ' Delayed Data'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={handleSetCurrentPrice}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center space-x-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Use Current Price</span>
                      </button>
                    </div>
                  </div>
                )}

                {priceLoading && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-gray-500" />
                      <p className="text-gray-700">Fetching current market price...</p>
                    </div>
                  </div>
                )}

                {priceError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-700">
                      Unable to fetch current market price. You can still set an anchor price
                      manually.
                    </p>
                    <button
                      type="button"
                      onClick={() => refetchPrice()}
                      className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                    >
                      Try Again
                    </button>
                  </div>
                )}

                <div>
                  <label className="label">Anchor Price</label>
                  <input
                    type="number"
                    value={anchorPrice}
                    onChange={(e) => setAnchorPrice(Number(e.target.value))}
                    className="input"
                    min="0"
                    step="0.01"
                    placeholder="e.g., 150.00"
                    required
                  />
                </div>

                <div className="bg-gray-50 p-3 rounded-lg text-sm">
                  <p className="font-medium text-gray-900 mb-1">Trigger Zones:</p>
                  <p className="text-gray-600">
                    Buy: ≤ ${(anchorPrice * 0.97).toFixed(2)} (3% below)
                  </p>
                  <p className="text-gray-600">
                    Sell: ≥ ${(anchorPrice * 1.03).toFixed(2)} (3% above)
                  </p>
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAnchorForm(false)}
                    className="btn btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={setAnchorPriceMutation.isPending || !anchorPrice}
                    className="btn btn-primary flex-1"
                  >
                    {setAnchorPriceMutation.isPending ? 'Setting...' : 'Set Anchor Price'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
