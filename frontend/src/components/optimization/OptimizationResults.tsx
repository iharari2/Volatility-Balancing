// Optimization Results Component
// Displays optimization results in a table format with sorting and filtering

import React, { useState, useMemo } from 'react';
import { OptimizationResult, OptimizationMetric, TradeLogEntry } from '../../types/optimization';

interface OptimizationResultsProps {
  results: OptimizationResult[];
  loading?: boolean;
  onResultClick?: (result: OptimizationResult) => void;
}

type SortField =
  | 'sharpe_ratio'
  | 'total_return'
  | 'buy_hold_return'
  | 'max_drawdown'
  | 'volatility'
  | 'win_rate'
  | 'trade_count'
  | 'total_commissions';
type SortDirection = 'asc' | 'desc';

const COLUMN_TOOLTIPS: Record<string, string> = {
  sharpe_ratio: 'Risk-adjusted return. Higher is better. >1 good, >2 excellent.',
  total_return: "Algorithm's total percentage gain/loss over the simulation period.",
  buy_hold_return: 'Baseline return from simply buying and holding the stock.',
  max_drawdown: 'Largest peak-to-trough decline. Closer to 0% is better.',
  volatility: 'Annualized standard deviation of daily returns. Lower = less risky.',
  win_rate: 'Percentage of trading days with positive returns.',
  trade_count: 'Total number of trades executed by the algorithm.',
  total_commissions: 'Total trading commissions paid across all trades.',
};

