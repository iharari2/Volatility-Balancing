/**
 * DecisionHistoryTable - Historical view of trading decisions
 *
 * Shows timeline of evaluation events with expandable column groups.
 * Supports verbose (all columns) and standard (key columns) views.
 * Exportable to Excel.
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import {
  Download,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Table,
  TableProperties,
  Filter,
} from 'lucide-react';
import toast from 'react-hot-toast';

// ============== TYPE DEFINITIONS ==============

interface TimelineRow {
  id: string;
  timestamp: string;

  // Event Metadata
  tenant_id?: string;
  portfolio_id?: string;
  portfolio_name?: string;
  position_id?: string;
  symbol?: string;
  exchange?: string;
  market_session?: string;
  evaluation_type?: string;
  evaluation_seq?: number;
  trace_id?: string;
  mode?: string;
  simulation_run_id?: string;

  // Market Data Snapshot
  open_price?: number;
  high_price?: number;
  low_price?: number;
  close_price?: number;
  volume?: number;
  last_trade_price?: number;
  best_bid?: number;
  best_ask?: number;
  official_close_price?: number;
  effective_price?: number;
  price_policy_requested?: string;
  price_policy_effective?: string;
  price_fallback_reason?: string;
  data_provider?: string;
  is_market_hours?: boolean | number;
  allow_after_hours?: boolean;
  trading_hours_policy?: string;
  is_fresh?: boolean;
  is_inline?: boolean;

  // Position Values (Before)
  position_qty_before?: number;
  position_cash_before?: number;
  position_stock_value_before?: number;
  position_total_value_before?: number;
  position_stock_pct_before?: number;
  position_dividend_receivable_before?: number;
  cash_pct?: number;
  stock_pct?: number;

  // Strategy Thresholds - Anchor
  anchor_price?: number;
  pct_change_from_anchor?: number;
  pct_change_from_prev?: number;
  anchor_updated?: boolean;
  anchor_reset_old_value?: number;
  anchor_reset_reason?: string;

  // Strategy Thresholds - Trigger
  trigger_up_threshold?: number;
  trigger_down_threshold?: number;
  trigger_direction?: string;
  trigger_fired?: boolean | number;
  trigger_reason?: string;

  // Guardrail Thresholds
  guardrail_min_stock_pct?: number;
  guardrail_max_stock_pct?: number;
  guardrail_max_trade_pct?: number;
  guardrail_max_orders_per_day?: number;
  guardrail_allowed?: boolean;
  guardrail_block_reason?: string;

  // Action & Reason
  action?: string;
  action_reason?: string;
  trade_intent_qty?: number;
  trade_intent_value?: number;
  trade_intent_cash_delta?: number;
  action_taken?: string;
  action_side?: string;
  action_qty_raw?: number;
  action_qty_trimmed?: number;
  action_notional?: number;
  action_commission_estimated?: number;
  action_trimming_reason?: string;
  decision_allowed?: boolean;
  decision_rejections?: string[];
  decision_warnings?: string[];
  decision_explanation?: string;

  // Results / Execution
  order_id?: string;
  trade_id?: string;
  execution_price?: number;
  execution_qty?: number;
  execution_commission?: number;
  execution_timestamp?: string;
  execution_status?: string;

  // Position Values (After)
  position_qty_after?: number;
  position_cash_after?: number;
  position_stock_value_after?: number;
  position_total_value_after?: number;
  position_stock_pct_after?: number;
  new_anchor_price?: number;

  // Dividend Data
  dividend_declared?: boolean;
  dividend_ex_date?: string;
  dividend_pay_date?: string;
  dividend_rate?: number;
  dividend_gross_value?: number;
  dividend_tax?: number;
  dividend_net_value?: number;
  dividend_applied?: boolean;
}

interface ColumnDef {
  key: string;
  label: string;
  group: string;
  format?: 'currency' | 'percent' | 'number' | 'datetime' | 'date' | 'boolean' | 'text';
  width?: string;
  standard?: boolean; // Include in standard view
}

interface DecisionHistoryTableProps {
  portfolioId: string;
  positionId: string;
  limit?: number;
}

// ============== COLUMN DEFINITIONS ==============

const COLUMN_GROUPS = [
  { id: 'event', label: 'Event Metadata', color: 'bg-slate-100' },
  { id: 'position', label: 'Position Context', color: 'bg-blue-50' },
  { id: 'market', label: 'Market Data', color: 'bg-green-50' },
  { id: 'values', label: 'Position Values', color: 'bg-yellow-50' },
  { id: 'trigger', label: 'Strategy Thresholds', color: 'bg-orange-50' },
  { id: 'guardrail', label: 'Guardrails', color: 'bg-red-50' },
  { id: 'action', label: 'Action & Reason', color: 'bg-purple-50' },
  { id: 'results', label: 'Results', color: 'bg-pink-50' },
  { id: 'performance', label: 'Performance', color: 'bg-cyan-50' },
];

const COLUMNS: ColumnDef[] = [
  // Event Metadata
  { key: 'timestamp', label: 'Timestamp', group: 'event', format: 'datetime', standard: true },
  { key: 'evaluation_type', label: 'Event Type', group: 'event', standard: true },
  { key: 'evaluation_seq', label: 'Seq #', group: 'event', format: 'number' },
  { key: 'market_session', label: 'Session', group: 'event' },
  { key: 'mode', label: 'Mode', group: 'event' },
  { key: 'trace_id', label: 'Trace ID', group: 'event' },

  // Position Context
  { key: 'symbol', label: 'Symbol', group: 'position', standard: true },
  { key: 'portfolio_name', label: 'Portfolio', group: 'position' },
  { key: 'exchange', label: 'Exchange', group: 'position' },

  // Market Data
  { key: 'effective_price', label: 'Price', group: 'market', format: 'currency', standard: true },
  { key: 'last_trade_price', label: 'Last Trade', group: 'market', format: 'currency' },
  { key: 'best_bid', label: 'Bid', group: 'market', format: 'currency' },
  { key: 'best_ask', label: 'Ask', group: 'market', format: 'currency' },
  { key: 'official_close_price', label: 'Prev Close', group: 'market', format: 'currency' },
  { key: 'open_price', label: 'Open', group: 'market', format: 'currency' },
  { key: 'high_price', label: 'High', group: 'market', format: 'currency' },
  { key: 'low_price', label: 'Low', group: 'market', format: 'currency' },
  { key: 'volume', label: 'Volume', group: 'market', format: 'number' },
  { key: 'is_market_hours', label: 'Mkt Hours', group: 'market', format: 'boolean' },
  { key: 'is_fresh', label: 'Fresh', group: 'market', format: 'boolean' },
  { key: 'data_provider', label: 'Provider', group: 'market' },
  { key: 'price_policy_effective', label: 'Price Policy', group: 'market' },

  // Position Values
  { key: 'position_qty_before', label: 'Qty Before', group: 'values', format: 'number' },
  { key: 'position_cash_before', label: 'Cash Before', group: 'values', format: 'currency' },
  { key: 'position_stock_value_before', label: 'Stock Val Before', group: 'values', format: 'currency' },
  { key: 'position_total_value_before', label: 'Total Before', group: 'values', format: 'currency', standard: true },
  { key: 'stock_pct', label: 'Stock %', group: 'values', format: 'percent', standard: true },
  { key: 'cash_pct', label: 'Cash %', group: 'values', format: 'percent' },

  // Strategy Thresholds - Trigger
  { key: 'anchor_price', label: 'Anchor', group: 'trigger', format: 'currency', standard: true },
  { key: 'pct_change_from_anchor', label: 'Delta %', group: 'trigger', format: 'percent', standard: true },
  { key: 'pct_change_from_prev', label: 'vs Prev %', group: 'trigger', format: 'percent' },
  { key: 'trigger_up_threshold', label: 'Up Thresh', group: 'trigger', format: 'percent' },
  { key: 'trigger_down_threshold', label: 'Down Thresh', group: 'trigger', format: 'percent' },
  { key: 'trigger_direction', label: 'Trigger Dir', group: 'trigger', standard: true },
  { key: 'trigger_fired', label: 'Triggered', group: 'trigger', format: 'boolean', standard: true },
  { key: 'trigger_reason', label: 'Trigger Reason', group: 'trigger' },
  { key: 'anchor_updated', label: 'Anchor Updated', group: 'trigger', format: 'boolean' },
  { key: 'anchor_reset_reason', label: 'Anchor Reset Reason', group: 'trigger' },

  // Guardrails
  { key: 'guardrail_min_stock_pct', label: 'Min Stock %', group: 'guardrail', format: 'percent' },
  { key: 'guardrail_max_stock_pct', label: 'Max Stock %', group: 'guardrail', format: 'percent' },
  { key: 'guardrail_max_trade_pct', label: 'Max Trade %', group: 'guardrail', format: 'percent' },
  { key: 'guardrail_max_orders_per_day', label: 'Max Orders/Day', group: 'guardrail', format: 'number' },
  { key: 'guardrail_allowed', label: 'Allowed', group: 'guardrail', format: 'boolean', standard: true },
  { key: 'guardrail_block_reason', label: 'Block Reason', group: 'guardrail' },

  // Action & Reason
  { key: 'action', label: 'Action', group: 'action', standard: true },
  { key: 'action_reason', label: 'Reason', group: 'action', standard: true },
  { key: 'trade_intent_qty', label: 'Intent Qty', group: 'action', format: 'number' },
  { key: 'trade_intent_value', label: 'Intent Value', group: 'action', format: 'currency' },
  { key: 'action_qty_raw', label: 'Raw Qty', group: 'action', format: 'number' },
  { key: 'action_qty_trimmed', label: 'Trimmed Qty', group: 'action', format: 'number' },
  { key: 'action_notional', label: 'Notional', group: 'action', format: 'currency' },
  { key: 'action_trimming_reason', label: 'Trim Reason', group: 'action' },
  { key: 'decision_explanation', label: 'Explanation', group: 'action' },

  // Results
  { key: 'order_id', label: 'Order ID', group: 'results' },
  { key: 'execution_status', label: 'Exec Status', group: 'results', standard: true },
  { key: 'execution_price', label: 'Exec Price', group: 'results', format: 'currency' },
  { key: 'execution_qty', label: 'Exec Qty', group: 'results', format: 'number' },
  { key: 'execution_commission', label: 'Commission', group: 'results', format: 'currency' },
  { key: 'position_qty_after', label: 'Qty After', group: 'results', format: 'number' },
  { key: 'position_cash_after', label: 'Cash After', group: 'results', format: 'currency' },
  { key: 'position_total_value_after', label: 'Total After', group: 'results', format: 'currency' },
  { key: 'position_stock_pct_after', label: 'Stock % After', group: 'results', format: 'percent' },
  { key: 'new_anchor_price', label: 'New Anchor', group: 'results', format: 'currency' },

  // Performance (calculated)
  { key: 'value_change', label: 'Value Change', group: 'performance', format: 'currency' },
  { key: 'value_change_pct', label: 'Return %', group: 'performance', format: 'percent' },
];

const TENANT_ID = 'default';
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// ============== FORMATTERS ==============

function formatValue(value: any, format?: string): string {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    case 'percent':
      return `${Number(value).toFixed(2)}%`;
    case 'number':
      return Number(value).toLocaleString(undefined, { maximumFractionDigits: 4 });
    case 'datetime':
      return new Date(value).toLocaleString();
    case 'date':
      return new Date(value).toLocaleDateString();
    case 'boolean':
      return value ? 'Yes' : 'No';
    default:
      return String(value);
  }
}

function formatValueForExcel(value: any, format?: string): any {
  if (value === null || value === undefined) return '';

  switch (format) {
    case 'currency':
    case 'percent':
    case 'number':
      return Number(value);
    case 'datetime':
    case 'date':
      return new Date(value).toISOString();
    case 'boolean':
      return value ? 'Yes' : 'No';
    default:
      return String(value);
  }
}

// ============== COMPONENT ==============

export default function DecisionHistoryTable({
  portfolioId,
  positionId,
  limit = 100,
}: DecisionHistoryTableProps) {
  const [data, setData] = useState<TimelineRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'standard' | 'verbose'>('standard');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(['event', 'market', 'trigger', 'action', 'results'])
  );
  const [exporting, setExporting] = useState(false);

  const loadData = useCallback(async () => {
    if (!portfolioId || !positionId) return;

    try {
      setLoading(true);
      setError(null);
      const url = `${API_BASE}/v1/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/timeline?limit=${limit}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch timeline');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [portfolioId, positionId, limit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Calculate derived performance columns
  const enrichedData = useMemo(() => {
    return data.map((row, idx) => {
      const prevRow = data[idx + 1]; // Data is newest first
      const valueChange = row.position_total_value_after && prevRow?.position_total_value_before
        ? row.position_total_value_after - prevRow.position_total_value_before
        : null;
      const valueChangePct = valueChange && prevRow?.position_total_value_before
        ? (valueChange / prevRow.position_total_value_before) * 100
        : null;

      return {
        ...row,
        value_change: valueChange,
        value_change_pct: valueChangePct,
      };
    });
  }, [data]);

  // Filter columns based on view mode
  const visibleColumns = useMemo(() => {
    if (viewMode === 'standard') {
      return COLUMNS.filter(col => col.standard);
    }
    return COLUMNS.filter(col => expandedGroups.has(col.group));
  }, [viewMode, expandedGroups]);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  const exportToExcel = async () => {
    setExporting(true);
    try {
      // Dynamic import xlsx
      const XLSX = await import('xlsx');

      // Prepare data for export
      const exportColumns = viewMode === 'standard'
        ? COLUMNS.filter(col => col.standard)
        : COLUMNS;

      const headers = exportColumns.map(col => col.label);
      const rows = enrichedData.map(row =>
        exportColumns.map(col => formatValueForExcel((row as any)[col.key], col.format))
      );

      // Create workbook
      const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Decision History');

      // Auto-size columns
      const colWidths = headers.map((h, i) => ({
        wch: Math.max(
          h.length,
          ...rows.map(r => String(r[i]).length)
        ) + 2
      }));
      ws['!cols'] = colWidths;

      // Download
      const filename = `decision_history_${positionId}_${new Date().toISOString().split('T')[0]}.xlsx`;
      XLSX.writeFile(wb, filename);
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Export failed. Make sure xlsx package is installed.');
    } finally {
      setExporting(false);
    }
  };

  if (loading && data.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center text-gray-500">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />
          Loading history...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-red-500 text-center">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Table className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold text-gray-900">Decision History</h3>
          <span className="text-sm text-gray-500">({data.length} events)</span>
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

          <button
            onClick={loadData}
            className="p-2 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={exportToExcel}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {exporting ? 'Exporting...' : 'Export Excel'}
          </button>
        </div>
      </div>

      {/* Column Group Toggles (Verbose Mode) */}
      {viewMode === 'verbose' && (
        <div className="px-4 py-2 border-b border-gray-200 bg-gray-50 flex flex-wrap gap-2">
          <span className="text-xs text-gray-500 uppercase tracking-wide mr-2 self-center">
            Column Groups:
          </span>
          {COLUMN_GROUPS.map(group => (
            <button
              key={group.id}
              onClick={() => toggleGroup(group.id)}
              className={`px-2 py-1 text-xs rounded flex items-center gap-1 ${
                expandedGroups.has(group.id)
                  ? `${group.color} text-gray-800 border border-gray-300`
                  : 'bg-white text-gray-500 border border-gray-200'
              }`}
            >
              {expandedGroups.has(group.id) ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              {group.label}
            </button>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {/* Group Header Row (Verbose Mode) */}
            {viewMode === 'verbose' && (
              <tr className="border-b border-gray-200">
                {COLUMN_GROUPS.filter(g => expandedGroups.has(g.id)).map(group => {
                  const groupCols = visibleColumns.filter(c => c.group === group.id);
                  if (groupCols.length === 0) return null;
                  return (
                    <th
                      key={group.id}
                      colSpan={groupCols.length}
                      className={`px-3 py-2 text-center text-xs font-semibold uppercase tracking-wide ${group.color}`}
                    >
                      {group.label}
                    </th>
                  );
                })}
              </tr>
            )}
            {/* Column Header Row */}
            <tr className="border-b border-gray-200 bg-gray-50">
              {visibleColumns.map(col => (
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
            {enrichedData.map((row, idx) => (
              <tr
                key={row.id || idx}
                className={`hover:bg-gray-50 ${
                  row.action === 'BUY' ? 'bg-green-50/30' :
                  row.action === 'SELL' ? 'bg-red-50/30' :
                  ''
                }`}
              >
                {visibleColumns.map(col => {
                  const value = (row as any)[col.key];
                  const formatted = formatValue(value, col.format);

                  // Special styling for certain columns
                  let cellClass = 'px-3 py-2 whitespace-nowrap';
                  if (col.key === 'action') {
                    cellClass += value === 'BUY' ? ' text-green-700 font-semibold' :
                                value === 'SELL' ? ' text-red-700 font-semibold' :
                                ' text-gray-600';
                  } else if (col.key === 'trigger_fired' || col.key === 'guardrail_allowed') {
                    cellClass += value ? ' text-green-600' : ' text-gray-400';
                  } else if (col.key === 'pct_change_from_anchor') {
                    cellClass += value > 0 ? ' text-green-600' :
                                value < 0 ? ' text-red-600' :
                                ' text-gray-600';
                  } else if (col.key === 'action_reason' || col.key === 'decision_explanation' || col.key === 'trigger_reason') {
                    cellClass = 'px-3 py-2 max-w-xs truncate';
                  }

                  return (
                    <td key={col.key} className={cellClass} title={col.format === undefined ? String(value || '') : ''}>
                      {formatted}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {data.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          <Filter className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No decision history available</p>
          <p className="text-sm mt-1">Run position evaluations to see data here</p>
        </div>
      )}
    </div>
  );
}
