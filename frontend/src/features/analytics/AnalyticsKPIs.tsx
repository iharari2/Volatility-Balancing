import { useMemo } from 'react';
import { Position } from '../../contexts/PortfolioContext';

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

  const kpiCards = [
    {
      label: 'Return',
      value: `${metrics.return >= 0 ? '+' : ''}${metrics.return.toFixed(2)}%`,
      color: metrics.return >= 0 ? 'text-green-600' : 'text-red-600',
    },
    { label: 'Volatility', value: `${metrics.volatility.toFixed(2)}%`, color: 'text-gray-900' },
    { label: 'Max Drawdown', value: `${metrics.maxDrawdown.toFixed(1)}%`, color: 'text-red-600' },
    { label: 'Sharpe-like', value: metrics.sharpeLike.toFixed(2), color: 'text-gray-900' },
    {
      label: 'Commission Total',
      value: `$${metrics.commissionTotal.toFixed(2)}`,
      color: 'text-gray-900',
    },
    {
      label: 'Dividend Total',
      value: `$${metrics.dividendTotal.toFixed(2)}`,
      color: 'text-green-600',
    },
  ];

  // Check if we have real analytics data
  const hasRealData = analyticsData?.time_series?.length > 0;

  return (
    <div className="space-y-2">
      {!hasRealData && (
        <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-center gap-2">
          <svg className="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>Limited data available. Run simulations or execute trades to see detailed analytics.</span>
        </div>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {kpiCards.map((kpi) => (
          <div key={kpi.label} className="card p-4 flex flex-col justify-between">
            <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              {kpi.label}
            </dt>
            <dd className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</dd>
          </div>
        ))}
      </div>
    </div>
  );
}
