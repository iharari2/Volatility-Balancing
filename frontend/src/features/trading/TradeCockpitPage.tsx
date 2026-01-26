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
import PerformanceChart from '../../components/charts/PerformanceChart';
import { Briefcase, TrendingUp, BarChart3 } from 'lucide-react';
import { useParams } from 'react-router-dom';

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
  const [chartInterval, setChartInterval] = useState<'1h' | '4h' | '1d'>('1h');

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
        const data = await getPositionCockpit(selectedPortfolioId, selectedPositionId);
        setCockpitData(data);
      } catch (error) {
        console.error('Error loading cockpit:', error);
      } finally {
        setLoadingCockpit(false);
      }
    };

    loadCockpit();
  }, [selectedPortfolioId, selectedPositionId]);

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

              {/* Performance Chart */}
              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-gray-500" />
                    <h3 className="text-sm font-semibold text-gray-900">Performance Over Time</h3>
                  </div>
                  <div className="flex gap-1">
                    {(['1h', '4h', '1d'] as const).map((interval) => (
                      <button
                        key={interval}
                        onClick={() => setChartInterval(interval)}
                        className={`px-3 py-1 text-xs rounded ${
                          chartInterval === interval
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {interval}
                      </button>
                    ))}
                  </div>
                </div>
                <PerformanceChart
                  portfolioId={selectedPortfolioId!}
                  positionId={selectedPositionId!}
                  interval={chartInterval}
                  height={250}
                  chartType="area"
                />
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
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Timeline / Events</h3>
                  {cockpitData.timeline_rows.length === 0 ? (
                    <p className="text-sm text-gray-500">No timeline rows available.</p>
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
                          {cockpitData.timeline_rows.map((row, index) => (
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
