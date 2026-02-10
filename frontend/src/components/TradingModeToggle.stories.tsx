import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import TradingModeToggle, { TradingMode } from './TradingModeToggle';

const meta: Meta<typeof TradingModeToggle> = {
  title: 'Components/TradingModeToggle',
  component: TradingModeToggle,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    mode: {
      control: 'radio',
      options: ['live', 'simulation'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const LiveMode: Story = {
  args: {
    mode: 'live',
    onModeChange: (mode) => console.log('Mode changed to:', mode),
    isSimulationRunning: false,
  },
};

export const SimulationMode: Story = {
  args: {
    mode: 'simulation',
    onModeChange: (mode) => console.log('Mode changed to:', mode),
    isSimulationRunning: false,
  },
};

export const SimulationRunning: Story = {
  args: {
    mode: 'simulation',
    onModeChange: (mode) => console.log('Mode changed to:', mode),
    isSimulationRunning: true,
  },
};

// Interactive example
const InteractiveExample = () => {
  const [mode, setMode] = useState<TradingMode>('live');
  const [isSimRunning, setIsSimRunning] = useState(false);

  const handleModeChange = (newMode: TradingMode) => {
    setMode(newMode);
    if (newMode === 'simulation') {
      // Simulate a running simulation
      setIsSimRunning(true);
      setTimeout(() => setIsSimRunning(false), 3000);
    }
  };

  return (
    <div className="space-y-4">
      <TradingModeToggle
        mode={mode}
        onModeChange={handleModeChange}
        isSimulationRunning={isSimRunning}
      />
      <div className="text-sm text-gray-600">
        Current mode: <span className="font-medium">{mode}</span>
        {isSimRunning && (
          <span className="ml-2 text-orange-600">(simulation running...)</span>
        )}
      </div>
    </div>
  );
};

export const Interactive: Story = {
  render: () => <InteractiveExample />,
};

// In context example
export const InHeader: Story = {
  render: () => (
    <div className="bg-white shadow-sm border-b p-4 flex items-center justify-between w-[600px]">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">AAPL Position</h1>
        <p className="text-sm text-gray-500">Apple Inc.</p>
      </div>
      <TradingModeToggle
        mode="live"
        onModeChange={(mode) => console.log('Mode changed to:', mode)}
      />
    </div>
  ),
};
