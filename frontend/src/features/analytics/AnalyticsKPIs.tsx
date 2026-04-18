import { useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { Position } from '../../contexts/PortfolioContext';
import MetricTooltip from '../../components/MetricTooltip';
import MetricsMethodologyModal from '../../components/MetricsMethodologyModal';

interface AnalyticsKPIsProps {
  positions: Position[];
  analyticsData?: any;
}

export default function AnalyticsKPIs({ positions, analyticsData }: AnalyticsKPIsProps) {
  const metrics = useMemo(() => {
    // Use backend analytics data - all metrics come from real data
    if (analyticsData?.kpis) {
      return {
        return: analyticsData.kpis.pnl_pct || 0,
        volatility: analyticsData.kpis.volatility || 0,
        maxDrawdown: analyticsData.kpis.max_drawdown || 0,
        sharpeLike: analyticsData.kpis.sharpe_like || 0,
        commissionTotal: analyticsData.kpis.commission_total || 0,
        dividendTotal: analyticsData.kpis.dividend_total || 0,
      };
    }

    // If no backend data, return zeros (no mock data)
    return {
      return: 0,
      volatility: 0,
      maxDrawdown: 0,
      sharpeLike: 0,
      commissionTotal: 0,
      dividendTotal: 0,
    };
  }, [analyticsData]);

  const zoneTime = analyticsData?.kpis?.zone_time;
  const tradeStats = analyticsData?.kpis?.trade_stats;

  const kpiCards = [
    {
      label: 'Return',
      tooltip: 'Total percentage gain or loss on the portfolio over the selected period.',
      value: `${metrics.return >= 0 ? '+' : ''}${metrics.return.toFixed(2)}%`,
      color: metrics.return >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      label: 'Volatility',
      tooltip: 'Annualized standard deviation of daily returns. Higher values mean larger price swings.',
      value: `${metrics.volatility.toFixed(2)}%`,
      color: 'text-gray-900',
    },
    {
      label: 'Max Drawdown',
      tooltip: 'Largest peak-to-trough decline in portfolio value. Measures worst-case loss before recovery.',
      value: `${metrics.maxDrawdown.toFixed(1)}%`,
      color: 'text-red-600',
    },
    {
      label: 'Sharpe-like',
      tooltip: 'Risk-adjusted return: portfolio return divided by its volatility. Higher is better.',
      value: metrics.sharpeLike.toFixed(2),
      color: 'text-gray-900',
    },
    {
      label: 'Commission Total',
      tooltip: 'Total brokerage commissions paid across all trades in the selected period.',
      value: `$${metrics.commissionTotal.toFixed(2)}`,
      color: 'text-gray-900',
    },
    {
      label: 'Dividend Total',
      tooltip: 'Total net dividend income received during the selected period, after withholding tax.',
      value: `$${metrics.dividendTotal.toFixed(2)}`,
      color: 'text-green-600',
    },
    {
      label: 'In Target Zone',
      tooltip: 'Percentage of trading days the stock allocation stayed within the guardrail target band. Higher is better.',
      value: zoneTime ? `${zoneTime.in_pct.toFixed(0)}%` : '—',
      color: zoneTime && zoneTime.in_pct >= 70 ? 'text-green-600' : zoneTime ? 'text-amber-600' : 'text-gray-400',
    },
    {
      label: 'Trades',
      tooltip: 'Total number of guardrail trades executed. Shows buys and sells separately.',
      value: tradeStats ? `${tradeStats.total_trades}` : '—',
      subValue: tradeStats ? `${tradeStats.buy_count}B / ${tradeStats.sell_count}S` : undefined,
      color: 'text-gray-900',
    },
  ];

  const [showMethodology, setShowMethodology] = useState(false);

  // Check if we have real analytics data
  const hasRealData = analyticsData?.time_series?.length > 0;

  return (
    <div className="space-y-2">
      {showMethodology && <MetricsMethodologyModal onClose={() => setShowMethodology(false)} />}
      {!hasRealData && (
        <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-center gap-2">
          <svg className="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>Limited data available. Run simulations or execute trades to see detailed analytics.</span>
        </div>
      )}
      <div className="flex justify-end">
        <button
          onClick={() => setShowMethodology(true)}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          <Info className="h-3.5 w-3.5" />
          How are these calculated?
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-8">
        {kpiCards.map((kpi) => (
          <div key={kpi.label} className="card p-4 flex flex-col justify-between">
            <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center">
              {kpi.label}
              <MetricTooltip text={kpi.tooltip} />
            </dt>
            <dd className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</dd>
            {'subValue' in kpi && kpi.subValue && (
              <span className="text-[10px] text-gray-400 mt-0.5">{kpi.subValue}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
