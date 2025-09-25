// Optimization Results Component
// Displays optimization results in a table format with sorting and filtering

import React, { useState, useMemo } from 'react';
import { OptimizationResult, OptimizationMetric } from '../../types/optimization';

interface OptimizationResultsProps {
  results: OptimizationResult[];
  loading?: boolean;
  onResultClick?: (result: OptimizationResult) => void;
}

type SortField =
  | 'sharpe_ratio'
  | 'total_return'
  | 'max_drawdown'
  | 'volatility'
  | 'win_rate'
  | 'trade_count';
type SortDirection = 'asc' | 'desc';

export const OptimizationResults: React.FC<OptimizationResultsProps> = ({
  results,
  loading = false,
  onResultClick,
}) => {
  const [sortField, setSortField] = useState<SortField>('sharpe_ratio');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filterMetric, setFilterMetric] = useState<OptimizationMetric | 'all'>('all');
  const [filterValue, setFilterValue] = useState<string>('');

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
        return value > 0.1 ? 'text-green-600' : value > 0 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.MAX_DRAWDOWN:
        return value > -0.05 ? 'text-green-600' : value > -0.1 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.VOLATILITY:
        return value < 0.1 ? 'text-green-600' : value < 0.2 ? 'text-yellow-600' : 'text-red-600';
      case OptimizationMetric.TRADE_COUNT:
        return value > 50 ? 'text-green-600' : value > 20 ? 'text-yellow-600' : 'text-red-600';
      default:
        return 'text-gray-900';
    }
  };

  // Sort indicator
  const SortIndicator: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) return null;
    return <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
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
              <option value={OptimizationMetric.SHARPE_RATIO}>Sharpe Ratio ≥</option>
              <option value={OptimizationMetric.TOTAL_RETURN}>Total Return ≥</option>
              <option value={OptimizationMetric.WIN_RATE}>Win Rate ≥</option>
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
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('sharpe_ratio')}
                >
                  Sharpe Ratio
                  <SortIndicator field="sharpe_ratio" />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('total_return')}
                >
                  Total Return
                  <SortIndicator field="total_return" />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('max_drawdown')}
                >
                  Max Drawdown
                  <SortIndicator field="max_drawdown" />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('volatility')}
                >
                  Volatility
                  <SortIndicator field="volatility" />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('win_rate')}
                >
                  Win Rate
                  <SortIndicator field="win_rate" />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('trade_count')}
                >
                  Trades
                  <SortIndicator field="trade_count" />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parameters
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {processedResults.map((result, index) => (
                <tr
                  key={result.id}
                  className={`hover:bg-gray-50 ${onResultClick ? 'cursor-pointer' : ''}`}
                  onClick={() => onResultClick?.(result)}
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
    </div>
  );
};

export default OptimizationResults;
