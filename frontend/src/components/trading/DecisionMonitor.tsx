/**
 * DecisionMonitor - Real-time display of trading decision dynamics
 *
 * Shows: Market Price, Delta vs Anchor, Trigger Status, Guardrails, Decision
 * Auto-refreshes to show latest evaluation state
 */

import { useEffect, useState, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Target,
  Shield,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface TimelineRow {
  id?: string;
  timestamp?: string;
  evaluated_at?: string;

  // Market data
  market_price_raw?: number;
  effective_price?: number;
  is_market_hours?: boolean | number;
  market_session?: string;

  // Anchor & Trigger
  anchor_price?: number;
  anchor_price_at_eval?: number;
  pct_change_from_anchor?: number;
  anchor_delta_pct?: number;
  trigger_fired?: boolean | number;
  trigger_detected?: boolean;
  trigger_direction?: string;
  trigger_reason?: string;

  // Guardrails & Allocation
  guardrail_allowed?: boolean;
  guardrail_block_reason?: string;
  stock_pct?: number;
  position_stock_pct_before?: number;
  position_stock_pct_after?: number;
  cash_pct?: number;

  // Position state
  position_qty_before?: number;
  position_cash_before?: number;
  position_total_value_before?: number;
  position_total_value_after?: number;

  // Decision
  action?: string;
  action_taken?: string;
  action_reason?: string;
  decision_explanation?: string;
}

interface DecisionMonitorProps {
  portfolioId: string;
  positionId: string;
  refreshInterval?: number; // seconds
}

const TENANT_ID = 'default';
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function fetchLatestTimeline(portfolioId: string, positionId: string): Promise<TimelineRow[]> {
  const url = `${API_BASE}/v1/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/timeline?limit=10`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch timeline');
  }
  return response.json();
}

