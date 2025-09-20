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
  onSharedConfigChange?: (updates: any) => void;
}

export default function SimulationControls({
  config,
  onConfigChange,
  onRunSimulation,
  onStopSimulation,
  isRunning,
  className = '',
  onSharedConfigChange,
}: SimulationControlsProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Quick date presets
  const quickDatePresets = [
    { label: 'Last 3 days', days: 3 },
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 14 days', days: 14 },
    { label: 'Last 30 days', days: 30 },
  ];

  const applyQuickDate = (days: number) => {
    const today = new Date();
    const startDate = new Date(today.getTime() - days * 24 * 60 * 60 * 1000);
    const endDate = new Date(today.getTime() - 1 * 24 * 60 * 60 * 1000); // Yesterday

    onConfigChange({
      ...config,
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
    });
  };

  // Calculate actual simulation time window
  const getSimulationTimeWindow = () => {
    const startDate = new Date(config.startDate);
    const endDate = new Date(config.endDate);
    const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    // Better trading days calculation
    // Weekends are Saturday (6) and Sunday (0)
    let tradingDays = 0;
    const currentDate = new Date(startDate);

    while (currentDate <= endDate) {
      const dayOfWeek = currentDate.getDay();
      // Count Monday (1) through Friday (5) as trading days
      if (dayOfWeek >= 1 && dayOfWeek <= 5) {
        tradingDays++;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }

    return {
      start: startDate.toLocaleDateString(),
      end: endDate.toLocaleDateString(),
      days: daysDiff,
      tradingDays: Math.max(1, tradingDays),
    };
  };

  const timeWindow = getSimulationTimeWindow();

  // Date validation
  const validateDates = () => {
    const startDate = new Date(config.startDate);
    const endDate = new Date(config.endDate);
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    const errors = [];
    const warnings = [];

    if (startDate > today) {
      errors.push('Start date cannot be in the future');
    }
    if (endDate > today) {
      errors.push('End date cannot be in the future');
    }
    if (startDate >= endDate) {
      errors.push('Start date must be before end date');
    }
    // Allow exactly 30 days (with some tolerance)
    const thirtyDaysAgoTolerance = new Date(today.getTime() - 31 * 24 * 60 * 60 * 1000); // 31 days ago
    if (endDate < thirtyDaysAgoTolerance) {
      errors.push('End date is too far in the past (yfinance only supports last 30 days)');
    }
    if (startDate < thirtyDaysAgoTolerance) {
      warnings.push('Start date is far in the past - may have limited data');
    }

    return { errors, warnings };
  };

  const validation = validateDates();

  const handleConfigChange = (field: string, value: any) => {
    let newConfig;
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      newConfig = {
        ...config,
        [parent]: {
          ...config[parent as keyof SimulationConfig],
          [child]: value,
        },
      };
    } else {
      newConfig = {
        ...config,
        [field]: value,
      };
    }

    onConfigChange(newConfig);

    // Also update shared configuration for persistent settings
    if (onSharedConfigChange) {
      const sharedFields = [
        'triggerThresholdPct',
        'rebalanceRatio',
        'commissionRate',
        'minNotional',
        'allowAfterHours',
        'guardrails.minStockAllocPct',
        'guardrails.maxStockAllocPct',
      ];

      if (sharedFields.includes(field) || field.startsWith('guardrails.')) {
        if (field.includes('.')) {
          const [parent, child] = field.split('.');
          onSharedConfigChange({
            [parent]: {
              ...config[parent as keyof SimulationConfig],
              [child]: value,
            },
          });
        } else {
          onSharedConfigChange({
            [field]: value,
          });
        }
      }
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
                className={`input pl-10 ${
                  validation.errors.some((e) => e.includes('Start date')) ? 'border-red-300' : ''
                }`}
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
                className={`input pl-10 ${
                  validation.errors.some((e) => e.includes('End date')) ? 'border-red-300' : ''
                }`}
              />
            </div>
          </div>
        </div>

        {/* Time Window Display */}
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-blue-900">Simulation Time Window</h4>
            <div className="text-xs text-blue-600">
              {timeWindow.days} day{timeWindow.days !== 1 ? 's' : ''} • ~{timeWindow.tradingDays}{' '}
              trading day{timeWindow.tradingDays !== 1 ? 's' : ''}
            </div>
          </div>
          <div className="text-sm text-blue-800">
            <span className="font-medium">{timeWindow.start}</span> to{' '}
            <span className="font-medium">{timeWindow.end}</span>
          </div>
          <div className="mt-2 text-xs text-blue-600">
            <AlertCircle className="w-3 h-3 inline mr-1" />
            Data limited to last 30 days for 1-minute intervals
          </div>
        </div>

        {/* Validation Messages */}
        {(validation.errors.length > 0 || validation.warnings.length > 0) && (
          <div className="mt-4 space-y-2">
            {validation.errors.map((error, index) => (
              <div
                key={index}
                className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg"
              >
                <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                <span className="text-sm text-red-700">{error}</span>
              </div>
            ))}
            {validation.warnings.map((warning, index) => (
              <div
                key={index}
                className="flex items-center p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
              >
                <AlertCircle className="w-4 h-4 text-yellow-500 mr-2" />
                <span className="text-sm text-yellow-700">{warning}</span>
              </div>
            ))}
          </div>
        )}

        {/* Quick Date Picker */}
        <div className="mt-4">
          <label className="label">Quick Date Selection</label>
          <div className="flex flex-wrap gap-2">
            {quickDatePresets.map((preset) => (
              <button
                key={preset.days}
                onClick={() => applyQuickDate(preset.days)}
                className="btn btn-outline btn-sm"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Preset Configurations */}
        <div className="mt-4">
          <label className="label">Quick Presets</label>
          <div className="flex space-x-2">
            <button onClick={() => applyPreset('conservative')} className="btn btn-outline btn-sm">
              Conservative
            </button>
            <button onClick={() => applyPreset('moderate')} className="btn btn-outline btn-sm">
              Moderate
            </button>
            <button onClick={() => applyPreset('aggressive')} className="btn btn-outline btn-sm">
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
                  onChange={(e) =>
                    handleConfigChange('triggerThresholdPct', Number(e.target.value) / 100)
                  }
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
                  onChange={(e) =>
                    handleConfigChange('commissionRate', Number(e.target.value) / 100)
                  }
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
                <p className="text-xs text-gray-500 mt-1">Minimum order value to execute</p>
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
                    value={Math.round(config.guardrails.minStockAllocPct * 100)}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      if (!isNaN(value) && value >= 0 && value <= 100) {
                        handleConfigChange('guardrails.minStockAllocPct', value / 100);
                      }
                    }}
                    className="input"
                    min="0"
                    max="100"
                    step="1"
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-600">Maximum Stock %</label>
                  <input
                    type="number"
                    value={Math.round(config.guardrails.maxStockAllocPct * 100)}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      if (!isNaN(value) && value >= 0 && value <= 100) {
                        handleConfigChange('guardrails.maxStockAllocPct', value / 100);
                      }
                    }}
                    className="input"
                    min="0"
                    max="100"
                    step="1"
                    placeholder="75"
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
      </div>

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
              <button onClick={onStopSimulation} className="btn btn-danger">
                <Square className="w-4 h-4 mr-2" />
                Stop
              </button>
            ) : (
              <button
                onClick={onRunSimulation}
                disabled={
                  !config.ticker ||
                  !config.startDate ||
                  !config.endDate ||
                  validation.errors.length > 0
                }
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
  );
}
