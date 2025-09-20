import { useState } from 'react';
import { Settings, Save, RotateCcw } from 'lucide-react';

export interface UnifiedConfig {
  // Basic parameters
  ticker: string;
  initialCash: number;

  // Trading parameters
  triggerThresholdPct: number;
  rebalanceRatio: number;
  commissionRate: number;
  minNotional: number;
  allowAfterHours: boolean;

  // Guardrails
  guardrails: {
    minStockAllocPct: number;
    maxStockAllocPct: number;
    maxOrdersPerDay: number;
  };

  // Simulation-specific (optional)
  startDate?: string;
  endDate?: string;
}

interface UnifiedConfigPanelProps {
  config: UnifiedConfig;
  onConfigChange: (config: UnifiedConfig) => void;
  onSave?: () => void;
  onReset?: () => void;
  isLoading?: boolean;
  showAdvanced?: boolean;
  mode?: 'trading' | 'simulation';
  className?: string;
}

const defaultConfig: UnifiedConfig = {
  ticker: 'AAPL',
  initialCash: 10000,
  triggerThresholdPct: 0.03, // 3%
  rebalanceRatio: 0.5,
  commissionRate: 0.0001, // 0.01%
  minNotional: 100,
  allowAfterHours: true, // Default to after hours ON
  guardrails: {
    minStockAllocPct: 0.25, // 25%
    maxStockAllocPct: 0.75, // 75%
    maxOrdersPerDay: 5,
  },
};

export default function UnifiedConfigPanel({
  config,
  onConfigChange,
  onSave,
  onReset,
  isLoading = false,
  showAdvanced = false,
  mode = 'trading',
  className = '',
}: UnifiedConfigPanelProps) {
  const [localConfig, setLocalConfig] = useState<UnifiedConfig>({ ...config });
  const [showAdvancedLocal, setShowAdvancedLocal] = useState(showAdvanced);

  const updateConfig = (updates: Partial<UnifiedConfig>) => {
    const newConfig = { ...localConfig, ...updates };
    setLocalConfig(newConfig);
    onConfigChange(newConfig);
  };

  const updateGuardrails = (field: keyof UnifiedConfig['guardrails'], value: number) => {
    updateConfig({
      guardrails: {
        ...localConfig.guardrails,
        [field]: value,
      },
    });
  };

  const handleSave = () => {
    if (onSave) {
      onSave();
    }
  };

  const handleReset = () => {
    setLocalConfig({ ...defaultConfig });
    onConfigChange({ ...defaultConfig });
    if (onReset) {
      onReset();
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            {mode === 'simulation' ? 'Simulation Configuration' : 'Position Configuration'}
          </h3>
        </div>
        <div className="flex space-x-2">
          {onReset && (
            <button onClick={handleReset} className="btn btn-secondary" disabled={isLoading}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </button>
          )}
          {onSave && (
            <button onClick={handleSave} className="btn btn-primary" disabled={isLoading}>
              <Save className="w-4 h-4 mr-2" />
              {isLoading ? 'Saving...' : 'Save'}
            </button>
          )}
        </div>
      </div>

      {/* Basic Parameters */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Basic Parameters</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Ticker Symbol</label>
            <input
              type="text"
              value={localConfig.ticker}
              onChange={(e) => updateConfig({ ticker: e.target.value.toUpperCase() })}
              className="input"
              placeholder="AAPL"
            />
            <p className="text-xs text-gray-500 mt-1">Stock symbol to trade</p>
          </div>

          <div>
            <label className="label">Initial Cash ($)</label>
            <input
              type="number"
              value={localConfig.initialCash}
              onChange={(e) => updateConfig({ initialCash: Number(e.target.value) })}
              className="input"
              min="100"
              step="100"
            />
            <p className="text-xs text-gray-500 mt-1">Starting cash amount</p>
          </div>
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
              value={localConfig.triggerThresholdPct * 100}
              onChange={(e) => updateConfig({ triggerThresholdPct: Number(e.target.value) / 100 })}
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
              value={localConfig.rebalanceRatio}
              onChange={(e) => updateConfig({ rebalanceRatio: Number(e.target.value) })}
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
              value={localConfig.commissionRate * 100}
              onChange={(e) => updateConfig({ commissionRate: Number(e.target.value) / 100 })}
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
              value={localConfig.minNotional}
              onChange={(e) => updateConfig({ minNotional: Number(e.target.value) })}
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
                checked={localConfig.allowAfterHours}
                onChange={(e) => updateConfig({ allowAfterHours: e.target.checked })}
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

      {/* Advanced Settings Toggle */}
      <div className="flex justify-center">
        <button
          onClick={() => setShowAdvancedLocal(!showAdvancedLocal)}
          className="btn btn-secondary"
        >
          <Settings className="w-4 h-4 mr-2" />
          {showAdvancedLocal ? 'Hide' : 'Show'} Advanced Settings
        </button>
      </div>

      {/* Advanced Settings */}
      {showAdvancedLocal && (
        <div className="card">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Guardrail Settings</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Minimum Stock Allocation (%)</label>
              <input
                type="number"
                value={localConfig.guardrails.minStockAllocPct * 100}
                onChange={(e) => updateGuardrails('minStockAllocPct', Number(e.target.value) / 100)}
                className="input"
                min="0"
                max="100"
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">
                Minimum percentage of portfolio in stocks (default: 25%)
              </p>
            </div>

            <div>
              <label className="label">Maximum Stock Allocation (%)</label>
              <input
                type="number"
                value={localConfig.guardrails.maxStockAllocPct * 100}
                onChange={(e) => updateGuardrails('maxStockAllocPct', Number(e.target.value) / 100)}
                className="input"
                min="0"
                max="100"
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum percentage of portfolio in stocks (default: 75%)
              </p>
            </div>

            <div>
              <label className="label">Max Orders Per Day</label>
              <input
                type="number"
                value={localConfig.guardrails.maxOrdersPerDay}
                onChange={(e) => updateGuardrails('maxOrdersPerDay', Number(e.target.value))}
                className="input"
                min="1"
                max="100"
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum number of orders per day (default: 5)
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
