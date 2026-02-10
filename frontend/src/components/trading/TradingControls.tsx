import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Play,
  Pause,
  Power,
  PowerOff,
  RefreshCw,
  Clock,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';

export interface WorkerStatus {
  engineState: 'NOT_CONFIGURED' | 'READY' | 'RUNNING' | 'PAUSED' | 'ERROR';
  workerActive: boolean;
  workerIntervalSeconds: number;
  lastCycleTime: string | null;
  lastCycleResult: string | null;
  lastCycleTraceId: string | null;
}

interface TradingControlsProps {
  portfolioId: string;
  positionId?: string;
  workerStatus: WorkerStatus | null;
  onToggleWorker?: () => Promise<void>;
  onRunManualCycle?: () => Promise<void>;
  onRefresh?: () => void;
  refreshInterval?: number;
  onRefreshIntervalChange?: (interval: number) => void;
  variant?: 'full' | 'compact' | 'minimal';
  className?: string;
}

const engineStateColors: Record<string, string> = {
  RUNNING: 'badge-success',
  READY: 'badge-info',
  PAUSED: 'badge-warning',
  ERROR: 'badge-danger',
  NOT_CONFIGURED: 'badge-secondary',
};

export default function TradingControls({
  portfolioId,
  positionId,
  workerStatus,
  onToggleWorker,
  onRunManualCycle,
  onRefresh,
  refreshInterval = 30,
  onRefreshIntervalChange,
  variant = 'full',
  className = '',
}: TradingControlsProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [isRunningCycle, setIsRunningCycle] = useState(false);

  const handleToggleWorker = async () => {
    if (!onToggleWorker) return;

    setIsToggling(true);
    try {
      await onToggleWorker();
    } catch (error: any) {
      toast.error(`Failed to toggle worker: ${error.message || 'Unknown error'}`);
    } finally {
      setIsToggling(false);
    }
  };

  const handleRunManualCycle = async () => {
    if (!onRunManualCycle) return;

    setIsRunningCycle(true);
    try {
      await onRunManualCycle();
      toast.success('Manual cycle completed');
    } catch (error: any) {
      toast.error(`Failed to run cycle: ${error.message || 'Unknown error'}`);
    } finally {
      setIsRunningCycle(false);
    }
  };

  // Minimal variant - just status badge
  if (variant === 'minimal') {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <span
          className={`badge ${
            workerStatus ? engineStateColors[workerStatus.engineState] || 'badge-secondary' : 'badge-secondary'
          }`}
        >
          {workerStatus?.engineState || 'UNKNOWN'}
        </span>
        {workerStatus?.workerActive && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
        )}
      </div>
    );
  }

  // Compact variant - status and toggle button
  if (variant === 'compact') {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        <span
          className={`badge ${
            workerStatus ? engineStateColors[workerStatus.engineState] || 'badge-secondary' : 'badge-secondary'
          }`}
        >
          {workerStatus?.engineState || 'UNKNOWN'}
        </span>

        {onToggleWorker && (
          <button
            onClick={handleToggleWorker}
            disabled={isToggling}
            className={`btn btn-sm flex items-center gap-1 ${
              workerStatus?.workerActive ? 'btn-danger' : 'btn-success'
            }`}
          >
            {isToggling ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : workerStatus?.workerActive ? (
              <>
                <PowerOff className="h-3 w-3" /> Stop
              </>
            ) : (
              <>
                <Power className="h-3 w-3" /> Start
              </>
            )}
          </button>
        )}

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4 text-gray-600" />
          </button>
        )}
      </div>
    );
  }

  // Full variant - complete control panel
  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Trading Controls</h2>
        <span
          className={`badge ${
            workerStatus ? engineStateColors[workerStatus.engineState] || 'badge-secondary' : 'badge-secondary'
          }`}
        >
          {workerStatus?.engineState || 'NOT CONFIGURED'}
        </span>
      </div>

      {!workerStatus ? (
        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          <AlertCircle className="h-5 w-5 text-gray-400" />
          <span className="text-sm text-gray-600">Worker status unavailable</span>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-4">
            {onToggleWorker && (
              <button
                onClick={handleToggleWorker}
                disabled={isToggling}
                className={`btn flex items-center gap-2 ${
                  workerStatus.workerActive ? 'btn-danger' : 'btn-success'
                }`}
              >
                {isToggling ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : workerStatus.workerActive ? (
                  <>
                    <PowerOff className="h-4 w-4" /> Suspend Worker
                  </>
                ) : (
                  <>
                    <Power className="h-4 w-4" /> Enable Worker
                  </>
                )}
              </button>
            )}

            {onRunManualCycle && (
              <button
                onClick={handleRunManualCycle}
                disabled={isRunningCycle}
                className="btn btn-secondary flex items-center gap-2"
              >
                {isRunningCycle ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Run Manual Cycle
              </button>
            )}

            {onRefresh && (
              <button
                onClick={onRefresh}
                className="btn btn-secondary flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            )}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div>
              <span className="text-sm text-gray-500 block mb-1">Worker Interval</span>
              {onRefreshIntervalChange ? (
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <select
                    value={refreshInterval}
                    onChange={(e) => onRefreshIntervalChange(Number(e.target.value))}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value={10}>10s</option>
                    <option value={30}>30s</option>
                    <option value={60}>60s</option>
                    <option value={300}>5m</option>
                  </select>
                </div>
              ) : (
                <span className="font-medium text-gray-900">
                  {workerStatus.workerIntervalSeconds}s
                </span>
              )}
            </div>

            <div>
              <span className="text-sm text-gray-500 block mb-1">Last Cycle Time</span>
              <span className="font-medium text-gray-900">
                {workerStatus.lastCycleTime
                  ? new Date(workerStatus.lastCycleTime).toLocaleTimeString()
                  : 'N/A'}
              </span>
            </div>

            <div>
              <span className="text-sm text-gray-500 block mb-1">Last Cycle Result</span>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">
                  {workerStatus.lastCycleResult || 'N/A'}
                </span>
                {workerStatus.lastCycleTraceId && (
                  <Link
                    to={`/audit?trace_id=${workerStatus.lastCycleTraceId}`}
                    className="text-primary-600 hover:text-primary-700 flex items-center gap-1 text-xs"
                  >
                    View Trace <ExternalLink className="h-3 w-3" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Hook to manage worker status
export function useWorkerStatus() {
  const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchWorkerStatus = async () => {
    try {
      const { request } = await import('../../lib/api');
      const status = await request<{
        running: boolean;
        enabled: boolean;
        interval_seconds: number;
      }>('/v1/trading/worker/status');

      setWorkerStatus({
        engineState: status.enabled ? 'RUNNING' : 'PAUSED',
        workerActive: status.enabled,
        workerIntervalSeconds: status.interval_seconds,
        lastCycleTime: new Date().toISOString(),
        lastCycleResult: 'Success',
        lastCycleTraceId: null,
      });
    } catch (error) {
      console.error('Error fetching worker status:', error);
      setWorkerStatus({
        engineState: 'ERROR',
        workerActive: false,
        workerIntervalSeconds: 60,
        lastCycleTime: null,
        lastCycleResult: null,
        lastCycleTraceId: null,
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleWorker = async () => {
    if (!workerStatus) return;

    const { request } = await import('../../lib/api');
    const newEnabledState = !workerStatus.workerActive;

    const result = await request<{
      message: string;
      enabled: boolean;
      running: boolean;
      interval_seconds: number;
    }>('/v1/trading/worker/enable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: newEnabledState }),
    });

    setWorkerStatus({
      ...workerStatus,
      workerActive: result.enabled,
      engineState: result.enabled ? 'RUNNING' : 'PAUSED',
      workerIntervalSeconds: result.interval_seconds,
    });

    toast.success(result.message || `Worker ${newEnabledState ? 'enabled' : 'disabled'}`);
  };

  return {
    workerStatus,
    loading,
    fetchWorkerStatus,
    toggleWorker,
  };
}
