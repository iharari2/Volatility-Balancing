import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Copy, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface TraceEvent {
  event_type: string;
  timestamp: string;
  payload: any;
}

interface Trace {
  trace_id: string;
  time: string;
  asset: string;
  summary: string;
  source: 'worker' | 'manual' | 'simulation';
  events?: TraceEvent[];
}

export default function AuditTrailPage() {
  const { selectedPortfolio } = useTenantPortfolio();
  const { positions } = usePortfolio();
  const [searchParams, setSearchParams] = useSearchParams();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  // Filter state
  const [assetFilter, setAssetFilter] = useState(searchParams.get('asset') || '');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sourceFilter, setSourceFilter] = useState<string>('any');
  const [traceIdFilter, setTraceIdFilter] = useState(searchParams.get('trace_id') || '');

  useEffect(() => {
    if (traceIdFilter) {
      setSearchParams({ trace_id: traceIdFilter });
      loadTraceDetails(traceIdFilter);
    } else {
      loadTraces();
    }
  }, [traceIdFilter, assetFilter, startDate, endDate, sourceFilter]);

  const loadTraces = async () => {
    setLoading(true);
    try {
      // TODO: Fetch traces from API
      // For now, return empty list instead of mock data
      setTraces([]);
    } catch (error) {
      console.error('Error loading traces:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTraceDetails = async (traceId: string) => {
    setLoading(true);
    try {
      // TODO: Fetch trace details from API
      // For now, return null instead of mock data
      setSelectedTrace(null);
    } catch (error) {
      console.error('Error loading trace details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTraceClick = (trace: Trace) => {
    if (trace.trace_id === selectedTrace?.trace_id) {
      setSelectedTrace(null);
    } else {
      loadTraceDetails(trace.trace_id);
    }
  };

  const toggleEventExpansion = (eventType: string) => {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventType)) {
      newExpanded.delete(eventType);
    } else {
      newExpanded.add(eventType);
    }
    setExpandedEvents(newExpanded);
  };

  const handleCopyTraceId = (traceId: string) => {
    navigator.clipboard.writeText(traceId);
    // TODO: Show toast notification
  };

  const handleExportTrace = (trace: Trace) => {
    const dataStr = JSON.stringify(trace, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trace_${trace.trace_id}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!selectedPortfolio) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">Please select a portfolio to view audit trail</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Trail</h1>
          <p className="text-sm text-gray-500 mt-1">
            System logs and decision traces for {selectedPortfolio.name}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Panel - Filters */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
            <div className="space-y-4">
              <div>
                <label className="label">Asset</label>
                <select
                  value={assetFilter}
                  onChange={(e) => setAssetFilter(e.target.value)}
                  className="input"
                >
                  <option value="">Any</option>
                  {positions.map((pos) => (
                    <option key={pos.id} value={pos.ticker || pos.asset}>
                      {pos.ticker || pos.asset}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Date Range</label>
                <div className="space-y-2">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="input"
                  />
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label className="label">Trace ID</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={traceIdFilter}
                    onChange={(e) => setTraceIdFilter(e.target.value)}
                    className="input"
                    placeholder="8f0d-33bf..."
                  />
                </div>
                <button
                  onClick={() => loadTraceDetails(traceIdFilter)}
                  className="mt-3 w-full btn btn-primary py-2 text-sm"
                >
                  Search Trace
                </button>
              </div>

              <div>
                <label className="label">Source</label>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="input"
                >
                  <option value="any">Any</option>
                  <option value="worker">Worker</option>
                  <option value="manual">Manual</option>
                  <option value="simulation">Simulation</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Trace List / Timeline */}
        <div className="lg:col-span-3">
          {selectedTrace && selectedTrace.events ? (
            /* Timeline View */
            <div className="card">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-100">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setSelectedTrace(null)}
                    className="text-primary-600 hover:text-primary-800 text-sm font-semibold"
                  >
                    ← Back to List
                  </button>
                  <h2 className="text-xl font-bold text-gray-900">
                    Trace: {selectedTrace.trace_id.substring(0, 8)}
                  </h2>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExportTrace(selectedTrace)}
                    className="btn btn-secondary py-1.5 text-xs flex items-center"
                  >
                    <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                    Export JSON
                  </button>
                  <button
                    onClick={() => handleCopyTraceId(selectedTrace.trace_id)}
                    className="btn btn-secondary py-1.5 text-xs flex items-center"
                  >
                    <Copy className="h-3.5 w-3.5 mr-1.5" />
                    Copy ID
                  </button>
                </div>
              </div>

              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-100"></div>
                <div className="space-y-6">
                  {selectedTrace.events.map((event, idx) => {
                    const isExpanded = expandedEvents.has(`${event.event_type}-${idx}`);
                    return (
                      <div key={idx} className="relative pl-10">
                        <div
                          className={`absolute left-2.5 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white ring-4 ring-white ${
                            event.event_type.includes('Error')
                              ? 'bg-danger-500'
                              : event.event_type.includes('Execution')
                              ? 'bg-success-500'
                              : 'bg-primary-500'
                          }`}
                        ></div>
                        <div
                          className={`card p-4 transition-all ${
                            isExpanded ? 'bg-gray-50' : 'hover:bg-gray-50 cursor-pointer'
                          }`}
                          onClick={() => toggleEventExpansion(`${event.event_type}-${idx}`)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4 text-gray-400" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-gray-400" />
                              )}
                              <span className="font-bold text-gray-900">{event.event_type}</span>
                            </div>
                            <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded border border-gray-100">
                              {new Date(event.timestamp).toLocaleTimeString()}
                            </span>
                          </div>

                          {isExpanded && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <pre className="text-xs text-gray-600 bg-white p-3 rounded-lg border border-gray-100 overflow-x-auto font-mono">
                                {JSON.stringify(event.payload, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Trace List View */
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Activity Traces</h2>
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-4 text-sm text-gray-500">Loading traces...</p>
                </div>
              ) : traces.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-sm text-gray-500 italic">
                    {traceIdFilter
                      ? 'No trace found with this ID'
                      : 'Audit Trail is currently under migration to real-time logs. Please use the Position Cockpit Event Timeline for detailed logs.'}
                  </p>
                </div>
              ) : (
                <div className="-mx-6 overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Time
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Asset
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Summary
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Trace ID
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {traces.map((trace) => (
                        <tr
                          key={trace.trace_id}
                          onClick={() => handleTraceClick(trace)}
                          className="hover:bg-primary-50 cursor-pointer transition-colors"
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {trace.time}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                            {trace.asset}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700">{trace.summary}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-400">
                            {trace.trace_id.substring(0, 8)}...
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}







