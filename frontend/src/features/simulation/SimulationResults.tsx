import { useState } from 'react';
import { Download, Play, Filter, Clock, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Scatter,
  Cell,
} from 'recharts';

interface TimelineEvent {
  timestamp: string;
  date: string;
  time: string;
  price: number;
  anchor_price: number;
  price_change_pct: number;
  trigger_threshold_pct: number;
  triggered: boolean;
  side: string | null;
  executed: boolean;
  shares: number;
  cash: number;
  total_value: number;
  asset_allocation_pct: number;
  trade_qty?: number;
  commission?: number;
  reason?: string;
}

interface DividendEvent {
  date: string;
  ex_date: string;
  shares_held: number;
  dps: number;
  gross_amount: number;
  withholding_tax: number;
  net_amount: number;
  anchor_adjustment: number;
}

interface SimulationResultsProps {
  result: {
    finalValue?: number;
    return?: number;
    maxDrawdown?: number;
    volatility?: number;
    trades?: Array<{
      time: string;
      action: string;
      qty: number;
      price: number;
      commission: number;
    }>;
    equityCurve?: Array<{ date: string; value: number }>;
    priceData?: Array<{ date: string; price: number; trigger?: string }>;
    time_series_data?: TimelineEvent[];
    algorithm_return_pct?: number;
    algorithm_max_drawdown?: number;
    algorithm_volatility?: number;
    algorithm_trades?: number;
    trade_log?: Array<{
      timestamp: string;
      side: string;
      qty: number;
      price: number;
      commission: number;
    }>;
    // Dividend fields
    total_dividends_received?: number;
    dividend_events?: DividendEvent[];
    dividend_analysis?: {
      total_dividends?: number;
      dividend_yield?: number;
      dividend_count?: number;
      withholding_tax_total?: number;
    };
  } | null;
}

