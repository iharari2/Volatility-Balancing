import React, { ReactNode } from 'react';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  PieChart,
  Activity,
  Target,
  Percent,
  BarChart3,
  Wallet,
  LucideIcon,
} from 'lucide-react';

export interface KPIMetric {
  id: string;
  label: string;
  value: string | number;
  subValue?: string;
  icon?: LucideIcon | ReactNode;
  iconBgColor?: string;
  iconColor?: string;
  valueColor?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

interface KPICardGridProps {
  metrics: KPIMetric[];
  columns?: 2 | 3 | 4 | 6;
  variant?: 'portfolio' | 'position' | 'compact';
  className?: string;
}

const defaultIconMap: Record<string, { icon: LucideIcon; bgColor: string; color: string }> = {
  total_value: { icon: DollarSign, bgColor: 'bg-primary-100', color: 'text-primary-600' },
  cash: { icon: Wallet, bgColor: 'bg-success-100', color: 'text-success-600' },
  stock_value: { icon: BarChart3, bgColor: 'bg-blue-100', color: 'text-blue-600' },
  allocation: { icon: PieChart, bgColor: 'bg-warning-100', color: 'text-warning-600' },
  pnl: { icon: TrendingUp, bgColor: 'bg-indigo-100', color: 'text-indigo-600' },
  return: { icon: Percent, bgColor: 'bg-emerald-100', color: 'text-emerald-600' },
  volatility: { icon: Activity, bgColor: 'bg-orange-100', color: 'text-orange-600' },
  drawdown: { icon: TrendingDown, bgColor: 'bg-red-100', color: 'text-red-600' },
  sharpe: { icon: Target, bgColor: 'bg-purple-100', color: 'text-purple-600' },
};

function getIconConfig(metricId: string): { icon: LucideIcon; bgColor: string; color: string } {
  const key = Object.keys(defaultIconMap).find((k) => metricId.toLowerCase().includes(k));
  return key ? defaultIconMap[key] : { icon: Activity, bgColor: 'bg-gray-100', color: 'text-gray-600' };
}

export default function KPICardGrid({
  metrics,
  columns = 4,
  variant = 'portfolio',
  className = '',
}: KPICardGridProps) {
  const gridColsMap = {
    2: 'sm:grid-cols-2',
    3: 'sm:grid-cols-2 lg:grid-cols-3',
    4: 'sm:grid-cols-2 lg:grid-cols-4',
    6: 'sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6',
  };

  if (variant === 'compact') {
    return (
      <div className={`grid grid-cols-1 gap-4 ${gridColsMap[columns]} ${className}`}>
        {metrics.map((metric) => (
          <div key={metric.id} className="card p-4 flex flex-col justify-between">
            <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              {metric.label}
            </dt>
            <dd className={`text-xl font-bold ${metric.valueColor || 'text-gray-900'}`}>
              {metric.value}
              {metric.subValue && (
                <span className="text-xs font-normal text-gray-500 ml-2">{metric.subValue}</span>
              )}
            </dd>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 gap-5 ${gridColsMap[columns]} ${className}`}>
      {metrics.map((metric) => {
        const iconConfig = getIconConfig(metric.id);
        const IconComponent = metric.icon
          ? typeof metric.icon === 'function'
            ? metric.icon
            : null
          : iconConfig.icon;
        const bgColor = metric.iconBgColor || iconConfig.bgColor;
        const iconColor = metric.iconColor || iconConfig.color;

        return (
          <div key={metric.id} className="card">
            <div className="flex items-center">
              <div className={`flex-shrink-0 ${bgColor} p-3 rounded-lg`}>
                {IconComponent ? (
                  <IconComponent className={`h-6 w-6 ${iconColor}`} />
                ) : typeof metric.icon === 'object' ? (
                  metric.icon as React.ReactNode
                ) : null}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate uppercase tracking-wider">
                    {metric.label}
                  </dt>
                  <dd className={`text-2xl font-bold ${metric.valueColor || 'text-gray-900'}`}>
                    <div className="flex flex-col">
                      <span className="flex items-center gap-2">
                        {metric.value}
                        {metric.trend && metric.trendValue && (
                          <span
                            className={`text-sm font-medium flex items-center ${
                              metric.trend === 'up'
                                ? 'text-success-600'
                                : metric.trend === 'down'
                                ? 'text-danger-600'
                                : 'text-gray-500'
                            }`}
                          >
                            {metric.trend === 'up' && <TrendingUp className="h-4 w-4 mr-1" />}
                            {metric.trend === 'down' && <TrendingDown className="h-4 w-4 mr-1" />}
                            {metric.trendValue}
                          </span>
                        )}
                      </span>
                      {metric.subValue && (
                        <span className="text-xs text-gray-500 font-normal">{metric.subValue}</span>
                      )}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Utility function to format currency values
export function formatCurrency(value: number, options?: { compact?: boolean }): string {
  if (options?.compact && Math.abs(value) >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (options?.compact && Math.abs(value) >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// Utility function to format percentage values
export function formatPercent(value: number, options?: { showSign?: boolean }): string {
  const sign = options?.showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

// Utility function to get value color based on positive/negative
export function getValueColor(value: number): string {
  if (value > 0) return 'text-success-600';
  if (value < 0) return 'text-danger-600';
  return 'text-gray-900';
}
