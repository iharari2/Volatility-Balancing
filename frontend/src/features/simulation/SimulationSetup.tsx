import { useState, useEffect, useMemo } from 'react';
import { Play } from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';

// Max history yfinance supports per resolution
const RESOLUTION_MAX_DAYS: Record<string, number> = {
  '1min':  7,
  '5min':  60,
  '15min': 60,
  '30min': 60,
  '1hour': 730,
  'daily': 99999,
};

interface SimulationSetupProps {
  onRun: (config: SimulationConfig) => void;
  isRunning: boolean;
  runningMsg?: string;
  initialConfig?: Partial<SimulationConfig>;
}

interface SimulationConfig {
  asset: string;
  startDate: string;
  endDate: string;
  strategy: 'portfolio' | 'template' | 'custom';
  template?: string;
  mode: 'single' | 'sweep';
  resolution: '1min' | '5min' | '15min' | '30min' | '1hour' | 'daily';
  allowAfterHours: boolean;
  triggerThresholdPct: number;
  rebalanceRatio: number;
  commissionRate: number;
  minStockAllocPct: number;
  maxStockAllocPct: number;
  maxTradePct: number;
  initialCash: number;
  initialStock: number;
  comparisonTicker: string;
}

export { type SimulationConfig };

export default function SimulationSetup({ onRun, isRunning, runningMsg, initialConfig }: SimulationSetupProps) {
  const { positions } = usePortfolio();
  const TEMPLATES = {
    conservative: { triggerThresholdPct: 2, rebalanceRatio: 1.2, commissionRate: 0.001, minStockAllocPct: 30, maxStockAllocPct: 70 },
    default:      { triggerThresholdPct: 3, rebalanceRatio: 1.6667, commissionRate: 0.001, minStockAllocPct: 25, maxStockAllocPct: 75 },
    aggressive:   { triggerThresholdPct: 5, rebalanceRatio: 2.0, commissionRate: 0.001, minStockAllocPct: 20, maxStockAllocPct: 80 },
  };

  const defaults: SimulationConfig = {
    asset: positions[0]?.ticker || 'AAPL',
    startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    strategy: 'portfolio',
    mode: 'single',
    resolution: 'daily',
    allowAfterHours: true,
    triggerThresholdPct: 3,
    rebalanceRatio: 1.6667,
    commissionRate: 0.001,
    minStockAllocPct: 25,
    maxStockAllocPct: 75,
    maxTradePct: 20,
    initialCash: 10000,
    initialStock: 0,
    comparisonTicker: '',
  };
  const [config, setConfig] = useState<SimulationConfig>({ ...defaults, ...initialConfig });

  // Update config when initialConfig changes (e.g., rerun with modified params)
  useEffect(() => {
    if (initialConfig) {
      setConfig(prev => ({ ...prev, ...initialConfig }));
    }
  }, [initialConfig]);

  const resolutionWarning = useMemo(() => {
    if (!config.startDate || !config.endDate) return null;
    const days = (new Date(config.endDate).getTime() - new Date(config.startDate).getTime()) / 86400000;
    const maxDays = RESOLUTION_MAX_DAYS[config.resolution] ?? 99999;
    if (days > maxDays) {
      return `${config.resolution} data is only available for the last ${maxDays} days. Use Daily or 1 Hour for longer periods.`;
    }
    return null;
  }, [config.startDate, config.endDate, config.resolution]);

  const handleRun = () => {
    onRun(config);
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Simulation Setup</h2>

      <div className="space-y-6">
        <div>
          <label className="label">Asset to Simulate</label>
          <div className="relative">
            <input
              type="text"
              list="ticker-suggestions"
              value={config.asset}
              onChange={(e) => setConfig({ ...config, asset: e.target.value.toUpperCase() })}
              placeholder="Enter any ticker (e.g., AAPL, TSLA, MSFT)"
              className="input"
            />
            <datalist id="ticker-suggestions">
              {positions.map((pos) => (
                <option key={pos.id} value={pos.ticker || pos.asset} />
              ))}
              {/* Common tickers as suggestions */}
              <option value="AAPL" />
              <option value="MSFT" />
              <option value="GOOGL" />
              <option value="AMZN" />
              <option value="TSLA" />
              <option value="META" />
              <option value="NVDA" />
              <option value="SPY" />
              <option value="QQQ" />
              <option value="VOO" />
            </datalist>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Type any ticker symbol available on Yahoo Finance
          </p>
        </div>

        <div>
          <label className="label">Compare With (Optional)</label>
          <div className="relative">
            <input
              type="text"
              list="comparison-ticker-suggestions"
              value={config.comparisonTicker}
              onChange={(e) => setConfig({ ...config, comparisonTicker: e.target.value.toUpperCase() })}
              placeholder="e.g., SPY, QQQ, or leave empty"
              className="input"
            />
            <datalist id="comparison-ticker-suggestions">
              <option value="SPY">S&P 500 ETF</option>
              <option value="QQQ">Nasdaq 100 ETF</option>
              <option value="VOO">Vanguard S&P 500</option>
              <option value="IWM">Russell 2000</option>
              <option value="DIA">Dow Jones ETF</option>
              <option value="VTI">Total Stock Market</option>
            </datalist>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Compare strategy performance against another ticker (e.g., SPY for market benchmark)
          </p>
        </div>

        <div>
          <label className="label">Simulation Period</label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs text-gray-400 mb-1 block uppercase">Start Date</span>
              <input
                type="date"
                value={config.startDate}
                onChange={(e) => setConfig({ ...config, startDate: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <span className="text-xs text-gray-400 mb-1 block uppercase">End Date</span>
              <input
                type="date"
                value={config.endDate}
                onChange={(e) => setConfig({ ...config, endDate: e.target.value })}
                className="input"
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Price Resolution</label>
            <select
              value={config.resolution}
              onChange={(e) =>
                setConfig({
                  ...config,
                  resolution: e.target.value as SimulationConfig['resolution'],
                })
              }
              className="input"
            >
              <option value="1min">1 Minute (last 7 days only)</option>
              <option value="5min">5 Minutes (last 60 days only)</option>
              <option value="15min">15 Minutes (last 60 days only)</option>
              <option value="30min">30 Minutes (last 60 days only)</option>
              <option value="1hour">1 Hour (last 2 years)</option>
              <option value="daily">Daily (full history)</option>
            </select>
            {resolutionWarning && (
              <p className="mt-1 text-xs text-amber-600 font-medium">⚠ {resolutionWarning}</p>
            )}
          </div>
          <div className="flex items-end">
            <label className="flex items-center cursor-pointer mb-2">
              <input
                type="checkbox"
                checked={config.allowAfterHours}
                onChange={(e) => setConfig({ ...config, allowAfterHours: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Extended Hours</span>
            </label>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Initial Cash</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={config.initialCash}
                onChange={(e) => setConfig({ ...config, initialCash: parseFloat(e.target.value) || 0 })}
                min={0}
                step={1000}
                className="input pl-7"
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Total: ${(config.initialCash + config.initialStock).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <label className="label">Initial Stock ($)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={config.initialStock}
                onChange={(e) => setConfig({ ...config, initialStock: parseFloat(e.target.value) || 0 })}
                min={0}
                step={1000}
                className="input pl-7"
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Value of stock held at sim start
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Trigger Threshold</label>
            <div className="relative">
              <input
                type="number"
                value={config.triggerThresholdPct}
                onChange={(e) => setConfig({ ...config, triggerThresholdPct: parseFloat(e.target.value) || 3 })}
                min={0.1}
                max={50}
                step={0.5}
                className="input pr-7"
                disabled={config.strategy === 'portfolio'}
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Buy when price drops {config.triggerThresholdPct}%, sell when it rises {config.triggerThresholdPct}%
            </p>
          </div>
          <div>
            <label className="label">Max Trade per Trigger</label>
            <div className="relative">
              <input
                type="number"
                value={config.maxTradePct}
                onChange={(e) => setConfig({ ...config, maxTradePct: parseFloat(e.target.value) || 20 })}
                min={1}
                max={100}
                step={5}
                className="input pr-7"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Max % of total position value traded in a single order (default 20%)
            </p>
          </div>
        </div>

        <div>
          <label className="label">Strategy</label>
          <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex gap-4">
              {(['portfolio', 'template', 'custom'] as const).map((s) => (
                <label key={s} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="strategy"
                    value={s}
                    checked={config.strategy === s}
                    onChange={() => {
                      if (s === 'template') {
                        const tpl = TEMPLATES[(config.template as keyof typeof TEMPLATES) || 'default'];
                        setConfig({ ...config, strategy: s, ...tpl });
                      } else {
                        setConfig({ ...config, strategy: s });
                      }
                    }}
                    className="h-4 w-4 text-primary-600"
                  />
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {s === 'portfolio' ? 'Current Portfolio' : s === 'template' ? 'Template' : 'Custom'}
                  </span>
                </label>
              ))}
            </div>

            {config.strategy === 'template' && (
              <select
                value={config.template || 'default'}
                onChange={(e) => {
                  const tpl = TEMPLATES[e.target.value as keyof typeof TEMPLATES] || TEMPLATES.default;
                  setConfig({ ...config, template: e.target.value, ...tpl });
                }}
                className="input py-1 text-sm"
              >
                <option value="conservative">Conservative (2% trigger, ratio 1.2, 30–70%)</option>
                <option value="default">Standard (3% trigger, ratio 1.667, 25–75%)</option>
                <option value="aggressive">Aggressive (5% trigger, ratio 2.0, 20–80%)</option>
              </select>
            )}

            {config.strategy === 'portfolio' && (
              <p className="text-xs text-gray-500">
                Uses the saved config of the selected position. Trigger threshold, rebalance ratio, and guardrails are loaded from the live position.
              </p>
            )}
          </div>
        </div>

        {config.strategy !== 'portfolio' && (
          <div>
            <label className="label">Strategy Parameters</label>
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
              <div>
                <label className="text-xs font-medium text-gray-600 uppercase mb-1 block">Rebalance Ratio</label>
                <input
                  type="number"
                  value={config.rebalanceRatio}
                  onChange={(e) => setConfig({ ...config, rebalanceRatio: parseFloat(e.target.value) || 1.6667 })}
                  min={0.5}
                  max={5}
                  step={0.1}
                  className="input"
                />
                <p className="text-xs text-gray-400 mt-1">Order sizing multiplier (default 1.6667)</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 uppercase mb-1 block">Commission Rate</label>
                <div className="relative">
                  <input
                    type="number"
                    value={+(config.commissionRate * 100).toFixed(4)}
                    onChange={(e) => setConfig({ ...config, commissionRate: (parseFloat(e.target.value) || 0.1) / 100 })}
                    min={0}
                    max={5}
                    step={0.05}
                    className="input pr-7"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">Per-trade commission (default 0.1%)</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 uppercase mb-1 block">Min Stock Allocation</label>
                <div className="relative">
                  <input
                    type="number"
                    value={config.minStockAllocPct}
                    onChange={(e) => setConfig({ ...config, minStockAllocPct: parseFloat(e.target.value) || 25 })}
                    min={0}
                    max={config.maxStockAllocPct - 5}
                    step={5}
                    className="input pr-7"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">Lower guardrail: buy when below this</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 uppercase mb-1 block">Max Stock Allocation</label>
                <div className="relative">
                  <input
                    type="number"
                    value={config.maxStockAllocPct}
                    onChange={(e) => setConfig({ ...config, maxStockAllocPct: parseFloat(e.target.value) || 75 })}
                    min={config.minStockAllocPct + 5}
                    max={100}
                    step={5}
                    className="input pr-7"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">Upper guardrail: sell when above this</p>
              </div>
            </div>
          </div>
        )}

        <div className="pt-4">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="w-full btn btn-primary py-3 flex items-center justify-center shadow-lg"
          >
            {isRunning ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                {runningMsg || 'Running…'}
              </div>
            ) : (
              <>
                <Play className="h-5 w-5 mr-2 fill-current" /> Run Simulation
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