export default function SimulationResults({ result }: SimulationResultsProps) {
  const [showTriggersOnly, setShowTriggersOnly] = useState(true);
  const [activeTab, setActiveTab] = useState<'trades' | 'timeline' | 'dividends'>('timeline');

  if (!result) {
    return (
      <div className="card h-full flex flex-col items-center justify-center text-center p-12">
        <div className="bg-gray-50 p-6 rounded-full mb-4">
          <Play className="h-12 w-12 text-gray-300 fill-current" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Ready to Simulate</h2>
        <p className="text-sm text-gray-500 max-w-xs">
          Configure your parameters and click "Run Simulation" to see projected performance.
        </p>
      </div>
    );
  }

  // Get timeline events with optional filtering
  const timelineEvents = result.time_series_data || [];
  const filteredEvents = showTriggersOnly
    ? timelineEvents.filter((e) => e.triggered)
    : timelineEvents;
  const triggeredCount = timelineEvents.filter((e) => e.triggered).length;

  const handleExportExcel = () => {
    window.open('/api/v1/excel/simulation/export?format=xlsx', '_blank');
  };

  const handleExportJSON = () => {
    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `simulation_results_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Build equity curve from time_series_data if available
  const equityData = result.equityCurve || (timelineEvents.length > 0
    ? timelineEvents.map((event) => ({
        date: event.date,
        value: event.total_value,
      }))
    : Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 100000 + (result.return || 0) * 1000 * (i / 30),
      })));

  // Build price data from time_series_data if available
  const priceData = result.priceData || (timelineEvents.length > 0
    ? timelineEvents.map((event) => ({
        date: event.date,
        price: event.price,
        trigger: event.triggered ? event.side : undefined,
      }))
    : Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        price: 200 + Math.sin(i / 5) * 10,
        trigger: i % 10 === 0 ? (i % 20 === 0 ? 'BUY' : 'SELL') : undefined,
      })));

  // Build price chart data with buy/sell markers
  const priceChartData = timelineEvents.length > 0
    ? timelineEvents.map((event) => ({
        date: event.date,
        price: event.price,
        buyMarker: event.triggered && event.side === 'BUY' ? event.price : null,
        sellMarker: event.triggered && event.side === 'SELL' ? event.price : null,
        tradeQty: event.trade_qty,
        side: event.side,
      }))
    : priceData.map((d) => ({
        ...d,
        buyMarker: d.trigger === 'BUY' ? d.price : null,
        sellMarker: d.trigger === 'SELL' ? d.price : null,
      }));

  // Build equity chart data with trade markers
  const equityChartData = timelineEvents.length > 0
    ? timelineEvents.map((event) => ({
        date: event.date,
        value: event.total_value,
        buyMarker: event.triggered && event.side === 'BUY' ? event.total_value : null,
        sellMarker: event.triggered && event.side === 'SELL' ? event.total_value : null,
      }))
    : equityData.map((d) => ({
        ...d,
        buyMarker: null,
        sellMarker: null,
      }));

  return (
    <div className="card space-y-8">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100">
        <h2 className="text-xl font-bold text-gray-900">Simulation Results</h2>
        <div className="flex gap-2">
          <button
            onClick={handleExportExcel}
            className="btn btn-secondary py-1.5 text-xs flex items-center"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Excel
          </button>
          <button
            onClick={handleExportJSON}
            className="btn btn-secondary py-1.5 text-xs flex items-center"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            JSON
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Final Value
          </p>
          <p className="text-xl font-bold text-gray-900">
            ${(result.finalValue || timelineEvents[timelineEvents.length - 1]?.total_value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Return
          </p>
          <p
            className={`text-xl font-bold ${
              (result.return || result.algorithm_return_pct || 0) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {(result.return || result.algorithm_return_pct || 0) >= 0 ? '+' : ''}
            {(result.return || result.algorithm_return_pct || 0).toFixed(1)}%
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Max Drawdown
          </p>
          <p className="text-xl font-bold text-red-600">
            {(result.maxDrawdown || result.algorithm_max_drawdown || 0).toFixed(1)}%
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Volatility
          </p>
          <p className="text-xl font-bold text-gray-900">{(result.volatility || result.algorithm_volatility || 0).toFixed(2)}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Trades
          </p>
          <p className="text-xl font-bold text-purple-600">{result.algorithm_trades || result.trades?.length || result.trade_log?.length || 0}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Dividends
          </p>
          <p className="text-xl font-bold text-teal-600">
            ${(result.total_dividends_received || result.dividend_analysis?.total_dividends || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
          {(result.dividend_events?.length || result.dividend_analysis?.dividend_count || 0) > 0 && (
            <p className="text-xs text-gray-500 mt-0.5">
              {result.dividend_events?.length || result.dividend_analysis?.dividend_count || 0} payment{(result.dividend_events?.length || result.dividend_analysis?.dividend_count || 0) !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>

      <div className="space-y-8">
        {/* Equity Curve Chart */}
        <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-inner">
          <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">
            Equity Curve
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={equityChartData}>
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
                formatter={(value: number, name: string) => {
                  if (name === 'buyMarker') return [`$${value?.toLocaleString()}`, '🟢 BUY'];
                  if (name === 'sellMarker') return [`$${value?.toLocaleString()}`, '🔴 SELL'];
                  return [`$${value?.toLocaleString()}`, 'Portfolio Value'];
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={false} name="value" />
              <Scatter dataKey="buyMarker" fill="#22c55e" shape="triangle" name="buyMarker">
                {equityChartData.map((entry, index) => (
                  <Cell key={`buy-${index}`} fill={entry.buyMarker ? '#22c55e' : 'transparent'} />
                ))}
              </Scatter>
              <Scatter dataKey="sellMarker" fill="#ef4444" shape="triangle" name="sellMarker">
                {equityChartData.map((entry, index) => (
                  <Cell key={`sell-${index}`} fill={entry.sellMarker ? '#ef4444' : 'transparent'} />
                ))}
              </Scatter>
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Price Chart */}
        <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-inner">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              Asset Price & Triggers
            </h3>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 bg-green-500 rounded-full inline-block"></span>
                BUY
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 bg-red-500 rounded-full inline-block"></span>
                SELL
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={priceChartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: '#9ca3af' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{
                  borderRadius: '8px',
                  border: 'none',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                formatter={(value: number, name: string, props: { payload?: { tradeQty?: number } }) => {
                  if (name === 'buyMarker') {
                    const qty = props.payload?.tradeQty;
                    return [`$${value?.toFixed(2)}${qty ? ` (${qty.toFixed(2)} shares)` : ''}`, '🟢 BUY'];
                  }
                  if (name === 'sellMarker') {
                    const qty = props.payload?.tradeQty;
                    return [`$${value?.toFixed(2)}${qty ? ` (${qty.toFixed(2)} shares)` : ''}`, '🔴 SELL'];
                  }
                  return [`$${value?.toFixed(2)}`, 'Price'];
                }}
              />
              <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={false} name="price" />
              <Scatter dataKey="buyMarker" fill="#22c55e" name="buyMarker">
                {priceChartData.map((entry, index) => (
                  <Cell key={`buy-${index}`} fill={entry.buyMarker ? '#22c55e' : 'transparent'} />
                ))}
              </Scatter>
              <Scatter dataKey="sellMarker" fill="#ef4444" name="sellMarker">
                {priceChartData.map((entry, index) => (
                  <Cell key={`sell-${index}`} fill={entry.sellMarker ? '#ef4444' : 'transparent'} />
                ))}
              </Scatter>
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2 ${
                activeTab === 'timeline'
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Clock className="h-4 w-4" />
              Timeline ({triggeredCount} triggers)
            </button>
            <button
              onClick={() => setActiveTab('trades')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'trades'
                  ? 'bg-green-100 text-green-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Trade Log ({result.trades?.length || result.trade_log?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('dividends')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2 ${
                activeTab === 'dividends'
                  ? 'bg-teal-100 text-teal-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <DollarSign className="h-4 w-4" />
              Dividends ({result.dividend_events?.length || result.dividend_analysis?.dividend_count || 0})
            </button>
          </div>

          {activeTab === 'timeline' && (
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                checked={showTriggersOnly}
                onChange={(e) => setShowTriggersOnly(e.target.checked)}
                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <Filter className="h-4 w-4" />
              Triggers only
            </label>
          )}
        </div>

        {/* Timeline / Events Tab */}
        {activeTab === 'timeline' && (
          <>
            {filteredEvents.length > 0 ? (
              <div className="-mx-6 overflow-x-auto max-h-96 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Anchor
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Change %
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Trigger
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Shares
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Value
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Reason
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {filteredEvents.map((event, idx) => (
                      <tr
                        key={idx}
                        className={`hover:bg-gray-50 transition-colors ${
                          event.triggered ? 'bg-yellow-50' : ''
                        }`}
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600">
                          <div>{event.date}</div>
                          <div className="text-gray-400">{event.time}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-right font-medium text-gray-900">
                          ${event.price.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-gray-600">
                          ${event.anchor_price?.toFixed(2) || '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-right">
                          <span
                            className={`font-medium ${
                              event.price_change_pct > 0
                                ? 'text-green-600'
                                : event.price_change_pct < 0
                                  ? 'text-red-600'
                                  : 'text-gray-500'
                            }`}
                          >
                            {event.price_change_pct > 0 ? '+' : ''}
                            {event.price_change_pct?.toFixed(2) || '0.00'}%
                          </span>
                          <div className="text-gray-400 text-[10px]">
                            threshold: ±{event.trigger_threshold_pct?.toFixed(1) || '3.0'}%
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          {event.triggered ? (
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${
                                event.side === 'BUY'
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-red-100 text-red-700'
                              }`}
                            >
                              {event.side === 'BUY' ? (
                                <TrendingUp className="h-3 w-3" />
                              ) : (
                                <TrendingDown className="h-3 w-3" />
                              )}
                              {event.side}
                              {event.executed && ' ✓'}
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-gray-600">
                          {event.shares?.toFixed(2) || '0'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-right font-medium text-gray-900">
                          ${event.total_value?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || '0'}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate" title={event.reason || ''}>
                          {event.reason || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                <Clock className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-500 italic">
                  {showTriggersOnly
                    ? 'No triggers detected during this simulation.'
                    : 'No timeline events available.'}
                </p>
                {showTriggersOnly && timelineEvents.length > 0 && (
                  <button
                    onClick={() => setShowTriggersOnly(false)}
                    className="mt-2 text-sm text-purple-600 hover:text-purple-800 underline"
                  >
                    Show all {timelineEvents.length} events
                  </button>
                )}
              </div>
            )}
          </>
        )}

        {/* Trades Tab */}
        {activeTab === 'trades' && (
          <>
            {(result.trades && result.trades.length > 0) ||
            (result.trade_log && result.trade_log.length > 0) ? (
              <div className="-mx-6 overflow-x-auto max-h-96 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Qty
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Fees
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {(result.trades || result.trade_log || []).map((trade, idx) => (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600">
                          {'time' in trade ? trade.time : trade.timestamp}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${
                              ('action' in trade ? trade.action : trade.side) === 'BUY'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {'action' in trade ? trade.action : trade.side}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-right font-medium text-gray-900">
                          {trade.qty.toFixed(4)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-right font-medium text-gray-900">
                          ${trade.price.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-right text-gray-500">
                          ${trade.commission.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                <p className="text-sm text-gray-500 italic">
                  No trades executed during this simulation.
                </p>
              </div>
            )}
          </>
        )}

        {/* Dividends Tab */}
        {activeTab === 'dividends' && (
          <>
            {(result.dividend_events && result.dividend_events.length > 0) ? (
              <div className="space-y-4">
                {/* Dividend Summary */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-teal-50 rounded-lg border border-teal-100">
                  <div>
                    <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">Total Gross</p>
                    <p className="text-lg font-bold text-gray-900">
                      ${result.dividend_events.reduce((sum, d) => sum + (d.gross_amount || 0), 0).toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">Withholding Tax</p>
                    <p className="text-lg font-bold text-red-600">
                      -${result.dividend_events.reduce((sum, d) => sum + (d.withholding_tax || 0), 0).toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">Net Received</p>
                    <p className="text-lg font-bold text-teal-700">
                      ${result.dividend_events.reduce((sum, d) => sum + (d.net_amount || 0), 0).toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">Payments</p>
                    <p className="text-lg font-bold text-gray-900">{result.dividend_events.length}</p>
                  </div>
                </div>

                {/* Dividend Events Table */}
                <div className="-mx-6 overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Ex-Date
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Shares Held
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          $/Share
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Gross
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Tax (25%)
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Net
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          Anchor Adj.
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {result.dividend_events.map((dividend, idx) => (
                        <tr key={idx} className="hover:bg-teal-50 transition-colors">
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-900 font-medium">
                            {dividend.ex_date || dividend.date}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-gray-600">
                            {dividend.shares_held?.toFixed(2) || '-'}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-gray-600">
                            ${dividend.dps?.toFixed(4) || '-'}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right font-medium text-gray-900">
                            ${dividend.gross_amount?.toFixed(2) || '-'}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-red-600">
                            -${dividend.withholding_tax?.toFixed(2) || '0.00'}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right font-medium text-teal-700">
                            ${dividend.net_amount?.toFixed(2) || '-'}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-right text-gray-500">
                            -${dividend.anchor_adjustment?.toFixed(2) || dividend.dps?.toFixed(2) || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                <DollarSign className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-500 italic">
                  No dividend payments during this simulation period.
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Dividends are processed on ex-dividend dates when you hold shares.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
