import { useState, useEffect, useMemo, useCallback } from 'react';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';
import { format } from 'date-fns';
import { Filter, X } from 'lucide-react';
import DateRangeFilter, { DateRange, dateRangeToParams } from '../../../components/shared/DateRangeFilter';
import EventTypeFilter from '../../../components/shared/EventTypeFilter';

interface TimelineRow {
  id: string;
  timestamp: string;
  evaluation_type: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  effective_price?: number;
  anchor_price?: number;
  trigger_up_threshold?: number;
  trigger_down_threshold?: number;
  action?: string;
  action_reason?: string;
  position_qty_before?: number;
  position_qty_after?: number;
  position_cash_before?: number;
  position_cash_after?: number;
  position_total_value_after?: number;
  guardrail_min_stock_alloc_pct?: number;
  guardrail_max_stock_alloc_pct?: number;
  guardrail_block_reason?: string;
  [key: string]: any;
}

interface EventLogSectionProps {
  position: PortfolioPosition;
  tenantId: string;
  portfolioId: string;
}

// Available action types for filtering
const actionTypes = [
  { value: 'BUY', label: 'Buy' },
  { value: 'SELL', label: 'Sell' },
  { value: 'HOLD', label: 'Hold' },
  { value: 'SKIP', label: 'Skip' },
];

// Available evaluation types
const evaluationTypes = [
  { value: 'DAILY_CHECK', label: 'Daily Check' },
  { value: 'PRICE_UPDATE', label: 'Price Update' },
  { value: 'TRIGGER_EVALUATED', label: 'Trigger Evaluated' },
  { value: 'EXECUTION', label: 'Execution' },
];

export default function EventLogSection({ position, tenantId, portfolioId }: EventLogSectionProps) {
  const [timeline, setTimeline] = useState<TimelineRow[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });
  const [selectedActions, setSelectedActions] = useState<string[]>(['BUY', 'SELL', 'SKIP']);
  const [selectedEventTypes, setSelectedEventTypes] = useState<string[]>([]);

  const loadTimeline = useCallback(async () => {
    try {
      // Build query params with filters
      const params = new URLSearchParams({
        limit: '100',
        mode: 'LIVE',
      });

      // Add date range params
      if (dateRange.startDate) {
        params.append('start_date', new Date(dateRange.startDate).toISOString());
      }
      if (dateRange.endDate) {
        params.append('end_date', new Date(dateRange.endDate).toISOString());
      }

      // Add action filter
      if (selectedActions.length > 0) {
        params.append('action', selectedActions.join(','));
      }

      // Add event type filter
      if (selectedEventTypes.length > 0) {
        params.append('event_type', selectedEventTypes.join(','));
      }

      const response = await fetch(
        `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${position.id}/timeline?${params.toString()}`,
      );
      if (response.ok) {
        const data = await response.json();
        setTimeline(data);
      }
    } catch (error) {
      console.error('Error loading timeline:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId, portfolioId, position.id, dateRange, selectedActions, selectedEventTypes]);

  useEffect(() => {
    loadTimeline();
    const interval = setInterval(loadTimeline, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [loadTimeline]);

  const hasActiveFilters = dateRange.startDate || dateRange.endDate || selectedActions.length > 0 || selectedEventTypes.length > 0;

  const handleClearFilters = () => {
    setDateRange({ startDate: null, endDate: null });
    setSelectedActions([]);
    setSelectedEventTypes([]);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Event Log</h2>
        <div className="text-sm text-gray-500">Loading events...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Event Log (Chronological)</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded border transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-primary-50 border-primary-300 text-primary-700'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters
            {hasActiveFilters && (
              <span className="bg-primary-600 text-white px-1.5 py-0.5 rounded-full text-xs">
                {(dateRange.startDate || dateRange.endDate ? 1 : 0) +
                  (selectedActions.length > 0 ? 1 : 0) +
                  (selectedEventTypes.length > 0 ? 1 : 0)}
              </span>
            )}
          </button>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center gap-1 px-2 py-1.5 text-sm text-gray-500 hover:text-gray-700"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg space-y-4">
          <div className="flex flex-wrap items-start gap-6">
            <div className="flex-1 min-w-[300px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
              <DateRangeFilter value={dateRange} onChange={setDateRange} compact />
            </div>
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
              <EventTypeFilter
                selectedTypes={selectedActions}
                onChange={setSelectedActions}
                availableTypes={actionTypes}
                compact
                placeholder="All Actions"
              />
            </div>
            <div className="min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">Event Type</label>
              <EventTypeFilter
                selectedTypes={selectedEventTypes}
                onChange={setSelectedEventTypes}
                availableTypes={evaluationTypes}
                compact
                placeholder="All Types"
              />
            </div>
          </div>
        </div>
      )}

      {hasActiveFilters && (
        <div className="mb-4 text-sm text-gray-500">
          Showing {timeline.length} events{' '}
          {dateRange.startDate || dateRange.endDate ? '(filtered by date)' : ''}
        </div>
      )}

      {timeline.length === 0 ? (
        <div className="text-sm text-gray-500">
          {hasActiveFilters ? 'No events match your filters' : 'No events yet'}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Price (O/H/L/C)
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Effective Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Anchor
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Triggers
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Guardrails
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Qty Before/After
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cash Before/After
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Value After
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {timeline.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {format(new Date(row.timestamp), 'MMM d, yyyy HH:mm:ss')}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.open !== undefined ||
                    row.high !== undefined ||
                    row.low !== undefined ||
                    row.close !== undefined ? (
                      <div>
                        O: {row.open?.toFixed(2) || '—'} | H: {row.high?.toFixed(2) || '—'} | L:{' '}
                        {row.low?.toFixed(2) || '—'} | C: {row.close?.toFixed(2) || '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {row.effective_price ? `$${row.effective_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {row.anchor_price ? `$${row.anchor_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.trigger_up_threshold || row.trigger_down_threshold ? (
                      <div>
                        Up:{' '}
                        {row.trigger_up_threshold ? `$${row.trigger_up_threshold.toFixed(2)}` : '—'}
                        <br />
                        Down:{' '}
                        {row.trigger_down_threshold
                          ? `$${row.trigger_down_threshold.toFixed(2)}`
                          : '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.guardrail_min_stock_alloc_pct !== undefined ||
                    row.guardrail_max_stock_alloc_pct !== undefined ? (
                      <div>
                        Min: {row.guardrail_min_stock_alloc_pct?.toFixed(1) || '—'}% | Max:{' '}
                        {row.guardrail_max_stock_alloc_pct?.toFixed(1) || '—'}%
                        {row.guardrail_block_reason && (
                          <div className="text-red-600 mt-1">
                            Blocked: {row.guardrail_block_reason}
                          </div>
                        )}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs">
                    <div className="font-medium text-gray-900">{row.action || 'NONE'}</div>
                    {row.action_reason && (
                      <div className="text-gray-500 mt-1">{row.action_reason}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.position_qty_before !== undefined ||
                    row.position_qty_after !== undefined ? (
                      <div>
                        {row.position_qty_before?.toFixed(4) || '—'} →{' '}
                        {row.position_qty_after?.toFixed(4) || '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.position_cash_before !== undefined ||
                    row.position_cash_after !== undefined ? (
                      <div>
                        ${row.position_cash_before?.toFixed(2) || '—'} → $
                        {row.position_cash_after?.toFixed(2) || '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {row.position_total_value_after
                      ? `$${row.position_total_value_after.toFixed(2)}`
                      : '—'}
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