export const OptimizationResults: React.FC<OptimizationResultsProps> = ({
  results,
  loading = false,
  onResultClick,
}) => {
  const [sortField, setSortField] = useState<SortField>('sharpe_ratio');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filterMetric, setFilterMetric] = useState<OptimizationMetric | 'all'>('all');
  const [filterValue, setFilterValue] = useState<string>('');
  const [selectedResult, setSelectedResult] = useState<OptimizationResult | null>(null);

  // Sort and filter results
  const processedResults = useMemo(() => {
    let filtered = results;

    // Filter by metric value
    if (filterMetric !== 'all' && filterValue) {
      const value = parseFloat(filterValue);
      if (!isNaN(value)) {
        filtered = filtered.filter((result) => {
          const metricValue = result.metrics[filterMetric];
          return metricValue !== undefined && metricValue >= value;
        });
      }
    }

    // Sort results
    filtered.sort((a, b) => {
      const aValue = a.metrics[sortField] || 0;
      const bValue = b.metrics[sortField] || 0;

      if (sortDirection === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });

    return filtered;
  }, [results, sortField, sortDirection, filterMetric, filterValue]);

  // Handle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Format metric value
  const formatMetricValue = (value: number, metric: OptimizationMetric): string => {
    if (value === undefined || value === null) return 'N/A';

    switch (metric) {
      case OptimizationMetric.TOTAL_RETURN:
      case OptimizationMetric.BUY_HOLD_RETURN:
      case OptimizationMetric.MAX_DRAWDOWN:
      case OptimizationMetric.VOLATILITY:
        return `${(value * 100).toFixed(2)}%`;
      case OptimizationMetric.SHARPE_RATIO:
      case OptimizationMetric.CALMAR_RATIO:
      case OptimizationMetric.SORTINO_RATIO:
      case OptimizationMetric.PROFIT_FACTOR:
        return value.toFixed(3);
      case OptimizationMetric.WIN_RATE:
        return `${(value * 100).toFixed(1)}%`;
      case OptimizationMetric.TRADE_COUNT:
        return Math.round(value).toString();
      case OptimizationMetric.TOTAL_COMMISSIONS:
        return `$${value.toFixed(2)}`;
      case OptimizationMetric.AVG_TRADE_DURATION:
        return `${value.toFixed(1)} days`;
      default:
        return value.toFixed(3);
    }
  };

  // Get metric color class
  const getMetricColorClass = (value: number, metric: OptimizationMetric): string => {
    if (value === undefined || value === null) return 'text-gray-400';

    switch (metric) {
      case OptimizationMetric.SHARPE_RATIO:
      case OptimizationMetric.CALMAR_RATIO:
      case OptimizationMetric.SORTINO_RATIO:
      case OptimizationMetric.PROFIT_FACTOR:
      case OptimizationMetric.WIN_RATE:
        return value > 1 ? 'text-green-600' : value > 0.5 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.TOTAL_RETURN:
      case OptimizationMetric.BUY_HOLD_RETURN:
        return value > 0.10 ? 'text-green-600' : value > 0 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.MAX_DRAWDOWN:
        return value > -0.05 ? 'text-green-600' : value > -0.10 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.VOLATILITY:
        return value < 0.10 ? 'text-green-600' : value < 0.20 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.TRADE_COUNT:
        return value > 50 ? 'text-green-600' : value > 20 ? 'text-yellow-600' : 'text-red-600';
      default:
        return 'text-gray-900';
    }
  };

  // Sort indicator
  const SortIndicator: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) return null;
    return <span className="ml-1">{sortDirection === 'asc' ? '\u2191' : '\u2193'}</span>;
  };

  // Sortable header with tooltip
  const SortableHeader: React.FC<{ field: SortField; label: string }> = ({ field, label }) => (
    <th
      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => handleSort(field)}
    >
      <span
        title={COLUMN_TOOLTIPS[field]}
        className="cursor-help border-b border-dotted border-gray-400"
      >
        {label}
      </span>
      <SortIndicator field={field} />
    </th>
  );

  // Handle row click — open detail modal
  const handleRowClick = (result: OptimizationResult) => {
    setSelectedResult(result);
    onResultClick?.(result);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 text-center">
          <div className="text-gray-500 text-lg">No results available</div>
          <div className="text-gray-400 text-sm mt-2">Run an optimization to see results here</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            Optimization Results ({processedResults.length} of {results.length})
          </h3>

          {/* Filters */}
          <div className="flex space-x-4">
            <select
              value={filterMetric}
              onChange={(e) => setFilterMetric(e.target.value as OptimizationMetric | 'all')}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Results</option>
              <option value={OptimizationMetric.SHARPE_RATIO}>Sharpe Ratio &ge;</option>
              <option value={OptimizationMetric.TOTAL_RETURN}>Total Return &ge;</option>
              <option value={OptimizationMetric.WIN_RATE}>Win Rate &ge;</option>
            </select>

            {filterMetric !== 'all' && (
              <input
                type="number"
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
                placeholder="Min value"
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                step="0.01"
              />
            )}
          </div>
        </div>

        {/* Results Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <SortableHeader field="sharpe_ratio" label="Sharpe Ratio" />
                <SortableHeader field="total_return" label="Total Return" />
                <SortableHeader field="buy_hold_return" label="Buy & Hold" />
                <SortableHeader field="max_drawdown" label="Max Drawdown" />
                <SortableHeader field="volatility" label="Volatility" />
                <SortableHeader field="win_rate" label="Win Rate" />
                <SortableHeader field="trade_count" label="Trades" />
                <SortableHeader field="total_commissions" label="Commissions" />
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parameters
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {processedResults.map((result, index) => (
                <tr
                  key={result.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleRowClick(result)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{index + 1}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.sharpe_ratio,
                        OptimizationMetric.SHARPE_RATIO,
                      )}
                    >
                      {formatMetricValue(
                        result.metrics.sharpe_ratio,
                        OptimizationMetric.SHARPE_RATIO,
                      )}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.total_return,
                        OptimizationMetric.TOTAL_RETURN,
                      )}
                    >
                      {formatMetricValue(
                        result.metrics.total_return,
                        OptimizationMetric.TOTAL_RETURN,
                      )}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.buy_hold_return,
                        OptimizationMetric.BUY_HOLD_RETURN,
                      )}
                    >
                      {formatMetricValue(
                        result.metrics.buy_hold_return,
                        OptimizationMetric.BUY_HOLD_RETURN,
                      )}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.max_drawdown,
                        OptimizationMetric.MAX_DRAWDOWN,
                      )}
                    >
                      {formatMetricValue(
                        result.metrics.max_drawdown,
                        OptimizationMetric.MAX_DRAWDOWN,
                      )}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.volatility,
                        OptimizationMetric.VOLATILITY,
                      )}
                    >
                      {formatMetricValue(result.metrics.volatility, OptimizationMetric.VOLATILITY)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.win_rate,
                        OptimizationMetric.WIN_RATE,
                      )}
                    >
                      {formatMetricValue(result.metrics.win_rate, OptimizationMetric.WIN_RATE)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={getMetricColorClass(
                        result.metrics.trade_count,
                        OptimizationMetric.TRADE_COUNT,
                      )}
                    >
                      {formatMetricValue(
                        result.metrics.trade_count,
                        OptimizationMetric.TRADE_COUNT,
                      )}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatMetricValue(
                      result.metrics.total_commissions,
                      OptimizationMetric.TOTAL_COMMISSIONS,
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="max-w-xs truncate">
                      {Object.entries(result.parameter_combination.parameters).map(
                        ([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-medium">{key}:</span>{' '}
                            {typeof value === 'object' ? JSON.stringify(value) : value}
                          </div>
                        ),
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Best Sharpe Ratio</div>
            <div className="text-2xl font-bold text-green-600">
              {Math.max(...results.map((r) => r.metrics.sharpe_ratio || 0)).toFixed(3)}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Best Total Return</div>
            <div className="text-2xl font-bold text-green-600">
              {formatMetricValue(
                Math.max(...results.map((r) => r.metrics.total_return || 0)),
                OptimizationMetric.TOTAL_RETURN,
              )}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Lowest Drawdown</div>
            <div className="text-2xl font-bold text-green-600">
              {formatMetricValue(
                Math.max(...results.map((r) => r.metrics.max_drawdown || -1)),
                OptimizationMetric.MAX_DRAWDOWN,
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedResult && (
        <DetailModal result={selectedResult} onClose={() => setSelectedResult(null)} formatMetricValue={formatMetricValue} />
      )}
    </div>
  );
};

// Detail modal component
interface DetailModalProps {
  result: OptimizationResult;
  onClose: () => void;
  formatMetricValue: (value: number, metric: OptimizationMetric) => string;
}

const DetailModal: React.FC<DetailModalProps> = ({ result, onClose, formatMetricValue }) => {
  const tradeLog: TradeLogEntry[] = result.simulation_result?.trade_log || [];

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Simulation Detail</h3>
            <div className="mt-1 flex flex-wrap gap-2">
              {Object.entries(result.parameter_combination.parameters).map(([key, value]) => (
                <span key={key} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {key}={typeof value === 'number' ? (value as number).toFixed(4) : String(value)}
                </span>
              ))}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        {/* Metrics Grid */}
        <div className="p-6 border-b border-gray-200">
          <h4 className="text-sm font-medium text-gray-500 mb-3">Metrics</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {([
              [OptimizationMetric.SHARPE_RATIO, 'Sharpe Ratio'],
              [OptimizationMetric.TOTAL_RETURN, 'Total Return'],
              [OptimizationMetric.BUY_HOLD_RETURN, 'Buy & Hold'],
              [OptimizationMetric.MAX_DRAWDOWN, 'Max Drawdown'],
              [OptimizationMetric.VOLATILITY, 'Volatility'],
              [OptimizationMetric.WIN_RATE, 'Win Rate'],
              [OptimizationMetric.TRADE_COUNT, 'Trades'],
              [OptimizationMetric.TOTAL_COMMISSIONS, 'Commissions'],
              [OptimizationMetric.CALMAR_RATIO, 'Calmar Ratio'],
              [OptimizationMetric.SORTINO_RATIO, 'Sortino Ratio'],
              [OptimizationMetric.PROFIT_FACTOR, 'Profit Factor'],
            ] as [OptimizationMetric, string][]).map(([metric, label]) => {
              const val = result.metrics[metric];
              if (val === undefined) return null;
              return (
                <div key={metric} className="bg-gray-50 p-3 rounded">
                  <div className="text-xs text-gray-500">{label}</div>
                  <div className="text-sm font-semibold">{formatMetricValue(val, metric)}</div>
                </div>
              );
            })}
            {result.simulation_result && (
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-xs text-gray-500">Algorithm P&L</div>
                <div className="text-sm font-semibold">${result.simulation_result.algorithm_pnl.toFixed(2)}</div>
              </div>
            )}
          </div>
        </div>

        {/* Trade Log */}
        <div className="flex-1 overflow-auto p-6">
          <h4 className="text-sm font-medium text-gray-500 mb-3">
            Trade Log ({tradeLog.length} trades)
          </h4>
          {tradeLog.length === 0 ? (
            <div className="text-gray-400 text-sm">No trade log available for this result.</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Commission</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Cash After</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Shares After</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tradeLog.map((trade, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-1.5 text-gray-600">{trade.timestamp}</td>
                    <td className="px-4 py-1.5">
                      <span className={trade.side === 'BUY' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-4 py-1.5 text-right">{Math.abs(trade.qty)}</td>
                    <td className="px-4 py-1.5 text-right">${(trade.price || 0).toFixed(2)}</td>
                    <td className="px-4 py-1.5 text-right">${(trade.commission || 0).toFixed(4)}</td>
                    <td className="px-4 py-1.5 text-right">${(trade.cash_after || 0).toFixed(2)}</td>
                    <td className="px-4 py-1.5 text-right">{trade.shares_after ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default OptimizationResults;