export default function DecisionMonitor({
  portfolioId,
  positionId,
  refreshInterval = 10
}: DecisionMonitorProps) {
  const [timeline, setTimeline] = useState<TimelineRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = useCallback(async () => {
    if (!portfolioId || !positionId) return;

    try {
      setError(null);
      const data = await fetchLatestTimeline(portfolioId, positionId);
      setTimeline(data);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [portfolioId, positionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(loadData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, loadData]);

  const latest = timeline[0];

  if (loading && timeline.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center text-gray-500">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />
          Loading decision data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center text-red-500">
          <AlertTriangle className="h-5 w-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  if (!latest) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">
          <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No evaluation data yet</p>
          <p className="text-xs mt-1">Run a position evaluation to see decision dynamics</p>
        </div>
      </div>
    );
  }

  const deltaVsAnchor = latest.pct_change_from_anchor ??
    (latest.anchor_price && latest.effective_price
      ? ((latest.effective_price - latest.anchor_price) / latest.anchor_price) * 100
      : null);

  const actionColor = {
    'BUY': 'text-green-600 bg-green-50',
    'SELL': 'text-red-600 bg-red-50',
    'HOLD': 'text-gray-600 bg-gray-50',
    'SKIP': 'text-yellow-600 bg-yellow-50',
  }[latest.action || 'HOLD'] || 'text-gray-600 bg-gray-50';

  const triggerIcon = latest.trigger_direction === 'UP'
    ? <TrendingUp className="h-4 w-4" />
    : latest.trigger_direction === 'DOWN'
    ? <TrendingDown className="h-4 w-4" />
    : <Minus className="h-4 w-4" />;

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold text-gray-900">Decision Monitor</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            Updated {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1.5 rounded ${autoRefresh ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}
            title={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
          </button>
          <button
            onClick={loadData}
            className="p-1.5 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
            title="Refresh now"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Latest Decision Summary */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wide">Latest Decision</span>
            <div className={`mt-1 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg font-bold text-lg ${actionColor}`}>
              {latest.action || 'HOLD'}
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-gray-500">
              {latest.evaluated_at || latest.timestamp
                ? new Date(latest.evaluated_at || latest.timestamp!).toLocaleString()
                : '-'}
            </span>
            {latest.action_reason && (
              <p className="text-sm text-gray-600 mt-1 max-w-xs">{latest.action_reason}</p>
            )}
          </div>
        </div>
      </div>

      {/* Decision Factors Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 divide-x divide-y lg:divide-y-0 divide-gray-200">

        {/* Market Price */}
        <div className="p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide mb-2">
            <TrendingUp className="h-3.5 w-3.5" />
            Market Price
          </div>
          <div className="text-xl font-bold text-gray-900">
            ${(latest.effective_price || latest.market_price_raw || 0).toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {latest.is_market_hours ? '🟢 Market Open' : '🔴 Market Closed'}
          </div>
        </div>

        {/* Delta vs Anchor */}
        <div className="p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide mb-2">
            <Target className="h-3.5 w-3.5" />
            Delta vs Anchor
          </div>
          <div className={`text-xl font-bold ${
            deltaVsAnchor === null ? 'text-gray-400' :
            deltaVsAnchor > 0 ? 'text-green-600' :
            deltaVsAnchor < 0 ? 'text-red-600' : 'text-gray-900'
          }`}>
            {deltaVsAnchor !== null ? `${deltaVsAnchor >= 0 ? '+' : ''}${deltaVsAnchor.toFixed(2)}%` : '-'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Anchor: ${(latest.anchor_price || 0).toFixed(2)}
          </div>
        </div>

        {/* Trigger Status */}
        <div className="p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide mb-2">
            <AlertTriangle className="h-3.5 w-3.5" />
            Trigger
          </div>
          <div className={`text-xl font-bold flex items-center gap-2 ${
            latest.trigger_fired ? 'text-orange-600' : 'text-gray-400'
          }`}>
            {triggerIcon}
            {latest.trigger_fired
              ? latest.trigger_direction || 'TRIGGERED'
              : 'None'}
          </div>
          <div className="text-xs text-gray-500 mt-1 truncate" title={latest.trigger_reason || ''}>
            {latest.trigger_reason || 'No trigger'}
          </div>
        </div>

        {/* Guardrails */}
        <div className="p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide mb-2">
            <Shield className="h-3.5 w-3.5" />
            Guardrails
          </div>
          <div className={`text-xl font-bold flex items-center gap-2 ${
            latest.guardrail_allowed === false ? 'text-red-600' : 'text-green-600'
          }`}>
            {latest.guardrail_allowed === false
              ? <><XCircle className="h-5 w-5" /> Blocked</>
              : <><CheckCircle className="h-5 w-5" /> OK</>
            }
          </div>
          <div className="text-xs text-gray-500 mt-1 truncate" title={latest.guardrail_block_reason || ''}>
            {latest.guardrail_block_reason || `Stock: ${(latest.stock_pct || 0).toFixed(1)}%`}
          </div>
        </div>
      </div>

      {/* Recent Evaluations */}
      <div className="border-t border-gray-200">
        <div className="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Recent Evaluations
        </div>
        <div className="divide-y divide-gray-100 max-h-48 overflow-y-auto">
          {timeline.slice(0, 5).map((row, idx) => {
            const rowDelta = row.pct_change_from_anchor ??
              (row.anchor_price && row.effective_price
                ? ((row.effective_price - row.anchor_price) / row.anchor_price) * 100
                : null);

            return (
              <div key={row.id || idx} className="px-4 py-2 flex items-center justify-between text-sm hover:bg-gray-50">
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500 w-20">
                    {row.evaluated_at || row.timestamp
                      ? new Date(row.evaluated_at || row.timestamp!).toLocaleTimeString()
                      : '-'}
                  </span>
                  <span className="font-medium w-16">
                    ${(row.effective_price || 0).toFixed(2)}
                  </span>
                  <span className={`w-16 ${
                    rowDelta === null ? 'text-gray-400' :
                    rowDelta > 0 ? 'text-green-600' :
                    rowDelta < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {rowDelta !== null ? `${rowDelta >= 0 ? '+' : ''}${rowDelta.toFixed(1)}%` : '-'}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {row.trigger_fired && (
                    <span className="px-2 py-0.5 text-xs rounded bg-orange-100 text-orange-700">
                      {row.trigger_direction}
                    </span>
                  )}
                  {row.guardrail_allowed === false && (
                    <span className="px-2 py-0.5 text-xs rounded bg-red-100 text-red-700">
                      Blocked
                    </span>
                  )}
                  <span className={`px-2 py-0.5 text-xs rounded font-medium ${
                    row.action === 'BUY' ? 'bg-green-100 text-green-700' :
                    row.action === 'SELL' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {row.action || 'HOLD'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
