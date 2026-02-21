import { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { marketApi } from '../../lib/api';

interface PerformanceChartProps {
  portfolioId: string;
  positionId: string;
  interval: string;
  ticker?: string;
  height?: number;
  chartType?: 'area' | 'line';
}

function getDateRange(interval: string): { startDate: string; endDate: string } {
  const now = new Date();
  const end = now.toISOString();
  let start: Date;

  switch (interval) {
    case '1D':
      start = new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000);
      break;
    case '1W':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case '1M':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
    case '3M':
      start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
      break;
    case '6M':
      start = new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000);
      break;
    case '1Y':
      start = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
      break;
    default:
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  }

  return { startDate: start.toISOString(), endDate: end };
}

export default function PerformanceChart({
  portfolioId,
  positionId,
  interval,
  ticker,
  height = 200,
  chartType = 'area',
}: PerformanceChartProps) {
  const [data, setData] = useState<Array<{ date: string; value: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setData([]);
      return;
    }

    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const { startDate, endDate } = getDateRange(interval);
        const resp = await marketApi.getHistoricalData(ticker!, startDate, endDate);

        if (cancelled) return;

        const mapped = resp.price_data.map((p) => ({
          date: new Date(p.timestamp).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
          }),
          value: p.price,
        }));

        setData(mapped);
      } catch (err) {
        if (!cancelled) {
          setError('Failed to load price data');
          setData([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [ticker, interval, portfolioId, positionId]);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height }}
      >
        <p className="text-xs text-gray-500">Loading chart...</p>
      </div>
    );
  }

  if (error || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height }}
      >
        <div className="text-center text-gray-500">
          <svg
            className="h-8 w-8 mx-auto mb-2 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
            />
          </svg>
          <p className="text-xs">{error || 'Performance chart data not available'}</p>
        </div>
      </div>
    );
  }

  const Chart = chartType === 'area' ? AreaChart : LineChart;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: '#9ca3af' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#9ca3af' }}
          axisLine={false}
          tickLine={false}
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{
            borderRadius: '8px',
            border: 'none',
            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
          }}
          formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
        />
        {chartType === 'area' ? (
          <Area
            type="monotone"
            dataKey="value"
            stroke="#2563eb"
            fill="#2563eb"
            fillOpacity={0.2}
            strokeWidth={2}
          />
        ) : (
          <Line
            type="monotone"
            dataKey="value"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />
        )}
      </Chart>
    </ResponsiveContainer>
  );
}
