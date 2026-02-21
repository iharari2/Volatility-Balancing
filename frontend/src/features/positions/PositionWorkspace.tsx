import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Settings,
  DollarSign,
  Copy,
  AlertCircle,
  TrendingUp,
  Briefcase,
  Activity,
  BarChart3,
  Grid3X3,
} from 'lucide-react';
import { portfolioApi, marketApi } from '../../lib/api';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import EmptyState from '../../components/shared/EmptyState';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import KPICardGrid, { formatCurrency, formatPercent, getValueColor } from '../../components/shared/KPICardGrid';
import PositionSelector, { PositionOption } from '../../components/positions/PositionSelector';
import TradingControls, { useWorkerStatus, WorkerStatus } from '../../components/trading/TradingControls';
import PositionsTab from './tabs/PositionsTab';
import CashTab from './tabs/CashTab';
import StrategyConfigTab from './tabs/StrategyConfigTab';
import { portfolioScopedApi, PortfolioConfig } from '../../services/portfolioScopedApi';
import AnalyticsKPIs from '../analytics/AnalyticsKPIs';
import AnalyticsCharts from '../analytics/AnalyticsCharts';
import PerformanceChart from '../../components/charts/PerformanceChart';
import DecisionMonitor from '../../components/trading/DecisionMonitor';
import DecisionHistoryTable from '../../components/trading/DecisionHistoryTable';
import OrdersPanel from '../../components/trading/OrdersPanel';

interface Position {
  id: string;
  ticker?: string;
  asset?: string;
  qty: number;
  cash: number;
  anchor_price: number | null;
  avg_cost?: number | null;
  total_dividends_received?: number;
  current_price?: number;
  position_value?: number;
  weight_percent?: number;
  pnl?: number;
  pnl_percent?: number;
  status?: string;
}

interface EffectiveConfig {
  trigger_up: number;
  trigger_down: number;
  min_stock_pct: number;
  max_stock_pct: number;
  max_trade_pct_of_position: number;
  commission_base_rate: number;
  commission_overrides_count: number;
  market_hours_policy: string;
  last_updated: string;
}

type TabId = 'cells' | 'trade' | 'analytics' | 'cash' | 'config';

const tabs: { id: TabId; label: string; icon: typeof TrendingUp }[] = [
  { id: 'cells', label: 'Cells', icon: Grid3X3 },
  { id: 'trade', label: 'Trade', icon: Activity },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'cash', label: 'Cash', icon: DollarSign },
  { id: 'config', label: 'Config', icon: Settings },
];

function sanitizeTicker(ticker: string | null | undefined): string | null {
  if (!ticker) return null;
  const sanitized = ticker.replace(/[\\\n\r\t]/g, '').trim().toUpperCase();
  return sanitized.length > 0 ? sanitized : null;
}

