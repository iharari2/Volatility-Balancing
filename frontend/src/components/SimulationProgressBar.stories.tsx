import type { Meta, StoryObj } from '@storybook/react';
import { useState, useEffect } from 'react';
import SimulationProgressBar from './SimulationProgressBar';
import { Button } from './ui/button';

const meta: Meta<typeof SimulationProgressBar> = {
  title: 'Components/SimulationProgressBar',
  component: SimulationProgressBar,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Note: Since the component polls for data, we show it in different states
// by controlling the simulationId prop

export const Initializing: Story = {
  args: {
    simulationId: 'sim-123',
    show: true,
  },
};

export const Hidden: Story = {
  args: {
    simulationId: 'sim-123',
    show: false,
  },
};

export const NoSimulation: Story = {
  args: {
    simulationId: null,
    show: true,
  },
};

// Interactive demo that simulates progress
const ProgressDemo = () => {
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const startSimulation = () => {
    setSimulationId(`sim-${Date.now()}`);
    setCompleted(false);
  };

  const handleComplete = () => {
    setCompleted(true);
  };

  return (
    <div className="space-y-4 max-w-xl">
      <div className="flex items-center space-x-4">
        <Button onClick={startSimulation} disabled={simulationId !== null && !completed}>
          {simulationId && !completed ? 'Running...' : 'Start Simulation'}
        </Button>
        {completed && (
          <span className="text-green-600 font-medium">Simulation completed!</span>
        )}
      </div>

      <SimulationProgressBar
        simulationId={simulationId}
        onComplete={handleComplete}
        onError={(error) => console.error('Simulation error:', error)}
        show={simulationId !== null}
      />

      <p className="text-sm text-gray-500">
        Click "Start Simulation" to see the progress bar animation.
        The component simulates progress internally when no real API data is available.
      </p>
    </div>
  );
};

export const InteractiveDemo: Story = {
  render: () => <ProgressDemo />,
};

// Static preview showing the visual states
export const VisualStates: Story = {
  render: () => (
    <div className="space-y-6 max-w-xl">
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Processing (30%)</h4>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <h3 className="text-sm font-medium text-gray-900">Running Simulation</h3>
            </div>
            <div className="text-xs text-gray-500">12s</div>
          </div>
          <div className="mb-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Fetching market data...</span>
              <span>30%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '30%' }} />
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Step 2 of 8</span>
            <span>fetching data</span>
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Processing (70%)</h4>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <h3 className="text-sm font-medium text-gray-900">Running Simulation</h3>
            </div>
            <div className="text-xs text-gray-500">28s</div>
          </div>
          <div className="mb-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Computing performance metrics...</span>
              <span>70%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full transition-all" style={{ width: '70%' }} />
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Step 6 of 8</span>
            <span>computing metrics</span>
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Completed</h4>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 text-green-500">✓</div>
              <h3 className="text-sm font-medium text-gray-900">Simulation Complete</h3>
            </div>
            <div className="text-xs text-gray-500">45s</div>
          </div>
          <div className="mb-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Simulation finished</span>
              <span>100%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: '100%' }} />
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Step 8 of 8</span>
            <span>complete</span>
          </div>
          <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
            Simulation completed successfully! Results are now available.
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Error</h4>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 text-red-500">✗</div>
              <h3 className="text-sm font-medium text-gray-900">Simulation Error</h3>
            </div>
            <div className="text-xs text-gray-500">15s</div>
          </div>
          <div className="mb-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Failed to fetch market data</span>
              <span>25%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-red-500 h-2 rounded-full" style={{ width: '25%' }} />
            </div>
          </div>
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            Failed to fetch historical data for ticker INVALID
          </div>
        </div>
      </div>
    </div>
  ),
};
