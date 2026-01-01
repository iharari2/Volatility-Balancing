import { useState, useEffect } from 'react';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';
import { format } from 'date-fns';

interface TimelineRow {
  id: string;
  timestamp: string;
  evaluation_type: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  effective_price?: number;
  anchor_price?: number;
  trigger_up_threshold?: number;
  trigger_down_threshold?: number;
  action?: string;
  action_reason?: string;
  position_qty_before?: number;
  position_qty_after?: number;
  position_cash_before?: number;
  position_cash_after?: number;
  position_total_value_after?: number;
  guardrail_min_stock_alloc_pct?: number;
  guardrail_max_stock_alloc_pct?: number;
  guardrail_block_reason?: string;
  [key: string]: any;
}

interface EventLogSectionProps {
  position: PortfolioPosition;
  tenantId: string;
  portfolioId: string;
}

export default function EventLogSection({ position, tenantId, portfolioId }: EventLogSectionProps) {
  const [timeline, setTimeline] = useState<TimelineRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTimeline = async () => {
      try {
        const response = await fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${position.id}/timeline?limit=100&mode=LIVE`,
        );
        if (response.ok) {
          const data = await response.json();
          setTimeline(data);
        }
      } catch (error) {
        console.error('Error loading timeline:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTimeline();
    const interval = setInterval(loadTimeline, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [tenantId, portfolioId, position.id]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Event Log</h2>
        <div className="text-sm text-gray-500">Loading events...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Event Log (Chronological)</h2>
      {timeline.length === 0 ? (
        <div className="text-sm text-gray-500">No events yet</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Price (O/H/L/C)
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Effective Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Anchor
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Triggers
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Guardrails
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Qty Before/After
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cash Before/After
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Value After
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {timeline.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {format(new Date(row.timestamp), 'MMM d, yyyy HH:mm:ss')}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.open !== undefined ||
                    row.high !== undefined ||
                    row.low !== undefined ||
                    row.close !== undefined ? (
                      <div>
                        O: {row.open?.toFixed(2) || '—'} | H: {row.high?.toFixed(2) || '—'} | L:{' '}
                        {row.low?.toFixed(2) || '—'} | C: {row.close?.toFixed(2) || '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {row.effective_price ? `$${row.effective_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {row.anchor_price ? `$${row.anchor_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.trigger_up_threshold || row.trigger_down_threshold ? (
                      <div>
                        Up:{' '}
                        {row.trigger_up_threshold ? `$${row.trigger_up_threshold.toFixed(2)}` : '—'}
                        <br />
                        Down:{' '}
                        {row.trigger_down_threshold
                          ? `$${row.trigger_down_threshold.toFixed(2)}`
                          : '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.guardrail_min_stock_alloc_pct !== undefined ||
                    row.guardrail_max_stock_alloc_pct !== undefined ? (
                      <div>
                        Min: {row.guardrail_min_stock_alloc_pct?.toFixed(1) || '—'}% | Max:{' '}
                        {row.guardrail_max_stock_alloc_pct?.toFixed(1) || '—'}%
                        {row.guardrail_block_reason && (
                          <div className="text-red-600 mt-1">
                            Blocked: {row.guardrail_block_reason}
                          </div>
                        )}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs">
                    <div className="font-medium text-gray-900">{row.action || 'NONE'}</div>
                    {row.action_reason && (
                      <div className="text-gray-500 mt-1">{row.action_reason}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.position_qty_before !== undefined ||
                    row.position_qty_after !== undefined ? (
                      <div>
                        {row.position_qty_before?.toFixed(4) || '—'} →{' '}
                        {row.position_qty_after?.toFixed(4) || '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                    {row.position_cash_before !== undefined ||
                    row.position_cash_after !== undefined ? (
                      <div>
                        ${row.position_cash_before?.toFixed(2) || '—'} → $
                        {row.position_cash_after?.toFixed(2) || '—'}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900">
                    {row.position_total_value_after
                      ? `$${row.position_total_value_after.toFixed(2)}`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}








