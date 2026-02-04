import { useState } from 'react';
import { Play } from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';

interface SimulationSetupProps {
  onRun: (config: SimulationConfig) => void;
  isRunning: boolean;
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
  // Trigger thresholds (as percentages, e.g., 3 = 3%)
  triggerThresholdPct: number;
  initialCash: number;
  // Comparison ticker for SIM-3
  comparisonTicker: string;
}

export default function SimulationSetup({ onRun, isRunning }: SimulationSetupProps) {
  const { positions } = usePortfolio();
  const [config, setConfig] = useState<SimulationConfig>({
    asset: positions[0]?.ticker || 'AAPL',
    startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    strategy: 'portfolio',
    mode: 'single',
    resolution: '30min',
    allowAfterHours: true,
    triggerThresholdPct: 3,
    initialCash: 10000,
    comparisonTicker: '',
  });

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
              <option value="1min">1 Minute</option>
              <option value="5min">5 Minutes</option>
              <option value="15min">15 Minutes</option>
              <option value="30min">30 Minutes</option>
              <option value="1hour">1 Hour</option>
              <option value="daily">Daily</option>
            </select>
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
            <label className="label">Initial Capital</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={config.initialCash}
                onChange={(e) => setConfig({ ...config, initialCash: parseFloat(e.target.value) || 10000 })}
                min={100}
                step={1000}
                className="input pl-7"
              />
            </div>
          </div>
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
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Buy when price drops {config.triggerThresholdPct}%, sell when it rises {config.triggerThresholdPct}%
            </p>
          </div>
        </div>

        <div>
          <label className="label">Strategy Configuration</label>
          <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-100">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="strategy"
                value="portfolio"
                checked={config.strategy === 'portfolio'}
                onChange={(e) =>
                  setConfig({ ...config, strategy: e.target.value as SimulationConfig['strategy'] })
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
              />
              <span className="ml-2 text-sm font-medium text-gray-900">
                Current Portfolio Config
              </span>
            </label>
            <div className="flex items-center gap-3">
              <input
                type="radio"
                name="strategy"
                value="template"
                checked={config.strategy === 'template'}
                onChange={(e) =>
                  setConfig({ ...config, strategy: e.target.value as SimulationConfig['strategy'] })
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
              />
              <select
                value={config.template || 'conservative'}
                onChange={(e) => setConfig({ ...config, template: e.target.value })}
                disabled={config.strategy !== 'template'}
                className="flex-1 input py-1 text-sm disabled:opacity-50"
              >
                <option value="conservative">Conservative Template</option>
                <option value="default">Standard Template</option>
                <option value="aggressive">Aggressive Template</option>
              </select>
            </div>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="strategy"
                value="custom"
                checked={config.strategy === 'custom'}
                onChange={(e) =>
                  setConfig({ ...config, strategy: e.target.value as SimulationConfig['strategy'] })
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
              />
              <span className="ml-2 text-sm font-medium text-gray-900">Custom Overrides</span>
              <button
                disabled={config.strategy !== 'custom'}
                className="ml-auto text-xs font-bold text-primary-600 uppercase hover:text-primary-800 disabled:opacity-30"
              >
                Configure
              </button>
            </label>
          </div>
        </div>

        <div className="pt-4">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="w-full btn btn-primary py-3 flex items-center justify-center shadow-lg"
          >
            {isRunning ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Running...
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
