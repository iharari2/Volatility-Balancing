import { X, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';

interface PositionDetailsDrawerProps {
  position: PortfolioPosition;
  portfolioId: string;
  tenantId: string;
  onClose: () => void;
}

interface PositionBaseline {
  baseline_price: number;
  baseline_qty: number;
  baseline_cash: number;
  baseline_total_value: number;
  baseline_stock_value: number;
  baseline_timestamp: string;
}

interface PositionEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  effective_price?: number;
  action: string;
  action_reason?: string;
  qty_before: number;
  qty_after: number;
  cash_before: number;
  cash_after: number;
  total_value_after: number;
}

export default function PositionDetailsDrawer({
  position,
  portfolioId,
  tenantId,
  onClose,
}: PositionDetailsDrawerProps) {
  const [baseline, setBaseline] = useState<PositionBaseline | null>(null);
  const [events, setEvents] = useState<PositionEvent[]>([]);
  const [loadingBaseline, setLoadingBaseline] = useState(true);
  const [loadingEvents, setLoadingEvents] = useState(true);

  const lastPrice = position.last_price ?? 0;
  const positionCash = position.cash || 0;
  const stockValue = lastPrice * position.qty;
  const positionTotal = positionCash + stockValue;
  const stockPctOfPosition = positionTotal > 0 ? (stockValue / positionTotal) * 100 : 0;

  // Load baseline and events
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load baseline
        const baselineRes = await fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${position.id}/baseline`,
        );
        if (baselineRes.ok) {
          const baselineData = await baselineRes.json();
          setBaseline(baselineData);
        }
        setLoadingBaseline(false);
      } catch (error) {
        console.error('Error loading baseline:', error);
        setLoadingBaseline(false);
      }

      try {
        // Load events
        const eventsRes = await fetch(
          `/api/v1/tenants/${tenantId}/portfolios/${portfolioId}/positions/${position.id}/events?limit=50`,
        );
        if (eventsRes.ok) {
          const eventsData = await eventsRes.json();
          setEvents(eventsData);
        }
        setLoadingEvents(false);
      } catch (error) {
        console.error('Error loading events:', error);
        setLoadingEvents(false);
      }
    };

    loadData();
  }, [tenantId, portfolioId, position.id]);

  // Calculate baseline comparison
  const baselineComparison = baseline
    ? {
        priceChange: lastPrice - baseline.baseline_price,
        priceChangePct:
          baseline.baseline_price > 0
            ? ((lastPrice - baseline.baseline_price) / baseline.baseline_price) * 100
            : 0,
        qtyChange: position.qty - baseline.baseline_qty,
        cashChange: positionCash - baseline.baseline_cash,
        totalValueChange: positionTotal - baseline.baseline_total_value,
        totalValueChangePct:
          baseline.baseline_total_value > 0
            ? ((positionTotal - baseline.baseline_total_value) / baseline.baseline_total_value) *
              100
            : 0,
      }
    : null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-white shadow-xl">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Position Details</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="space-y-6">
            {/* Current Position Snapshot */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Current Position Snapshot</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm text-gray-500">Ticker</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {position.asset || position.ticker}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Quantity</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {position.qty.toLocaleString()} shares
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Anchor Price</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {position.anchor_price ? `$${position.anchor_price.toFixed(2)}` : 'Not set'}
                  </dd>
                </div>
                {position.avg_cost && (
                  <div>
                    <dt className="text-sm text-gray-500">Average Cost</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      ${position.avg_cost.toFixed(2)}
                    </dd>
                  </div>
                )}
                {lastPrice > 0 && (
                  <div>
                    <dt className="text-sm text-gray-500">Market Price</dt>
                    <dd className="text-sm font-medium text-gray-900">${lastPrice.toFixed(2)}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm text-gray-500">Cash (Position)</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    $
                    {positionCash.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Stock Value</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    $
                    {stockValue.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Total Position Value</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    $
                    {positionTotal.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Stock % of Position</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {stockPctOfPosition.toFixed(1)}%
                  </dd>
                </div>
                {position.total_dividends_received != null && (
                  <div>
                    <dt className="text-sm text-gray-500">Dividends (Total)</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      $
                      {(position.total_dividends_received || 0).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Baseline Comparison */}
            {baseline && baselineComparison && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Baseline Comparison</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="text-xs text-gray-500 mb-2">
                    Baseline: {new Date(baseline.baseline_timestamp).toLocaleString()}
                  </div>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-sm text-gray-600">Price Change</dt>
                      <dd
                        className={`text-sm font-medium ${
                          baselineComparison.priceChange >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {baselineComparison.priceChange >= 0 ? '+' : ''}$
                        {baselineComparison.priceChange.toFixed(2)} (
                        {baselineComparison.priceChangePct >= 0 ? '+' : ''}
                        {baselineComparison.priceChangePct.toFixed(2)}%)
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-sm text-gray-600">Quantity Change</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {baselineComparison.qtyChange >= 0 ? '+' : ''}
                        {baselineComparison.qtyChange.toFixed(4)} shares
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-sm text-gray-600">Cash Change</dt>
                      <dd
                        className={`text-sm font-medium ${
                          baselineComparison.cashChange >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {baselineComparison.cashChange >= 0 ? '+' : ''}$
                        {baselineComparison.cashChange.toFixed(2)}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-sm text-gray-600">Total Value Change</dt>
                      <dd
                        className={`text-sm font-medium ${
                          baselineComparison.totalValueChange >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {baselineComparison.totalValueChange >= 0 ? '+' : ''}$
                        {baselineComparison.totalValueChange.toFixed(2)} (
                        {baselineComparison.totalValueChangePct >= 0 ? '+' : ''}
                        {baselineComparison.totalValueChangePct.toFixed(2)}%)
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            )}

            {/* Event Log */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Events</h3>
              {loadingEvents ? (
                <div className="text-sm text-gray-500">Loading events...</div>
              ) : events.length === 0 ? (
                <div className="text-sm text-gray-500">No events yet</div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {events.slice(0, 10).map((event) => (
                    <div
                      key={event.event_id}
                      className="border border-gray-200 rounded p-2 text-xs"
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-gray-900">{event.event_type}</span>
                        <span className="text-gray-500">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {event.action !== 'NONE' && (
                        <div className="text-gray-600 mb-1">
                          Action: <span className="font-medium">{event.action}</span>
                        </div>
                      )}
                      {event.action_reason && (
                        <div className="text-gray-500 text-xs">{event.action_reason}</div>
                      )}
                      {event.effective_price && (
                        <div className="text-gray-500 text-xs mt-1">
                          Price: ${event.effective_price.toFixed(2)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Links</h3>
              <div className="space-y-2">
                <Link
                  to={`/audit?asset=${position.ticker}&portfolio_id=${portfolioId}`}
                  className="block text-sm text-primary-600 hover:text-primary-900 flex items-center gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  Audit events for this asset
                </Link>
                <Link
                  to={`/audit?asset=${position.ticker}&portfolio_id=${portfolioId}&verbose=true`}
                  className="block text-sm text-primary-600 hover:text-primary-900 flex items-center gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  Verbose timeline for this asset
                </Link>
                <Link
                  to={`/audit?asset=${position.ticker}&portfolio_id=${portfolioId}&type=trade`}
                  className="block text-sm text-primary-600 hover:text-primary-900 flex items-center gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  Trades/executions for this asset
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}








