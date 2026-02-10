import { useState, useMemo } from 'react';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Target,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Filter,
  Download,
} from 'lucide-react';

export type ActivityEventType =
  | 'position_created'
  | 'anchor_set'
  | 'trigger_detected'
  | 'order_submitted'
  | 'order_filled'
  | 'order_cancelled'
  | 'order_rejected'
  | 'hold'
  | 'buy'
  | 'sell'
  | 'error'
  | 'info'
  | 'dividend'
  | 'deposit'
  | 'withdrawal';

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: ActivityEventType | string;
  asset?: string;
  message: string;
  traceId?: string;
  details?: {
    stockValue?: number;
    cashValue?: number;
    totalValue?: number;
    qty?: number;
    price?: number;
    commission?: number;
    [key: string]: any;
  };
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
}

interface ActivityFeedProps {
  events: ActivityEvent[];
  maxItems?: number;
  showFilters?: boolean;
  showExport?: boolean;
  variant?: 'timeline' | 'table' | 'compact';
  emptyMessage?: string;
  onExport?: () => void;
  className?: string;
}

const eventIconMap: Record<string, typeof Activity> = {
  position_created: Activity,
  anchor_set: Target,
  trigger_detected: AlertCircle,
  order_submitted: TrendingUp,
  order_filled: CheckCircle,
  order_cancelled: XCircle,
  order_rejected: XCircle,
  hold: Info,
  buy: TrendingUp,
  sell: TrendingDown,
  error: XCircle,
  info: Info,
  dividend: CheckCircle,
  deposit: TrendingUp,
  withdrawal: TrendingDown,
};

const eventColorMap: Record<string, string> = {
  position_created: 'text-primary-600 bg-primary-100',
  anchor_set: 'text-warning-600 bg-warning-100',
  trigger_detected: 'text-danger-600 bg-danger-100',
  order_submitted: 'text-primary-600 bg-primary-100',
  order_filled: 'text-success-600 bg-success-100',
  order_cancelled: 'text-danger-600 bg-danger-100',
  order_rejected: 'text-danger-600 bg-danger-100',
  hold: 'text-gray-600 bg-gray-100',
  buy: 'text-success-600 bg-success-100',
  sell: 'text-danger-600 bg-danger-100',
  error: 'text-danger-600 bg-danger-100',
  info: 'text-blue-600 bg-blue-100',
  dividend: 'text-success-600 bg-success-100',
  deposit: 'text-success-600 bg-success-100',
  withdrawal: 'text-warning-600 bg-warning-100',
};

const badgeColorMap: Record<string, string> = {
  buy: 'badge-success',
  sell: 'badge-danger',
  hold: 'badge-info',
  error: 'badge-danger',
};

function getEventIcon(type: string) {
  const key = type.toLowerCase().replace(/\s+/g, '_');
  return eventIconMap[key] || Info;
}

function getEventColor(type: string) {
  const key = type.toLowerCase().replace(/\s+/g, '_');
  return eventColorMap[key] || 'text-gray-600 bg-gray-100';
}

function getBadgeColor(type: string) {
  const key = type.toLowerCase().replace(/\s+/g, '_');
  return badgeColorMap[key] || 'badge-info';
}

