import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioScopedApi, PortfolioConfig } from '../../services/portfolioScopedApi';

export default function StrategyConfigForm() {
  const { selectedTenantId, selectedPortfolioId } = useTenantPortfolio();
  const tenantId = selectedTenantId || 'default';

  const [config, setConfig] = useState<PortfolioConfig>({
    trigger_threshold_up_pct: 3.0,
    trigger_threshold_down_pct: -3.0,
    min_stock_pct: 25.0,
    max_stock_pct: 75.0,
    max_trade_pct_of_position: 50.0,
    commission_rate: 0.1,
    market_hours_policy: 'market-open-only',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const loadConfig = async () => {
      if (!selectedPortfolioId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const editableConfig = await portfolioScopedApi.getConfig(tenantId, selectedPortfolioId);
        setConfig(editableConfig);
      } catch (error) {
        console.error('Error loading config:', error);
        // Keep default values on error
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [tenantId, selectedPortfolioId]);

  const validateConfig = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (config.trigger_threshold_up_pct <= 0) {
      newErrors.trigger_threshold_up_pct = 'Up threshold must be > 0';
    }
    if (config.trigger_threshold_down_pct >= 0) {
      newErrors.trigger_threshold_down_pct = 'Down threshold must be < 0';
    }
    if (config.min_stock_pct < 0 || config.min_stock_pct >= config.max_stock_pct) {
      newErrors.min_stock_pct = 'Min stock % must be >= 0 and < max stock %';
    }
    if (config.max_stock_pct > 100 || config.max_stock_pct <= config.min_stock_pct) {
      newErrors.max_stock_pct = 'Max stock % must be <= 100 and > min stock %';
    }
    if (config.max_trade_pct_of_position <= 0 || config.max_trade_pct_of_position > 100) {
      newErrors.max_trade_pct_of_position = 'Max trade % must be > 0 and <= 100';
    }
    if (config.commission_rate < 0) {
      newErrors.commission_rate = 'Commission rate must be >= 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field: keyof PortfolioConfig, value: number | string) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSave = async () => {
    if (!selectedPortfolioId) {
      toast.error('No portfolio selected');
      return;
    }
    if (!validateConfig()) {
      toast.error('Please fix validation errors');
      return;
    }

    setSaving(true);
    try {
      await portfolioScopedApi.updateConfig(tenantId, selectedPortfolioId, config);
      toast.success('Config saved successfully');
    } catch (error: any) {
      console.error('Error saving config:', error);
      toast.error(error?.message || 'Failed to save config');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (!window.confirm('Reset to default values? This will discard your changes.')) {
      return;
    }
    setConfig({
      trigger_threshold_up_pct: 3.0,
      trigger_threshold_down_pct: -3.0,
      min_stock_pct: 25.0,
      max_stock_pct: 75.0,
      max_trade_pct_of_position: 50.0,
      commission_rate: 0.1,
      market_hours_policy: 'market-open-only',
    });
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading config...</div>;
  }

  if (!selectedPortfolioId) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Please select a portfolio to configure strategy</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Configuration</h3>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Trigger Thresholds</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">Up Threshold %</label>
            <input
              type="number"
              step="0.01"
              value={config.trigger_threshold_up_pct}
              onChange={(e) =>
                handleChange('trigger_threshold_up_pct', parseFloat(e.target.value) || 0)
              }
              className={`mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                errors.trigger_threshold_up_pct ? 'border-red-300' : 'border-gray-300'
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
            <label className="block text-sm font-medium text-gray-700">Down Threshold %</label>
            <input
              type="number"
              step="0.01"
              value={config.trigger_threshold_down_pct}
              onChange={(e) =>
                handleChange('trigger_threshold_down_pct', parseFloat(e.target.value) || 0)
              }
              className={`mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                errors.trigger_threshold_down_pct ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.trigger_threshold_down_pct && (
              <p className="mt-1 text-sm text-red-600">{errors.trigger_threshold_down_pct}</p>
            )}
            <p className="mt-1 text-sm text-gray-500">
              Buy trigger when price falls below anchor by this % (negative value)
            </p>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Guardrails</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">Min Stock %</label>
            <input
              type="number"
              step="1"
              value={config.min_stock_pct}
              onChange={(e) => handleChange('min_stock_pct', parseFloat(e.target.value) || 0)}
              className={`mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                errors.min_stock_pct ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.min_stock_pct && (
              <p className="mt-1 text-sm text-red-600">{errors.min_stock_pct}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Max Stock %</label>
            <input
              type="number"
              step="1"
              value={config.max_stock_pct}
              onChange={(e) => handleChange('max_stock_pct', parseFloat(e.target.value) || 0)}
              className={`mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                errors.max_stock_pct ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.max_stock_pct && (
              <p className="mt-1 text-sm text-red-600">{errors.max_stock_pct}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Max Trade % of Position
            </label>
            <input
              type="number"
              step="1"
              value={config.max_trade_pct_of_position}
              onChange={(e) =>
                handleChange('max_trade_pct_of_position', parseFloat(e.target.value) || 0)
              }
              className={`mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                errors.max_trade_pct_of_position ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.max_trade_pct_of_position && (
              <p className="mt-1 text-sm text-red-600">{errors.max_trade_pct_of_position}</p>
            )}
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Commission</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Commission Rate (%)
            </label>
            <input
              type="number"
              step="0.01"
              value={config.commission_rate}
              onChange={(e) => handleChange('commission_rate', parseFloat(e.target.value) || 0)}
              className={`mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                errors.commission_rate ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="0.10"
            />
            {errors.commission_rate && (
              <p className="mt-1 text-sm text-red-600">{errors.commission_rate}</p>
            )}
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Market Hours</h4>
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
                <span className="ml-2 text-sm text-gray-700">Market Hours Only</span>
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
                <span className="ml-2 text-sm text-gray-700">Market Hours + After Hours</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          onClick={handleReset}
          className="inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Reset to Default
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
  );
}
