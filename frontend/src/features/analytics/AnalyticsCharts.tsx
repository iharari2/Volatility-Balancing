import { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Position } from '../../contexts/PortfolioContext';

interface AnalyticsChartsProps {
  positions: Position[];
  analyticsData?: any;
}

export default function AnalyticsCharts({ positions, analyticsData }: AnalyticsChartsProps) {
  const isSinglePosition = positions.length === 1;
  const mainLabel = isSinglePosition
    ? `${positions[0].ticker || 'Position'} Value`
    : 'Portfolio Value';

  // Use real time series data from backend - no mock data fallback
  const portfolioValueData = useMemo(() => {
    if (analyticsData?.time_series?.length > 0) {
      return analyticsData.time_series.map((point: any) => ({
        date: point.date,
        value: point.value,
      }));
    }
    // Return empty array if no data - chart will be empty
    return [];
  }, [analyticsData]);

  const allocationData = useMemo(() => {
    if (analyticsData?.time_series?.length > 0) {
      return analyticsData.time_series.map((point: any) => ({
        date: point.date,
        stock: point.stock_pct,
        cash: point.cash_pct,
      }));
    }
    // Return empty array if no data - chart will be empty
    return [];
  }, [analyticsData]);

  const buyHoldData = useMemo(() => {
    if (!analyticsData?.time_series?.length || portfolioValueData.length === 0) {
      return [];
    }

    // Calculate buy & hold from initial stock value and price changes
    // For single position, we can track stock price changes
    // For portfolio, we'd need individual stock prices which we don't have in time series
    // So we'll show portfolio value vs a simple buy & hold of the initial stock allocation
    const timeSeries = analyticsData.time_series;
    const initialPoint = timeSeries[0];
    const initialStockValue = initialPoint.stock || 0;
    const initialCash = initialPoint.cash || 0;
    const initialValue = initialPoint.value || 0;

    if (initialValue === 0) return [];

    // Calculate buy & hold: assume we hold initial stock allocation and it grows with market
    // Since we don't have individual stock prices, we'll use the stock value ratio
    return portfolioValueData.map((point: { date: string; value: number }, i: number) => {
      const currentPoint = timeSeries[i];
      if (!currentPoint) return { date: point.date, portfolio: point.value, buyHold: initialValue };

      // Buy & hold: initial stock value grows proportionally to portfolio stock value
      // This is a simplified approximation
      const stockGrowthRatio =
        initialStockValue > 0 && currentPoint.stock > 0
          ? currentPoint.stock / initialStockValue
          : 1.0;
      const buyHoldValue = initialStockValue * stockGrowthRatio + initialCash;

      return {
        date: point.date,
        portfolio: point.value,
        buyHold: buyHoldValue,
      };
    });
  }, [portfolioValueData, analyticsData, isSinglePosition]);

  const rollingReturnsData = useMemo(() => {
    if (!analyticsData?.time_series?.length || portfolioValueData.length < 2) {
      return [];
    }

    // Calculate weekly returns from time series
    // Group by week and calculate return for each week
    const weeklyReturns: Array<{ date: string; return: number }> = [];
    const timeSeries = analyticsData.time_series;

    // Group data points by week
    const weeklyData: Record<string, { startValue: number; endValue: number; date: string }> = {};

    timeSeries.forEach((point: any, index: number) => {
      const date = new Date(point.date);
      const weekKey = `${date.getFullYear()}-W${Math.ceil(
        (date.getTime() - new Date(date.getFullYear(), 0, 1).getTime()) / (7 * 24 * 60 * 60 * 1000),
      )}`;

      if (!weeklyData[weekKey]) {
        weeklyData[weekKey] = {
          startValue: point.value,
          endValue: point.value,
          date: point.date,
        };
      } else {
        weeklyData[weekKey].endValue = point.value;
        weeklyData[weekKey].date = point.date; // Use last date of the week
      }
    });

    // Calculate returns for each week
    Object.values(weeklyData).forEach((week) => {
      if (week.startValue > 0) {
        const weeklyReturn = ((week.endValue - week.startValue) / week.startValue) * 100;
        weeklyReturns.push({
          date: week.date,
          return: weeklyReturn,
        });
      }
    });

    return weeklyReturns.sort((a, b) => a.date.localeCompare(b.date));
  }, [analyticsData, portfolioValueData]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Portfolio Value Over Time */}
      <div className="card">
        <h3 className="text-sm font-bold text-gray-900 mb-6 uppercase tracking-wider">
          {mainLabel} Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={portfolioValueData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#2563eb"
              strokeWidth={3}
              dot={false}
              name={isSinglePosition ? 'Total Value' : 'Portfolio Value'}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Stock Allocation Over Time */}
      <div className="card">
        <h3 className="text-sm font-bold text-gray-900 mb-6 uppercase tracking-wider">
          {isSinglePosition ? 'Asset Allocation' : 'Portfolio Allocation'} Trend
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={allocationData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            <Area
              type="monotone"
              dataKey="stock"
              stackId="1"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.6}
              name="Stock %"
            />
            <Area
              type="monotone"
              dataKey="cash"
              stackId="1"
              stroke="#2563eb"
              fill="#2563eb"
              fillOpacity={0.6}
              name="Cash %"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Buy & Hold Comparison */}
      <div className="card">
        <h3 className="text-sm font-bold text-gray-900 mb-6 uppercase tracking-wider">
          {isSinglePosition ? 'Stock' : 'Benchmark'} Comparison
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={buyHoldData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            <Line
              type="monotone"
              dataKey="portfolio"
              stroke="#2563eb"
              strokeWidth={3}
              dot={false}
              name={isSinglePosition ? 'Managed' : 'Portfolio'}
            />
            <Line
              type="monotone"
              dataKey="buyHold"
              stroke="#9ca3af"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Buy & Hold"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Rolling Returns */}
      <div className="card">
        <h3 className="text-sm font-bold text-gray-900 mb-6 uppercase tracking-wider">
          Performance Volatility
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={rollingReturnsData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            <Line
              type="monotone"
              dataKey="return"
              stroke="#8b5cf6"
              strokeWidth={3}
              dot={false}
              name="Weekly Return %"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
