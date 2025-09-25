// Main Optimization Page
// Dashboard for parameter optimization system

import React, { useState, useEffect } from 'react';
import { useOptimization } from '../contexts/OptimizationContext';
import ParameterConfigForm from '../components/optimization/ParameterConfigForm';
import OptimizationResults from '../components/optimization/OptimizationResults';
import OptimizationProgress from '../components/optimization/OptimizationProgress';
import { OptimizationConfig, OptimizationResult } from '../types/optimization';

export const Optimization: React.FC = () => {
  const { state, getResults, clearError, startOptimization } = useOptimization();
  const [showConfigForm, setShowConfigForm] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<OptimizationConfig | null>(null);
  const [selectedResults, setSelectedResults] = useState<OptimizationResult[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);

  // Load results when a config is selected
  useEffect(() => {
    if (selectedConfig) {
      setLoadingResults(true);
      getResults(selectedConfig.id)
        .then((results) => {
          setSelectedResults(results);
        })
        .finally(() => {
          setLoadingResults(false);
        });
    }
  }, [selectedConfig, getResults]);

  // Handle config creation
  const handleConfigCreated = (configId: string) => {
    setShowConfigForm(false);
    // Find the created config and select it
    const config = state.configs.find((c) => c.id === configId);
    if (config) {
      setSelectedConfig(config);
    }
  };

  // Handle config selection
  const handleConfigSelect = (config: OptimizationConfig) => {
    setSelectedConfig(config);
  };

  // Handle result click
  const handleResultClick = (result: OptimizationResult) => {
    console.log('Result clicked:', result);
    // TODO: Navigate to detailed result view
  };

  // Get active optimizations
  const activeOptimizations = Array.from(state.activeOptimizations.values());

  // Derive the latest selected config (including live status updates)
  const currentSelectedConfig = selectedConfig
    ? state.configs.find((c) => c.id === selectedConfig.id) || selectedConfig
    : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Parameter Optimization</h1>
          <p className="mt-2 text-gray-600">
            Optimize trading parameters to find the best performing strategies
          </p>
        </div>

        {/* Error Display */}
        {state.error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{state.error}</div>
                <div className="mt-4">
                  <button
                    onClick={clearError}
                    className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Active Optimizations */}
        {activeOptimizations.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Optimizations</h2>
            <div className="space-y-4">
              {activeOptimizations.map((progress) => (
                <OptimizationProgress
                  key={progress.config_id}
                  configId={progress.config_id}
                  progress={progress}
                  onComplete={() => {
                    // Refresh results if this is the selected config
                    if (selectedConfig && selectedConfig.id === progress.config_id) {
                      getResults(selectedConfig.id).then(setSelectedResults);
                    }
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Configuration Form */}
        {showConfigForm && (
          <div className="mb-8">
            <ParameterConfigForm
              onConfigCreated={handleConfigCreated}
              onCancel={() => setShowConfigForm(false)}
            />
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Configurations */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Configurations</h2>
                  <button
                    onClick={() => setShowConfigForm(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    New Configuration
                  </button>
                </div>

                {state.configs.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-500 text-lg mb-2">No configurations yet</div>
                    <div className="text-gray-400 text-sm">
                      Create your first optimization configuration
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {state.configs.map((config) => (
                      <div
                        key={config.id}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          selectedConfig?.id === config.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                        onClick={() => handleConfigSelect(config)}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-medium text-gray-900">{config.name}</h3>
                            <p className="text-sm text-gray-500">{config.ticker}</p>
                            <p className="text-xs text-gray-400">
                              {config.total_combinations} combinations
                            </p>
                          </div>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              config.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : config.status === 'running'
                                ? 'bg-blue-100 text-blue-800'
                                : config.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {config.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2">
            {currentSelectedConfig ? (
              <div>
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Results for {currentSelectedConfig.name}
                  </h2>
                  <div className="text-sm text-gray-600">
                    {currentSelectedConfig.ticker} • {currentSelectedConfig.start_date} to{' '}
                    {currentSelectedConfig.end_date}
                  </div>
                  {/* Start Optimization Action */}
                  {currentSelectedConfig.status !== 'running' && currentSelectedConfig.status !== 'completed' && (
                    <div className="mt-4">
                      <button
                        onClick={async () => {
                          await startOptimization(currentSelectedConfig.id);
                          // Results will be polled via context; fetch once as well
                          getResults(currentSelectedConfig.id).then(setSelectedResults);
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        Start Optimization
                      </button>
                    </div>
                  )}
                </div>

                <OptimizationResults
                  results={selectedResults}
                  loading={loadingResults}
                  onResultClick={handleResultClick}
                />
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 text-center">
                  <div className="text-gray-500 text-lg mb-2">Select a configuration</div>
                  <div className="text-gray-400 text-sm">
                    Choose a configuration from the left to view optimization results
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        {state.configs.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Total Configurations</div>
              <div className="text-2xl font-bold text-gray-900">{state.configs.length}</div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Completed</div>
              <div className="text-2xl font-bold text-green-600">
                {state.configs.filter((c) => c.status === 'completed').length}
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Running</div>
              <div className="text-2xl font-bold text-blue-600">
                {state.configs.filter((c) => c.status === 'running').length}
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Total Combinations</div>
              <div className="text-2xl font-bold text-purple-600">
                {state.configs.reduce((sum, c) => sum + c.total_combinations, 0)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Optimization;
