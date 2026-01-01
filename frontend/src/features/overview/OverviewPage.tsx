import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Play,
  BarChart3,
  FileSearch,
  Download,
  TrendingUp,
  DollarSign,
  PieChart,
  Briefcase,
  ExternalLink,
} from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import EmptyState from '../../components/shared/EmptyState';
import RecentTradesTable from './RecentTradesTable';
import TriggerEventsTable from './TriggerEventsTable';
import AssetAllocationChart from './AssetAllocationChart';

export default function OverviewPage() {
  const { positions, overview, loading: portfolioLoading } = usePortfolio();
  const { selectedPortfolio, loading: contextLoading } = useTenantPortfolio();
  const [totalValue, setTotalValue] = useState(0);
  const [cashBalance, setCashBalance] = useState(0);
  const [cashAllocation, setCashAllocation] = useState(0);
  const [stockAllocation, setStockAllocation] = useState(0);
  const [pnl, setPnl] = useState(0);
  const [pnlPercent, setPnlPercent] = useState(0);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');

  const loading = portfolioLoading || contextLoading;

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
    if (overview) {
      setTotalValue(overview.kpis.total_value);
      setCashBalance(overview.cash.cash_balance);
      setStockAllocation(overview.kpis.stock_pct);
      setCashAllocation(overview.kpis.cash_pct);
      setPnl(overview.kpis.pnl_abs || 0);
      setPnlPercent(overview.kpis.pnl_pct || 0);
    } else if (positions.length > 0) {
      // Fallback calculation if overview is not yet loaded
      const totalCash = positions.reduce((sum, pos) => sum + (pos.cashAmount || 0), 0);
      const totalStock = positions.reduce((sum, pos) => sum + (pos.marketValue || 0), 0);
      const total = totalCash + totalStock;

      setTotalValue(total);
      setCashBalance(totalCash);
      setCashAllocation(total > 0 ? (totalCash / total) * 100 : 0);
      setStockAllocation(total > 0 ? (totalStock / total) * 100 : 0);
    }
  }, [overview, positions]);

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">Loading portfolio data...</p>
      </div>
    );
  }

  // Show loading while context is initializing
  if (contextLoading) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">Loading portfolios...</p>
      </div>
    );
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Overview</h1>
          <p className="text-sm text-gray-500 mt-1">{selectedPortfolio.name}</p>
        </div>
        <div className="flex items-center gap-x-2">
          <span className="text-sm text-gray-500">Market:</span>
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${marketHoursService.getStatusColor(
              marketStatus,
            )}`}
          >
            {marketHoursService.getStatusLabel(marketStatus)}
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-primary-100 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate uppercase tracking-wider">
                  Total Value
                </dt>
                <dd className="text-2xl font-bold text-gray-900">
                  $
                  {totalValue.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-success-100 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-success-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate uppercase tracking-wider">
                  Cash Balance
                </dt>
                <dd className="text-2xl font-bold text-gray-900">
                  $
                  {cashBalance.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-warning-100 p-3 rounded-lg">
              <PieChart className="h-6 w-6 text-warning-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate uppercase tracking-wider">
                  Portfolio Stock %
                </dt>
                <dd className="text-2xl font-bold text-gray-900">{stockAllocation.toFixed(1)}%</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-indigo-100 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6 text-indigo-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate uppercase tracking-wider">
                  Total P&L
                </dt>
                <dd
                  className={`text-2xl font-bold ${
                    pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}
                >
                  <div className="flex flex-col">
                    <span>
                      {pnl >= 0 ? '+' : ''}
                      {pnlPercent.toFixed(2)}%
                    </span>
                    <span className="text-xs opacity-80">
                      {pnl >= 0 ? '+' : ''}$
                      {pnl.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

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
              to="/simulation"
              className="w-full btn btn-secondary flex items-center justify-start"
            >
              <BarChart3 className="h-5 w-5 mr-3 text-primary-600" />
              Run Simulation
            </Link>
            <Link to="/audit" className="w-full btn btn-secondary flex items-center justify-start">
              <FileSearch className="h-5 w-5 mr-3 text-primary-600" />
              View Audit Trail
            </Link>
            <button className="w-full btn btn-secondary flex items-center justify-start">
              <Download className="h-5 w-5 mr-3 text-primary-600" />
              Export Excel
            </button>
            <Link to="/trading" className="w-full btn btn-primary flex items-center justify-start">
              <Play className="h-5 w-5 mr-3 text-white" />
              Open Trading Console
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Trades */}
      <div className="card">
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Recent Trades (last 10)</h2>
          <Link
            to="/audit"
            className="text-sm text-primary-600 hover:text-primary-900 font-semibold flex items-center gap-1"
          >
            View All Traces <ExternalLink className="h-4 w-4" />
          </Link>
        </div>
        <div className="-mx-6">
          <RecentTradesTable />
        </div>
      </div>

      {/* Trigger & Guardrail Events */}
      <div className="card">
        <div className="mb-4 pb-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Trigger & Guardrail Events</h2>
        </div>
        <div className="-mx-6">
          <TriggerEventsTable />
        </div>
      </div>
    </div>
  );
}
