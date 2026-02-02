import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, DollarSign, PieChart, BarChart3 } from 'lucide-react';
import { useWorkspace } from '../../WorkspaceContext';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';
import { getPositionCockpit, CockpitResponse } from '../../../../api/cockpit';
import LoadingSpinner from '../../../../components/shared/LoadingSpinner';

const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
};

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined) return '-';
  return `${value.toFixed(2)}%`;
};

interface KPICardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  trend?: number | null;
}

function KPICard({ label, value, icon, trend }: KPICardProps) {
  const trendPositive = trend !== null && trend !== undefined && trend >= 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-500 uppercase">{label}</span>
        <div className="text-gray-400">{icon}</div>
      </div>
      <div className="flex items-end justify-between">
        <span className="text-xl font-bold text-gray-900">{value}</span>
        {trend !== null && trend !== undefined && (
          <span
            className={`flex items-center text-xs font-semibold ${
              trendPositive ? 'text-success-600' : 'text-danger-600'
            }`}
          >
            {trendPositive ? (
              <TrendingUp className="h-3 w-3 mr-0.5" />
            ) : (
              <TrendingDown className="h-3 w-3 mr-0.5" />
            )}
            {trendPositive ? '+' : ''}
            {trend.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  );
}

export default function OverviewTab() {
  const { selectedPosition, portfolioId } = useWorkspace();
  const [cockpitData, setCockpitData] = useState<CockpitResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!portfolioId || !selectedPosition) {
      setCockpitData(null);
      setLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);
        const data = await getPositionCockpit(portfolioId, selectedPosition.position_id, '7d');
        setCockpitData(data);
      } catch (error) {
        console.error('Error loading cockpit data:', error);
        setCockpitData(null);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [portfolioId, selectedPosition?.position_id]);

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading overview..." />
      </div>
    );
  }

  if (!cockpitData || !selectedPosition) {
    return (
      <div className="p-8 text-center text-gray-500">
        Unable to load position data
      </div>
    );
  }

  const { position_summary, baseline_comparison, allocation_band } = cockpitData;

  // Allocation band visualization
  const minBand = allocation_band?.min_stock_pct ?? 0;
  const maxBand = allocation_band?.max_stock_pct ?? 100;
  const currentAlloc = allocation_band?.current_stock_pct ?? 50;
  const bandStart = Math.max(0, Math.min(100, minBand));
  const bandEnd = Math.max(0, Math.min(100, maxBand));
  const bandWidth = Math.max(0, bandEnd - bandStart);
  const markerPos = Math.max(0, Math.min(100, currentAlloc));

  return (
    <div className="p-6 space-y-6">
      {/* Position Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            {selectedPosition.asset_symbol} Position
          </h2>
          <p className="text-sm text-gray-500">Overview and performance metrics</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            selectedPosition.status === 'RUNNING'
              ? 'bg-success-100 text-success-700'
              : 'bg-gray-100 text-gray-700'
          }`}
        >
          {selectedPosition.status || 'RUNNING'}
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Value"
          value={formatCurrency(position_summary.total_value)}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <KPICard
          label="Stock Value"
          value={formatCurrency(position_summary.stock_value)}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <KPICard
          label="Quantity"
          value={position_summary.qty.toFixed(2)}
          icon={<PieChart className="h-4 w-4" />}
        />
        <KPICard
          label="Cash"
          value={formatCurrency(position_summary.cash)}
          icon={<DollarSign className="h-4 w-4" />}
        />
      </div>

      {/* Two-column section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Baseline Comparison */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Baseline Comparison</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Position vs Baseline</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatPercent(baseline_comparison.position_vs_baseline_pct)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Absolute</p>
                <p
                  className={`text-sm font-medium ${
                    (baseline_comparison.position_vs_baseline_abs ?? 0) >= 0
                      ? 'text-success-600'
                      : 'text-danger-600'
                  }`}
                >
                  {formatCurrency(baseline_comparison.position_vs_baseline_abs)}
                </p>
              </div>
            </div>
            <div className="border-t border-gray-100 pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Stock vs Baseline</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatPercent(baseline_comparison.stock_vs_baseline_pct)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Absolute</p>
                  <p
                    className={`text-sm font-medium ${
                      (baseline_comparison.stock_vs_baseline_abs ?? 0) >= 0
                        ? 'text-success-600'
                        : 'text-danger-600'
                    }`}
                  >
                    {formatCurrency(baseline_comparison.stock_vs_baseline_abs)}
                  </p>
                </div>
              </div>
            </div>
            <div className="border-t border-gray-100 pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Performance</p>
                  <p className="text-sm text-gray-700">
                    {(baseline_comparison.position_vs_baseline_pct ?? 0) >
                    (baseline_comparison.stock_vs_baseline_pct ?? 0)
                      ? 'Outperforming'
                      : (baseline_comparison.position_vs_baseline_pct ?? 0) <
                        (baseline_comparison.stock_vs_baseline_pct ?? 0)
                      ? 'Underperforming'
                      : 'In Line'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Allocation Band */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Guardrail Allocation Band</h3>
          <div className="space-y-4">
            {/* Visual Band */}
            <div className="relative h-4 bg-gray-200 rounded-full">
              {/* Safe zone */}
              <div
                className="absolute h-4 bg-emerald-200 rounded-full"
                style={{ left: `${bandStart}%`, width: `${bandWidth}%` }}
              />
              {/* Current position marker */}
              <div
                className="absolute -top-1 w-2 h-6 bg-gray-900 rounded"
                style={{ left: `calc(${markerPos}% - 4px)` }}
              />
            </div>

            {/* Labels */}
            <div className="flex justify-between text-xs text-gray-500">
              <span>Min: {formatPercent(minBand)}</span>
              <span
                className={`font-semibold ${
                  allocation_band?.within_band ? 'text-success-600' : 'text-danger-600'
                }`}
              >
                Current: {formatPercent(currentAlloc)}
              </span>
              <span>Max: {formatPercent(maxBand)}</span>
            </div>

            {/* Status */}
            <div className="border-t border-gray-100 pt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Status</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-semibold ${
                    allocation_band?.within_band
                      ? 'bg-success-100 text-success-700'
                      : 'bg-danger-100 text-danger-700'
                  }`}
                >
                  {allocation_band?.within_band ? 'Within Band' : 'Outside Band'}
                </span>
              </div>
            </div>

            {/* Stock/Cash breakdown */}
            <div className="border-t border-gray-100 pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Stock Allocation</span>
                <span className="font-semibold text-gray-900">{formatPercent(currentAlloc)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Cash Allocation</span>
                <span className="font-semibold text-gray-900">
                  {formatPercent(100 - (currentAlloc ?? 50))}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Market Data */}
      {cockpitData.recent_quotes.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Recent Market Snapshot</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <p className="text-xs text-gray-500">Last Price</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatCurrency(cockpitData.recent_quotes[0].effective_price)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Open</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatCurrency(cockpitData.recent_quotes[0].open)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">High</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatCurrency(cockpitData.recent_quotes[0].high)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Low</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatCurrency(cockpitData.recent_quotes[0].low)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Close</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatCurrency(cockpitData.recent_quotes[0].close)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Volume</p>
              <p className="text-sm font-semibold text-gray-900">
                {cockpitData.recent_quotes[0].volume
                  ? `${(cockpitData.recent_quotes[0].volume / 1000000).toFixed(1)}M`
                  : '-'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
