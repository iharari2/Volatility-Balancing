import { useState, useEffect } from 'react';
import { Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { simulationApi } from '../lib/api';

interface VerboseTimelineViewProps {
  simulationId: string;
  ticker: string;
}

interface TimelineRow {
  DateTime: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  AnchorPrice: number;
  DividendPercent: number;
  DividendValue: number;
  PctChangeFromPrev: number | null;
  PctChangeFromAnchor: number | null;
  Quantity: number;
  PositionValue: number;
  Cash: number;
  TotalPortfolioValue: number;
  DeltaTotalValue: number | null;
  PctDeltaTotalValue: number | null;
  PctStockChangeFromBaseline: number | null;
  PctPortfolioChangeFromBaseline: number | null;
  TriggerThresholdUp: number;
  TriggerThresholdDown: number;
  TriggerSignal: string;
  TriggerReason: string;
  GuardrailMinStockPct: number;
  GuardrailMaxStockPct: number;
  GuardrailMaxTradePctOfPosition: number;
  GuardrailAllowed: string;
  GuardrailReason: string;
  Action: string;
  ActionReason: string;
  TradeSide: string | null;
  TradeQuantity: number;
  TradePrice: number;
  TradeNotional: number;
  TradeCommission: number;
  TradeCommissionRateEffective: number;
  DividendCashThisLine: number;
}

const ROWS_PER_PAGE = 50;

export default function VerboseTimelineView({ simulationId, ticker }: VerboseTimelineViewProps) {
  const [rows, setRows] = useState<TimelineRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (simulationId) {
      loadTimeline();
    } else {
      setLoading(false);
      setError('Simulation ID is required');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [simulationId]);

  const loadTimeline = async () => {
    if (!simulationId) {
      setError('Simulation ID is required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      console.log('[VerboseTimeline] Loading timeline for simulation:', simulationId);
      const data = await simulationApi.getVerboseTimeline(simulationId);
      console.log('[VerboseTimeline] Received data:', {
        simulation_id: data.simulation_id,
        ticker: data.ticker,
        total_rows: data.total_rows,
        rows_count: data.rows?.length || 0,
      });
      setRows((data.rows || []) as TimelineRow[]);
      if (!data.rows || data.rows.length === 0) {
        console.warn('[VerboseTimeline] No timeline rows returned');
      }
    } catch (err: any) {
      console.error('[VerboseTimeline] Error loading timeline:', err);
      console.error('[VerboseTimeline] Error details:', {
        message: err.message,
        status: err.status,
        stack: err.stack,
      });
      setError(err.message || 'Failed to load verbose timeline');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      // Use the existing export endpoint which now includes verbose timeline
      const response = await fetch(`/api/v1/simulations/${simulationId}/export?format=xlsx`);
      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `verbose_timeline_${ticker}_${simulationId}_${
        new Date().toISOString().split('T')[0]
      }.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '-';
    return `$${value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(2)}%`;
  };

  const formatNumber = (value: number | null | undefined, decimals: number = 0) => {
    if (value === null || value === undefined) return '-';
    return value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatDateTime = (value: string) => {
    if (!value) return '-';
    try {
      const date = new Date(value);
      return date.toLocaleString();
    } catch {
      return value;
    }
  };

  const totalPages = Math.ceil(rows.length / ROWS_PER_PAGE);
  const startIndex = (currentPage - 1) * ROWS_PER_PAGE;
  const endIndex = startIndex + ROWS_PER_PAGE;
  const paginatedRows = rows.slice(startIndex, endIndex);

  // Column definitions
  const columns = [
    { key: 'DateTime', label: 'DateTime', width: '150px' },
    { key: 'Open', label: 'Open', width: '80px', format: formatCurrency },
    { key: 'High', label: 'High', width: '80px', format: formatCurrency },
    { key: 'Low', label: 'Low', width: '80px', format: formatCurrency },
    { key: 'Close', label: 'Close', width: '80px', format: formatCurrency },
    { key: 'Volume', label: 'Volume', width: '100px', format: formatNumber },
    { key: 'AnchorPrice', label: 'AnchorPrice', width: '100px', format: formatCurrency },
    { key: 'DividendPercent', label: 'Dividend%', width: '90px', format: formatPercent },
    { key: 'DividendValue', label: 'DividendValue', width: '110px', format: formatCurrency },
    { key: 'PctChangeFromPrev', label: 'PctChgPrev', width: '100px', format: formatPercent },
    { key: 'PctChangeFromAnchor', label: 'PctChgAnchor', width: '110px', format: formatPercent },
    { key: 'Quantity', label: 'Quantity', width: '80px', format: formatNumber },
    { key: 'PositionValue', label: 'PositionValue', width: '120px', format: formatCurrency },
    { key: 'Cash', label: 'Cash', width: '100px', format: formatCurrency },
    { key: 'TotalPortfolioValue', label: 'TotalValue', width: '120px', format: formatCurrency },
    { key: 'DeltaTotalValue', label: 'DeltaValue', width: '110px', format: formatCurrency },
    { key: 'PctDeltaTotalValue', label: 'PctDeltaValue', width: '120px', format: formatPercent },
    {
      key: 'PctStockChangeFromBaseline',
      label: 'PctStockBaseline',
      width: '140px',
      format: formatPercent,
    },
    {
      key: 'PctPortfolioChangeFromBaseline',
      label: 'PctPortBaseline',
      width: '150px',
      format: formatPercent,
    },
    { key: 'TriggerThresholdUp', label: 'TrigThreshUp', width: '110px', format: formatPercent },
    { key: 'TriggerThresholdDown', label: 'TrigThreshDown', width: '120px', format: formatPercent },
    { key: 'TriggerSignal', label: 'TriggerSignal', width: '110px' },
    { key: 'TriggerReason', label: 'TriggerReason', width: '130px' },
    { key: 'GuardrailMinStockPct', label: 'GuardMin%', width: '100px', format: formatPercent },
    { key: 'GuardrailMaxStockPct', label: 'GuardMax%', width: '100px', format: formatPercent },
    {
      key: 'GuardrailMaxTradePctOfPosition',
      label: 'GuardMaxTrade%',
      width: '130px',
      format: formatPercent,
    },
    { key: 'GuardrailAllowed', label: 'GuardAllowed', width: '120px' },
    { key: 'GuardrailReason', label: 'GuardReason', width: '130px' },
    { key: 'Action', label: 'Action', width: '90px' },
    { key: 'ActionReason', label: 'ActionReason', width: '200px' },
    { key: 'TradeSide', label: 'TradeSide', width: '90px' },
    { key: 'TradeQuantity', label: 'TradeQty', width: '90px', format: formatNumber },
    { key: 'TradePrice', label: 'TradePrice', width: '100px', format: formatCurrency },
    { key: 'TradeNotional', label: 'TradeNotional', width: '120px', format: formatCurrency },
    { key: 'TradeCommission', label: 'TradeComm', width: '100px', format: formatCurrency },
    {
      key: 'TradeCommissionRateEffective',
      label: 'TradeCommRate%',
      width: '130px',
      format: formatPercent,
    },
    { key: 'DividendCashThisLine', label: 'DivCashLine', width: '120px', format: formatCurrency },
  ];

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading verbose timeline...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadTimeline}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <p className="text-gray-500">No timeline data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with export button */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Verbose Timeline</h3>
          <p className="text-sm text-gray-500">
            {rows.length} rows • Showing {startIndex + 1}-{Math.min(endIndex, rows.length)} of{' '}
            {rows.length}
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
        >
          <Download className="w-4 h-4 mr-2" />
          {exporting ? 'Exporting...' : 'Export to Excel'}
        </button>
      </div>

      {/* Table container with horizontal scroll */}
      <div className="card overflow-x-auto">
        <div className="min-w-full">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap"
                    style={{ width: col.width }}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  {columns.map((col) => {
                    const value = row[col.key as keyof TimelineRow];
                    const displayValue = col.format ? col.format(value as any) : value || '-';
                    return (
                      <td
                        key={col.key}
                        className="px-3 py-2 text-xs text-gray-900 whitespace-nowrap"
                      >
                        {displayValue}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
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














