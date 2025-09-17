import { useState } from 'react';
import { useRunSimulation } from '../hooks/useSimulation';
import TradingModeToggle, { TradingMode } from '../components/TradingModeToggle';
import SimulationControls, { SimulationConfig } from '../components/SimulationControls';
import SimulationResults, { SimulationResult } from '../components/SimulationResults';

export default function Simulation() {
  const [mode, setMode] = useState<TradingMode>('simulation');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);

  const runSimulationMutation = useRunSimulation();

  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig>({
    ticker: 'AAPL',
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    endDate: new Date().toISOString().split('T')[0], // Today
    initialCash: 10000,
    triggerThresholdPct: 0.03,
    rebalanceRatio: 1.6667,
    commissionRate: 0.0001,
    minNotional: 100,
    allowAfterHours: false,
    guardrails: {
      minStockAllocPct: 0.25,
      maxStockAllocPct: 0.75,
    },
  });

  const handleRunSimulation = async () => {
    setIsSimulationRunning(true);
    setSimulationResult(null);

    try {
      const result = await runSimulationMutation.mutateAsync(simulationConfig);
      setSimulationResult(result);
    } catch (error) {
      console.error('Simulation failed:', error);
      // You could add a toast notification here
    } finally {
      setIsSimulationRunning(false);
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

      {/* Mode-specific content */}
      {mode === 'simulation' ? (
        <div className="space-y-6">
          {/* Simulation Controls */}
          <SimulationControls
            config={simulationConfig}
            onConfigChange={setSimulationConfig}
            onRunSimulation={handleRunSimulation}
            onStopSimulation={handleStopSimulation}
            isRunning={isSimulationRunning}
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
  );
}
