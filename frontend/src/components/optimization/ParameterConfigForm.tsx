// Parameter Configuration Form Component
// Form for creating optimization configurations

import React, { useState, useEffect } from 'react';
import { useOptimization } from '../../contexts/OptimizationContext';
import {
  CreateConfigRequest,
  ParameterRangeRequest,
  OptimizationCriteriaRequest,
  ConstraintRequest,
  OptimizationMetric,
  ParameterType,
  ParameterTypeInfo,
  ConstraintType,
} from '../../types/optimization';
import {
  OPTIMIZATION_PARAMETERS,
  getParameterById,
  getParametersByCategory,
  getParameterCategories,
} from '../../data/optimizationParameters';

const METRIC_LABELS: Record<string, string> = {
  total_return: 'Total Return',
  sharpe_ratio: 'Sharpe Ratio',
  max_drawdown: 'Max Drawdown',
  volatility: 'Volatility',
  calmar_ratio: 'Calmar Ratio',
  sortino_ratio: 'Sortino Ratio',
  win_rate: 'Win Rate',
  profit_factor: 'Profit Factor',
  trade_count: 'Trade Count',
  avg_trade_duration: 'Avg Trade Duration',
};

function formatMetricLabel(metric: string): string {
  return METRIC_LABELS[metric] || metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

interface ParameterConfigFormProps {
  onConfigCreated?: (configId: string) => void;
  onCancel?: () => void;
}

export const ParameterConfigForm: React.FC<ParameterConfigFormProps> = ({
  onConfigCreated,
  onCancel,
}) => {
  const { createConfig, getMetrics, getParameterTypes, state } = useOptimization();

  // Form state
  const [formData, setFormData] = useState<CreateConfigRequest>({
    name: '',
    ticker: 'AAPL',
    start_date: '',
    end_date: '',
    parameter_ranges: {},
    optimization_criteria: {
      primary_metric: OptimizationMetric.TOTAL_RETURN,
      secondary_metrics: [OptimizationMetric.SHARPE_RATIO],
      minimize: false,
    },
    constraints: [],
  });

  const [availableMetrics, setAvailableMetrics] = useState<OptimizationMetric[]>([]);
  const [availableParameterTypes, setAvailableParameterTypes] = useState<ParameterTypeInfo[]>([]);
  const [parameterTypesLoading, setParameterTypesLoading] = useState(true);
  const [parameterRanges, setParameterRanges] = useState<Record<string, ParameterRangeRequest>>({});
  const [constraints, setConstraints] = useState<ConstraintRequest[]>([]);
  const [selectedParameterId, setSelectedParameterId] = useState<string>('');
  const [parameterCategories] = useState<string[]>(getParameterCategories());
  const [metricWeights, setMetricWeights] = useState<Record<string, number>>({
    [OptimizationMetric.TOTAL_RETURN]: 1.0,
    [OptimizationMetric.SHARPE_RATIO]: 0.5,
  });

  // Get available secondary metrics (excluding primary metric)
  const getAvailableSecondaryMetrics = () => {
    return availableMetrics.filter(
      (metric) => metric !== formData.optimization_criteria.primary_metric,
    );
  };

  // Load metadata on component mount
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        setParameterTypesLoading(true);
        const [metrics, parameterTypes] = await Promise.all([getMetrics(), getParameterTypes()]);
        setAvailableMetrics(metrics);
        setAvailableParameterTypes(parameterTypes);
        setParameterTypesLoading(false);
      } catch (error) {
        console.error('Failed to load metadata:', error);
        setParameterTypesLoading(false);
      }
    };

    loadMetadata();
  }, [getMetrics, getParameterTypes]);

  // Set default dates
  useEffect(() => {
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());

    setFormData((prev) => ({
      ...prev,
      start_date: oneYearAgo.toISOString().split('T')[0],
      end_date: today.toISOString().split('T')[0],
    }));
  }, []);

  // Clean up weights when selected metrics change
  useEffect(() => {
    const selectedMetrics = getAllSelectedMetrics();
    ensureWeightsForMetrics(selectedMetrics);
  }, [
    formData.optimization_criteria.primary_metric,
    formData.optimization_criteria.secondary_metrics,
  ]);

  // Add parameter range from predefined list
  const addParameterRange = () => {
    if (selectedParameterId) {
      const param = getParameterById(selectedParameterId);
      if (param && !parameterRanges[param.id]) {
        setParameterRanges((prev) => ({
          ...prev,
          [param.id]: {
            parameter_type: param.parameter_type as ParameterType,
            min_value: param.default_min,
            max_value: param.default_max,
            step_size: param.default_step,
            name: param.name,
            description: param.description,
          },
        }));
        setSelectedParameterId(''); // Reset selection
      }
    }
  };

  // Update parameter range
  const updateParameterRange = (
    paramName: string,
    field: keyof ParameterRangeRequest,
    value: any,
  ) => {
    setParameterRanges((prev) => ({
      ...prev,
      [paramName]: {
        ...prev[paramName],
        [field]: value,
      },
    }));
  };

  // Remove parameter range
  const removeParameterRange = (paramName: string) => {
    setParameterRanges((prev) => {
      const newRanges = { ...prev };
      delete newRanges[paramName];
      return newRanges;
    });
  };

  // Add constraint
  const addConstraint = () => {
    setConstraints((prev) => [
      ...prev,
      {
        metric: OptimizationMetric.MAX_DRAWDOWN,
        constraint_type: ConstraintType.MAX_VALUE,
        value: -0.1,
        description: '',
      },
    ]);
  };

  // Update constraint
  const updateConstraint = (index: number, field: keyof ConstraintRequest, value: any) => {
    setConstraints((prev) =>
      prev.map((constraint, i) => (i === index ? { ...constraint, [field]: value } : constraint)),
    );
  };

  // Remove constraint
  const removeConstraint = (index: number) => {
    setConstraints((prev) => prev.filter((_, i) => i !== index));
  };

  // Update metric weight
  const updateMetricWeight = (metric: string, weight: number) => {
    setMetricWeights((prev) => ({
      ...prev,
      [metric]: weight,
    }));
  };

  // Ensure weights exist for all selected metrics and remove weights for unselected metrics
  const ensureWeightsForMetrics = (metrics: string[]) => {
    setMetricWeights((prev) => {
      const newWeights: Record<string, number> = {};
      metrics.forEach((metric) => {
        // Keep existing weight or set default
        newWeights[metric] =
          prev[metric] || (metric === formData.optimization_criteria.primary_metric ? 1.0 : 0.5);
      });
      return newWeights;
    });
  };

  // Get all selected metrics (primary + secondary)
  const getAllSelectedMetrics = () => {
    return [
      formData.optimization_criteria.primary_metric,
      ...formData.optimization_criteria.secondary_metrics,
    ];
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Convert the form data to match backend expectations
      const configData = {
        name: formData.name,
        ticker: formData.ticker,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        parameter_ranges: parameterRanges,
        optimization_criteria: {
          primary_metric: formData.optimization_criteria.primary_metric,
          secondary_metrics: formData.optimization_criteria.secondary_metrics,
          constraints: constraints,
          weights: Object.fromEntries(
            Object.entries(metricWeights).filter(([metric]) =>
              getAllSelectedMetrics().includes(metric as OptimizationMetric),
            ),
          ),
          minimize: formData.optimization_criteria.minimize,
          description: '',
        },
        constraints: constraints,
        created_by: '550e8400-e29b-41d4-a716-446655440000', // TODO: Get from auth context
        description: `Optimization for ${formData.ticker}`,
        max_combinations: 1000, // Default limit
        batch_size: 10,
      };

      const config = await createConfig(configData as any);
      onConfigCreated?.((config as any)?.id || 'new-config');
    } catch (error) {
      console.error('Failed to create config:', error);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Optimization Configuration</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Configuration Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., AAPL Volatility Optimization"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Ticker Symbol</label>
            <input
              type="text"
              value={formData.ticker}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, ticker: e.target.value.toUpperCase() }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="AAPL"
              required
            />
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData((prev) => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData((prev) => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        {/* Parameter Ranges */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Optimization Parameters</h3>
            <div className="flex items-center space-x-3">
              <select
                value={selectedParameterId}
                onChange={(e) => setSelectedParameterId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={!selectedParameterId && Object.keys(parameterRanges).length > 0}
              >
                <option value="">Select a parameter to add...</option>
                {parameterCategories.map((category) => (
                  <optgroup
                    key={category}
                    label={category.charAt(0).toUpperCase() + category.slice(1)}
                  >
                    {getParametersByCategory(category).map((param) => (
                      <option key={param.id} value={param.id} disabled={!!parameterRanges[param.id]}>
                        {param.name} - {param.description}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <button
                type="button"
                onClick={addParameterRange}
                disabled={!selectedParameterId}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add Parameter
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {Object.entries(parameterRanges).map(([paramName, range]) => {
              const paramInfo = getParameterById(paramName);
              return (
                <div key={paramName} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{(range as any).name || paramName}</h4>
                      <p className="text-sm text-gray-600 mt-1">{range.description}</p>
                      {paramInfo?.examples && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 font-medium">Examples:</p>
                          <p className="text-xs text-gray-500">{paramInfo.examples.join(', ')}</p>
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => removeParameterRange(paramName)}
                      className="text-red-600 hover:text-red-800 ml-4"
                    >
                      Remove
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                      <select
                        value={range.parameter_type}
                        onChange={(e) =>
                          updateParameterRange(
                            paramName,
                            'parameter_type',
                            e.target.value as ParameterType,
                          )
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {parameterTypesLoading ? (
                          <option value="">Loading parameter types...</option>
                        ) : availableParameterTypes.length === 0 ? (
                          <option value="">No parameter types available</option>
                        ) : (
                          availableParameterTypes.map((type, index) => (
                            <option key={`${type.value}-${index}`} value={type.value}>
                              {type.name} - {type.description}
                            </option>
                          ))
                        )}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Min Value {paramInfo?.unit && `(${paramInfo.unit})`}
                      </label>
                      <input
                        type="number"
                        value={range.min_value}
                        onChange={(e) =>
                          updateParameterRange(paramName, 'min_value', parseFloat(e.target.value))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        step={range.parameter_type === 'integer' ? '1' : '0.01'}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Value {paramInfo?.unit && `(${paramInfo.unit})`}
                      </label>
                      <input
                        type="number"
                        value={range.max_value}
                        onChange={(e) =>
                          updateParameterRange(paramName, 'max_value', parseFloat(e.target.value))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        step={range.parameter_type === 'integer' ? '1' : '0.01'}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Step Size {paramInfo?.unit && `(${paramInfo.unit})`}
                      </label>
                      <input
                        type="number"
                        value={range.step_size}
                        onChange={(e) =>
                          updateParameterRange(paramName, 'step_size', parseFloat(e.target.value))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        step={range.parameter_type === 'integer' ? '1' : '0.01'}
                      />
                    </div>
                  </div>

                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <input
                      type="text"
                      value={range.description || ''}
                      onChange={(e) =>
                        updateParameterRange(paramName, 'description', e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Trigger threshold percentage"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Optimization Criteria */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Criteria</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Primary Metric</label>
              <select
                value={formData.optimization_criteria.primary_metric}
                onChange={(e) => {
                  const newPrimaryMetric = e.target.value as OptimizationMetric;
                  setFormData((prev) => {
                    const newFormData = {
                      ...prev,
                      optimization_criteria: {
                        ...prev.optimization_criteria,
                        primary_metric: newPrimaryMetric,
                        // Remove the new primary metric from secondary metrics if it exists
                        secondary_metrics: prev.optimization_criteria.secondary_metrics.filter(
                          (metric) => metric !== newPrimaryMetric,
                        ),
                      },
                    };

                    // Update weights for the new metric selection
                    const allMetrics = [
                      newPrimaryMetric,
                      ...newFormData.optimization_criteria.secondary_metrics,
                    ];
                    ensureWeightsForMetrics(allMetrics);

                    return newFormData;
                  });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableMetrics.map((metric, index) => (
                  <option key={`${metric}-${index}`} value={metric}>
                    {formatMetricLabel(metric)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Minimize</label>
              <input
                type="checkbox"
                checked={formData.optimization_criteria.minimize}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    optimization_criteria: {
                      ...prev.optimization_criteria,
                      minimize: e.target.checked,
                    },
                  }))
                }
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Minimize instead of maximize</span>
            </div>
          </div>

          {/* Secondary Metrics */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Secondary Metrics <span className="text-red-500">*</span>
              <span className="text-xs text-gray-400 ml-1">(at least one required)</span>
            </label>
            <div className="space-y-2">
              {formData.optimization_criteria.secondary_metrics.map((metric, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {formatMetricLabel(metric)}
                  </span>
                  <button
                    type="button"
                    disabled={formData.optimization_criteria.secondary_metrics.length <= 1}
                    onClick={() => {
                      setFormData((prev) => {
                        const newFormData = {
                          ...prev,
                          optimization_criteria: {
                            ...prev.optimization_criteria,
                            secondary_metrics: prev.optimization_criteria.secondary_metrics.filter(
                              (_, i) => i !== index,
                            ),
                          },
                        };

                        // Update weights for the new metric selection
                        const allMetrics = [
                          newFormData.optimization_criteria.primary_metric,
                          ...newFormData.optimization_criteria.secondary_metrics,
                        ];
                        ensureWeightsForMetrics(allMetrics);

                        return newFormData;
                      });
                    }}
                    className="text-red-600 hover:text-red-800 text-sm disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <select
                value=""
                onChange={(e) => {
                  const newMetric = e.target.value as OptimizationMetric;
                  if (
                    newMetric &&
                    !formData.optimization_criteria.secondary_metrics.includes(newMetric)
                  ) {
                    setFormData((prev) => {
                      const newFormData = {
                        ...prev,
                        optimization_criteria: {
                          ...prev.optimization_criteria,
                          secondary_metrics: [
                            ...prev.optimization_criteria.secondary_metrics,
                            newMetric,
                          ],
                        },
                      };

                      // Update weights for the new metric selection
                      const allMetrics = [
                        newFormData.optimization_criteria.primary_metric,
                        ...newFormData.optimization_criteria.secondary_metrics,
                      ];
                      ensureWeightsForMetrics(allMetrics);

                      return newFormData;
                    });
                  }
                  e.target.value = ''; // Reset selection
                }}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Add secondary metric...</option>
                {getAvailableSecondaryMetrics().map((metric, index) => (
                  <option key={`${metric}-${index}`} value={metric}>
                    {formatMetricLabel(metric)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Metric Weights */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Metric Weights</label>
            <div className="space-y-3">
              {getAllSelectedMetrics().map((metric) => (
                <div key={metric} className="flex items-center space-x-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700">
                      {metric === formData.optimization_criteria.primary_metric ? (
                        <span>
                          {formatMetricLabel(metric)} <span className="text-blue-600">(Primary)</span>
                        </span>
                      ) : (
                        <span>
                          {formatMetricLabel(metric)} <span className="text-gray-500">(Secondary)</span>
                        </span>
                      )}
                    </label>
                  </div>
                  <div className="w-24">
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.1"
                      value={metricWeights[metric] || 0}
                      onChange={(e) => updateMetricWeight(metric, parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.0"
                    />
                  </div>
                  <div className="w-16 text-sm text-gray-500">{metricWeights[metric] || 0}x</div>
                </div>
              ))}
              {getAllSelectedMetrics().length === 0 && (
                <p className="text-sm text-gray-500 italic">
                  Select primary and secondary metrics to configure weights
                </p>
              )}
            </div>
            <div className="mt-2 text-xs text-gray-500">
              <p>• Primary metric typically has weight 1.0</p>
              <p>• Secondary metrics usually have weights 0.1-0.5</p>
              <p>• Higher weights = more influence on optimization score</p>
            </div>
          </div>
        </div>

        {/* Constraints */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Constraints</h3>
            <button
              type="button"
              onClick={addConstraint}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              Add Constraint
            </button>
          </div>

          <div className="space-y-4">
            {constraints.map((constraint, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium text-gray-900">Constraint {index + 1}</h4>
                  <button
                    type="button"
                    onClick={() => removeConstraint(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Metric</label>
                    <select
                      value={constraint.metric}
                      onChange={(e) =>
                        updateConstraint(index, 'metric', e.target.value as OptimizationMetric)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {availableMetrics.map((metric, index) => (
                        <option key={`constraint-${metric}-${index}`} value={metric}>
                          {formatMetricLabel(metric)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      value={constraint.constraint_type}
                      onChange={(e) =>
                        updateConstraint(index, 'constraint_type', e.target.value as ConstraintType)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={ConstraintType.MAX_VALUE}>Max Value</option>
                      <option value={ConstraintType.MIN_VALUE}>Min Value</option>
                      <option value={ConstraintType.EQUAL_TO}>Equal To</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Value</label>
                    <input
                      type="number"
                      value={constraint.value}
                      onChange={(e) => updateConstraint(index, 'value', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      step="0.01"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {state.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{state.error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end space-x-4">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
          )}

          <button
            type="submit"
            disabled={state.loading || Object.keys(parameterRanges).length === 0}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {state.loading ? 'Creating...' : 'Create Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ParameterConfigForm;
