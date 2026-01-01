import { Download, Play } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

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
  } | null;
}

export default function SimulationResults({ result }: SimulationResultsProps) {
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

  // Mock equity curve data if not provided
  const equityData =
    result.equityCurve ||
    Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: 100000 + (result.return || 0) * 1000 * (i / 30),
    }));

  // Mock price data with triggers if not provided
  const priceData =
    result.priceData ||
    Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      price: 200 + Math.sin(i / 5) * 10,
      trigger: i % 10 === 0 ? (i % 20 === 0 ? 'BUY' : 'SELL') : undefined,
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
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Final Value
          </p>
          <p className="text-xl font-bold text-gray-900">
            ${(result.finalValue || 0).toLocaleString()}
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Return
          </p>
          <p
            className={`text-xl font-bold ${
              result.return && result.return >= 0 ? 'text-success-600' : 'text-danger-600'
            }`}
          >
            {result.return ? (result.return >= 0 ? '+' : '') : ''}
            {(result.return || 0).toFixed(1)}%
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Max Drawdown
          </p>
          <p className="text-xl font-bold text-danger-600">
            {(result.maxDrawdown || 0).toFixed(1)}%
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Volatility
          </p>
          <p className="text-xl font-bold text-gray-900">{(result.volatility || 0).toFixed(2)}</p>
        </div>
      </div>

      <div className="space-y-8">
        {/* Equity Curve Chart */}
        <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-inner">
          <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">
            Equity Curve
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={equityData}>
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
              <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Price Chart */}
        <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-inner">
          <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">
            Asset Price & Triggers
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={priceData}>
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
              <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trades Table */}
      <div className="pt-4">
        <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Trade Log</h3>
        {result.trades && result.trades.length > 0 ? (
          <div className="-mx-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
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
                {result.trades.map((trade, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600">
                      {trade.time}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`badge ${
                          trade.action === 'BUY' ? 'badge-success' : 'badge-danger'
                        }`}
                      >
                        {trade.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-right font-medium text-gray-900">
                      {trade.qty.toLocaleString()}
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
      </div>
    </div>
  );
}
