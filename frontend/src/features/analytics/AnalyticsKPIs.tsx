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

  return (
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
  );
}
