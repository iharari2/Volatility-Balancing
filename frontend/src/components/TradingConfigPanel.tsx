import { useState } from 'react';
import { OrderPolicy, Guardrails } from '../types';
import { Settings, Save, RotateCcw } from 'lucide-react';

interface TradingConfigPanelProps {
  orderPolicy: OrderPolicy;
  guardrails: Guardrails;
  withholdingTaxRate: number;
  onSave: (config: {
    orderPolicy: OrderPolicy;
    guardrails: Guardrails;
    withholdingTaxRate: number;
  }) => void;
  onReset: () => void;
  isLoading?: boolean;
}

const defaultOrderPolicy: OrderPolicy = {
  min_qty: 0,
  min_notional: 100,
  lot_size: 0,
  qty_step: 0,
  action_below_min: 'hold',
  trigger_threshold_pct: 0.03, // 3%
  rebalance_ratio: 0.5, // Updated to match simulation default
  commission_rate: 0.0001, // 0.01%
  allow_after_hours: true, // Default to after hours ON
};

const defaultGuardrails: Guardrails = {
  min_stock_alloc_pct: 0.25, // 25%
  max_stock_alloc_pct: 0.75, // 75%
  max_orders_per_day: 5,
};

export default function TradingConfigPanel({
  orderPolicy,
  guardrails,
  withholdingTaxRate,
  onSave,
  onReset,
  isLoading = false,
}: TradingConfigPanelProps) {
  const [config, setConfig] = useState({
    orderPolicy: { ...orderPolicy },
    guardrails: { ...guardrails },
    withholdingTaxRate,
  });

  const handleSave = () => {
    onSave(config);
  };

  const handleReset = () => {
    setConfig({
      orderPolicy: { ...defaultOrderPolicy },
      guardrails: { ...defaultGuardrails },
      withholdingTaxRate: 0.25,
    });
    onReset();
  };

  const updateOrderPolicy = (field: keyof OrderPolicy, value: any) => {
    setConfig((prev) => ({
      ...prev,
      orderPolicy: { ...prev.orderPolicy, [field]: value },
    }));
  };

  const updateGuardrails = (field: keyof Guardrails, value: number) => {
    setConfig((prev) => ({
      ...prev,
      guardrails: { ...prev.guardrails, [field]: value },
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Trading Configuration</h3>
        </div>
        <div className="flex space-x-2">
          <button onClick={handleReset} className="btn btn-secondary" disabled={isLoading}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </button>
          <button onClick={handleSave} className="btn btn-primary" disabled={isLoading}>
            <Save className="w-4 h-4 mr-2" />
            {isLoading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Trading Parameters */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Trading Parameters</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Trigger Threshold (%)</label>
            <input
              type="number"
              value={(config.orderPolicy.trigger_threshold_pct || 0.03) * 100}
              onChange={(e) =>
                updateOrderPolicy('trigger_threshold_pct', Number(e.target.value) / 100)
              }
              className="input"
              min="0.1"
              max="10"
              step="0.1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Price movement threshold to trigger trades (default: 3%)
            </p>
          </div>

          <div>
            <label className="label">Rebalance Ratio</label>
            <input
              type="number"
              value={config.orderPolicy.rebalance_ratio || 0.5}
              onChange={(e) => updateOrderPolicy('rebalance_ratio', Number(e.target.value))}
              className="input"
              min="0.1"
              max="5"
              step="0.1"
            />
            <p className="text-xs text-gray-500 mt-1">Order sizing multiplier (default: 0.5)</p>
          </div>

          <div>
            <label className="label">Commission Rate (%)</label>
            <input
              type="number"
              value={(config.orderPolicy.commission_rate || 0.0001) * 100}
              onChange={(e) => updateOrderPolicy('commission_rate', Number(e.target.value) / 100)}
              className="input"
              min="0"
              max="1"
              step="0.001"
            />
            <p className="text-xs text-gray-500 mt-1">
              Commission as percentage of order value (default: 0.01%)
            </p>
          </div>

          <div>
            <label className="label">Minimum Order ($)</label>
            <input
              type="number"
              value={config.orderPolicy.min_notional || 100}
              onChange={(e) => updateOrderPolicy('min_notional', Number(e.target.value))}
              className="input"
              min="0"
              step="1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Minimum order value to execute (default: $100)
            </p>
          </div>

          <div className="md:col-span-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.orderPolicy.allow_after_hours ?? true}
                onChange={(e) => updateOrderPolicy('allow_after_hours', e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Allow After-Hours Trading</span>
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Enable trading outside regular market hours (4:00 PM - 9:30 AM ET)
            </p>
          </div>
        </div>
      </div>

      {/* Guardrail Settings */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Guardrail Settings</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Minimum Stock Allocation (%)</label>
            <input
              type="number"
              value={Math.round((config.guardrails.min_stock_alloc_pct || 0.25) * 100)}
              onChange={(e) => {
                const value = Number(e.target.value);
                if (!isNaN(value) && value >= 0 && value <= 100) {
                  updateGuardrails('min_stock_alloc_pct', value / 100);
                }
              }}
              className="input"
              min="0"
              max="100"
              step="1"
              placeholder="25"
            />
            <p className="text-xs text-gray-500 mt-1">
              Minimum percentage of portfolio in stocks (default: 25%)
            </p>
          </div>

          <div>
            <label className="label">Maximum Stock Allocation (%)</label>
            <input
              type="number"
              value={Math.round((config.guardrails.max_stock_alloc_pct || 0.75) * 100)}
              onChange={(e) => {
                const value = Number(e.target.value);
                if (!isNaN(value) && value >= 0 && value <= 100) {
                  updateGuardrails('max_stock_alloc_pct', value / 100);
                }
              }}
              className="input"
              min="0"
              max="100"
              step="1"
              placeholder="75"
            />
            <p className="text-xs text-gray-500 mt-1">
              Maximum percentage of portfolio in stocks (default: 75%)
            </p>
          </div>

          <div>
            <label className="label">Maximum Orders Per Day</label>
            <input
              type="number"
              value={config.guardrails.max_orders_per_day || 5}
              onChange={(e) => updateGuardrails('max_orders_per_day', Number(e.target.value))}
              className="input"
              min="1"
              max="20"
              step="1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Maximum number of orders per day (default: 5)
            </p>
          </div>
        </div>

        {/* Guardrail Visualization */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h5 className="text-sm font-medium text-gray-700 mb-2">Asset Allocation Range</h5>
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2 relative">
              <div
                className="bg-primary-500 h-2 rounded-full absolute"
                style={{
                  left: `${config.guardrails.min_stock_alloc_pct * 100}%`,
                  width: `${
                    (config.guardrails.max_stock_alloc_pct -
                      config.guardrails.min_stock_alloc_pct) *
                    100
                  }%`,
                }}
              />
            </div>
            <div className="text-xs text-gray-600">
              {config.guardrails.min_stock_alloc_pct * 100}% -{' '}
              {config.guardrails.max_stock_alloc_pct * 100}%
            </div>
          </div>
        </div>
      </div>

      {/* Dividend Settings */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Dividend Settings</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Withholding Tax Rate (%)</label>
            <input
              type="number"
              value={(config.withholdingTaxRate || 0.25) * 100}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, withholdingTaxRate: Number(e.target.value) / 100 }))
              }
              className="input"
              min="0"
              max="50"
              step="0.1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tax withholding rate for dividends (default: 25%)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
