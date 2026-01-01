/**
 * PositionActions Component
 *
 * Reusable component for position actions (tick execution).
 * Decoupled from PositionCockpit to allow reuse in other contexts.
 */

import { useState } from 'react';
import { Play } from 'lucide-react';
import toast from 'react-hot-toast';
import { tickPosition } from '../../api/positions';

interface PositionActionsProps {
  positionId: string;
  onAfterAction?: () => void;
  showRun10Ticks?: boolean;
}

export default function PositionActions({
  positionId,
  onAfterAction,
  showRun10Ticks = false,
}: PositionActionsProps) {
  const [runningTick, setRunningTick] = useState(false);
  const [runningTicks, setRunningTicks] = useState(false);

  const handleRunTick = async () => {
    if (runningTick || !positionId) return;

    setRunningTick(true);
    try {
      toast.loading('Running 1 tick...', { id: 'tick-running' });

      const result = await tickPosition(positionId);
      const action = result?.cycle_result?.action || 'HOLD';

      toast.success(`Tick executed. Action: ${action}`, {
        id: 'tick-running',
      });

      // Notify parent to refresh data
      if (onAfterAction) {
        onAfterAction();
      }
    } catch (error: any) {
      toast.error(`Failed to run tick: ${error.message || 'Unknown error'}`, {
        id: 'tick-running',
      });
    } finally {
      setRunningTick(false);
    }
  };

  const handleRun10Ticks = async () => {
    if (runningTicks || !positionId) return;

    setRunningTicks(true);
    try {
      toast.loading('Running 10 ticks...', { id: 'ticks-running' });

      let lastAction = 'HOLD';
      for (let i = 0; i < 10; i++) {
        try {
          const result = await tickPosition(positionId);
          lastAction = result?.cycle_result?.action || 'HOLD';
          // Small delay between ticks to avoid overwhelming the server
          if (i < 9) {
            await new Promise((resolve) => setTimeout(resolve, 100));
          }
        } catch (tickError: any) {
          console.error(`Tick ${i + 1} failed:`, tickError);
          // Continue with remaining ticks even if one fails
        }
      }

      toast.success(`10 ticks completed. Last action: ${lastAction}`, {
        id: 'ticks-running',
      });

      // Notify parent to refresh data
      if (onAfterAction) {
        onAfterAction();
      }
    } catch (error: any) {
      toast.error(`Error running ticks: ${error.message || 'Unknown error'}`, {
        id: 'ticks-running',
      });
    } finally {
      setRunningTicks(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleRunTick}
        disabled={runningTick || runningTicks}
        className={`px-3 py-1.5 rounded-lg text-sm font-bold border transition-colors flex items-center ${
          runningTick || runningTicks
            ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
            : 'text-green-600 bg-green-50 border-green-200 hover:bg-green-100'
        }`}
        title="Execute one deterministic trading evaluation cycle"
      >
        <Play className={`h-4 w-4 mr-2 ${runningTick ? 'animate-spin' : ''}`} />
        {runningTick ? 'Running...' : 'Run 1 Tick'}
      </button>

      {showRun10Ticks && (
        <button
          onClick={handleRun10Ticks}
          disabled={runningTick || runningTicks}
          className={`px-3 py-1.5 rounded-lg text-sm font-bold border transition-colors flex items-center ${
            runningTick || runningTicks
              ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
              : 'text-blue-600 bg-blue-50 border-blue-200 hover:bg-blue-100'
          }`}
          title="Execute 10 ticks in sequence"
        >
          <Play className={`h-4 w-4 mr-2 ${runningTicks ? 'animate-spin' : ''}`} />
          {runningTicks ? 'Running 10...' : 'Run 10 Ticks'}
        </button>
      )}
    </div>
  );
}







