/**
 * ExplainabilityTable - Unified trade tracking view
 *
 * Shows the complete trade lifecycle at each evaluation point:
 * market data → trigger evaluation → guardrail checks → order submission →
 * execution → position impact.
 *
 * Features:
 * - Column group toggles (Time, Market, Trigger, Guardrails, Action, Order, Execution, Position, Dividends, Anchor)
 * - Date range and action filters
 * - Daily/All aggregation toggle
 * - Excel export
 * - Pagination
 * - Row highlighting for BUY/SELL actions
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Download,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Table,
  TableProperties,
  Filter,
  X,
  ChevronLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
} from 'lucide-react';
import { explainabilityApi } from '../../lib/api';
import {
  ExplainabilityRow,
  ExplainabilityTimeline,
  ExplainabilityParams,
  EXPLAINABILITY_COLUMN_GROUPS,
  DEFAULT_VISIBLE_COLUMNS,
  DEFAULT_ENABLED_GROUPS,
  ACTION_TYPES,
  ORDER_STATUS_COLORS,
  ColumnGroup,
} from '../../types/explainability';
import DateRangeFilter, { DateRange } from '../shared/DateRangeFilter';
import EventTypeFilter from '../shared/EventTypeFilter';

interface ExplainabilityTableProps {
  // For live positions
  tenantId?: string;
  portfolioId?: string;
  positionId?: string;
  // For simulations
  simulationId?: string;
  // Common
  mode: 'LIVE' | 'SIMULATION';
  symbol?: string;
}

const ROWS_PER_PAGE = 50;

// Formatters
function formatValue(value: any, format?: string): string {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      return `$${Number(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    case 'percent':
      return `${Number(value).toFixed(2)}%`;
    case 'number':
      return Number(value).toLocaleString(undefined, { maximumFractionDigits: 4 });
    case 'datetime':
      return new Date(value).toLocaleString();
    case 'date':
      return value;
    case 'boolean':
      return value ? 'Yes' : 'No';
    default:
      return String(value);
  }
}

// Action badge component
function ActionBadge({ action }: { action: string }) {
  const config: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    BUY: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      icon: <TrendingUp className="h-3 w-3" />,
    },
    SELL: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      icon: <TrendingDown className="h-3 w-3" />,
    },
    HOLD: {
      bg: 'bg-gray-100',
      text: 'text-gray-600',
      icon: <Minus className="h-3 w-3" />,
    },
    SKIP: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      icon: <AlertTriangle className="h-3 w-3" />,
    },
  };

  const style = config[action] || config.HOLD;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${style.bg} ${style.text}`}
    >
      {style.icon}
      {action}
    </span>
  );
}

// Order status badge component
function OrderStatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-gray-400">-</span>;

  const colorClass = ORDER_STATUS_COLORS[status] || 'bg-gray-100 text-gray-700';

  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {status}
    </span>
  );
}

// Trigger indicator component
function TriggerIndicator({ fired, direction }: { fired: boolean; direction: string | null }) {
  if (!fired) {
    return <span className="text-gray-400">-</span>;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
        direction === 'UP' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}
    >
      {direction === 'UP' ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {direction}
    </span>
  );
}

export default function ExplainabilityTable({
  tenantId,
  portfolioId,
  positionId,
  simulationId,
  mode,
  symbol,
}: ExplainabilityTableProps) {
  // Data state
  const [data, setData] = useState<ExplainabilityTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  // View state
  const [viewMode, setViewMode] = useState<'standard' | 'verbose'>('standard');
  const [enabledGroups, setEnabledGroups] = useState<Set<string>>(new Set(DEFAULT_ENABLED_GROUPS));

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });
  const [selectedActions, setSelectedActions] = useState<string[]>([]);
  const [aggregation, setAggregation] = useState<'daily' | 'all'>('daily');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ExplainabilityParams = {
        aggregation,
        limit: 1000,
      };

      if (dateRange.startDate) params.start_date = dateRange.startDate;
      if (dateRange.endDate) params.end_date = dateRange.endDate;
      if (selectedActions.length > 0) params.action = selectedActions.join(',');

      let result: ExplainabilityTimeline;

      console.log('[ExplainabilityTable] Loading data...', { mode, tenantId, portfolioId, positionId, simulationId, params });

      if (mode === 'LIVE' && tenantId && portfolioId && positionId) {
        result = await explainabilityApi.getLiveTimeline(tenantId, portfolioId, positionId, params);
      } else if (mode === 'SIMULATION' && simulationId) {
        result = await explainabilityApi.getSimulationTimeline(simulationId, params);
      } else {
        throw new Error('Invalid configuration: missing required IDs');
      }

      console.log('[ExplainabilityTable] Loaded:', { total_rows: result.total_rows, filtered_rows: result.filtered_rows, rows_length: result.rows?.length });

      setData(result);
      setCurrentPage(1);
    } catch (err: any) {
      console.error('[ExplainabilityTable] Failed to load:', err);
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [
    mode,
    tenantId,
    portfolioId,
    positionId,
    simulationId,
    dateRange,
    selectedActions,
    aggregation,
  ]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [dateRange, selectedActions, aggregation]);

  // Export handler
  const handleExport = async () => {
    try {
      setExporting(true);

      const params: ExplainabilityParams = {
        aggregation,
      };

      if (dateRange.startDate) params.start_date = dateRange.startDate;
      if (dateRange.endDate) params.end_date = dateRange.endDate;
      if (selectedActions.length > 0) params.action = selectedActions.join(',');

      if (mode === 'LIVE' && tenantId && portfolioId && positionId) {
        await explainabilityApi.exportLiveTimeline(tenantId, portfolioId, positionId, params);
      } else if (mode === 'SIMULATION' && simulationId) {
        await explainabilityApi.exportSimulationTimeline(simulationId, params);
      }
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  // Column visibility
  const visibleColumns = useMemo(() => {
    if (viewMode === 'standard') {
      return EXPLAINABILITY_COLUMN_GROUPS.flatMap((group) =>
        group.columns.filter((col) => DEFAULT_VISIBLE_COLUMNS.includes(col.key)),
      );
    }
    return EXPLAINABILITY_COLUMN_GROUPS.filter((g) => enabledGroups.has(g.id)).flatMap(
      (g) => g.columns,
    );
  }, [viewMode, enabledGroups]);

  // Visible groups for header rendering
  const visibleGroups = useMemo(() => {
    return EXPLAINABILITY_COLUMN_GROUPS.filter((g) => enabledGroups.has(g.id));
  }, [enabledGroups]);

  // Pagination
  const rows = data?.rows || [];
  const totalPages = Math.ceil(rows.length / ROWS_PER_PAGE);
  const startIndex = (currentPage - 1) * ROWS_PER_PAGE;
  const endIndex = startIndex + ROWS_PER_PAGE;
  const paginatedRows = rows.slice(startIndex, endIndex);

  // Toggle column group
  const toggleGroup = (groupId: string) => {
    setEnabledGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  // Clear filters
  const handleClearFilters = () => {
    setDateRange({ startDate: null, endDate: null });
    setSelectedActions([]);
    setAggregation('daily');
  };

  const hasActiveFilters =
    dateRange.startDate || dateRange.endDate || selectedActions.length > 0 || aggregation !== 'daily';

  // Render cell with special formatting
  const renderCell = (row: ExplainabilityRow, key: keyof ExplainabilityRow, format?: string) => {
    const value = row[key];

    // Special rendering for specific columns
    if (key === 'action') {
      return <ActionBadge action={value as string} />;
    }

    if (key === 'order_status') {
      return <OrderStatusBadge status={value as string | null} />;
    }

    if (key === 'trigger_fired') {
      return <TriggerIndicator fired={value as boolean} direction={row.trigger_direction} />;
    }

    if (key === 'trigger_direction') {
      if (!row.trigger_fired) return <span className="text-gray-400">-</span>;
      return (
        <span
          className={
            value === 'UP' ? 'text-green-600 font-medium' : value === 'DOWN' ? 'text-red-600 font-medium' : ''
          }
        >
          {value || '-'}
        </span>
      );
    }

    if (key === 'guardrail_allowed') {
      return (
        <span className={value ? 'text-green-600' : 'text-red-600 font-medium'}>
          {value ? 'Yes' : 'No'}
        </span>
      );
    }

    if (key === 'delta_pct') {
      const numValue = value as number | null;
      if (numValue === null || numValue === undefined) return <span className="text-gray-400">-</span>;
      return (
        <span className={numValue > 0 ? 'text-green-600' : numValue < 0 ? 'text-red-600' : ''}>
          {numValue > 0 ? '+' : ''}
          {numValue.toFixed(2)}%
        </span>
      );
    }

    if (key === 'dividend_declared' || key === 'dividend_applied' || key === 'anchor_reset') {
      return value ? (
        <span className="text-green-600 font-medium">Yes</span>
      ) : (
        <span className="text-gray-400">-</span>
      );
    }

    // Default formatting
    return formatValue(value, format);
  };

  // Loading state
  if (loading && !data) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center text-gray-500">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />
          Loading explainability data...
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-red-500 text-center mb-4">{error}</div>
        <div className="text-center">
          <button
            onClick={loadData}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Table className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold text-gray-900">Trade Tracking</h3>
          <span className="text-sm text-gray-500">
            ({data?.filtered_rows || 0} of {data?.total_rows || 0} rows)
          </span>
          {symbol && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">{symbol}</span>
          )}
          <span
            className={`px-2 py-0.5 text-xs rounded ${
              mode === 'LIVE' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
            }`}
          >
            {mode}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('standard')}
              className={`px-3 py-1.5 text-sm flex items-center gap-1.5 ${
                viewMode === 'standard'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Table className="h-4 w-4" />
              Standard
            </button>
            <button
              onClick={() => setViewMode('verbose')}
              className={`px-3 py-1.5 text-sm flex items-center gap-1.5 ${
                viewMode === 'verbose'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <TableProperties className="h-4 w-4" />
              Verbose
            </button>
          </div>

          {/* Filters button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded border transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-blue-50 border-blue-300 text-blue-700'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="bg-blue-600 text-white px-1.5 py-0.5 rounded-full text-xs">!</span>
            )}
          </button>

          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center gap-1 px-2 py-2 text-sm text-gray-500 hover:text-gray-700"
            >
              <X className="w-3 h-3" />
              Clear
            </button>
          )}

          {/* Refresh button */}
          <button
            onClick={loadData}
            className="p-2 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {/* Export button */}
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {exporting ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>

      {/* Column Group Toggles (Verbose Mode) */}
      {viewMode === 'verbose' && (
        <div className="px-4 py-2 border-b border-gray-200 bg-gray-50 flex flex-wrap gap-2">
          <span className="text-xs text-gray-500 uppercase tracking-wide mr-2 self-center">
            Column Groups:
          </span>
          {EXPLAINABILITY_COLUMN_GROUPS.map((group) => (
            <button
              key={group.id}
              onClick={() => toggleGroup(group.id)}
              className={`px-2 py-1 text-xs rounded flex items-center gap-1 ${
                enabledGroups.has(group.id)
                  ? `${group.color} text-gray-800 border border-gray-300`
                  : 'bg-white text-gray-500 border border-gray-200'
              }`}
            >
              {enabledGroups.has(group.id) ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              {group.label}
            </button>
          ))}
        </div>
      )}

      {/* Filter Panel */}
      {showFilters && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 space-y-4">
          <div className="flex flex-wrap items-start gap-6">
            <div className="flex-1 min-w-[300px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
              <DateRangeFilter value={dateRange} onChange={setDateRange} compact />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
              <EventTypeFilter
                selectedTypes={selectedActions}
                onChange={setSelectedActions}
                availableTypes={ACTION_TYPES}
                compact
                placeholder="All Actions"
              />
            </div>
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">Aggregation</label>
              <select
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value as 'daily' | 'all')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="daily">Daily (compact)</option>
                <option value="all">All rows</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {/* Group Header Row (Verbose Mode) */}
            {viewMode === 'verbose' && (
              <tr className="border-b border-gray-200">
                {visibleGroups.map((group) => (
                  <th
                    key={group.id}
                    colSpan={group.columns.length}
                    className={`px-3 py-2 text-center text-xs font-semibold uppercase tracking-wide ${group.color}`}
                  >
                    {group.label}
                  </th>
                ))}
              </tr>
            )}
            {/* Column Header Row */}
            <tr className="border-b border-gray-200 bg-gray-50">
              {visibleColumns.map((col) => (
                <th
                  key={col.key}
                  className="px-3 py-2 text-left text-xs font-semibold text-gray-700 whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {paginatedRows.map((row, idx) => (
              <tr
                key={idx}
                className={`hover:bg-gray-50 ${
                  row.action === 'BUY'
                    ? 'bg-green-50/30'
                    : row.action === 'SELL'
                      ? 'bg-red-50/30'
                      : row.action === 'SKIP'
                        ? 'bg-yellow-50/20'
                        : ''
                }`}
              >
                {visibleColumns.map((col) => {
                  // Special styling for certain columns
                  let cellClass = 'px-3 py-2 whitespace-nowrap';
                  if (
                    col.key === 'action_reason' ||
                    col.key === 'guardrail_block_reason' ||
                    col.key === 'trigger_reason' ||
                    col.key === 'anchor_reset_reason'
                  ) {
                    cellClass = 'px-3 py-2 max-w-xs truncate';
                  }

                  return (
                    <td key={col.key} className={cellClass} title={String(row[col.key] || '')}>
                      {renderCell(row, col.key, col.format)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {rows.length === 0 && !loading && (
        <div className="p-8 text-center text-gray-500">
          <Filter className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No trade tracking data available</p>
          <p className="text-sm mt-1">
            {mode === 'LIVE'
              ? 'Run position evaluations to see data here'
              : 'Run a simulation to see decision history'}
          </p>
          <p className="text-xs mt-2 text-gray-400">
            API returned: {data?.total_rows || 0} total, {data?.filtered_rows || 0} filtered
          </p>
          <p className="text-xs text-gray-400">
            Position: {positionId} | Portfolio: {portfolioId}
          </p>
          {hasActiveFilters && (
            <p className="text-xs text-yellow-600 mt-1">Filters may be hiding rows</p>
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            Showing {startIndex + 1}-{Math.min(endIndex, rows.length)} of {rows.length} rows
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
