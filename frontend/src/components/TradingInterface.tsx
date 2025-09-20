import { useState } from 'react';
import { Position } from '../types';
import {
  useEvaluatePosition,
  useAutoSizeOrder,
  useEvaluatePositionWithMarketData,
  useAutoSizeOrderWithMarketData,
} from '../hooks/usePositions';
import { useCreateOrder as useCreateOrderMutation } from '../hooks/useOrders';
import { useMarketPrice } from '../hooks/useMarketData';
import MarketDataStatus from './MarketDataStatus';
import {
  Play,
  Target,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Wifi,
  WifiOff,
} from 'lucide-react';

interface TradingInterfaceProps {
  position: Position;
}

export default function TradingInterface({ position }: TradingInterfaceProps) {
  const [currentPrice, setCurrentPrice] = useState<number>(position.anchor_price || 150);
  const [useMarketData, setUseMarketData] = useState(true);

  // Check if position has anchor price
  const hasAnchorPrice = position.anchor_price !== null && position.anchor_price !== undefined;

  // Market data integration
  const { data: marketPrice } = useMarketPrice(position.ticker);

  // Evaluation with market data
  const { data: marketEvaluation, isLoading: isMarketEvaluating } =
    useEvaluatePositionWithMarketData(position.id);

  // Manual evaluation
  const { data: evaluation, isLoading: isEvaluating } = useEvaluatePosition(
    position.id,
    currentPrice,
  );

  const createOrderMutation = useCreateOrderMutation(position.id);
  const autoSizeMutation = useAutoSizeOrder(position.id);
  const autoSizeMarketMutation = useAutoSizeOrderWithMarketData(position.id);

  // Use market data evaluation if enabled and available
  const activeEvaluation = useMarketData && marketEvaluation ? marketEvaluation : evaluation;
  const isActiveEvaluating = useMarketData ? isMarketEvaluating : isEvaluating;

  const handleEvaluate = () => {
    // The evaluation will automatically trigger when currentPrice changes
  };

  const handleManualOrder = async (side: 'BUY' | 'SELL') => {
    if (!evaluation?.order_proposal) return;

    try {
      await createOrderMutation.mutateAsync({
        data: {
          side,
          qty: evaluation.order_proposal.trimmed_qty,
          price: currentPrice,
        },
        idempotencyKey: `manual-${side}-${Date.now()}`,
      });
    } catch (error) {
      console.error('Failed to create order:', error);
    }
  };

  const handleAutoOrder = async () => {
    try {
      if (useMarketData) {
        await autoSizeMarketMutation.mutateAsync(`auto-market-${Date.now()}`);
      } else {
        await autoSizeMutation.mutateAsync({
          currentPrice,
          idempotencyKey: `auto-${Date.now()}`,
        });
      }
    } catch (error) {
      console.error('Failed to create auto order:', error);
    }
  };

  const getTriggerStatus = () => {
    if (!activeEvaluation) return { status: 'loading', message: 'Evaluating...' };

    if (activeEvaluation.trigger_detected) {
      return {
        status: 'trigger',
        message: `${activeEvaluation.trigger_type} trigger detected`,
        icon: activeEvaluation.trigger_type === 'BUY' ? TrendingUp : TrendingDown,
        color: activeEvaluation.trigger_type === 'BUY' ? 'text-success-600' : 'text-danger-600',
      };
    }

    return {
      status: 'no-trigger',
      message: 'No trigger - price within normal range',
      icon: CheckCircle,
      color: 'text-gray-600',
    };
  };

  const triggerStatus = getTriggerStatus();

  return (
    <div className="space-y-6">
      {/* Market Data Status */}
      <MarketDataStatus ticker={position.ticker} showPrice={true} />

      {/* Anchor Price Warning */}
      {!hasAnchorPrice && (
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">No Anchor Price Set</h3>
              <p className="text-sm text-yellow-700">
                This position doesn't have an anchor price set. Volatility trading requires an
                anchor price to calculate triggers. The current price is set to ${currentPrice} for
                demonstration purposes.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Trading Mode Toggle */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Trading Mode</h3>
            <p className="text-sm text-gray-600">
              {useMarketData
                ? 'Using real-time market data for evaluation'
                : 'Using manual price input for evaluation'}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setUseMarketData(!useMarketData)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                useMarketData ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {useMarketData ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              <span>{useMarketData ? 'Market Data' : 'Manual'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Price Input (only show in manual mode) */}
      {!useMarketData && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Manual Price Evaluation</h3>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="label">Current Price</label>
              <input
                type="number"
                value={currentPrice}
                onChange={(e) => setCurrentPrice(Number(e.target.value))}
                className="input"
                step="0.01"
                min="0"
              />
            </div>
            <button
              onClick={handleEvaluate}
              disabled={isEvaluating}
              className="btn btn-primary self-end"
            >
              <Play className="w-4 h-4 mr-2" />
              {isEvaluating ? 'Evaluating...' : 'Evaluate'}
            </button>
          </div>
        </div>
      )}

      {/* Market Data Info (only show in market data mode) */}
      {useMarketData && marketPrice && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Data</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-gray-500">Current Price</label>
              <p className="text-lg font-semibold">${marketPrice.price.toFixed(2)}</p>
            </div>
            <div>
              <label className="text-xs text-gray-500">Source</label>
              <p className="text-sm font-medium">{marketPrice.source}</p>
            </div>
            <div>
              <label className="text-xs text-gray-500">Fresh</label>
              <p className="text-sm font-medium">{marketPrice.is_fresh ? 'Yes' : 'No'}</p>
            </div>
            <div>
              <label className="text-xs text-gray-500">Market Hours</label>
              <p className="text-sm font-medium">{marketPrice.is_market_hours ? 'Yes' : 'No'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Evaluation Results */}
      {isActiveEvaluating ? (
        <div className="card">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Evaluating position...</span>
          </div>
        </div>
      ) : activeEvaluation ? (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Evaluation Results</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Trigger Status */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                {triggerStatus.icon && (
                  <triggerStatus.icon className={`w-6 h-6 ${triggerStatus.color}`} />
                )}
                <div>
                  <h4 className="font-medium text-gray-900">Trigger Status</h4>
                  <p className={`text-sm ${triggerStatus.color}`}>{triggerStatus.message}</p>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Current Price:</span>
                  <span className="font-medium">
                    ${activeEvaluation?.current_price?.toFixed(2) || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Anchor Price:</span>
                  <span className="font-medium">
                    ${activeEvaluation?.anchor_price?.toFixed(2) || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Price Change:</span>
                  <span
                    className={`font-medium ${
                      (activeEvaluation?.current_price ?? 0) > (activeEvaluation?.anchor_price ?? 0)
                        ? 'text-danger-600'
                        : 'text-success-600'
                    }`}
                  >
                    {activeEvaluation?.current_price && activeEvaluation?.anchor_price ? (
                      <>
                        {(
                          ((activeEvaluation.current_price - activeEvaluation.anchor_price) /
                            activeEvaluation.anchor_price) *
                          100
                        ).toFixed(2)}
                        %
                      </>
                    ) : (
                      'N/A'
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* Order Proposal */}
            {activeEvaluation.order_proposal && (
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Order Proposal</h4>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Side:</span>
                    <span
                      className={`font-medium ${
                        activeEvaluation.order_proposal.side === 'BUY'
                          ? 'text-success-600'
                          : 'text-danger-600'
                      }`}
                    >
                      {activeEvaluation.order_proposal.side}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Quantity:</span>
                    <span className="font-medium">
                      {activeEvaluation.order_proposal.trimmed_qty}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Notional:</span>
                    <span className="font-medium">
                      ${activeEvaluation.order_proposal.notional.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Commission:</span>
                    <span className="font-medium">
                      ${activeEvaluation.order_proposal.commission.toFixed(2)}
                    </span>
                  </div>
                </div>

                {activeEvaluation.order_proposal.validation.valid ? (
                  <div className="flex items-center text-success-600 text-sm">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Order validation passed
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center text-danger-600 text-sm">
                      <XCircle className="w-4 h-4 mr-2" />
                      Order validation failed
                    </div>
                    <ul className="text-xs text-danger-600 space-y-1">
                      {activeEvaluation.order_proposal.validation.rejections.map(
                        (rejection, index) => (
                          <li key={index}>• {rejection}</li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {activeEvaluation.trigger_detected &&
            activeEvaluation.order_proposal?.validation.valid && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleManualOrder(activeEvaluation.order_proposal!.side)}
                      disabled={createOrderMutation.isPending}
                      className={`btn ${
                        activeEvaluation.order_proposal!.side === 'BUY'
                          ? 'btn-success'
                          : 'btn-danger'
                      }`}
                    >
                      {activeEvaluation.order_proposal!.side === 'BUY' ? (
                        <TrendingUp className="w-4 h-4 mr-2" />
                      ) : (
                        <TrendingDown className="w-4 h-4 mr-2" />
                      )}
                      Manual {activeEvaluation.order_proposal!.side}
                    </button>

                    <button
                      onClick={handleAutoOrder}
                      disabled={
                        useMarketData
                          ? autoSizeMarketMutation.isPending
                          : autoSizeMutation.isPending
                      }
                      className="btn btn-primary"
                    >
                      <Target className="w-4 h-4 mr-2" />
                      Auto-Size Order
                    </button>
                  </div>

                  <div className="text-xs text-gray-500">
                    {activeEvaluation?.reasoning || 'No reasoning available'}
                  </div>
                </div>
              </div>
            )}
        </div>
      ) : (
        <div className="card">
          <div className="text-center py-8">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Evaluation Available</h3>
            <p className="text-gray-500">
              Unable to evaluate position. Please check your connection and try again.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
