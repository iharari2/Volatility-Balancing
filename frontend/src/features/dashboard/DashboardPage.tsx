import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Play,
  BarChart3,
  FileSearch,
  Download,
  TrendingUp,
  TrendingDown,
  Briefcase,
  ExternalLink,
  Activity,
  Settings,
  Grid3X3,
} from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import EmptyState from '../../components/shared/EmptyState';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import KPICardGrid, { KPIMetric, formatCurrency, formatPercent, getValueColor } from '../../components/shared/KPICardGrid';
import ActivityFeed, { ActivityEvent } from '../../components/shared/ActivityFeed';
import TradingControls, { useWorkerStatus } from '../../components/trading/TradingControls';
import AssetAllocationChart from '../overview/AssetAllocationChart';

export default function DashboardPage() {
  const { positions, overview, loading: portfolioLoading } = usePortfolio();
  const { selectedPortfolio, selectedPortfolioId, loading: contextLoading } = useTenantPortfolio();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [recentActivity, setRecentActivity] = useState<ActivityEvent[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(false);

  const { workerStatus, fetchWorkerStatus, toggleWorker } = useWorkerStatus();

  const loading = portfolioLoading || contextLoading;

  // Calculate KPIs from overview or positions
  const kpis = useMemo(() => {
    if (overview) {
      return {
        totalValue: overview.kpis.total_value,
        cashBalance: overview.cash.cash_balance,
        stockAllocation: overview.kpis.stock_pct,
        cashAllocation: overview.kpis.cash_pct,
        pnl: overview.kpis.pnl_abs || 0,
        pnlPercent: overview.kpis.pnl_pct || 0,
      };
    }

    if (positions.length > 0) {
      const totalCash = positions.reduce((sum, pos) => sum + (pos.cashAmount || 0), 0);
      const totalStock = positions.reduce((sum, pos) => sum + (pos.marketValue || 0), 0);
      const total = totalCash + totalStock;

      return {
        totalValue: total,
        cashBalance: totalCash,
        stockAllocation: total > 0 ? (totalStock / total) * 100 : 0,
        cashAllocation: total > 0 ? (totalCash / total) * 100 : 0,
        pnl: 0,
        pnlPercent: 0,
      };
    }

    return {
      totalValue: 0,
      cashBalance: 0,
      stockAllocation: 0,
      cashAllocation: 0,
      pnl: 0,
      pnlPercent: 0,
    };
  }, [overview, positions]);

  // KPI metrics for display
  const kpiMetrics: KPIMetric[] = useMemo(() => [
    {
      id: 'total_value',
      label: 'Total Value',
      value: formatCurrency(kpis.totalValue),
    },
    {
      id: 'cash_balance',
      label: 'Cash Balance',
      value: formatCurrency(kpis.cashBalance),
    },
    {
      id: 'stock_allocation',
      label: 'Stock Allocation',
      value: formatPercent(kpis.stockAllocation),
    },
    {
      id: 'pnl',
      label: 'Total P&L',
      value: formatPercent(kpis.pnlPercent, { showSign: true }),
      subValue: formatCurrency(kpis.pnl),
      valueColor: getValueColor(kpis.pnl),
      trend: kpis.pnl >= 0 ? 'up' : 'down',
    },
  ], [kpis]);

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };
    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchWorkerStatus();
  }, []);

  useEffect(() => {
    if (!selectedPortfolioId) return;

    const fetchActivity = async () => {
      setLoadingActivity(true);
      try {
        const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${apiBase}/v1/audit/traces?limit=10`);
        if (response.ok) {
          const data = await response.json();
          const events: ActivityEvent[] = (data.traces || []).map((trace: any) => ({
            id: trace.trace_id || crypto.randomUUID(),
            timestamp: trace.time,
            type: trace.summary?.toLowerCase().includes('buy')
              ? 'buy'
              : trace.summary?.toLowerCase().includes('sell')
              ? 'sell'
              : 'hold',
            asset: trace.asset,
            message: trace.summary,
            traceId: trace.trace_id,
          }));
          setRecentActivity(events);
        }
      } catch (error) {
        console.error('Error fetching activity:', error);
      } finally {
        setLoadingActivity(false);
      }
    };

    fetchActivity();
  }, [selectedPortfolioId]);

  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  if (!selectedPortfolio) {
    return (
      <EmptyState
        icon={<Briefcase className="h-16 w-16 text-gray-400" />}
        title="No Portfolio Selected"
        description="Create your first portfolio to start managing positions and trading"
        action={{
          label: 'Create Portfolio',
          to: '/portfolios',
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">{selectedPortfolio.name}</p>
        </div>
        <div className="flex items-center gap-4">
          <TradingControls
            portfolioId={selectedPortfolioId || ''}
            workerStatus={workerStatus}
            onToggleWorker={toggleWorker}
            variant="compact"
          />
          <span className={`badge ${marketHoursService.getStatusColor(marketStatus)}`}>
            {marketHoursService.getStatusLabel(marketStatus)}
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <KPICardGrid metrics={kpiMetrics} columns={4} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Asset Allocation Chart */}
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Asset Allocation</h2>
          <AssetAllocationChart />
        </div>

        {/* Quick Actions */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/positions?tab=cells"
              className="w-full btn btn-secondary flex items-center justify-start"
            >
              <Grid3X3 className="h-5 w-5 mr-3 text-primary-600" />
              View Position Cells
            </Link>
            <Link
              to="/positions?tab=trade"
              className="w-full btn btn-secondary flex items-center justify-start"
            >
              <Activity className="h-5 w-5 mr-3 text-primary-600" />
              Open Trading Cockpit
            </Link>
            <Link
              to="/simulation"
              className="w-full btn btn-secondary flex items-center justify-start"
            >
              <BarChart3 className="h-5 w-5 mr-3 text-primary-600" />
              Run Simulation
            </Link>
            <Link
              to="/audit"
              className="w-full btn btn-secondary flex items-center justify-start"
            >
              <FileSearch className="h-5 w-5 mr-3 text-primary-600" />
              View Audit Trail
            </Link>
            <Link
              to="/positions?tab=config"
              className="w-full btn btn-secondary flex items-center justify-start"
            >
              <Settings className="h-5 w-5 mr-3 text-primary-600" />
              Strategy Settings
            </Link>
          </div>
        </div>
      </div>

      {/* Position Summary Cards */}
      {positions.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Positions ({positions.length})</h2>
            <Link
              to="/positions?tab=cells"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
            >
              View All <ExternalLink className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {positions.slice(0, 8).map((position) => {
              const isPositive = (position.pnlPercent || 0) >= 0;
              const totalValue = (position.marketValue || 0) + (position.cashAmount || 0);
              const stockPct = totalValue > 0 ? ((position.marketValue || 0) / totalValue) * 100 : 0;

              return (
                <Link
                  key={position.id}
                  to={`/positions?tab=trade&positionId=${position.id}`}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-gray-900">{position.ticker}</span>
                    <span
                      className={`flex items-center text-sm font-medium ${
                        isPositive ? 'text-success-600' : 'text-danger-600'
                      }`}
                    >
                      {isPositive ? (
                        <TrendingUp className="h-4 w-4 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 mr-1" />
                      )}
                      {formatPercent(position.pnlPercent || 0, { showSign: true })}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Value:</span>
                      <span className="font-medium">{formatCurrency(totalValue)}</span>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span>Stock %:</span>
                      <span className="font-medium">{stockPct.toFixed(1)}%</span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="card">
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          <Link
            to="/audit"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
          >
            View All <ExternalLink className="h-4 w-4" />
          </Link>
        </div>
        {loadingActivity ? (
          <div className="text-center py-8 text-gray-500">Loading activity...</div>
        ) : (
          <ActivityFeed
            events={recentActivity}
            maxItems={10}
            variant="compact"
            emptyMessage="No recent trading activity"
          />
        )}
      </div>
    </div>
  );
}
