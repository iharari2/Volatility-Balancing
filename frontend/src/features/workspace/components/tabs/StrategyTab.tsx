import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useWorkspace } from '../../WorkspaceContext';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';
import {
  portfolioScopedApi,
  EffectiveConfig,
  PortfolioConfig,
} from '../../../../services/portfolioScopedApi';
import { marketHoursService, MarketStatus } from '../../../../services/marketHoursService';
import LoadingSpinner from '../../../../components/shared/LoadingSpinner';

export default function StrategyTab() {
  const { selectedPosition, portfolioId } = useWorkspace();
  const { selectedTenantId } = useTenantPortfolio();
  const tenantId = selectedTenantId || 'default';

  const [effectiveConfig, setEffectiveConfig] = useState<EffectiveConfig | null>(null);
  const [editableConfig, setEditableConfig] = useState<PortfolioConfig | null>(null);
  const [config, setConfig] = useState<PortfolioConfig | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isPositionSpecific, setIsPositionSpecific] = useState(false);

  useEffect(() => {
    const loadConfig = async () => {
      if (!portfolioId || !selectedPosition) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);

        // Load market status
        const marketState = await marketHoursService.getMarketState();
        setMarketStatus(marketState.status);

        // Load effective config
        const effective = await portfolioScopedApi.getEffectiveConfig(tenantId, portfolioId);
        setEffectiveConfig(effective);

        // Load position-specific config
        try {
          const posConfig = await portfolioScopedApi.getPositionConfig(
            tenantId,
            portfolioId,
            selectedPosition.position_id
          );
          setConfig({
            trigger_threshold_up_pct: posConfig.trigger_threshold_up_pct,
            trigger_threshold_down_pct: posConfig.trigger_threshold_down_pct,
            min_stock_pct: posConfig.min_stock_pct,
            max_stock_pct: posConfig.max_stock_pct,
            max_trade_pct_of_position: posConfig.max_trade_pct_of_position,
            commission_rate: posConfig.commission_rate,
            market_hours_policy: 'market-open-only',
          });
          setIsPositionSpecific(posConfig.is_position_specific);
        } catch (error) {
          // Fall back to effective config
          setConfig({
            trigger_threshold_up_pct: effective.trigger_threshold_up_pct,
            trigger_threshold_down_pct: effective.trigger_threshold_down_pct,
            min_stock_pct: effective.min_stock_pct,
            max_stock_pct: effective.max_stock_pct,
            max_trade_pct_of_position: effective.max_trade_pct_of_position,
            commission_rate: effective.commission_rate,
            market_hours_policy: effective.market_hours_policy,
          });
          setIsPositionSpecific(false);
        }
      } catch (error) {
        console.error('Error loading config:', error);
        // Set default values
        setConfig({
          trigger_threshold_up_pct: 3.0,
          trigger_threshold_down_pct: -3.0,
          min_stock_pct: 25.0,
          max_stock_pct: 75.0,
          max_trade_pct_of_position: 50.0,
          commission_rate: 0.1,
          market_hours_policy: 'market-open-only',
        });
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [portfolioId, selectedPosition?.position_id, tenantId]);

  const validateConfig = (cfg: PortfolioConfig): boolean => {
    const newErrors: Record<string, string> = {};

    if (cfg.trigger_threshold_up_pct <= 0) {
      newErrors.trigger_threshold_up_pct = 'Up threshold must be > 0';
    }
    // Down threshold is stored as negative, but we validate the absolute value
    if (Math.abs(cfg.trigger_threshold_down_pct) <= 0) {
      newErrors.trigger_threshold_down_pct = 'Down threshold must be > 0';
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
    if (errors[field]) {
      const newErrors = { ...errors };
      delete newErrors[field];
      setErrors(newErrors);
    }
  };

  const handleSave = async () => {
    if (!config || !portfolioId || !selectedPosition) return;
    if (!validateConfig(config)) {
      toast.error('Please fix validation errors');
      return;
    }

    setSaving(true);
    try {
      await portfolioScopedApi.updatePositionConfig(
        tenantId,
        portfolioId,
        selectedPosition.position_id,
        {
          trigger_threshold_up_pct: config.trigger_threshold_up_pct,
          trigger_threshold_down_pct: config.trigger_threshold_down_pct,
          min_stock_pct: config.min_stock_pct,
          max_stock_pct: config.max_stock_pct,
          max_trade_pct_of_position: config.max_trade_pct_of_position,
          commission_rate: config.commission_rate,
        }
      );
      setIsPositionSpecific(true);

      // Reload effective config to show updated values in the "Current Effective Settings" panel
      try {
        const effective = await portfolioScopedApi.getEffectiveConfig(tenantId, portfolioId);
        setEffectiveConfig(effective);
      } catch (reloadError) {
        console.warn('Failed to reload effective config after save:', reloadError);
      }

      toast.success('Strategy saved successfully');
    } catch (error: any) {
      toast.error(error?.message || 'Failed to save strategy');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (!effectiveConfig) return;
    if (!window.confirm('Reset to portfolio defaults?')) return;

    setConfig({
      trigger_threshold_up_pct: effectiveConfig.trigger_threshold_up_pct,
      trigger_threshold_down_pct: effectiveConfig.trigger_threshold_down_pct,
      min_stock_pct: effectiveConfig.min_stock_pct,
      max_stock_pct: effectiveConfig.max_stock_pct,
      max_trade_pct_of_position: effectiveConfig.max_trade_pct_of_position,
      commission_rate: effectiveConfig.commission_rate,
      market_hours_policy: effectiveConfig.market_hours_policy,
    });
  };

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading strategy configuration..." />
      </div>
    );
  }

  if (!selectedPosition || !config) {
    return (
      <div className="p-8 text-center text-gray-500">
        Select a position to configure its strategy
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-gray-900">
          {selectedPosition.asset_symbol} Strategy
        </h2>
        <p className="text-sm text-gray-500">Configure trigger thresholds and guardrails</p>
      </div>

      {/* Position-specific indicator */}
      <div
        className={`border rounded-lg p-4 ${
          isPositionSpecific ? 'bg-success-50 border-success-200' : 'bg-warning-50 border-warning-200'
        }`}
      >
        <p className={`text-sm ${isPositionSpecific ? 'text-success-700' : 'text-warning-700'}`}>
          {isPositionSpecific
            ? 'This position has its own strategy settings (independent from portfolio defaults).'
            : 'Using portfolio-level strategy settings. Save to create position-specific settings.'}
        </p>
      </div>

      {/* Effective Config Summary */}
      {effectiveConfig && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-primary-900 mb-3">
            Current Effective Settings
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-primary-600">Up Trigger</span>
              <p className="font-semibold text-primary-900">
                +{effectiveConfig.trigger_threshold_up_pct.toFixed(1)}%
              </p>
            </div>
            <div>
              <span className="text-primary-600">Down Trigger</span>
              <p className="font-semibold text-primary-900">
                {effectiveConfig.trigger_threshold_down_pct.toFixed(1)}%
              </p>
            </div>
            <div>
              <span className="text-primary-600">Min Stock</span>
              <p className="font-semibold text-primary-900">
                {effectiveConfig.min_stock_pct.toFixed(0)}%
              </p>
            </div>
            <div>
              <span className="text-primary-600">Max Stock</span>
              <p className="font-semibold text-primary-900">
                {effectiveConfig.max_stock_pct.toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Editable Form */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-6">
        {/* Trigger Thresholds */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Trigger Thresholds</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Up Threshold %
              </label>
              <input
                type="number"
                step="0.1"
                value={config.trigger_threshold_up_pct}
                onChange={(e) =>
                  handleChange('trigger_threshold_up_pct', parseFloat(e.target.value))
                }
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                  errors.trigger_threshold_up_pct ? 'border-danger-300' : 'border-gray-300'
                }`}
              />
              {errors.trigger_threshold_up_pct && (
                <p className="mt-1 text-xs text-danger-600">{errors.trigger_threshold_up_pct}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">Sell trigger when price rises</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Down Threshold %
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">-</span>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={Math.abs(config.trigger_threshold_down_pct)}
                  onChange={(e) => {
                    const absValue = Math.abs(parseFloat(e.target.value) || 0);
                    handleChange('trigger_threshold_down_pct', -absValue);
                  }}
                  className={`w-full pl-7 pr-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    errors.trigger_threshold_down_pct ? 'border-danger-300' : 'border-gray-300'
                  }`}
                />
              </div>
              {errors.trigger_threshold_down_pct && (
                <p className="mt-1 text-xs text-danger-600">{errors.trigger_threshold_down_pct}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">Buy trigger when price falls (stored as negative)</p>
            </div>
          </div>
        </div>

        {/* Guardrails */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Allocation Guardrails</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Stock %
              </label>
              <input
                type="number"
                step="1"
                value={config.min_stock_pct}
                onChange={(e) => handleChange('min_stock_pct', parseFloat(e.target.value))}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                  errors.min_stock_pct ? 'border-danger-300' : 'border-gray-300'
                }`}
              />
              {errors.min_stock_pct && (
                <p className="mt-1 text-xs text-danger-600">{errors.min_stock_pct}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Stock %
              </label>
              <input
                type="number"
                step="1"
                value={config.max_stock_pct}
                onChange={(e) => handleChange('max_stock_pct', parseFloat(e.target.value))}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                  errors.max_stock_pct ? 'border-danger-300' : 'border-gray-300'
                }`}
              />
              {errors.max_stock_pct && (
                <p className="mt-1 text-xs text-danger-600">{errors.max_stock_pct}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Trade %
              </label>
              <input
                type="number"
                step="1"
                value={config.max_trade_pct_of_position}
                onChange={(e) =>
                  handleChange('max_trade_pct_of_position', parseFloat(e.target.value))
                }
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                  errors.max_trade_pct_of_position ? 'border-danger-300' : 'border-gray-300'
                }`}
              />
              {errors.max_trade_pct_of_position && (
                <p className="mt-1 text-xs text-danger-600">{errors.max_trade_pct_of_position}</p>
              )}
            </div>
          </div>
        </div>

        {/* Commission */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Commission</h3>
          <div className="max-w-xs">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Commission Rate %
            </label>
            <input
              type="number"
              step="0.01"
              value={config.commission_rate}
              onChange={(e) => handleChange('commission_rate', parseFloat(e.target.value))}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                errors.commission_rate ? 'border-danger-300' : 'border-gray-300'
              }`}
            />
            {errors.commission_rate && (
              <p className="mt-1 text-xs text-danger-600">{errors.commission_rate}</p>
            )}
          </div>
        </div>

        {/* Market Hours */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Market Hours Policy</h3>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                name="market-hours"
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
                checked={config.market_hours_policy === 'market-plus-after-hours'}
                onChange={() => handleChange('market_hours_policy', 'market-plus-after-hours')}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-700">Allow after-hours trading</span>
            </label>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Current market status: <span className="font-medium">{marketStatus}</span>
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Reset to Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Strategy'}
          </button>
        </div>
      </div>
    </div>
  );
}
