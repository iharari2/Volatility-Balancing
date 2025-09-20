import { useState, useEffect } from 'react';
import { useRunSimulation } from '../hooks/useSimulation';
import TradingModeToggle, { TradingMode } from '../components/TradingModeToggle';
import SimulationControls, { SimulationConfig } from '../components/SimulationControls';
import SimulationResults, { SimulationResult } from '../components/SimulationResults';
import SimulationAnalytics from '../components/SimulationAnalytics';
import SimulationProgressBar from '../components/SimulationProgressBar';
import { useConfiguration } from '../contexts/ConfigurationContext';
import { portfolioStateApi } from '../lib/api';
import { BarChart3, Play, Settings, Save, Download } from 'lucide-react';

export default function Simulation() {
  const [mode, setMode] = useState<TradingMode>('simulation');
  const [activeTab, setActiveTab] = useState<'simulation' | 'analytics'>('simulation');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);
  const [isSavingState, setIsSavingState] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [showProgressBar, setShowProgressBar] = useState(false);

  const runSimulationMutation = useRunSimulation();
  const { configuration, updateConfiguration } = useConfiguration();

  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig>({
    ticker: 'AAPL',
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days ago
    endDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Yesterday
    initialCash: 10000,
    initialAssetValue: 10000, // 50/50 split: equal cash and asset values
    initialAssetUnits: 0,
    triggerThresholdPct: configuration.triggerThresholdPct,
    rebalanceRatio: configuration.rebalanceRatio,
    commissionRate: configuration.commissionRate,
    minNotional: configuration.minNotional,
    allowAfterHours: configuration.allowAfterHours,
    guardrails: {
      minStockAllocPct: configuration.guardrails.minStockAllocPct,
      maxStockAllocPct: configuration.guardrails.maxStockAllocPct,
    },
  });

  // Update simulation config when shared configuration changes
  useEffect(() => {
    setSimulationConfig((prev) => ({
      ...prev,
      triggerThresholdPct: configuration.triggerThresholdPct,
      rebalanceRatio: configuration.rebalanceRatio,
      commissionRate: configuration.commissionRate,
      minNotional: configuration.minNotional,
      allowAfterHours: configuration.allowAfterHours,
      guardrails: {
        minStockAllocPct: configuration.guardrails.minStockAllocPct,
        maxStockAllocPct: configuration.guardrails.maxStockAllocPct,
      },
    }));
  }, [configuration]);

  // Auto-calculate asset value to maintain 50/50 split when cash changes
  useEffect(() => {
    setSimulationConfig((prev) => ({
      ...prev,
      initialAssetValue: prev.initialCash, // 50/50 split: equal cash and asset values
    }));
  }, [simulationConfig.initialCash]);

  // Load saved portfolio state on component mount
  useEffect(() => {
    const loadSavedState = async () => {
      try {
        const savedState = await portfolioStateApi.getActivePortfolioState();
        if (savedState) {
          setSimulationConfig((prev) => ({
            ...prev,
            ticker: savedState.ticker,
            initialCash: savedState.initial_cash,
            initialAssetValue: savedState.initial_asset_value,
            initialAssetUnits: savedState.initial_asset_units,
          }));
        }
      } catch (error) {
        console.log('No saved portfolio state found');
      }
    };
    loadSavedState();
  }, []);

  // Update asset value when loading saved state (maintain 50/50 split if asset value is 0)
  useEffect(() => {
    if (simulationConfig.initialAssetValue === 0 && simulationConfig.initialCash > 0) {
      setSimulationConfig((prev) => ({
        ...prev,
        initialAssetValue: prev.initialCash, // 50/50 split: equal cash and asset values
      }));
    }
  }, [simulationConfig.initialCash, simulationConfig.initialAssetValue]);

  const handleSavePortfolioState = async () => {
    setIsSavingState(true);
    try {
      const stateName = `Portfolio ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`;
      await portfolioStateApi.savePortfolioState({
        name: stateName,
        description: `Portfolio state saved on ${new Date().toLocaleString()}`,
        initial_cash: simulationConfig.initialCash,
        initial_asset_value: simulationConfig.initialAssetValue,
        initial_asset_units: simulationConfig.initialAssetUnits,
        current_cash: simulationConfig.initialCash, // In simulation, current = initial
        current_asset_value: simulationConfig.initialAssetValue,
        current_asset_units: simulationConfig.initialAssetUnits,
        ticker: simulationConfig.ticker,
      });
      alert('Portfolio state saved successfully!');
    } catch (error) {
      console.error('Error saving portfolio state:', error);
      alert('Error saving portfolio state. Please try again.');
    } finally {
      setIsSavingState(false);
    }
  };

  const handleRunSimulation = async () => {
    setIsSimulationRunning(true);
    setSimulationResult(null);
    setSimulationId(null);
    setShowProgressBar(true);

    try {
      // Validate dates before running simulation
      const startDate = new Date(simulationConfig.startDate);
      const endDate = new Date(simulationConfig.endDate);
      const today = new Date();
      const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

      if (startDate > today || endDate > today) {
        alert(
          'Simulation dates cannot be in the future. Please select dates within the last 30 days.',
        );
        return;
      }

      if (endDate < thirtyDaysAgo) {
        alert(
          'End date is too far in the past. yfinance only supports data from the last 30 days.',
        );
        return;
      }

      const result = await runSimulationMutation.mutateAsync(simulationConfig);
      setSimulationResult(result);

      // Extract simulation ID from result if available
      if (result.simulation_id) {
        setSimulationId(result.simulation_id);
      }
    } catch (error) {
      console.error('Simulation failed:', error);
      alert(`Simulation failed: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSimulationRunning(false);
      setShowProgressBar(false);
    }
  };

  const handleStopSimulation = () => {
    setIsSimulationRunning(false);
    // Note: In a real implementation, you'd need to cancel the running simulation
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trading & Simulation</h1>
          <p className="text-gray-600">
            Run live trades or simulate strategies with historical data
          </p>
        </div>
        <TradingModeToggle
          mode={mode}
          onModeChange={setMode}
          isSimulationRunning={isSimulationRunning}
        />
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('simulation')}
            className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'simulation'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Play className="w-4 h-4" />
            <span>Simulation</span>
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            disabled={!simulationResult}
            className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analytics'
                ? 'border-primary-500 text-primary-600'
                : simulationResult
                ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                : 'border-transparent text-gray-300 cursor-not-allowed'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics</span>
          </button>
        </nav>
      </div>

      {/* Data Availability Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Data Availability</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                Simulation data is limited to the last 30 days due to yfinance API constraints. For
                longer periods, daily data will be used instead of 1-minute intervals.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab-specific content */}
      {activeTab === 'simulation' ? (
        <div className="space-y-6">
          {/* Mode-specific content */}
          {mode === 'simulation' ? (
            <div className="space-y-6">
              {/* Portfolio State Management */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Portfolio State</h3>
                  <button
                    onClick={handleSavePortfolioState}
                    disabled={isSavingState}
                    className="btn btn-primary btn-sm"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {isSavingState ? 'Saving...' : 'Save State'}
                  </button>
                </div>
                <p className="text-sm text-gray-600">
                  Save your current portfolio configuration to restore it when you restart the
                  system.
                </p>
              </div>

              {/* Simulation Controls */}
              <SimulationControls
                config={simulationConfig}
                onConfigChange={setSimulationConfig}
                onRunSimulation={handleRunSimulation}
                onStopSimulation={handleStopSimulation}
                isRunning={isSimulationRunning}
                onSharedConfigChange={updateConfiguration}
              />

              {/* Simulation Progress Bar */}
              <SimulationProgressBar
                simulationId={simulationId}
                show={showProgressBar}
                onComplete={() => {
                  console.log('Simulation completed!');
                  setShowProgressBar(false);
                }}
                onError={(error) => {
                  console.error('Simulation error:', error);
                  alert(`Simulation error: ${error}`);
                  setShowProgressBar(false);
                }}
              />

              {/* Simulation Results */}
              <SimulationResults result={simulationResult} isLoading={isSimulationRunning} />
            </div>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Live Trading Mode</h3>
                <p className="text-gray-500 mb-4">
                  Live trading functionality is available in the Trading page.
                </p>
                <a href="/trading" className="btn btn-primary">
                  Go to Live Trading
                </a>
              </div>
            </div>
          )}
        </div>
      ) : (
        <SimulationAnalytics
          data={
            simulationResult
              ? {
                  simulationResult,
                  dailyReturns: simulationResult.daily_returns || [],
                  priceData: simulationResult.price_data || [],
                  tradeLog: simulationResult.trade_log || [],
                  triggerAnalysis: simulationResult.trigger_analysis || [],
                }
              : null
          }
          isLoading={isSimulationRunning}
        />
      )}
    </div>
  );
}
