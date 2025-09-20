import { useState } from 'react';
import { usePositions, useCreatePosition } from '../hooks/usePositions';
import TradingInterface from '../components/TradingInterface';
import CreatePositionForm from '../components/CreatePositionForm';
import TradingConfigPanel from '../components/TradingConfigPanel';
import { CreatePositionRequest } from '../types';
import { Settings } from 'lucide-react';
import { useConfiguration } from '../contexts/ConfigurationContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

export default function Trading() {
  const [selectedPositionId, setSelectedPositionId] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const { data: positions = [] } = usePositions();
  const createPosition = useCreatePosition();
  const { configuration, updateConfiguration } = useConfiguration();

  const selectedPosition = positions.find((p) => p.id === selectedPositionId);

  const handleCreatePosition = async (data: CreatePositionRequest) => {
    try {
      await createPosition.mutateAsync(data);
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create position:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Trading Interface</h1>
        <p className="text-gray-600">Real-time volatility evaluation and order execution</p>
      </div>

      {/* Position Selector */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Select Position</h3>
          <button onClick={() => setShowCreateForm(true)} className="btn btn-primary btn-sm">
            + Create New Position
          </button>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="label">Choose a position to trade</label>
            <select
              value={selectedPositionId}
              onChange={(e) => setSelectedPositionId(e.target.value)}
              className="input"
            >
              <option value="">Select a position...</option>
              {positions.map((position) => (
                <option key={position.id} value={position.id}>
                  {position.ticker} -{' '}
                  {position.anchor_price
                    ? `$${position.anchor_price.toFixed(2)}`
                    : 'No anchor price'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {positions.length === 0 && (
          <div className="mt-4 p-4 bg-warning-50 border border-warning-200 rounded-lg">
            <p className="text-warning-800 text-sm">
              No positions found. Create a position to start trading.
            </p>
          </div>
        )}

        {positions.length > 0 && positions.filter((p) => p.anchor_price).length === 0 && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 text-sm">
              Positions found but none have anchor prices set. Select a position and set an anchor
              price to enable volatility trading.
            </p>
          </div>
        )}
      </div>

      {/* Trading Interface */}
      {selectedPosition ? (
        <TradingInterface position={selectedPosition} />
      ) : selectedPositionId ? (
        <div className="card text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Position Not Found</h3>
          <p className="text-gray-500">
            The selected position could not be found or doesn't have an anchor price set.
          </p>
        </div>
      ) : (
        <div className="card text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Position</h3>
          <p className="text-gray-500">
            Choose a position from the dropdown above to start trading.
          </p>
        </div>
      )}

      {/* Configuration Section */}
      {selectedPosition && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Trading Configuration</h3>
            <button onClick={() => setShowConfig(!showConfig)} className="btn btn-secondary btn-sm">
              <Settings className="w-4 h-4 mr-2" />
              {showConfig ? 'Hide' : 'Show'} Configuration
            </button>
          </div>

          {/* Quick Configuration Summary */}
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Current Settings</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Trigger:</span>
                <span className="ml-1 font-medium">
                  ±
                  {(
                    (selectedPosition.order_policy?.trigger_threshold_pct ||
                      configuration.triggerThresholdPct) * 100
                  ).toFixed(1)}
                  %
                </span>
              </div>
              <div>
                <span className="text-gray-500">Rebalance:</span>
                <span className="ml-1 font-medium">
                  {(
                    selectedPosition.order_policy?.rebalance_ratio || configuration.rebalanceRatio
                  ).toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-gray-500">After Hours:</span>
                <span className="ml-1 font-medium">
                  {selectedPosition.order_policy?.allow_after_hours ?? configuration.allowAfterHours
                    ? 'Yes'
                    : 'No'}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Guardrails:</span>
                <span className="ml-1 font-medium">
                  {(
                    (selectedPosition.guardrails?.min_stock_alloc_pct ||
                      configuration.guardrails.minStockAllocPct) * 100
                  ).toFixed(0)}
                  % -{' '}
                  {(
                    (selectedPosition.guardrails?.max_stock_alloc_pct ||
                      configuration.guardrails.maxStockAllocPct) * 100
                  ).toFixed(0)}
                  %
                </span>
              </div>
            </div>
          </div>

          {showConfig && (
            <TradingConfigPanel
              orderPolicy={
                selectedPosition.order_policy || {
                  min_qty: 0,
                  min_notional: configuration.minNotional,
                  lot_size: 0,
                  qty_step: 0,
                  action_below_min: 'hold',
                  trigger_threshold_pct: configuration.triggerThresholdPct,
                  rebalance_ratio: configuration.rebalanceRatio,
                  commission_rate: configuration.commissionRate,
                  allow_after_hours: configuration.allowAfterHours,
                }
              }
              guardrails={
                selectedPosition.guardrails || {
                  min_stock_alloc_pct: configuration.guardrails.minStockAllocPct,
                  max_stock_alloc_pct: configuration.guardrails.maxStockAllocPct,
                  max_orders_per_day: configuration.guardrails.maxOrdersPerDay,
                }
              }
              withholdingTaxRate={
                selectedPosition.withholding_tax_rate || configuration.withholdingTaxRate
              }
              onSave={(config) => {
                // Update shared configuration
                updateConfiguration({
                  triggerThresholdPct: config.orderPolicy.trigger_threshold_pct,
                  rebalanceRatio: config.orderPolicy.rebalance_ratio,
                  commissionRate: config.orderPolicy.commission_rate,
                  minNotional: config.orderPolicy.min_notional,
                  allowAfterHours: config.orderPolicy.allow_after_hours,
                  guardrails: {
                    minStockAllocPct: config.guardrails.min_stock_alloc_pct,
                    maxStockAllocPct: config.guardrails.max_stock_alloc_pct,
                    maxOrdersPerDay: config.guardrails.max_orders_per_day,
                  },
                  withholdingTaxRate: config.withholdingTaxRate,
                });
                console.log('Configuration saved and synchronized across screens!');
                alert('Configuration saved and synchronized across screens!');
              }}
              onReset={() => {
                // Reset to shared configuration defaults
                updateConfiguration({
                  triggerThresholdPct: 0.03,
                  rebalanceRatio: 0.5,
                  commissionRate: 0.0001,
                  minNotional: 100,
                  allowAfterHours: true,
                  guardrails: {
                    minStockAllocPct: 0.25,
                    maxStockAllocPct: 0.75,
                    maxOrdersPerDay: 5,
                  },
                  withholdingTaxRate: 0.25,
                });
                console.log('Configuration reset to defaults');
                alert('Configuration reset to defaults');
              }}
            />
          )}
        </div>
      )}

      {/* Quick Actions */}
      {selectedPosition && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Test Common Prices</h4>
              <p className="text-sm text-gray-600 mb-3">
                Quickly test trigger detection at common price levels
              </p>
              <div className="space-y-2">
                {selectedPosition.anchor_price && (
                  <>
                    <button
                      className="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded"
                      onClick={() => {
                        // This would trigger price evaluation at the specified price
                        console.log('Test buy trigger at', selectedPosition.anchor_price! * 0.97);
                      }}
                    >
                      Buy Trigger: ${(selectedPosition.anchor_price * 0.97).toFixed(2)}
                    </button>
                    <button
                      className="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded"
                      onClick={() => {
                        console.log('Test sell trigger at', selectedPosition.anchor_price! * 1.03);
                      }}
                    >
                      Sell Trigger: ${(selectedPosition.anchor_price * 1.03).toFixed(2)}
                    </button>
                    <button
                      className="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded"
                      onClick={() => {
                        console.log('Test at anchor price', selectedPosition.anchor_price);
                      }}
                    >
                      At Anchor: ${selectedPosition.anchor_price.toFixed(2)}
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Position Info</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <p>
                  <span className="font-medium">Ticker:</span> {selectedPosition.ticker}
                </p>
                <p>
                  <span className="font-medium">Shares:</span>{' '}
                  {selectedPosition.qty.toLocaleString()}
                </p>
                <p>
                  <span className="font-medium">Cash:</span> $
                  {selectedPosition.cash.toLocaleString()}
                </p>
                <p>
                  <span className="font-medium">Anchor:</span> $
                  {selectedPosition.anchor_price?.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Trading Tips</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Triggers activate at ±3% from anchor</li>
                <li>• Orders are auto-sized based on position</li>
                <li>• Anchor updates after each trade</li>
                <li>• All actions are logged in events</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Create Position Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setShowCreateForm(false)}
            />
            <div className="relative bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <CreatePositionForm
                onSubmit={handleCreatePosition}
                onCancel={() => setShowCreateForm(false)}
                isLoading={createPosition.isPending}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