export default function ActivityFeed({
  events,
  maxItems,
  showFilters = false,
  showExport = false,
  variant = 'timeline',
  emptyMessage = 'No activity yet',
  onExport,
  className = '',
}: ActivityFeedProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  const filteredEvents = useMemo(() => {
    let result = events;
    if (filterType !== 'all') {
      result = events.filter((e) => e.type.toLowerCase().includes(filterType.toLowerCase()));
    }
    if (maxItems) {
      result = result.slice(0, maxItems);
    }
    return result;
  }, [events, filterType, maxItems]);

  const eventTypes = useMemo(() => {
    const types = new Set(events.map((e) => e.type));
    return Array.from(types);
  }, [events]);

  if (events.length === 0) {
    return (
      <div className={`card ${className}`}>
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Activity</h3>
          <p className="text-gray-500">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  // Compact list variant
  if (variant === 'compact') {
    return (
      <div className={className}>
        {showFilters && (
          <div className="flex items-center gap-3 mb-4">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="all">All Events</option>
              {eventTypes.map((type) => (
                <option key={type} value={type}>
                  {type.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        )}
        <ul className="space-y-2">
          {filteredEvents.map((event) => (
            <li
              key={event.id}
              className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg text-sm"
            >
              <span className="text-gray-500 text-xs whitespace-nowrap">
                {format(new Date(event.timestamp), 'HH:mm')}
              </span>
              {event.asset && <span className="font-semibold text-gray-900">{event.asset}</span>}
              <span className={`badge ${getBadgeColor(event.type)}`}>
                {event.type.replace(/_/g, ' ').toUpperCase()}
              </span>
              <span className="text-gray-600 truncate flex-1">{event.message}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  // Table variant
  if (variant === 'table') {
    return (
      <div className={className}>
        {(showFilters || showExport) && (
          <div className="flex items-center justify-between mb-4">
            {showFilters && (
              <div className="flex items-center gap-3">
                <Filter className="h-4 w-4 text-gray-400" />
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="all">All Events</option>
                  {eventTypes.map((type) => (
                    <option key={type} value={type}>
                      {type.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {showExport && onExport && (
              <button
                onClick={onExport}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
              >
                Export Excel <Download className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-10 px-4 py-3"></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
                {events.some((e) => e.asset) && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Asset
                  </th>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
                {events.some((e) => e.details?.totalValue) && (
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Value
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEvents.map((event) => (
                <>
                  <tr
                    key={event.id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
                  >
                    <td className="px-4 py-4">
                      {expandedId === event.id ? (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      )}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                      {format(new Date(event.timestamp), 'HH:mm:ss')}
                    </td>
                    {events.some((e) => e.asset) && (
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        {event.asset || '-'}
                      </td>
                    )}
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`badge ${getBadgeColor(event.type)}`}>
                        {event.type.replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">{event.message}</td>
                    {events.some((e) => e.details?.totalValue) && (
                      <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                        {event.details?.totalValue
                          ? `$${event.details.totalValue.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                            })}`
                          : '-'}
                      </td>
                    )}
                  </tr>
                  {expandedId === event.id && (
                    <tr className="bg-gray-50">
                      <td colSpan={6} className="px-14 py-4">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-sm">
                          {event.details?.stockValue !== undefined && (
                            <div>
                              <span className="text-gray-500 block mb-1">Stock Value</span>
                              <span className="font-medium text-gray-900">
                                ${event.details.stockValue.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {event.details?.cashValue !== undefined && (
                            <div>
                              <span className="text-gray-500 block mb-1">Cash Value</span>
                              <span className="font-medium text-gray-900">
                                ${event.details.cashValue.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {event.details?.qty !== undefined && (
                            <div>
                              <span className="text-gray-500 block mb-1">Quantity</span>
                              <span className="font-medium text-gray-900">{event.details.qty}</span>
                            </div>
                          )}
                          {event.details?.price !== undefined && (
                            <div>
                              <span className="text-gray-500 block mb-1">Price</span>
                              <span className="font-medium text-gray-900">
                                ${event.details.price.toFixed(2)}
                              </span>
                            </div>
                          )}
                          {event.traceId && (
                            <div>
                              <span className="text-gray-500 block mb-1">Trace ID</span>
                              <Link
                                to={`/audit?trace_id=${event.traceId}`}
                                className="text-primary-600 hover:text-primary-700 flex items-center gap-1"
                              >
                                {event.traceId.substring(0, 12)}...{' '}
                                <ExternalLink className="h-3 w-3" />
                              </Link>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // Timeline variant (default)
  return (
    <div className={`card ${className}`}>
      {showFilters && (
        <div className="flex items-center gap-3 mb-6">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All Events</option>
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type.replace(/_/g, ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="flow-root">
        <ul className="-mb-8">
          {filteredEvents.map((event, eventIdx) => {
            const Icon = getEventIcon(event.type);
            const colorClasses = getEventColor(event.type);

            return (
              <li key={event.id}>
                <div className="relative pb-8">
                  {eventIdx !== filteredEvents.length - 1 ? (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  ) : null}
                  <div className="relative flex space-x-3">
                    <div>
                      <span
                        className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${colorClasses}`}
                      >
                        <Icon className="h-4 w-4" />
                      </span>
                    </div>
                    <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            {event.type.replace(/_/g, ' ').toUpperCase()}
                          </h4>
                          {event.asset && (
                            <span className="text-xs font-bold text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
                              {event.asset}
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            {format(new Date(event.timestamp), 'MMM d, yyyy h:mm:ss a')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{event.message}</p>

                        {event.inputs && Object.keys(event.inputs).length > 0 && (
                          <div className="mt-2">
                            <details className="text-xs">
                              <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                                View Inputs
                              </summary>
                              <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                {JSON.stringify(event.inputs, null, 2)}
                              </pre>
                            </details>
                          </div>
                        )}

                        {event.outputs && Object.keys(event.outputs).length > 0 && (
                          <div className="mt-2">
                            <details className="text-xs">
                              <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                                View Outputs
                              </summary>
                              <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                {JSON.stringify(event.outputs, null, 2)}
                              </pre>
                            </details>
                          </div>
                        )}

                        {event.traceId && (
                          <Link
                            to={`/audit?trace_id=${event.traceId}`}
                            className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1 mt-2"
                          >
                            View trace <ExternalLink className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
