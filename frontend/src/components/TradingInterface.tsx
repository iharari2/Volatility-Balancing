import { useState } from 'react';
import { Position, EvaluationResult } from '../types';
import { useEvaluatePosition, useCreateOrder, useAutoSizeOrder } from '../hooks/usePositions';
import { useCreateOrder as useCreateOrderMutation } from '../hooks/useOrders';
import {
  Play,
  Target,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface TradingInterfaceProps {
  position: Position;
}

export default function TradingInterface({ position }: TradingInterfaceProps) {
  const [currentPrice, setCurrentPrice] = useState<number>(position.anchor_price || 150);
  const [isAutoMode, setIsAutoMode] = useState(false);

  const { data: evaluation, isLoading: isEvaluating } = useEvaluatePosition(
    position.id,
    currentPrice,
  );

  const createOrderMutation = useCreateOrderMutation(position.id);
  const autoSizeMutation = useAutoSizeOrder(position.id);

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
      await autoSizeMutation.mutateAsync({
        currentPrice,
        idempotencyKey: `auto-${Date.now()}`,
      });
    } catch (error) {
      console.error('Failed to create auto order:', error);
    }
  };

  const getTriggerStatus = () => {
    if (!evaluation) return { status: 'loading', message: 'Evaluating...' };

    if (evaluation.trigger_detected) {
      return {
        status: 'trigger',
        message: `${evaluation.trigger_type} trigger detected`,
        icon: evaluation.trigger_type === 'BUY' ? TrendingUp : TrendingDown,
        color: evaluation.trigger_type === 'BUY' ? 'text-success-600' : 'text-danger-600',
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
      {/* Price Input */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Price Evaluation</h3>
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

      {/* Evaluation Results */}
      {evaluation && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Evaluation Results</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Trigger Status */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <triggerStatus.icon className={`w-6 h-6 ${triggerStatus.color}`} />
                <div>
                  <h4 className="font-medium text-gray-900">Trigger Status</h4>
                  <p className={`text-sm ${triggerStatus.color}`}>{triggerStatus.message}</p>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Current Price:</span>
                  <span className="font-medium">${evaluation.current_price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Anchor Price:</span>
                  <span className="font-medium">${evaluation.anchor_price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Price Change:</span>
                  <span
                    className={`font-medium ${
                      evaluation.current_price > evaluation.anchor_price
                        ? 'text-danger-600'
                        : 'text-success-600'
                    }`}
                  >
                    {(
                      ((evaluation.current_price - evaluation.anchor_price) /
                        evaluation.anchor_price) *
                      100
                    ).toFixed(2)}
                    %
                  </span>
                </div>
              </div>
            </div>

            {/* Order Proposal */}
            {evaluation.order_proposal && (
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Order Proposal</h4>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Side:</span>
                    <span
                      className={`font-medium ${
                        evaluation.order_proposal.side === 'BUY'
                          ? 'text-success-600'
                          : 'text-danger-600'
                      }`}
                    >
                      {evaluation.order_proposal.side}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Quantity:</span>
                    <span className="font-medium">{evaluation.order_proposal.trimmed_qty}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Notional:</span>
                    <span className="font-medium">
                      ${evaluation.order_proposal.notional.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Commission:</span>
                    <span className="font-medium">
                      ${evaluation.order_proposal.commission.toFixed(2)}
                    </span>
                  </div>
                </div>

                {evaluation.order_proposal.validation.valid ? (
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
                      {evaluation.order_proposal.validation.rejections.map((rejection, index) => (
                        <li key={index}>• {rejection}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {evaluation.trigger_detected && evaluation.order_proposal?.validation.valid && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleManualOrder(evaluation.order_proposal!.side)}
                    disabled={createOrderMutation.isPending}
                    className={`btn ${
                      evaluation.order_proposal!.side === 'BUY' ? 'btn-success' : 'btn-danger'
                    }`}
                  >
                    {evaluation.order_proposal!.side === 'BUY' ? (
                      <TrendingUp className="w-4 h-4 mr-2" />
                    ) : (
                      <TrendingDown className="w-4 h-4 mr-2" />
                    )}
                    Manual {evaluation.order_proposal!.side}
                  </button>

                  <button
                    onClick={handleAutoOrder}
                    disabled={autoSizeMutation.isPending}
                    className="btn btn-primary"
                  >
                    <Target className="w-4 h-4 mr-2" />
                    Auto-Size Order
                  </button>
                </div>

                <div className="text-xs text-gray-500">{evaluation.reasoning}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


