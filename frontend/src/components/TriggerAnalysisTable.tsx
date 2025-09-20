import React from 'react';

interface TriggerAnalysisData {
  timestamp: string;
  date: string;
  time: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  anchor_price: number;
  price_change_pct: number;
  trigger_threshold: number;
  triggered: boolean;
  side: string | null;
  qty: number;
  reason: string;
  executed: boolean;
  execution_error?: string;
  commission?: number;
  cash_after?: number;
  shares_after?: number;
  dividend?: number;
}

interface TriggerAnalysisTableProps {
  data: TriggerAnalysisData[];
}

export default function TriggerAnalysisTable({ data }: TriggerAnalysisTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Trigger Analysis</h3>
        <p className="text-gray-500">No trigger data available</p>
      </div>
    );
  }

  // Filter to show only triggered events or significant price changes
  const significantEvents = data.filter(
    (trigger) =>
      trigger.triggered || Math.abs(trigger.price_change_pct) >= trigger.trigger_threshold * 0.5, // Show events within 50% of threshold
  );

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatPercentage = (pct: number) => {
    return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`;
  };

  const getStatusColor = (trigger: TriggerAnalysisData) => {
    if (trigger.executed) return 'text-green-600 bg-green-50';
    if (trigger.triggered && !trigger.executed) return 'text-red-600 bg-red-50';
    if (Math.abs(trigger.price_change_pct) >= trigger.trigger_threshold)
      return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getStatusText = (trigger: TriggerAnalysisData) => {
    if (trigger.executed) return 'Executed';
    if (trigger.triggered && !trigger.executed) return 'Failed';
    if (Math.abs(trigger.price_change_pct) >= trigger.trigger_threshold) return 'Near Trigger';
    return 'No Trigger';
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Trigger Analysis</h3>
      <p className="text-sm text-gray-600 mb-4">
        Showing {significantEvents.length} of {data.length} total evaluations
      </p>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Open
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                High
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Low
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Close
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Anchor
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Volume
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Change %
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Side
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Qty
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cash
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Shares
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Asset %
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Dividend
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reason
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {significantEvents.map((trigger, index) => {
              // Calculate asset percentage
              const totalValue =
                (trigger.cash_after || 0) + (trigger.shares_after || 0) * trigger.price;
              const assetPct =
                totalValue > 0
                  ? (((trigger.shares_after || 0) * trigger.price) / totalValue) * 100
                  : 0;

              return (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-2 py-2 text-sm text-gray-900">
                    {trigger.date || trigger.timestamp.split(' ')[0]}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    {trigger.time || trigger.timestamp.split(' ')[1] || '07:00:00'}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    ${(trigger.open || trigger.price).toFixed(2)}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    ${(trigger.high || trigger.price).toFixed(2)}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    ${(trigger.low || trigger.price).toFixed(2)}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">${trigger.price.toFixed(2)}</td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    ${(trigger.anchor_price || trigger.price).toFixed(2)}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    {(trigger.volume || 0).toLocaleString()}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">{formatPrice(trigger.price)}</td>
                  <td className="px-2 py-2 text-sm">
                    <span
                      className={`font-medium ${
                        trigger.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {formatPercentage(trigger.price_change_pct)}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                        trigger,
                      )}`}
                    >
                      {getStatusText(trigger)}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">{trigger.side || '-'}</td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    {trigger.qty > 0 ? trigger.qty.toFixed(1) : '-'}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    ${(trigger.cash_after || 0).toLocaleString()}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    {(trigger.shares_after || 0).toFixed(0)}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-900">{assetPct.toFixed(1)}%</td>
                  <td className="px-2 py-2 text-sm text-gray-900">
                    ${(trigger.dividend || 0).toFixed(2)}
                  </td>
                  <td className="px-2 py-2 text-sm text-gray-600">
                    <div className="max-w-xs">
                      <div className="truncate" title={trigger.reason}>
                        {trigger.reason}
                      </div>
                      {trigger.execution_error && (
                        <div className="text-xs text-red-500 mt-1" title={trigger.execution_error}>
                          Error: {trigger.execution_error}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {significantEvents.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No significant trigger events found in this simulation period.
        </div>
      )}
    </div>
  );
}
