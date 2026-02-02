import { useState, useEffect } from 'react';
import { Copy, Check } from 'lucide-react';
// @ts-ignore react-hot-toast types may be missing in this environment
import toast from 'react-hot-toast';
import {
  EffectiveConfig,
  PortfolioConfig,
  portfolioScopedApi,
} from '../../../services/portfolioScopedApi';
import { MarketStatus } from '../../../services/marketHoursService';

interface StrategyConfigTabProps {
  tenantId: string;
  portfolioId: string;
  positionId?: string; // Optional: if provided, edit position-specific config
  positionName?: string; // Optional: display name for position
  effectiveConfig: EffectiveConfig | null;
  editableConfig: PortfolioConfig | null;
  marketStatus: MarketStatus;
  onConfigChange: (config: PortfolioConfig) => void;
  onSave: (config: PortfolioConfig) => Promise<void>;
  onReload?: () => Promise<void>; // Optional: callback to reload data after save
  onCopyTraceId: (traceId: string) => void;
  copiedTraceId: string | null;
}

export default function StrategyConfigTab({
  tenantId,
  portfolioId,
  positionId,
  positionName,
  effectiveConfig,
  editableConfig,
  marketStatus,
  onConfigChange,
  onSave,
  onReload,
  onCopyTraceId,
  copiedTraceId,
}: StrategyConfigTabProps) {
  // Initialize with editableConfig if available, otherwise use defaults
  const getInitialConfig = (): PortfolioConfig => {
    if (editableConfig) {
      return editableConfig;
    }
    return {
      trigger_threshold_up_pct: 3.0,
      trigger_threshold_down_pct: -3.0,
      min_stock_pct: 25.0,
      max_stock_pct: 75.0,
      max_trade_pct_of_position: 50.0,
      commission_rate: 0.1,
      market_hours_policy: 'market-open-only',
    };
  };

  const [config, setConfig] = useState<PortfolioConfig>(getInitialConfig());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isPositionSpecific, setIsPositionSpecific] = useState(false);

  // Load position-specific config if positionId is provided
  useEffect(() => {
    // Reset loading state
    setLoading(false);

    if (positionId && tenantId && portfolioId) {
      // Only show loading if we're actually fetching
      setLoading(true);
      portfolioScopedApi
        .getPositionConfig(tenantId, portfolioId, positionId)
        .then((positionConfig) => {
          const posConfig: PortfolioConfig = {
            trigger_threshold_up_pct: positionConfig.trigger_threshold_up_pct,
            trigger_threshold_down_pct: positionConfig.trigger_threshold_down_pct,
            min_stock_pct: positionConfig.min_stock_pct,
            max_stock_pct: positionConfig.max_stock_pct,
            max_trade_pct_of_position: positionConfig.max_trade_pct_of_position,
            commission_rate: positionConfig.commission_rate,
            market_hours_policy: 'market-open-only', // Position config doesn't include market hours
          };
          setConfig(posConfig);
          setIsPositionSpecific(positionConfig.is_position_specific);
          onConfigChange(posConfig);
          setLoading(false);
        })
        .catch((err) => {
          console.error('Error loading position config:', err);
          // Fall back to editableConfig if position config fails, or use defaults
          const fallbackConfig = editableConfig || {
            trigger_threshold_up_pct: 3.0,
            trigger_threshold_down_pct: -3.0,
            min_stock_pct: 25.0,
            max_stock_pct: 75.0,
            max_trade_pct_of_position: 50.0,
            commission_rate: 0.1,
            market_hours_policy: 'market-open-only',
          };
          setConfig(fallbackConfig);
          setIsPositionSpecific(false);
          onConfigChange(fallbackConfig);
          setLoading(false);
        });
    } else {
      // No positionId - use editableConfig or defaults
      const configToUse = editableConfig || {
        trigger_threshold_up_pct: 3.0,
        trigger_threshold_down_pct: -3.0,
        min_stock_pct: 25.0,
        max_stock_pct: 75.0,
        max_trade_pct_of_position: 50.0,
        commission_rate: 0.1,
        market_hours_policy: 'market-open-only',
      };
      setConfig(configToUse);
      setIsPositionSpecific(false);
      if (editableConfig) {
        onConfigChange(configToUse);
      }
      setLoading(false);
    }
    // Note: onConfigChange is intentionally excluded from dependencies to prevent infinite loops
    // It's only called when we have new config data, not when the function reference changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positionId, tenantId, portfolioId, editableConfig]);

  const validateConfig = (cfg: PortfolioConfig): boolean => {
    const newErrors: Record<string, string> = {};

    if (cfg.trigger_threshold_up_pct <= 0) {
      newErrors.trigger_threshold_up_pct = 'Up threshold must be > 0';
    }
    if (cfg.trigger_threshold_down_pct >= 0) {
      newErrors.trigger_threshold_down_pct = 'Down threshold must be < 0';
    }
    if (cfg.min_stock_pct < 0 || cfg.min_stock_pct >= cfg.max_stock_pct) {
      newErrors.min_stock_pct = 'Min stock % must be >= 0 and < max stock %';
    }
    if (cfg.max_stock_pct > 100 || cfg.max_stock_pct <= cfg.min_stock_pct) {
      newErrors.max_stock_pct = 'Max stock % must be <= 100 and > min stock %';
    }
    if (cfg.max_trade_pct_of_position <= 0 || cfg.max_trade_pct_of_position > 100) {
      newErrors.max_trade_pct_of_position = 'Max trade % must be > 0 and <= 100';
    }
    if (cfg.commission_rate < 0) {
      newErrors.commission_rate = 'Commission rate must be >= 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field: keyof PortfolioConfig, value: number | string) => {
    if (!config) return;
    const newConfig = { ...config, [field]: value };
    setConfig(newConfig);
    onConfigChange(newConfig);
    // Clear error for this field
    if (errors[field]) {
      const newErrors = { ...errors };
      delete newErrors[field];
      setErrors(newErrors);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    if (!validateConfig(config)) {
      alert('Please fix validation errors before saving');
      return;
    }
    setSaving(true);
    try {
      // If positionId is provided, save position-specific config
      if (positionId && tenantId && portfolioId) {
        await portfolioScopedApi.updatePositionConfig(tenantId, portfolioId, positionId, {
          trigger_threshold_up_pct: config.trigger_threshold_up_pct,
          trigger_threshold_down_pct: config.trigger_threshold_down_pct,
          min_stock_pct: config.min_stock_pct,
          max_stock_pct: config.max_stock_pct,
          max_trade_pct_of_position: config.max_trade_pct_of_position,
          commission_rate: config.commission_rate,
        });
        setIsPositionSpecific(true);
        toast.success('Position strategy saved successfully');
        // Reload data to refresh effectiveConfig display
        if (onReload) {
          await onReload();
        }
      } else {
        // Otherwise, save portfolio-level config (onSave handles reload)
        await onSave(config);
      }
    } catch (error: any) {
      console.error('Error saving config:', error);
      const errorMsg = error?.message || 'Failed to save config';
      toast.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (!window.confirm('Reset to template values? This will discard your changes.')) {
      return;
    }
    // TODO: Load template values from API
    if (effectiveConfig) {
      const templateConfig: PortfolioConfig = {
        trigger_threshold_up_pct: 3.0,
        trigger_threshold_down_pct: -3.0,
        min_stock_pct: 25.0,
        max_stock_pct: 75.0,
        max_trade_pct_of_position: 50.0,
        commission_rate: 0.1,
        market_hours_policy: 'market-open-only',
      };
      setConfig(templateConfig);
      onConfigChange(templateConfig);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading config...</div>;
  }

  if (!config) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 mb-4">No configuration available</p>
        <p className="text-sm text-gray-400">
          {positionId
            ? 'Unable to load position configuration. Please try again or check if the position exists.'
            : 'Please ensure portfolio configuration is available.'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Position-specific indicator */}
      {positionId && (
        <div
          className={`border rounded-lg p-4 ${
            isPositionSpecific ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'
          }`}
        >
          <h4
            className={`text-sm font-medium mb-2 ${
              isPositionSpecific ? 'text-green-900' : 'text-yellow-900'
            }`}
          >
            {positionName ? `Editing Strategy for ${positionName}` : 'Editing Position Strategy'}
          </h4>
          <p className={`text-sm ${isPositionSpecific ? 'text-green-700' : 'text-yellow-700'}`}>
            {isPositionSpecific
              ? 'This position has its own strategy settings (independent from portfolio defaults).'
              : 'This position is currently using portfolio-level strategy settings. Saving will create position-specific settings.'}
          </p>
        </div>
      )}

      {/* Effective Config Summary (Read-only) */}
      {effectiveConfig && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-3">Effective Config (Read-only)</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-blue-700">Up Threshold:</span>{' '}
              <span className="font-medium text-blue-900">
                +{effectiveConfig.trigger_threshold_up_pct.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Down Threshold:</span>{' '}
              <span className="font-medium text-blue-900">
                {effectiveConfig.trigger_threshold_down_pct.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Min Stock %:</span>{' '}
              <span className="font-medium text-blue-900">
                {effectiveConfig.min_stock_pct.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Max Stock %:</span>{' '}
              <span className="font-medium text-blue-900">
                {effectiveConfig.max_stock_pct.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Max Trade %:</span>{' '}
              <span className="font-medium text-blue-900">
                {effectiveConfig.max_trade_pct_of_position.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Commission:</span>{' '}
              <span className="font-medium text-blue-900">
                {effectiveConfig.commission_rate.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Market Hours:</span>{' '}
              <span className="font-medium text-blue-900">
                {effectiveConfig.market_hours_policy === 'market-open-only'
                  ? 'Open-only'
                  : 'Open+After-hours'}
              </span>
            </div>
            <div>
              <span className="text-blue-700">Last Updated:</span>{' '}
              <span className="font-medium text-blue-900">
                {new Date(effectiveConfig.last_updated).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Editable Config Form */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Editable Config</h3>

        {/* Trigger Thresholds */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Trigger Thresholds</h4>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Up Threshold % <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={config.trigger_threshold_up_pct}
                onChange={(e) =>
                  handleChange('trigger_threshold_up_pct', parseFloat(e.target.value))
                }
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                  errors.trigger_threshold_up_pct ? 'border-red-300' : ''
                }`}
              />
              {errors.trigger_threshold_up_pct && (
                <p className="mt-1 text-sm text-red-600">{errors.trigger_threshold_up_pct}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Sell trigger when price exceeds anchor by this %
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Down Threshold % <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={config.trigger_threshold_down_pct}
                onChange={(e) =>
                  handleChange('trigger_threshold_down_pct', parseFloat(e.target.value))
                }
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                  errors.trigger_threshold_down_pct ? 'border-red-300' : ''
                }`}
              />
              {errors.trigger_threshold_down_pct && (
                <p className="mt-1 text-sm text-red-600">{errors.trigger_threshold_down_pct}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Buy trigger when price falls below anchor by this %
              </p>
            </div>
          </div>
        </div>

        {/* Guardrails */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Guardrails</h4>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Min Stock % <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={config.min_stock_pct}
                onChange={(e) => handleChange('min_stock_pct', parseFloat(e.target.value))}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                  errors.min_stock_pct ? 'border-red-300' : ''
                }`}
              />
              {errors.min_stock_pct && (
                <p className="mt-1 text-sm text-red-600">{errors.min_stock_pct}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Stock % <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={config.max_stock_pct}
                onChange={(e) => handleChange('max_stock_pct', parseFloat(e.target.value))}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                  errors.max_stock_pct ? 'border-red-300' : ''
                }`}
              />
              {errors.max_stock_pct && (
                <p className="mt-1 text-sm text-red-600">{errors.max_stock_pct}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Trade % of Position <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={config.max_trade_pct_of_position}
                onChange={(e) =>
                  handleChange('max_trade_pct_of_position', parseFloat(e.target.value))
                }
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                  errors.max_trade_pct_of_position ? 'border-red-300' : ''
                }`}
              />
              {errors.max_trade_pct_of_position && (
                <p className="mt-1 text-sm text-red-600">{errors.max_trade_pct_of_position}</p>
              )}
            </div>
          </div>
        </div>

        {/* Commission */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Commission</h4>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Commission Rate (% or bps) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={config.commission_rate}
                onChange={(e) => handleChange('commission_rate', parseFloat(e.target.value))}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                  errors.commission_rate ? 'border-red-300' : ''
                }`}
                placeholder="0.10"
              />
              {errors.commission_rate && (
                <p className="mt-1 text-sm text-red-600">{errors.commission_rate}</p>
              )}
            </div>
          </div>
        </div>

        {/* Market Hours Policy */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Market Hours Policy</h4>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Trade during:</p>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="market-hours"
                    value="market-open-only"
                    checked={config.market_hours_policy === 'market-open-only'}
                    onChange={() => handleChange('market_hours_policy', 'market-open-only')}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                  />
                  <span className="ml-2 text-sm text-gray-700">Trade during market open only</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="market-hours"
                    value="market-plus-after-hours"
                    checked={config.market_hours_policy === 'market-plus-after-hours'}
                    onChange={() => handleChange('market_hours_policy', 'market-plus-after-hours')}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                  />
                  <span className="ml-2 text-sm text-gray-700">Allow after-hours trading</span>
                </label>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Market Status:</p>
              <p className="text-sm text-gray-500">{marketStatus}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={handleReset}
            className="inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Reset to Template
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Config'}
          </button>
        </div>
      </div>
    </div>
  );
}







