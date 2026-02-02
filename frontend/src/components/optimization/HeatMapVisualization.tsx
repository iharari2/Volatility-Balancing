// Heat Map Visualization Component
// Displays optimization results as a 2D heatmap with parameter values on X and Y axes

import React, { useState, useEffect, useMemo } from 'react';
import { useOptimization } from '../../contexts/OptimizationContext';
import { HeatmapData, OptimizationMetric } from '../../types/optimization';

interface HeatMapVisualizationProps {
  configId: string;
  availableParameters: string[];
  onCellClick?: (x: number, y: number, value: number) => void;
}

const METRIC_OPTIONS: { value: OptimizationMetric; label: string }[] = [
  { value: OptimizationMetric.SHARPE_RATIO, label: 'Sharpe Ratio' },
  { value: OptimizationMetric.TOTAL_RETURN, label: 'Total Return' },
  { value: OptimizationMetric.MAX_DRAWDOWN, label: 'Max Drawdown' },
  { value: OptimizationMetric.VOLATILITY, label: 'Volatility' },
  { value: OptimizationMetric.CALMAR_RATIO, label: 'Calmar Ratio' },
  { value: OptimizationMetric.WIN_RATE, label: 'Win Rate' },
];

export const HeatMapVisualization: React.FC<HeatMapVisualizationProps> = ({
  configId,
  availableParameters,
  onCellClick,
}) => {
  const { getHeatmap } = useOptimization();
  const [xParameter, setXParameter] = useState<string>(availableParameters[0] || '');
  const [yParameter, setYParameter] = useState<string>(availableParameters[1] || '');
  const [metric, setMetric] = useState<OptimizationMetric>(OptimizationMetric.SHARPE_RATIO);
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCell, setHoveredCell] = useState<{ x: number; y: number } | null>(null);

  // Load heatmap data when parameters change
  useEffect(() => {
    if (!xParameter || !yParameter || xParameter === yParameter) {
      return;
    }

    const loadHeatmap = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getHeatmap(configId, xParameter, yParameter, metric);
        setHeatmapData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load heatmap data');
        setHeatmapData(null);
      } finally {
        setLoading(false);
      }
    };

    loadHeatmap();
  }, [configId, xParameter, yParameter, metric, getHeatmap]);

  // Calculate color for a cell based on its value
  const getCellColor = useMemo(() => {
    if (!heatmapData || !heatmapData.statistics) {
      return () => 'bg-gray-200';
    }

    const { min, max } = heatmapData.statistics;
    const range = max - min || 1;

    return (value: number | null, isValid: boolean) => {
      if (!isValid || value === null) {
        return 'bg-gray-300';
      }

      // Normalize value to 0-1
      const normalized = (value - min) / range;

      // For metrics where higher is better (sharpe, return, win rate)
      const isHigherBetter = [
        OptimizationMetric.SHARPE_RATIO,
        OptimizationMetric.TOTAL_RETURN,
        OptimizationMetric.CALMAR_RATIO,
        OptimizationMetric.WIN_RATE,
      ].includes(metric);

      // For max drawdown and volatility, lower is better
      const adjustedNormalized = isHigherBetter ? normalized : 1 - normalized;

      // Color gradient from red (bad) to yellow to green (good)
      if (adjustedNormalized < 0.33) {
        return 'bg-red-400 hover:bg-red-500';
      } else if (adjustedNormalized < 0.66) {
        return 'bg-yellow-400 hover:bg-yellow-500';
      } else {
        return 'bg-green-400 hover:bg-green-500';
      }
    };
  }, [heatmapData, metric]);

  // Format metric value for display
  const formatValue = (value: number | null, metricType: OptimizationMetric): string => {
    if (value === null || value === undefined) return 'N/A';

    switch (metricType) {
      case OptimizationMetric.TOTAL_RETURN:
      case OptimizationMetric.MAX_DRAWDOWN:
      case OptimizationMetric.VOLATILITY:
      case OptimizationMetric.WIN_RATE:
        return `${(value * 100).toFixed(1)}%`;
      case OptimizationMetric.SHARPE_RATIO:
      case OptimizationMetric.CALMAR_RATIO:
        return value.toFixed(2);
      default:
        return value.toFixed(3);
    }
  };

  // Build 2D grid from cells
  const grid = useMemo(() => {
    if (!heatmapData || !heatmapData.cells) {
      return null;
    }

    // Derive x_values and y_values from cells if not provided
    const xValues: number[] = heatmapData.x_values || [...new Set(heatmapData.cells.map(c => c.x_value))].sort((a, b) => a - b);
    const yValues: number[] = heatmapData.y_values || [...new Set(heatmapData.cells.map(c => c.y_value))].sort((a, b) => a - b);

    // Create a map for quick lookup
    const cellMap = new Map<string, (typeof heatmapData.cells)[0]>();
    for (const cell of heatmapData.cells) {
      const key = `${cell.x_value}-${cell.y_value}`;
      cellMap.set(key, cell);
    }

    return {
      xValues,
      yValues,
      cellMap,
    };
  }, [heatmapData]);

  if (availableParameters.length < 2) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Heat Map Visualization</h3>
        <p className="text-gray-500">
          At least 2 parameters are required to generate a heatmap visualization.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Heat Map Visualization</h3>

      {/* Parameter Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">X-Axis Parameter</label>
          <select
            value={xParameter}
            onChange={(e) => setXParameter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {availableParameters.map((param) => (
              <option key={param} value={param} disabled={param === yParameter}>
                {param}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Y-Axis Parameter</label>
          <select
            value={yParameter}
            onChange={(e) => setYParameter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {availableParameters.map((param) => (
              <option key={param} value={param} disabled={param === xParameter}>
                {param}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Metric</label>
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value as OptimizationMetric)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {METRIC_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading heatmap data...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Heatmap Grid */}
      {!loading && grid && (
        <div className="overflow-x-auto">
          {/* Legend */}
          <div className="flex items-center justify-end mb-4 gap-2">
            <span className="text-xs text-gray-500">Low</span>
            <div className="flex">
              <div className="w-6 h-4 bg-red-400"></div>
              <div className="w-6 h-4 bg-yellow-400"></div>
              <div className="w-6 h-4 bg-green-400"></div>
            </div>
            <span className="text-xs text-gray-500">High</span>
          </div>

          {/* Grid */}
          <div className="inline-block">
            {/* X-axis labels */}
            <div className="flex">
              <div className="w-20 h-8"></div>
              {grid.xValues.map((xVal: number) => (
                <div
                  key={xVal}
                  className="w-12 h-8 flex items-center justify-center text-xs font-medium text-gray-600"
                >
                  {xVal.toFixed(2)}
                </div>
              ))}
            </div>

            {/* Grid rows */}
            {grid.yValues.map((yVal: number) => (
              <div key={yVal} className="flex">
                {/* Y-axis label */}
                <div className="w-20 h-12 flex items-center justify-end pr-2 text-xs font-medium text-gray-600">
                  {yVal.toFixed(2)}
                </div>

                {/* Cells */}
                {grid.xValues.map((xVal: number) => {
                  const key = `${xVal}-${yVal}`;
                  const cell = grid.cellMap.get(key);
                  const value = cell?.metric_value ?? null;
                  const isValid = cell ? (cell.is_valid ?? true) : false;
                  const isHovered =
                    hoveredCell?.x === xVal && hoveredCell?.y === yVal;

                  return (
                    <div
                      key={key}
                      className={`w-12 h-12 border border-white cursor-pointer transition-all ${getCellColor(
                        value,
                        isValid,
                      )} ${isHovered ? 'ring-2 ring-blue-500 z-10' : ''}`}
                      onMouseEnter={() => setHoveredCell({ x: xVal as number, y: yVal as number })}
                      onMouseLeave={() => setHoveredCell(null)}
                      onClick={() => value !== null && onCellClick?.(xVal as number, yVal as number, value)}
                      title={`${xParameter}: ${xVal}, ${yParameter}: ${yVal}\n${
                        METRIC_OPTIONS.find((m) => m.value === metric)?.label
                      }: ${formatValue(value, metric)}`}
                    >
                      <div className="w-full h-full flex items-center justify-center text-xs font-medium text-white opacity-0 hover:opacity-100">
                        {formatValue(value, metric)}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* X-axis label */}
          <div className="text-center mt-2 text-sm font-medium text-gray-700">{xParameter}</div>
        </div>
      )}

      {/* Y-axis label (rotated) */}
      {!loading && grid && (
        <div className="absolute left-0 top-1/2 transform -rotate-90 -translate-x-1/2 text-sm font-medium text-gray-700">
          {yParameter}
        </div>
      )}

      {/* Statistics */}
      {heatmapData?.statistics && (
        <div className="mt-6 grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-gray-500">Min</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatValue(heatmapData.statistics.min, metric)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-gray-500">Max</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatValue(heatmapData.statistics.max, metric)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-gray-500">Mean</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatValue(heatmapData.statistics.mean, metric)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-gray-500">Median</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatValue(heatmapData.statistics.median, metric)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-gray-500">Std Dev</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatValue(heatmapData.statistics.std_dev, metric)}
            </div>
          </div>
        </div>
      )}

      {/* No Data State */}
      {!loading && !error && !heatmapData && xParameter && yParameter && xParameter !== yParameter && (
        <div className="text-center py-12 text-gray-500">
          No heatmap data available. Run the optimization first.
        </div>
      )}
    </div>
  );
};

export default HeatMapVisualization;
