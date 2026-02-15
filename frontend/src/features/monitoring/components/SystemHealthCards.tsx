import { Activity, Clock, AlertTriangle, Cpu } from 'lucide-react';
import type { SystemStatusResponse } from '../../../lib/api';

interface Props {
  data: SystemStatusResponse;
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

const statusColors: Record<string, string> = {
  healthy: 'text-green-700 bg-green-50 border-green-200',
  degraded: 'text-amber-700 bg-amber-50 border-amber-200',
  unhealthy: 'text-red-700 bg-red-50 border-red-200',
};

const statusDot: Record<string, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-amber-500',
  unhealthy: 'bg-red-500',
};

function workerLabel(worker: SystemStatusResponse['worker']): string {
  if (!worker.enabled) return 'Disabled';
  return worker.running ? 'Running' : 'Stopped';
}

function workerColor(worker: SystemStatusResponse['worker']): string {
  if (!worker.enabled) return 'text-gray-700 bg-gray-50 border-gray-200';
  return worker.running
    ? 'text-green-700 bg-green-50 border-green-200'
    : 'text-red-700 bg-red-50 border-red-200';
}

export default function SystemHealthCards({ data }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Overall Status */}
      <div className={`rounded-xl border p-5 ${statusColors[data.status] || statusColors.unhealthy}`}>
        <div className="flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4" />
          <span className="text-xs font-bold uppercase tracking-wider">System Status</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full ${statusDot[data.status] || statusDot.unhealthy} animate-pulse`} />
          <span className="text-xl font-black capitalize">{data.status}</span>
        </div>
      </div>

      {/* Uptime */}
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <div className="flex items-center gap-2 mb-3">
          <Clock className="h-4 w-4 text-gray-500" />
          <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Uptime</span>
        </div>
        <span className="text-xl font-black text-gray-900">
          {formatUptime(data.uptime_seconds)}
        </span>
      </div>

      {/* Worker Status */}
      <div className={`rounded-xl border p-5 ${workerColor(data.worker)}`}>
        <div className="flex items-center gap-2 mb-3">
          <Cpu className="h-4 w-4" />
          <span className="text-xs font-bold uppercase tracking-wider">Worker</span>
        </div>
        <span className="text-xl font-black">{workerLabel(data.worker)}</span>
        {data.worker.enabled && (
          <p className="text-xs mt-1 opacity-75">
            Interval: {data.worker.interval_seconds}s
          </p>
        )}
      </div>

      {/* Active Alerts */}
      <div
        className={`rounded-xl border p-5 ${
          data.active_alert_count > 0
            ? 'text-red-700 bg-red-50 border-red-200'
            : 'text-green-700 bg-green-50 border-green-200'
        }`}
      >
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-xs font-bold uppercase tracking-wider">Active Alerts</span>
        </div>
        <span className="text-xl font-black">{data.active_alert_count}</span>
      </div>
    </div>
  );
}
