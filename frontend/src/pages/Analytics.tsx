import { useState } from 'react';
import { usePositions, usePositionEvents } from '../hooks/usePositions';
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
} from 'recharts';
import { TrendingUp, DollarSign, Activity, Target } from 'lucide-react';

export default function Analytics() {
  const { data: positions = [] } = usePositions();
  const [selectedPositionId, setSelectedPositionId] = useState<string>('');

  const selectedPosition = positions.find((p) => p.id === selectedPositionId);
  const { data: events } = usePositionEvents(selectedPositionId);

  // Calculate analytics data
  const totalValue = positions.reduce((sum, pos) => {
    const value = pos.qty * (pos.anchor_price || 0) + pos.cash;
    return sum + value;
  }, 0);

  const totalCash = positions.reduce((sum, pos) => sum + pos.cash, 0);
  const totalShares = positions.reduce((sum, pos) => sum + pos.qty, 0);
  const activePositions = positions.filter((pos) => pos.anchor_price);

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
  const positionData = positions.map((pos) => ({
    ticker: pos.ticker,
    value: pos.qty * (pos.anchor_price || 0) + pos.cash,
    shares: pos.qty,
    cash: pos.cash,
    hasAnchor: !!pos.anchor_price,
  }));

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600">Performance metrics and trading insights</p>
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
              {positions.map((position) => {
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


