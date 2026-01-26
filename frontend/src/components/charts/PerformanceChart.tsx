/**
 * PerformanceChart - Displays position value over time
 *
 * Uses Recharts to show total value, stock value, and cash over time.
 */

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { getPerformanceSeries, PerformancePoint } from '../../api/positionHistory';

interface PerformanceChartProps {
  portfolioId: string;
  positionId: string;
  interval?: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d';
  height?: number;
  showLegend?: boolean;
  chartType?: 'line' | 'area';
}

const formatCurrency = (value: number) => {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
};

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  } else if (diffDays < 7) {
    return date.toLocaleDateString(undefined, { weekday: 'short', hour: '2-digit', minute: '2-digit' });
  } else {
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }
};

interface ChartDataPoint {
  timestamp: string;
  displayTime: string;
  totalValue: number;
  stockValue: number;
  cash: number;
  allocationPct: number;
}

export default function PerformanceChart({
  portfolioId,
  positionId,
  interval = '1h',
  height = 300,
  showLegend = true,
  chartType = 'area',
}: PerformanceChartProps) {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      if (!portfolioId || !positionId) {
        setData([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response = await getPerformanceSeries(portfolioId, positionId, {
          interval,
          mode: 'LIVE',
        });

        const chartData: ChartDataPoint[] = response.points.map((point: PerformancePoint) => ({
          timestamp: point.timestamp,
          displayTime: formatTime(point.timestamp),
          totalValue: point.total_value,
          stockValue: point.stock_value,
          cash: point.cash,
          allocationPct: point.allocation_pct,
        }));

        setData(chartData);
      } catch (err) {
        console.error('Error loading performance data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [portfolioId, positionId, interval]);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <div className="text-gray-500 text-sm">Loading chart...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center justify-center bg-red-50 rounded-lg"
        style={{ height }}
      >
        <div className="text-red-500 text-sm">{error}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <div className="text-gray-500 text-sm">No performance data available yet</div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const ChartComponent = chartType === 'area' ? AreaChart : LineChart;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ChartComponent data={data} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorStock" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="displayTime"
          tick={{ fontSize: 11, fill: '#6b7280' }}
          tickLine={{ stroke: '#d1d5db' }}
        />
        <YAxis
          tickFormatter={formatCurrency}
          tick={{ fontSize: 11, fill: '#6b7280' }}
          tickLine={{ stroke: '#d1d5db' }}
          width={80}
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && (
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
        )}
        {chartType === 'area' ? (
          <>
            <Area
              type="monotone"
              dataKey="totalValue"
              name="Total Value"
              stroke="#3b82f6"
              fill="url(#colorTotal)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="stockValue"
              name="Stock Value"
              stroke="#10b981"
              fill="url(#colorStock)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="cash"
              name="Cash"
              stroke="#f59e0b"
              fill="url(#colorCash)"
              strokeWidth={2}
            />
          </>
        ) : (
          <>
            <Line
              type="monotone"
              dataKey="totalValue"
              name="Total Value"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="stockValue"
              name="Stock Value"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="cash"
              name="Cash"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
            />
          </>
        )}
      </ChartComponent>
    </ResponsiveContainer>
  );
}
