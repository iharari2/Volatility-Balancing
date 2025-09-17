import { useState } from 'react';
import { Play, BarChart3, Settings, AlertCircle } from 'lucide-react';

export type TradingMode = 'live' | 'simulation';

interface TradingModeToggleProps {
  mode: TradingMode;
  onModeChange: (mode: TradingMode) => void;
  isSimulationRunning?: boolean;
  className?: string;
}

export default function TradingModeToggle({
  mode,
  onModeChange,
  isSimulationRunning = false,
  className = '',
}: TradingModeToggleProps) {
  return (
    <div className={`flex items-center space-x-1 bg-gray-100 rounded-lg p-1 ${className}`}>
      <button
        onClick={() => onModeChange('live')}
        disabled={isSimulationRunning}
        className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
          mode === 'live'
            ? 'bg-white text-primary-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        } ${isSimulationRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <Play className="w-4 h-4 mr-2" />
        Live Trading
      </button>
      
      <button
        onClick={() => onModeChange('simulation')}
        className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
          mode === 'simulation'
            ? 'bg-white text-primary-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`}
      >
        <BarChart3 className="w-4 h-4 mr-2" />
        Simulation
      </button>
    </div>
  );
}