export default function PositionWorkspace() {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { selectedTenantId, selectedPortfolioId, portfolios, selectedTenant } = useTenantPortfolio();

  const activeTab = (searchParams.get('tab') as TabId) || 'cells';
  const selectedPositionId = searchParams.get('positionId');

  const currentPortfolioId = portfolioId || selectedPortfolioId;
  const currentPortfolio = portfolios.find((p) => p.id === currentPortfolioId);
  const tenantId = selectedTenantId || 'default';
  const tenantName = selectedTenant?.name || 'Default Tenant';

  const [positions, setPositions] = useState<Position[]>([]);
  const [effectiveConfig, setEffectiveConfig] = useState<EffectiveConfig | null>(null);
  const [editableConfig, setEditableConfig] = useState<PortfolioConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [copiedTraceId, setCopiedTraceId] = useState<string | null>(null);
  const [chartInterval, setChartInterval] = useState<'1h' | '4h' | '1d'>('1h');

  const { workerStatus, fetchWorkerStatus, toggleWorker } = useWorkerStatus();

  // Calculate totals
  const totals = useMemo(() => {
    const totalCash = positions.reduce((sum, pos) => sum + (pos.cash || 0), 0);
    const totalStockValue = positions.reduce((sum, pos) => sum + (pos.position_value || 0), 0);
    const totalValue = totalCash + totalStockValue;
    const stockPct = totalValue > 0 ? (totalStockValue / totalValue) * 100 : 0;
    const totalPnl = positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);

    return { totalCash, totalStockValue, totalValue, stockPct, totalPnl };
  }, [positions]);

  // Convert positions to PositionOption format for selector
  const positionOptions: PositionOption[] = useMemo(() => {
    return positions.map((pos) => ({
      id: pos.id,
      asset: pos.asset || pos.ticker || 'UNKNOWN',
      qty: pos.qty,
      cash: pos.cash || 0,
      totalValue: (pos.position_value || 0) + (pos.cash || 0),
      stockPct: pos.position_value && pos.cash
        ? (pos.position_value / (pos.position_value + pos.cash)) * 100
        : 0,
      status: pos.status,
      priceChangePct: pos.pnl_percent,
    }));
  }, [positions]);

  // KPI metrics for the header
  const kpiMetrics = useMemo(() => [
    {
      id: 'total_value',
      label: 'Total Value',
      value: formatCurrency(totals.totalValue),
    },
    {
      id: 'stock_value',
      label: 'Stock Value',
      value: formatCurrency(totals.totalStockValue),
      subValue: `${totals.stockPct.toFixed(1)}%`,
    },
    {
      id: 'cash',
      label: 'Cash',
      value: formatCurrency(totals.totalCash),
    },
    {
      id: 'pnl',
      label: 'Unrealized P&L',
      value: formatCurrency(totals.totalPnl),
      valueColor: getValueColor(totals.totalPnl),
      trend: totals.totalPnl >= 0 ? 'up' as const : 'down' as const,
    },
  ], [totals]);

  useEffect(() => {
    if (!currentPortfolioId) {
      setError('No portfolio selected');
      setLoading(false);
      return;
    }
    loadData();
    fetchWorkerStatus();
  }, [currentPortfolioId]);

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };
    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    if (!currentPortfolioId) return;

    setLoading(true);
    setError(null);
    try {
      const [positionsData, summary] = await Promise.all([
        portfolioApi.getPositions(tenantId, currentPortfolioId).catch(() => []),
        portfolioApi.getSummary(tenantId, currentPortfolioId).catch(() => null),
      ]);

      const positionsWithPrices = await Promise.all(
        positionsData.map(async (pos: any) => {
          const tickerValue = pos.asset || pos.ticker || '';
          const sanitizedTicker = sanitizeTicker(tickerValue);

          if (!sanitizedTicker) {
            return {
              ...pos,
              ticker: tickerValue,
              asset: tickerValue,
              current_price: pos.anchor_price || 0,
              position_value: pos.qty * (pos.anchor_price || 0),
              weight_percent: 0,
            };
          }

          try {
            const priceData = await marketApi.getPrice(sanitizedTicker);
            const currentPrice = priceData.price;
            const positionValue = pos.qty * currentPrice;
            const totalValue = summary?.total_value || 0;
            return {
              ...pos,
              ticker: sanitizedTicker,
              asset: sanitizedTicker,
              cash: pos.cash || 0,
              current_price: currentPrice,
              position_value: positionValue,
              weight_percent: totalValue > 0 ? (positionValue / totalValue) * 100 : 0,
            };
          } catch (err: any) {
            return {
              ...pos,
              ticker: sanitizedTicker,
              asset: sanitizedTicker,
              current_price: pos.anchor_price || 0,
              position_value: pos.qty * (pos.anchor_price || 0),
              weight_percent: 0,
            };
          }
        }),
      );

      setPositions(positionsWithPrices);

      try {
        const [effective, editable] = await Promise.all([
          portfolioScopedApi.getEffectiveConfig(tenantId, currentPortfolioId),
          portfolioScopedApi.getConfig(tenantId, currentPortfolioId),
        ]);

        setEffectiveConfig({
          trigger_up: effective.trigger_threshold_up_pct,
          trigger_down: effective.trigger_threshold_down_pct,
          min_stock_pct: effective.min_stock_pct,
          max_stock_pct: effective.max_stock_pct,
          max_trade_pct_of_position: effective.max_trade_pct_of_position,
          commission_base_rate: effective.commission_rate,
          commission_overrides_count: 0,
          market_hours_policy: effective.market_hours_policy,
          last_updated: effective.last_updated,
        });

        setEditableConfig(editable);
      } catch (err: any) {
        setEffectiveConfig({
          trigger_up: 3.0,
          trigger_down: -3.0,
          min_stock_pct: 20,
          max_stock_pct: 60,
          max_trade_pct_of_position: 10,
          commission_base_rate: 0.1,
          commission_overrides_count: 0,
          market_hours_policy: 'market-open-only',
          last_updated: new Date().toISOString(),
        });
        setEditableConfig({
          trigger_threshold_up_pct: 3.0,
          trigger_threshold_down_pct: -3.0,
          min_stock_pct: 25.0,
          max_stock_pct: 75.0,
          max_trade_pct_of_position: 50.0,
          commission_rate: 0.1,
          market_hours_policy: 'market-open-only',
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load portfolio data');
    } finally {
      setLoading(false);
    }
  };

  const handlePositionSelect = (positionId: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('positionId', positionId);
    setSearchParams(newParams);
  };

  const handleTabChange = (tabId: TabId) => {
    navigate(`/positions?tab=${tabId}${selectedPositionId ? `&positionId=${selectedPositionId}` : ''}`);
  };

  if (!currentPortfolioId || !currentPortfolio) {
    return (
      <EmptyState
        icon={<Briefcase className="h-16 w-16 text-gray-400" />}
        title="No Portfolio Selected"
        description="Please select a portfolio from the sidebar to manage positions"
        action={{ label: 'Go to Portfolios', to: '/portfolios' }}
      />
    );
  }

  if (loading) {
    return <LoadingSpinner message="Loading workspace..." />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <button onClick={loadData} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  const selectedPosition = positions.find((p) => p.id === selectedPositionId);

  return (
    <div className="space-y-6">
      {/* Header with KPIs */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Position Workspace</h1>
            <p className="text-sm text-gray-500">{currentPortfolio.name}</p>
          </div>
          <div className="flex items-center gap-4">
            <TradingControls
              portfolioId={currentPortfolioId}
              workerStatus={workerStatus}
              onToggleWorker={toggleWorker}
              onRefresh={loadData}
              variant="compact"
            />
            <span className={`badge ${marketHoursService.getStatusColor(marketStatus)}`}>
              {marketHoursService.getStatusLabel(marketStatus)}
            </span>
          </div>
        </div>
        <KPICardGrid metrics={kpiMetrics} columns={4} variant="compact" />
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Cells Tab */}
          {activeTab === 'cells' && (
            <PositionsTab
              tenantId={tenantId}
              portfolioId={currentPortfolioId}
              effectiveConfig={effectiveConfig ? {
                trigger_threshold_up_pct: effectiveConfig.trigger_up,
                trigger_threshold_down_pct: effectiveConfig.trigger_down,
                min_stock_pct: effectiveConfig.min_stock_pct,
                max_stock_pct: effectiveConfig.max_stock_pct,
                max_trade_pct_of_position: effectiveConfig.max_trade_pct_of_position,
                commission_rate: effectiveConfig.commission_base_rate,
                market_hours_policy: effectiveConfig.market_hours_policy as 'market-open-only' | 'market-plus-after-hours',
                last_updated: effectiveConfig.last_updated,
                version: 1,
              } : null}
              positions={positions.map((pos) => ({
                id: pos.id,
                ticker: pos.asset || pos.ticker,
                asset: pos.asset || pos.ticker,
                qty: pos.qty,
                cash: pos.cash || 0,
                anchor_price: pos.anchor_price,
                avg_cost: pos.avg_cost,
                total_dividends_received: pos.total_dividends_received,
                last_price: pos.current_price,
                position_value: pos.position_value,
                weight_pct: pos.weight_percent,
                unrealized_pnl: pos.pnl,
                unrealized_pnl_pct: pos.pnl_percent,
              }))}
              onRefresh={loadData}
              onCopyTraceId={setCopiedTraceId}
              onPositionClick={(positionId) => navigate(`/portfolios/${currentPortfolioId}/positions/${positionId}`)}
            />
          )}

          {/* Trade Tab */}
          {activeTab === 'trade' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Position Selector Sidebar */}
                <div className="lg:col-span-1 bg-gray-50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Select Position</h3>
                  <PositionSelector
                    positions={positionOptions}
                    selectedId={selectedPositionId}
                    onSelect={handlePositionSelect}
                    variant="list"
                    showMetrics={true}
                  />
                </div>

                {/* Trading Cockpit */}
                <div className="lg:col-span-2 space-y-6">
                  {selectedPosition ? (
                    <>
                      {/* Position KPIs */}
                      <KPICardGrid
                        metrics={[
                          { id: 'qty', label: 'Quantity', value: selectedPosition.qty.toLocaleString() },
                          { id: 'cash', label: 'Cash', value: formatCurrency(selectedPosition.cash || 0) },
                          { id: 'stock_value', label: 'Stock Value', value: formatCurrency(selectedPosition.position_value || 0) },
                          { id: 'total', label: 'Total Value', value: formatCurrency((selectedPosition.position_value || 0) + (selectedPosition.cash || 0)) },
                        ]}
                        columns={4}
                        variant="compact"
                      />

                      {/* Decision Monitor */}
                      <DecisionMonitor
                        portfolioId={currentPortfolioId}
                        positionId={selectedPositionId!}
                        refreshInterval={10}
                      />

                      {/* Performance Chart */}
                      <div className="bg-white border border-gray-200 rounded-lg p-5">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm font-semibold text-gray-900">Performance</h3>
                          <div className="flex gap-1">
                            {(['1h', '4h', '1d'] as const).map((interval) => (
                              <button
                                key={interval}
                                onClick={() => setChartInterval(interval)}
                                className={`px-3 py-1 text-xs rounded ${
                                  chartInterval === interval
                                    ? 'bg-primary-500 text-white'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                              >
                                {interval}
                              </button>
                            ))}
                          </div>
                        </div>
                        <PerformanceChart
                          portfolioId={currentPortfolioId}
                          positionId={selectedPositionId!}
                          interval={chartInterval}
                          ticker={selectedPosition?.ticker || selectedPosition?.asset}
                          height={200}
                          chartType="area"
                        />
                      </div>

                      {/* Orders Panel */}
                      <OrdersPanel
                        portfolioId={currentPortfolioId}
                        positionId={selectedPositionId!}
                        limit={20}
                        refreshInterval={30}
                      />

                      {/* Decision History */}
                      <DecisionHistoryTable
                        portfolioId={currentPortfolioId}
                        positionId={selectedPositionId!}
                        limit={50}
                      />
                    </>
                  ) : (
                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                      <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">Select a position to view trading cockpit</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="flex items-center gap-4 mb-4">
                <PositionSelector
                  positions={[{ id: 'all', asset: 'All Positions', qty: 0, cash: 0, totalValue: totals.totalValue, stockPct: totals.stockPct }, ...positionOptions]}
                  selectedId={selectedPositionId || 'all'}
                  onSelect={(id) => handlePositionSelect(id === 'all' ? '' : id)}
                  variant="dropdown"
                  showMetrics={false}
                  className="w-64"
                />
              </div>

              <AnalyticsKPIs
                positions={(!selectedPositionId || selectedPositionId === 'all'
                  ? positions
                  : positions.filter((p) => p.id === selectedPositionId)
                ).map((p) => ({
                  ...p,
                  anchorPrice: p.anchor_price || 0,
                  currentPrice: p.current_price || 0,
                  marketValue: p.position_value || 0,
                  cashAmount: p.cash || 0,
                  ticker: p.asset || p.ticker || 'UNKNOWN',
                })) as any}
              />

              <AnalyticsCharts
                positions={(!selectedPositionId || selectedPositionId === 'all'
                  ? positions
                  : positions.filter((p) => p.id === selectedPositionId)
                ).map((p) => ({
                  ...p,
                  anchorPrice: p.anchor_price || 0,
                  currentPrice: p.current_price || 0,
                  marketValue: p.position_value || 0,
                  cashAmount: p.cash || 0,
                  ticker: p.asset || p.ticker || 'UNKNOWN',
                })) as any}
              />
            </div>
          )}

          {/* Cash Tab */}
          {activeTab === 'cash' && (
            <CashTab
              tenantId={tenantId}
              portfolioId={currentPortfolioId}
              cash={{
                cash_balance: totals.totalCash,
                reserved_cash: 0,
                available_cash: totals.totalCash,
              }}
              positions={positions.map((pos) => ({
                id: pos.id,
                ticker: pos.asset || pos.ticker,
                asset: pos.asset || pos.ticker,
                qty: pos.qty,
                cash: pos.cash || 0,
                anchor_price: pos.anchor_price,
                avg_cost: pos.avg_cost,
                last_price: pos.current_price,
              }))}
              onRefresh={loadData}
              onCopyTraceId={setCopiedTraceId}
              copiedTraceId={copiedTraceId}
            />
          )}

          {/* Config Tab */}
          {activeTab === 'config' && effectiveConfig && (
            <StrategyConfigTab
              tenantId={tenantId}
              portfolioId={currentPortfolioId}
              positionId={selectedPositionId && selectedPositionId !== 'all' ? selectedPositionId : undefined}
              positionName={selectedPositionId && selectedPositionId !== 'all'
                ? positions.find((p) => p.id === selectedPositionId)?.asset
                : undefined}
              effectiveConfig={{
                trigger_threshold_up_pct: effectiveConfig.trigger_up,
                trigger_threshold_down_pct: effectiveConfig.trigger_down,
                min_stock_pct: effectiveConfig.min_stock_pct,
                max_stock_pct: effectiveConfig.max_stock_pct,
                max_trade_pct_of_position: effectiveConfig.max_trade_pct_of_position,
                commission_rate: effectiveConfig.commission_base_rate,
                market_hours_policy: effectiveConfig.market_hours_policy as 'market-open-only' | 'market-plus-after-hours',
                last_updated: effectiveConfig.last_updated,
                version: 1,
              }}
              editableConfig={editableConfig}
              marketStatus={marketStatus}
              onConfigChange={(config) => setEditableConfig(config)}
              onSave={async (config) => {
                try {
                  if (!selectedPositionId || selectedPositionId === 'all') {
                    await portfolioScopedApi.updateConfig(tenantId, currentPortfolioId, config);
                    toast.success('Config saved successfully');
                    await loadData();
                  }
                } catch (err: any) {
                  toast.error(`Failed to save config: ${err.message}`);
                  throw err;
                }
              }}
              onCopyTraceId={setCopiedTraceId}
              copiedTraceId={copiedTraceId}
            />
          )}
        </div>
      </div>
    </div>
  );
}
