import { useState, useMemo } from 'react';
import { usePositions, usePositionEvents } from '../hooks/usePositions';
import { useHistoricalData } from '../hooks/useMarketData';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ComposedChart,
  Legend,
  Scatter,
} from 'recharts';
import {
  TrendingUp,
  DollarSign,
  Activity,
  Target,
  BarChart3,
  PieChart as PieChartIcon,
} from 'lucide-react';

export default function Analytics() {
  const { data: positions = [] } = usePositions();
  const [selectedPositionId, setSelectedPositionId] = useState<string>('');

  const selectedPosition = positions.find((p) => p.id === selectedPositionId);
  const { data: events } = usePositionEvents(selectedPositionId);

  // Filter positions based on selection
  const filteredPositions = selectedPositionId
    ? positions.filter((p) => p.id === selectedPositionId)
    : positions;

  // Calculate analytics data for filtered positions
  const totalValue = filteredPositions.reduce((sum, pos) => {
    const value = pos.qty * (pos.anchor_price || 0) + pos.cash;
    return sum + value;
  }, 0);

  const totalCash = filteredPositions.reduce((sum, pos) => sum + pos.cash, 0);
  const totalShares = filteredPositions.reduce((sum, pos) => sum + pos.qty, 0);
  const activePositions = filteredPositions.filter((pos) => pos.anchor_price);

  // Event analytics
  const eventCounts =
    events?.events.reduce((acc, event) => {
      acc[event.type] = (acc[event.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>) || {};

  const eventData = Object.entries(eventCounts).map(([type, count]) => ({
    type: type.replace(/_/g, ' ').toUpperCase(),
    count,
  }));

  // Position performance data
  const positionData = filteredPositions.map((pos) => ({
    ticker: pos.ticker,
    value: pos.qty * (pos.anchor_price || 0) + pos.cash,
    shares: pos.qty,
    cash: pos.cash,
    hasAnchor: !!pos.anchor_price,
  }));

  // Get historical data for the selected position (if any)
  const earliestPositionDate = useMemo(() => {
    if (filteredPositions.length === 0) return null;

    // Find the earliest position creation date
    const dates = filteredPositions
      .map((pos) => (pos.created_at ? new Date(pos.created_at) : null))
      .filter(Boolean)
      .sort((a, b) => a!.getTime() - b!.getTime());

    return dates.length > 0 ? dates[0] : null;
  }, [filteredPositions]);

  const startDate = earliestPositionDate
    ? earliestPositionDate.toISOString().split('T')[0]
    : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]; // 30 days ago as fallback

  const endDate = new Date().toISOString().split('T')[0];

  // Get historical data for the first position's ticker (if any)
  const firstPosition = filteredPositions[0];
  const { data: historicalData } = useHistoricalData(
    firstPosition?.ticker || 'AAPL',
    startDate,
    endDate,
    false, // Include after hours
  );

  // Generate timeline data using real historical data
  const timelineData = useMemo(() => {
    if (!historicalData?.price_data || historicalData.price_data.length === 0) {
      // Fallback to current values if no historical data
      return [
        {
          date: new Date().toISOString().split('T')[0],
          portfolioValue: Math.round(totalValue),
          assetValue: Math.round(totalValue - totalCash),
          cashValue: Math.round(totalCash),
          stockValue: Math.round(totalValue - totalCash),
          cashPercentage: Math.round((totalCash / totalValue) * 100 * 10) / 10,
          stockPercentage: Math.round(((totalValue - totalCash) / totalValue) * 100 * 10) / 10,
          day: 1,
        },
      ];
    }

    const data = [];
    const priceData = historicalData.price_data;

    // Group price data by date
    const dailyPrices = priceData.reduce((acc, point) => {
      const date = point.timestamp.split('T')[0];
      if (!acc[date]) {
        acc[date] = [];
      }
      acc[date].push(point);
      return acc;
    }, {} as Record<string, typeof priceData>);

    // Calculate portfolio value for each day
    let dayCount = 0;
    for (const [date, dayPrices] of Object.entries(dailyPrices)) {
      dayCount++;

      // Use the last price of the day
      const lastPrice = dayPrices[dayPrices.length - 1].price;

      // Calculate asset value based on current positions and historical price
      const assetValue = filteredPositions.reduce((sum, pos) => {
        if (pos.anchor_price) {
          // Calculate price change from anchor to historical price
          const priceChange = (lastPrice - pos.anchor_price) / pos.anchor_price;
          const currentValue = pos.qty * pos.anchor_price * (1 + priceChange);
          return sum + currentValue;
        }
        return sum;
      }, 0);

      // Portfolio value = asset value + cash
      const portfolioValue = assetValue + totalCash;

      // Calculate allocation percentages
      const cashPercentage = (totalCash / portfolioValue) * 100;
      const stockPercentage = (assetValue / portfolioValue) * 100;

      data.push({
        date,
        portfolioValue: Math.round(portfolioValue),
        assetValue: Math.round(assetValue),
        cashValue: Math.round(totalCash),
        stockValue: Math.round(assetValue),
        cashPercentage: Math.round(cashPercentage * 10) / 10,
        stockPercentage: Math.round(stockPercentage * 10) / 10,
        day: dayCount,
        price: lastPrice, // Add price for trade triggers chart
      });
    }

    return data;
  }, [historicalData, totalValue, totalCash, filteredPositions]);

  // Trade triggers data for overlay chart
  const tradeTriggersData = useMemo(() => {
    if (!events?.events || !timelineData.length) {
      console.log('No events or timeline data:', {
        events: events?.events?.length,
        timelineData: timelineData.length,
      });
      return [];
    }

    // Filter for trade-related events
    const tradeEvents = events.events.filter(
      (event) =>
        event.type === 'order_filled' ||
        event.type === 'order_submitted' ||
        event.type === 'threshold_crossed',
    );

    console.log('Trade events found:', tradeEvents.length);

    // Map events to timeline data points
    const result = tradeEvents.map((event) => {
      const eventDate = new Date(event.timestamp).toISOString().split('T')[0];
      const timelinePoint = timelineData.find((point) => point.date === eventDate);

      return {
        x: timelinePoint?.day || 0, // Day number for x-axis
        y: timelinePoint?.price || 0, // Price for y-axis
        date: eventDate,
        timestamp: event.timestamp,
        type: event.type,
        price: timelinePoint?.price || 0,
        portfolioValue: timelinePoint?.portfolioValue || 0,
        side: event.data?.side || 'unknown',
        qty: event.data?.qty || 0,
        reasoning: event.data?.reasoning || '',
      };
    });

    console.log('Trade triggers data:', result);
    return result;
  }, [events, timelineData]);

  // Portfolio performance comparison data
  const performanceData = useMemo(() => {
    return timelineData.map((point, index) => {
      const initialValue = timelineData[0].portfolioValue;
      const portfolioReturn = ((point.portfolioValue - initialValue) / initialValue) * 100;
      const assetReturn =
        ((point.assetValue - timelineData[0].assetValue) / timelineData[0].assetValue) * 100;

      return {
        ...point,
        portfolioReturn: Math.round(portfolioReturn * 100) / 100,
        assetReturn: Math.round(assetReturn * 100) / 100,
        alpha: Math.round((portfolioReturn - assetReturn) * 100) / 100,
      };
    });
  }, [timelineData]);

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600">Performance metrics and trading insights</p>
      </div>

      {/* Simulation Analytics Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <BarChart3 className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Simulation Analytics Available</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                For detailed simulation performance analysis, risk metrics, and strategy comparison,
                run a simulation and check the Analytics tab in the Simulation page.
              </p>
              <div className="mt-2">
                <a href="/simulation" className="text-blue-600 hover:text-blue-800 font-medium">
                  Go to Simulation Analytics →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Position Selector */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Analytics</h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="label">Select position for detailed analytics</label>
            <select
              value={selectedPositionId}
              onChange={(e) => setSelectedPositionId(e.target.value)}
              className="input"
            >
              <option value="">All Positions</option>
              {positions.map((position) => (
                <option key={position.id} value={position.id}>
                  {position.ticker} -{' '}
                  {position.anchor_price ? `$${position.anchor_price.toFixed(2)}` : 'No anchor'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Value</p>
              <p className="text-2xl font-semibold text-gray-900">${totalValue.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DollarSign className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Cash</p>
              <p className="text-2xl font-semibold text-gray-900">${totalCash.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Shares</p>
              <p className="text-2xl font-semibold text-gray-900">{totalShares.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Target className="h-8 w-8 text-danger-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Positions</p>
              <p className="text-2xl font-semibold text-gray-900">{activePositions.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position Values */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Values</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={positionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ticker" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Value']} />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Event Distribution */}
        {selectedPositionId && eventData.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Distribution</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={eventData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ type, count }) => `${type}: ${count}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {eventData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Timeline Charts */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-gray-900 flex items-center">
          <BarChart3 className="w-6 h-6 mr-2" />
          Portfolio Analysis
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Portfolio Value Over Time */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Portfolio Composition & Asset Performance
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Stack shows cash + asset value over time. Line shows asset performance as reference.
            </p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" tickFormatter={(value) => `Day ${value}`} />
                  <YAxis
                    yAxisId="left"
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip
                    formatter={(value, name) => {
                      if (
                        name === 'cashValue' ||
                        name === 'stockValue' ||
                        name === 'portfolioValue'
                      ) {
                        return [
                          `$${value.toLocaleString()}`,
                          name === 'cashValue'
                            ? 'Cash Value'
                            : name === 'stockValue'
                            ? 'Asset Value'
                            : 'Total Portfolio',
                        ];
                      }
                      return [`${value}%`, 'Asset Performance'];
                    }}
                    labelFormatter={(label) => `Day ${label}`}
                  />
                  <Legend />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="cashValue"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.6}
                    name="Cash Value"
                  />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="stockValue"
                    stackId="1"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.6}
                    name="Asset Value"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="assetReturn"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Asset Performance %"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Portfolio vs Asset Performance */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Portfolio vs Asset Performance
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" tickFormatter={(value) => `Day ${value}`} />
                  <YAxis tickFormatter={(value) => `${value}%`} />
                  <Tooltip
                    formatter={(value, name) => [
                      `${value}%`,
                      name === 'portfolioReturn'
                        ? 'Portfolio Return'
                        : name === 'assetReturn'
                        ? 'Asset Return'
                        : 'Alpha',
                    ]}
                    labelFormatter={(label) => `Day ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="portfolioReturn"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Portfolio Return"
                  />
                  <Line
                    type="monotone"
                    dataKey="assetReturn"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Asset Return"
                  />
                  <Line
                    type="monotone"
                    dataKey="alpha"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Alpha (Outperformance)"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Cash vs Stock Allocation Over Time */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Cash vs Stock Allocation Over Time
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tickFormatter={(value) => `Day ${value}`} />
                <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === 'cashValue' || name === 'stockValue') {
                      return [
                        `$${value.toLocaleString()}`,
                        name === 'cashValue' ? 'Cash Value' : 'Stock Value',
                      ];
                    }
                    return [`${value}%`, name === 'cashPercentage' ? 'Cash %' : 'Stock %'];
                  }}
                  labelFormatter={(label) => `Day ${label}`}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="cashValue" fill="#10b981" name="Cash Value" />
                <Bar yAxisId="left" dataKey="stockValue" fill="#3b82f6" name="Stock Value" />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cashPercentage"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Cash %"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="stockPercentage"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  name="Stock %"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Trade Triggers Over Asset Price */}
      {timelineData.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Trade Triggers Over Asset Price
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tickFormatter={(value) => `Day ${value}`} />
                <YAxis yAxisId="left" tickFormatter={(value) => `$${value.toFixed(2)}`} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === 'price') {
                      return [`$${value.toFixed(2)}`, 'Asset Price'];
                    }
                    return [`$${value.toLocaleString()}`, 'Portfolio Value'];
                  }}
                  labelFormatter={(label) => `Day ${label}`}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Asset Price"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="portfolioValue"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Portfolio Value"
                />
                {/* Trade trigger markers */}
                <Scatter
                  yAxisId="left"
                  data={tradeTriggersData}
                  fill={(entry) => (entry.side === 'buy' ? '#ef4444' : '#f59e0b')}
                  name="Trade Triggers"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            {tradeTriggersData.length > 0 ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span>Buy Triggers</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span>Sell Triggers</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span>Asset Price</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span>Portfolio Value</span>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500">
                No trade triggers found. Trade markers will appear here when trades are executed.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Position Breakdown */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ticker
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Shares
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cash
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Anchor Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredPositions.map((position) => {
                const value = position.qty * (position.anchor_price || 0) + position.cash;
                return (
                  <tr key={position.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {position.ticker}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.qty.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${position.cash.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.anchor_price ? `$${position.anchor_price.toFixed(2)}` : 'Not set'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${value.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`badge ${
                          position.anchor_price ? 'badge-success' : 'badge-warning'
                        }`}
                      >
                        {position.anchor_price ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trading Insights */}
      {selectedPositionId && events?.events && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Trading Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Total Events</h4>
              <p className="text-3xl font-bold text-primary-600">{events.events.length}</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Order Events</h4>
              <p className="text-3xl font-bold text-success-600">
                {events.events.filter((e) => e.type.includes('order')).length}
              </p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Trigger Events</h4>
              <p className="text-3xl font-bold text-warning-600">
                {events.events.filter((e) => e.type.includes('trigger')).length}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
