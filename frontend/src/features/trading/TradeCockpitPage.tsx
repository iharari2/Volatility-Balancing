import { useEffect, useMemo, useState } from 'react';
import {
  getPortfolios,
  getPortfolioPositions,
  getPositionCockpit,
  CockpitResponse,
  PortfolioListItem,
  PositionSummaryItem,
} from '../../api/cockpit';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import EmptyState from '../../components/shared/EmptyState';
import DateRangeFilter, { DateRange } from '../../components/shared/DateRangeFilter';
import EventTypeFilter from '../../components/shared/EventTypeFilter';
import { Briefcase, TrendingUp, Filter, X, Clock } from 'lucide-react';
import { useParams } from 'react-router-dom';

// Time window options for timeline/snapshot data
const timeWindowOptions = [
  { value: '1d', label: '1 Day' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: 'all', label: 'All Time' },
];

// Action types for filtering
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

const formatNumber = (value?: number | null, decimals: number = 2) => {
  if (value === null || value === undefined) return '-';
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export default function TradeCockpitPage() {
  const { portfolioId: routePortfolioId, positionId: routePositionId } = useParams<{
    portfolioId?: string;
    positionId?: string;
  }>();

  const [portfolios, setPortfolios] = useState<PortfolioListItem[]>([]);
  const [positions, setPositions] = useState<PositionSummaryItem[]>([]);
  const [cockpitData, setCockpitData] = useState<CockpitResponse | null>(null);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(
    routePortfolioId || null,
  );
  const [selectedPositionId, setSelectedPositionId] = useState<string | null>(
    routePositionId || null,
  );
  const [loadingPortfolios, setLoadingPortfolios] = useState(true);
  const [loadingPositions, setLoadingPositions] = useState(false);
  const [loadingCockpit, setLoadingCockpit] = useState(false);

  // Time window for data fetching
  const [timeWindow, setTimeWindow] = useState('7d');

  // Timeline filter state
  const [showFilters, setShowFilters] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });
  const [selectedActions, setSelectedActions] = useState<string[]>([]);

  useEffect(() => {
    const loadPortfolios = async () => {
      try {
        setLoadingPortfolios(true);
        const data = await getPortfolios();
        setPortfolios(data);
        if (!selectedPortfolioId && data.length > 0) {
          setSelectedPortfolioId(data[0].id);
        }
      } catch (error) {
        console.error('Error loading portfolios:', error);
      } finally {
        setLoadingPortfolios(false);
      }
    };

    loadPortfolios();
  }, []);

  useEffect(() => {
    if (!selectedPortfolioId) {
      setPositions([]);
      setSelectedPositionId(null);
      return;
    }

    const loadPositions = async () => {
      try {
        setLoadingPositions(true);
        const data = await getPortfolioPositions(selectedPortfolioId);
        setPositions(data);
        if (!selectedPositionId && data.length > 0) {
          setSelectedPositionId(data[0].position_id);
        }
      } catch (error) {
        console.error('Error loading positions:', error);
      } finally {
        setLoadingPositions(false);
      }
    };

    loadPositions();
  }, [selectedPortfolioId]);

  useEffect(() => {
    if (!selectedPortfolioId || !selectedPositionId) {
      setCockpitData(null);
      return;
    }

    const loadCockpit = async () => {
      try {
        setLoadingCockpit(true);
        const data = await getPositionCockpit(selectedPortfolioId, selectedPositionId, timeWindow);
        setCockpitData(data);
      } catch (error) {
        console.error('Error loading cockpit:', error);
      } finally {
        setLoadingCockpit(false);
      }
    };

    loadCockpit();
  }, [selectedPortfolioId, selectedPositionId, timeWindow]);

  const selectedPosition = useMemo(
    () => positions.find((pos) => pos.position_id === selectedPositionId) || null,
    [positions, selectedPositionId],
  );

  const allocationBand = cockpitData?.allocation_band;
  const allocationPct = allocationBand?.current_stock_pct ?? null;
  const minBand = allocationBand?.min_stock_pct ?? null;
  const maxBand = allocationBand?.max_stock_pct ?? null;
  const bandStart = minBand !== null ? Math.max(0, Math.min(100, minBand)) : 0;
  const bandEnd = maxBand !== null ? Math.max(0, Math.min(100, maxBand)) : 0;
  const bandWidth = Math.max(0, bandEnd - bandStart);
  const bandMarker = allocationPct !== null ? Math.max(0, Math.min(100, allocationPct)) : null;

  // Filter timeline rows
  const hasActiveFilters = dateRange.startDate !== null || dateRange.endDate !== null || selectedActions.length > 0;

  // Get unique actions from timeline for display
  const uniqueActions = useMemo(() => {
    if (!cockpitData?.timeline_rows) return new Set<string>();
    const actions = new Set<string>();
    cockpitData.timeline_rows.forEach((row) => {
      const action = (row.action || '').toUpperCase().trim();
      actions.add(action || '_EMPTY_');
    });
    return actions;
  }, [cockpitData?.timeline_rows]);

  const filteredTimelineRows = useMemo(() => {
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

  if (loadingPortfolios) {
    return <LoadingSpinner message="Loading portfolios..." />;
  }

  if (portfolios.length === 0) {
    return (
      <EmptyState
        icon={<Briefcase className="h-16 w-16 text-gray-400" />}
        title="No Portfolios"
        description="Create a portfolio first to view the position cockpit"
        action={{
          label: 'Go to Portfolios',
          to: '/portfolios',
        }}
      />
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <div className="px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-2xl font-bold text-gray-900">Trade Position Cockpit</h1>
        <p className="text-sm text-gray-500">Portfolio-scoped positions, summaries, and audit trail</p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-full max-w-sm border-r border-gray-200 bg-white flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <label className="block text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">
              Portfolio
            </label>
            <select
              value={selectedPortfolioId || ''}
              onChange={(event) => setSelectedPortfolioId(event.target.value || null)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose a portfolio...</option>
              {portfolios.map((portfolio) => (
                <option key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
              <h2 className="text-sm font-semibold text-gray-900">Positions</h2>
            </div>
            {loadingPositions ? (
              <LoadingSpinner message="Loading positions..." />
            ) : positions.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">
                <TrendingUp className="h-10 w-10 text-gray-400 mx-auto mb-3" />
                No positions in this portfolio
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {positions.map((pos) => (
                  <button
                    key={pos.position_id}
                    onClick={() => setSelectedPositionId(pos.position_id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                      pos.position_id === selectedPositionId
                        ? 'bg-blue-50 border-l-4 border-blue-500'
                        : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-gray-900">{pos.asset_symbol}</span>
                      <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                        {pos.status || 'RUNNING'}
                      </span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600">
                      <div>Qty: {formatNumber(pos.qty, 2)}</div>
                      <div>Cash: {formatCurrency(pos.cash)}</div>
                      <div>Total: {formatCurrency(pos.total_value)}</div>
                      <div>Stock %: {formatPercent(pos.stock_pct)}</div>
                      <div>Pos vs Base: {formatPercent(pos.position_vs_baseline_pct)}</div>
                      <div>Stock vs Base: {formatPercent(pos.stock_vs_baseline_pct)}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {!selectedPositionId || !selectedPosition ? (
            <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-500">
              Select a position to view the cockpit
            </div>
          ) : loadingCockpit ? (
            <LoadingSpinner message="Loading cockpit..." />
          ) : cockpitData ? (
            <>
              {/* Time Window Selector */}
              <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-500" />
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

              <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                {[
                  { label: 'Quantity', value: formatNumber(cockpitData.position_summary.qty, 2) },
                  { label: 'Cash', value: formatCurrency(cockpitData.position_summary.cash) },
                  {
                    label: 'Stock Value',
                    value: formatCurrency(cockpitData.position_summary.stock_value),
                  },
                  { label: 'Total Value', value: formatCurrency(cockpitData.position_summary.total_value) },
                ].map((card) => (
                  <div key={card.label} className="bg-white border border-gray-200 rounded-lg p-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase">{card.label}</p>
                    <p className="text-xl font-bold text-gray-900 mt-2">{card.value}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
                  <h3 className="text-sm font-semibold text-gray-900">Baseline Comparison</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-gray-500">Stock vs Baseline</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatPercent(cockpitData.baseline_comparison.stock_vs_baseline_pct)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatCurrency(cockpitData.baseline_comparison.stock_vs_baseline_abs)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Position vs Baseline</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatPercent(cockpitData.baseline_comparison.position_vs_baseline_pct)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatCurrency(cockpitData.baseline_comparison.position_vs_baseline_abs)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
                  <h3 className="text-sm font-semibold text-gray-900">Guardrail Allocation Band</h3>
                  <div className="relative h-3 bg-gray-200 rounded-full">
                    <div
                      className="absolute h-3 bg-emerald-200 rounded-full"
                      style={{ left: `${bandStart}%`, width: `${bandWidth}%` }}
                    />
                    {bandMarker !== null && (
                      <div
                        className="absolute -top-1 w-2 h-5 bg-gray-900 rounded"
                        style={{ left: `calc(${bandMarker}% - 4px)` }}
                      />
                    )}
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Min: {formatPercent(minBand)}</span>
                    <span>Current: {formatPercent(allocationPct)}</span>
                    <span>Max: {formatPercent(maxBand)}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    Status: {allocationBand?.within_band ? 'Within band' : 'Outside band'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-5 lg:col-span-1">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Recent Market Snapshot</h3>
                  {cockpitData.recent_quotes.length === 0 ? (
                    <p className="text-sm text-gray-500">No recent market data available.</p>
                  ) : (
                    <div className="space-y-3 text-sm text-gray-700">
                      <div>
                        <p className="text-xs text-gray-500">Timestamp</p>
                        <p>{cockpitData.recent_quotes[0].timestamp || '-'}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>Open: {formatCurrency(cockpitData.recent_quotes[0].open)}</div>
                        <div>High: {formatCurrency(cockpitData.recent_quotes[0].high)}</div>
                        <div>Low: {formatCurrency(cockpitData.recent_quotes[0].low)}</div>
                        <div>Close: {formatCurrency(cockpitData.recent_quotes[0].close)}</div>
                        <div>Volume: {formatNumber(cockpitData.recent_quotes[0].volume, 0)}</div>
                        <div>Policy: {cockpitData.recent_quotes[0].price_policy || '-'}</div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-5 lg:col-span-2">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-sm font-semibold text-gray-900">Timeline / Events</h3>
                      {hasActiveFilters && (
                        <span className="text-xs text-primary-600">
                          Showing {filteredTimelineRows.length} of {cockpitData.timeline_rows.length}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`flex items-center gap-1.5 px-2 py-1 text-xs rounded border transition-colors ${
                          showFilters || hasActiveFilters
                            ? 'bg-primary-50 border-primary-300 text-primary-700'
                            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <Filter className="h-3 w-3" />
                        Filters
                        {hasActiveFilters && (
                          <span className="bg-primary-600 text-white px-1 py-0.5 rounded-full text-[10px]">
                            {(dateRange.startDate || dateRange.endDate ? 1 : 0) + (selectedActions.length > 0 ? 1 : 0)}
                          </span>
                        )}
                      </button>
                      {hasActiveFilters && (
                        <button
                          onClick={handleClearFilters}
                          className="flex items-center gap-1 px-1 py-1 text-xs text-gray-500 hover:text-gray-700"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  </div>

                  {showFilters && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg space-y-3">
                      <div className="flex flex-wrap items-start gap-4">
                        <div className="flex-1 min-w-[200px]">
                          <label className="block text-xs font-medium text-gray-700 mb-1">Date Range</label>
                          <DateRangeFilter value={dateRange} onChange={setDateRange} compact />
                        </div>
                        <div className="min-w-[140px]">
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

                  {cockpitData.timeline_rows.length === 0 ? (
                    <p className="text-sm text-gray-500">No timeline rows available.</p>
                  ) : filteredTimelineRows.length === 0 ? (
                    <div className="text-sm text-gray-500 space-y-2">
                      <p>No events match your filters.</p>
                      <p className="text-xs">
                        Actions in data:{' '}
                        {Array.from(uniqueActions)
                          .map((a) => (a === '_EMPTY_' ? 'No Action' : a))
                          .join(', ') || 'None'}
                      </p>
                      {selectedActions.length > 0 && !selectedActions.some(a => uniqueActions.has(a)) && (
                        <p className="text-xs text-amber-600">
                          Tip: The actions you selected don't exist in this timeline.
                          This position may not have had any BUY/SELL triggers yet.
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-xs text-gray-700">
                        <thead>
                          <tr className="text-left border-b border-gray-200">
                            {[
                              'timestamp',
                              'effective_price',
                              'price_policy_effective',
                              'trigger_direction',
                              'trigger_reason',
                              'guardrail_allowed',
                              'guardrail_block_reason',
                              'action',
                              'action_reason',
                              'position_total_value_after',
                            ].map((header) => (
                              <th key={header} className="px-2 py-2 font-semibold text-gray-600">
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {filteredTimelineRows.map((row, index) => (
                            <tr key={`${row.id || row.timestamp || index}`} className="border-b border-gray-100">
                              <td className="px-2 py-2 whitespace-nowrap">{row.timestamp || '-'}</td>
                              <td className="px-2 py-2">{formatCurrency(row.effective_price)}</td>
                              <td className="px-2 py-2">{row.price_policy_effective || '-'}</td>
                              <td className="px-2 py-2">{row.trigger_direction || '-'}</td>
                              <td className="px-2 py-2">{row.trigger_reason || '-'}</td>
                              <td className="px-2 py-2">
                                {row.guardrail_allowed === null || row.guardrail_allowed === undefined
                                  ? '-'
                                  : row.guardrail_allowed
                                  ? 'YES'
                                  : 'NO'}
                              </td>
                              <td className="px-2 py-2">{row.guardrail_block_reason || '-'}</td>
                              <td className="px-2 py-2">{row.action || '-'}</td>
                              <td className="px-2 py-2">{row.action_reason || '-'}</td>
                              <td className="px-2 py-2">{formatCurrency(row.position_total_value_after)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-500">
              Cockpit data unavailable.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
