import { useState } from 'react';
import { CheckCircle, Eye } from 'lucide-react';
import type { AlertResponse } from '../../../lib/api';

type StatusFilter = 'all' | 'active' | 'acknowledged' | 'resolved';

interface Props {
  alerts: AlertResponse[];
  total: number;
  onAcknowledge: (id: string) => void;
  onResolve: (id: string) => void;
  acknowledging: boolean;
  resolving: boolean;
}

const severityStyles: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  warning: 'bg-amber-100 text-amber-800',
};

const statusStyles: Record<string, string> = {
  active: 'bg-red-100 text-red-700',
  acknowledged: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
};

const tabs: { key: StatusFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'acknowledged', label: 'Acknowledged' },
  { key: 'resolved', label: 'Resolved' },
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function AlertsTable({
  alerts,
  total,
  onAcknowledge,
  onResolve,
  acknowledging,
  resolving,
}: Props) {
  const [filter, setFilter] = useState<StatusFilter>('all');

  const filtered = filter === 'all' ? alerts : alerts.filter((a) => a.status === filter);

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-bold text-gray-900">
          Alerts <span className="text-gray-400 font-normal">({total})</span>
        </h3>
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                filter === tab.key
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="px-5 py-10 text-center text-sm text-gray-400">
          No alerts matching this filter.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                <th className="px-5 py-3">Severity</th>
                <th className="px-5 py-3">Title</th>
                <th className="px-5 py-3 hidden lg:table-cell">Detail</th>
                <th className="px-5 py-3 hidden md:table-cell">Condition</th>
                <th className="px-5 py-3">Created</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((alert) => (
                <tr key={alert.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 text-xs font-bold rounded-full ${
                        severityStyles[alert.severity] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {alert.severity}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-medium text-gray-900">{alert.title}</td>
                  <td className="px-5 py-3 text-gray-500 hidden lg:table-cell max-w-xs truncate">
                    {alert.detail}
                  </td>
                  <td className="px-5 py-3 text-gray-500 hidden md:table-cell">
                    <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                      {alert.condition}
                    </code>
                  </td>
                  <td className="px-5 py-3 text-gray-500 whitespace-nowrap">
                    {formatDate(alert.created_at)}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 text-xs font-bold rounded-full ${
                        statusStyles[alert.status] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {alert.status}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex gap-1">
                      {alert.status === 'active' && (
                        <button
                          onClick={() => onAcknowledge(alert.id)}
                          disabled={acknowledging}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-bold text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
                          title="Acknowledge"
                        >
                          <Eye className="h-3 w-3" />
                          Ack
                        </button>
                      )}
                      {alert.status !== 'resolved' && (
                        <button
                          onClick={() => onResolve(alert.id)}
                          disabled={resolving}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-bold text-green-700 bg-green-50 rounded-lg hover:bg-green-100 disabled:opacity-50 transition-colors"
                          title="Resolve"
                        >
                          <CheckCircle className="h-3 w-3" />
                          Resolve
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
