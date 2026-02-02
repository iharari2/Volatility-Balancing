import { useEffect, useState, useMemo } from 'react';
import { Filter, X, List, Clock as ClockIcon } from 'lucide-react';
import { useWorkspace } from '../../WorkspaceContext';
import { getPositionCockpit, CockpitResponse } from '../../../../api/cockpit';
import DateRangeFilter, { DateRange } from '../../../../components/shared/DateRangeFilter';
import EventTypeFilter from '../../../../components/shared/EventTypeFilter';
import LoadingSpinner from '../../../../components/shared/LoadingSpinner';

const actionFilterTypes = [
  { value: 'BUY', label: 'Buy' },
  { value: 'SELL', label: 'Sell' },
  { value: 'HOLD', label: 'Hold' },
  { value: 'SKIP', label: 'Skip' },
  { value: '_EMPTY_', label: 'No Action' },
];

const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
};

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined) return '-';
  return `${value.toFixed(2)}%`;
};

type ViewMode = 'timeline' | 'table';

export default function EventsTab() {
  const { selectedPosition, portfolioId } = useWorkspace();
  const [cockpitData, setCockpitData] = useState<CockpitResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeWindow, setTimeWindow] = useState('7d');
  const [viewMode, setViewMode] = useState<ViewMode>('table');

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });
  const [selectedActions, setSelectedActions] = useState<string[]>([]);

  useEffect(() => {
    if (!portfolioId || !selectedPosition) {
      setCockpitData(null);
      setLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);
        const data = await getPositionCockpit(portfolioId, selectedPosition.position_id, timeWindow);
        setCockpitData(data);
      } catch (error) {
        console.error('Error loading events:', error);
        setCockpitData(null);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [portfolioId, selectedPosition?.position_id, timeWindow]);

  const hasActiveFilters =
    dateRange.startDate !== null || dateRange.endDate !== null || selectedActions.length > 0;

  const filteredRows = useMemo(() => {
    if (!cockpitData?.timeline_rows) return [];

    return cockpitData.timeline_rows.filter((row) => {
      // Date range filter
      if (dateRange.startDate || dateRange.endDate) {
        const rowDate = row.timestamp ? new Date(row.timestamp) : null;
        if (rowDate) {
          if (dateRange.startDate && rowDate < new Date(dateRange.startDate)) return false;
          if (dateRange.endDate && rowDate > new Date(dateRange.endDate)) return false;
        }
      }

      // Action filter
      if (selectedActions.length > 0) {
        const action = (row.action || '').toUpperCase().trim();
        const actionKey = action || '_EMPTY_';
        if (!selectedActions.includes(actionKey)) return false;
      }

      return true;
    });
  }, [cockpitData?.timeline_rows, dateRange, selectedActions]);

  const handleClearFilters = () => {
    setDateRange({ startDate: null, endDate: null });
    setSelectedActions([]);
  };

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading events..." />
      </div>
    );
  }

  if (!selectedPosition) {
    return (
      <div className="p-8 text-center text-gray-500">Select a position to view events</div>
    );
  }

  const timeWindowOptions = [
    { value: '1d', label: '1 Day' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' },
    { value: 'all', label: 'All Time' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            {selectedPosition.asset_symbol} Events
          </h2>
          <p className="text-sm text-gray-500">Trading activity and decision timeline</p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded ${
                viewMode === 'table' ? 'bg-white shadow-sm' : 'text-gray-500'
              }`}
              title="Table View"
            >
              <List className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`p-1.5 rounded ${
                viewMode === 'timeline' ? 'bg-white shadow-sm' : 'text-gray-500'
              }`}
              title="Timeline View"
            >
              <ClockIcon className="h-4 w-4" />
            </button>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-primary-50 border-primary-300 text-primary-700'
                : 'border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters
            {hasActiveFilters && (
              <span className="bg-primary-600 text-white px-1.5 py-0.5 rounded-full text-[10px]">
                {(dateRange.startDate || dateRange.endDate ? 1 : 0) +
                  (selectedActions.length > 0 ? 1 : 0)}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Time Window Selector */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClockIcon className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Data Window:</span>
        </div>
        <div className="flex items-center gap-2">
          {timeWindowOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeWindow(option.value)}
              className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                timeWindow === option.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">Filters</span>
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
              >
                <X className="h-3 w-3" />
                Clear all
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs font-medium text-gray-700 mb-1">Date Range</label>
              <DateRangeFilter value={dateRange} onChange={setDateRange} compact />
            </div>
            <div className="min-w-[150px]">
              <label className="block text-xs font-medium text-gray-700 mb-1">Action</label>
              <EventTypeFilter
                selectedTypes={selectedActions}
                onChange={setSelectedActions}
                availableTypes={actionFilterTypes}
                compact
                placeholder="All Actions"
              />
            </div>
          </div>
        </div>
      )}

      {/* Events Count */}
      {cockpitData?.timeline_rows && (
        <div className="text-sm text-gray-500">
          {hasActiveFilters ? (
            <>
              Showing {filteredRows.length} of {cockpitData.timeline_rows.length} events
            </>
          ) : (
            <>{cockpitData.timeline_rows.length} events</>
          )}
        </div>
      )}

      {/* Events Content */}
      {viewMode === 'table' ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          {filteredRows.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {hasActiveFilters ? 'No events match your filters' : 'No events available'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Trigger
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Guardrail
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Reason
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Value After
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredRows.map((row, index) => (
                    <tr key={row.id || index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {row.timestamp ? new Date(row.timestamp).toLocaleString() : '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(row.effective_price)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        {row.trigger_direction ? (
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                              row.trigger_direction === 'UP'
                                ? 'bg-success-100 text-success-700'
                                : row.trigger_direction === 'DOWN'
                                ? 'bg-danger-100 text-danger-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {row.trigger_direction}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        {row.guardrail_allowed !== null && row.guardrail_allowed !== undefined ? (
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                              row.guardrail_allowed
                                ? 'bg-success-100 text-success-700'
                                : 'bg-danger-100 text-danger-700'
                            }`}
                          >
                            {row.guardrail_allowed ? 'OK' : 'BLOCKED'}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                            row.action === 'BUY'
                              ? 'bg-success-100 text-success-700'
                              : row.action === 'SELL'
                              ? 'bg-danger-100 text-danger-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {row.action || 'HOLD'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate" title={row.action_reason}>
                        {row.action_reason || row.guardrail_block_reason || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                        {formatCurrency(row.position_total_value_after)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        /* Timeline View */
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          {filteredRows.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {hasActiveFilters ? 'No events match your filters' : 'No events available'}
            </div>
          ) : (
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
              <div className="space-y-6">
                {filteredRows.map((row, index) => (
                  <div key={row.id || index} className="relative pl-10">
                    <div
                      className={`absolute left-2.5 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white ring-4 ring-white ${
                        row.action === 'BUY'
                          ? 'bg-success-500'
                          : row.action === 'SELL'
                          ? 'bg-danger-500'
                          : 'bg-gray-400'
                      }`}
                    />
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              row.action === 'BUY'
                                ? 'bg-success-100 text-success-700'
                                : row.action === 'SELL'
                                ? 'bg-danger-100 text-danger-700'
                                : 'bg-gray-200 text-gray-700'
                            }`}
                          >
                            {row.action || 'HOLD'}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {formatCurrency(row.effective_price)}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {row.timestamp ? new Date(row.timestamp).toLocaleString() : '-'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div>
                          <span className="text-gray-500">Trigger</span>
                          <p className="font-medium text-gray-900">
                            {row.trigger_direction || '-'}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500">Guardrail</span>
                          <p className="font-medium text-gray-900">
                            {row.guardrail_allowed !== null && row.guardrail_allowed !== undefined
                              ? row.guardrail_allowed
                                ? 'OK'
                                : 'Blocked'
                              : '-'}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500">Value After</span>
                          <p className="font-medium text-gray-900">
                            {formatCurrency(row.position_total_value_after)}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500">Reason</span>
                          <p className="font-medium text-gray-900 truncate" title={row.action_reason}>
                            {row.action_reason || row.trigger_reason || '-'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
