import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useWorkspace } from '../../WorkspaceContext';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';
import {
  portfolioScopedApi,
  PositionConfig,
  PortfolioConfig,
} from '../../../../services/portfolioScopedApi';
import { marketHoursService, MarketStatus } from '../../../../services/marketHoursService';
import LoadingSpinner from '../../../../components/shared/LoadingSpinner';
import { monitoringApi, SystemStatusResponse } from '../../../../lib/api';

// ── Worker Status Panel ───────────────────────────────────────────────────────

function WorkerStatusPanel() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const s = await monitoringApi.getSystemStatus();
        if (!cancelled) setStatus(s);
      } catch {
        // silent — worker status is non-critical
      }
    };

    load();
    const poll = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(poll); };
  }, []);

  // Countdown tick
  useEffect(() => {
    if (!status?.worker?.running || !status?.last_evaluation_time) {
      setCountdown(null);
      return;
    }

    const tick = () => {
      const lastMs = new Date(status.last_evaluation_time!).getTime();
      const intervalMs = (status.worker.interval_seconds ?? 60) * 1000;
      const nextMs = lastMs + intervalMs;
      const remaining = Math.max(0, Math.round((nextMs - Date.now()) / 1000));
      setCountdown(remaining);
    };

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [status]);

  const worker = status?.worker;
  const isRunning = worker?.running ?? false;
  const isEnabled = worker?.enabled ?? false;
  const intervalSec = worker?.interval_seconds ?? 60;
  const lastEval = status?.last_evaluation_time
    ? new Date(status.last_evaluation_time).toLocaleTimeString()
    : null;

  const formatCountdown = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}:${String(sec).padStart(2, '0')}` : `${sec}s`;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900">Worker Status</h3>

      <div className="grid grid-cols-2 gap-4">
        {/* Running */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isRunning ? 'bg-green-500' : 'bg-red-400'}`} />
          <div>
            <div className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide">Status</div>
            <div className={`text-sm font-bold ${isRunning ? 'text-green-700' : 'text-red-600'}`}>
              {isRunning ? 'Running' : 'Stopped'}
            </div>
          </div>
        </div>

        {/* Enabled */}
        <div>
          <div className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide">Auto-trade</div>
          <div className={`text-sm font-bold ${isEnabled ? 'text-green-700' : 'text-amber-600'}`}>
            {isEnabled ? 'Enabled' : 'Disabled'}
          </div>
        </div>

        {/* Interval */}
        <div>
          <div className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide">Cycle Interval</div>
          <div className="text-sm font-semibold text-gray-800">every {intervalSec}s</div>
        </div>

        {/* Last evaluation */}
        <div>
          <div className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide">Last Cycle</div>
          <div className="text-sm font-semibold text-gray-800">{lastEval ?? '—'}</div>
        </div>
      </div>

      {/* Countdown */}
      {isRunning && countdown !== null && (
        <div className="border-t border-gray-100 pt-3 flex items-center gap-3">
          <div className="text-2xl font-black text-indigo-600 tabular-nums">
            {formatCountdown(countdown)}
          </div>
          <div className="text-xs text-gray-500">until next evaluation</div>
        </div>
      )}

      {!isRunning && (
        <div className="border-t border-gray-100 pt-3 text-xs text-red-500 font-medium">
          Worker is not running — positions will not be evaluated
        </div>
      )}
    </div>
  );
}

export default function StrategyTab() {
  const { selectedPosition, portfolioId } = useWorkspace();
  const { selectedTenantId } = useTenantPortfolio();
  const tenantId = selectedTenantId || 'default';

  const [positionConfig, setPositionConfig] = useState<PositionConfig | null>(null);
  const [config, setConfig] = useState<PortfolioConfig | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const positionId = selectedPosition?.position_id;

  useEffect(() => {
    const loadConfig = async () => {
      if (!portfolioId || !positionId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const marketState = await marketHoursService.getMarketState();
        setMarketStatus(marketState.status);

        const pc = await portfolioScopedApi.getPositionConfig(tenantId, portfolioId, positionId);
        setPositionConfig(pc);
        setConfig({
          trigger_threshold_up_pct: pc.trigger_threshold_up_pct,
          trigger_threshold_down_pct: pc.trigger_threshold_down_pct,
          min_stock_pct: pc.min_stock_pct,
          max_stock_pct: pc.max_stock_pct,
          max_trade_pct_of_position: pc.max_trade_pct_of_position,
          commission_rate: pc.commission_rate,
          market_hours_policy: pc.allow_after_hours ? 'market-plus-after-hours' : 'market-open-only',
        });
      } catch (error) {
        console.error('Error loading config:', error);
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
  }, [portfolioId, positionId, tenantId]);

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
    if (!config || !portfolioId || !positionId) return;
    if (!validateConfig(config)) {
      toast.error('Please fix validation errors');
      return;
    }

    setSaving(true);
    try {
      await portfolioScopedApi.updatePositionConfig(tenantId, portfolioId, positionId, {
        trigger_threshold_up_pct: config.trigger_threshold_up_pct,
        trigger_threshold_down_pct: config.trigger_threshold_down_pct,
        min_stock_pct: config.min_stock_pct,
        max_stock_pct: config.max_stock_pct,
        max_trade_pct_of_position: config.max_trade_pct_of_position,
        commission_rate: config.commission_rate,
        allow_after_hours: config.market_hours_policy === 'market-plus-after-hours',
      });

      const confirmed = await portfolioScopedApi.getPositionConfig(tenantId, portfolioId, positionId);
      setPositionConfig(confirmed);
      setConfig({
        trigger_threshold_up_pct: confirmed.trigger_threshold_up_pct,
        trigger_threshold_down_pct: confirmed.trigger_threshold_down_pct,
        min_stock_pct: confirmed.min_stock_pct,
        max_stock_pct: confirmed.max_stock_pct,
        max_trade_pct_of_position: confirmed.max_trade_pct_of_position,
        commission_rate: confirmed.commission_rate,
        market_hours_policy: confirmed.allow_after_hours ? 'market-plus-after-hours' : 'market-open-only',
      });

      toast.success('Strategy saved successfully');
    } catch (error: any) {
      toast.error(error?.message || 'Failed to save strategy');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (!positionConfig) return;
    if (!window.confirm('Reset to portfolio defaults?')) return;
    setConfig({
      trigger_threshold_up_pct: positionConfig.trigger_threshold_up_pct,
      trigger_threshold_down_pct: positionConfig.trigger_threshold_down_pct,
      min_stock_pct: positionConfig.min_stock_pct,
      max_stock_pct: positionConfig.max_stock_pct,
      max_trade_pct_of_position: positionConfig.max_trade_pct_of_position,
      commission_rate: positionConfig.commission_rate,
      market_hours_policy: positionConfig.allow_after_hours ? 'market-plus-after-hours' : 'market-open-only',
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
      <div className="border rounded-lg p-4 bg-blue-50 border-blue-200">
        <p className="text-sm text-blue-700">
          {positionConfig?.is_position_specific
            ? `These settings are specific to ${selectedPosition.asset_symbol} and override portfolio defaults.`
            : `Using portfolio defaults. Saving will create a ${selectedPosition.asset_symbol}-specific override.`}
        </p>
      </div>

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

      <WorkerStatusPanel />
    </div>
  );
}
