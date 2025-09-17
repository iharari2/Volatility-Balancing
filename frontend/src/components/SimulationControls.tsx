import { useState } from 'react';
import { Play, Square, Calendar, DollarSign, Settings, AlertCircle } from 'lucide-react';

export interface SimulationConfig {
  ticker: string;
  startDate: string;
  endDate: string;
  initialCash: number;
  triggerThresholdPct: number;
  rebalanceRatio: number;
  commissionRate: number;
  minNotional: number;
  allowAfterHours: boolean;
  guardrails: {
    minStockAllocPct: number;
    maxStockAllocPct: number;
  };
}

interface SimulationControlsProps {
  config: SimulationConfig;
  onConfigChange: (config: SimulationConfig) => void;
  onRunSimulation: () => void;
  onStopSimulation: () => void;
  isRunning: boolean;
  className?: string;
}

export default function SimulationControls({
  config,
  onConfigChange,
  onRunSimulation,
  onStopSimulation,
  isRunning,
  className = '',
}: SimulationControlsProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleConfigChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      onConfigChange({
        ...config,
        [parent]: {
          ...config[parent as keyof SimulationConfig],
          [child]: value,
        },
      });
    } else {
      onConfigChange({
        ...config,
        [field]: value,
      });
    }
  };

  const defaultConfigs = {
    conservative: {
      triggerThresholdPct: 0.02,
      rebalanceRatio: 1.2,
      commissionRate: 0.0001,
      guardrails: { minStockAllocPct: 0.3, maxStockAllocPct: 0.7 },
    },
    moderate: {
      triggerThresholdPct: 0.03,
      rebalanceRatio: 1.6667,
      commissionRate: 0.0001,
      guardrails: { minStockAllocPct: 0.25, maxStockAllocPct: 0.75 },
    },
    aggressive: {
      triggerThresholdPct: 0.05,
      rebalanceRatio: 2.0,
      commissionRate: 0.0001,
      guardrails: { minStockAllocPct: 0.2, maxStockAllocPct: 0.8 },
    },
  };

  const applyPreset = (preset: keyof typeof defaultConfigs) => {
    const presetConfig = defaultConfigs[preset];
    onConfigChange({
      ...config,
      ...presetConfig,
    });
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Quick Setup */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Simulation Setup</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="btn btn-secondary btn-sm"
            >
              <Settings className="w-4 h-4 mr-2" />
              {showAdvanced ? 'Hide' : 'Show'} Advanced
            </button>
          </div>
        </div>

        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Ticker Symbol</label>
            <input
              type="text"
              value={config.ticker}
              onChange={(e) => handleConfigChange('ticker', e.target.value.toUpperCase())}
              className="input"
              placeholder="e.g., AAPL"
            />
          </div>

          <div>
            <label className="label">Initial Cash</label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="number"
                value={config.initialCash}
                onChange={(e) => handleConfigChange('initialCash', Number(e.target.value))}
                className="input pl-10"
                min="1000"
                step="100"
              />
            </div>
          </div>

          <div>
            <label className="label">Start Date</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={config.startDate}
                onChange={(e) => handleConfigChange('startDate', e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          <div>
            <label className="label">End Date</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={config.endDate}
                onChange={(e) => handleConfigChange('endDate', e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
        </div>

        {/* Preset Configurations */}
        <div className="mt-4">
          <label className="label">Quick Presets</label>
          <div className="flex space-x-2">
            <button
              onClick={() => applyPreset('conservative')}
              className="btn btn-outline btn-sm"
            >
              Conservative
            </button>
            <button
              onClick={() => applyPreset('moderate')}
              className="btn btn-outline btn-sm"
            >
              Moderate
            </button>
            <button
              onClick={() => applyPreset('aggressive')}
              className="btn btn-outline btn-sm"
            >
              Aggressive
            </button>
          </div>
        </div>

        {/* Advanced Configuration */}
        {showAdvanced && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="font-medium text-gray-900 mb-4">Advanced Parameters</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Trigger Threshold (%)</label>
                <input
                  type="number"
                  value={config.triggerThresholdPct * 100}
                  onChange={(e) => handleConfigChange('triggerThresholdPct', Number(e.target.value) / 100)}
                  className="input"
                  min="0.1"
                  max="10"
                  step="0.1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Price change threshold to trigger trades (±{config.triggerThresholdPct * 100}%)
                </p>
              </div>

              <div>
                <label className="label">Rebalance Ratio</label>
                <input
                  type="number"
                  value={config.rebalanceRatio}
                  onChange={(e) => handleConfigChange('rebalanceRatio', Number(e.target.value))}
                  className="input"
                  min="0.1"
                  max="5"
                  step="0.1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Order sizing multiplier for rebalancing
                </p>
              </div>

              <div>
                <label className="label">Commission Rate (%)</label>
                <input
                  type="number"
                  value={config.commissionRate * 100}
                  onChange={(e) => handleConfigChange('commissionRate', Number(e.target.value) / 100)}
                  className="input"
                  min="0"
                  max="1"
                  step="0.001"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Trading commission as percentage of notional
                </p>
              </div>

              <div>
                <label className="label">Min Notional</label>
                <input
                  type="number"
                  value={config.minNotional}
                  onChange={(e) => handleConfigChange('minNotional', Number(e.target.value))}
                  className="input"
                  min="0"
                  step="10"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum order value to execute
                </p>
              </div>
            </div>

            {/* Guardrails */}
            <div className="mt-4">
              <label className="label">Asset Allocation Guardrails (%)</label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Minimum Stock %</label>
                  <input
                    type="number"
                    value={config.guardrails.minStockAllocPct * 100}
                    onChange={(e) => handleConfigChange('guardrails.minStockAllocPct', Number(e.target.value) / 100)}
                    className="input"
                    min="0"
                    max="100"
                    step="1"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-600">Maximum Stock %</label>
                  <input
                    type="number"
                    value={config.guardrails.maxStockAllocPct * 100}
                    onChange={(e) => handleConfigChange('guardrails.maxStockAllocPct', Number(e.target.value) / 100)}
                    className="input"
                    min="0"
                    max="100"
                    step="1"
                  />
                </div>
              </div>
            </div>

            {/* Market Hours */}
            <div className="mt-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.allowAfterHours}
                  onChange={(e) => handleConfigChange('allowAfterHours', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">Allow after-hours trading</span>
              </label>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {isRunning ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                  Running simulation...
                </div>
              ) : (
                `Ready to simulate ${config.ticker} from ${config.startDate} to ${config.endDate}`
              )}
            </div>
            
            <div className="flex space-x-3">
              {isRunning ? (
                <button
                  onClick={onStopSimulation}
                  className="btn btn-danger"
                >
                  <Square className="w-4 h-4 mr-2" />
                  Stop
                </button>
              ) : (
                <button
                  onClick={onRunSimulation}
                  disabled={!config.ticker || !config.startDate || !config.endDate}
                  className="btn btn-primary"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Run Simulation
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

