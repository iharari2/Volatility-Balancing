import { useState, useEffect, useCallback } from 'react';
import { useOptimization } from '../../contexts/OptimizationContext';
import { ParameterConfigForm } from '../../components/optimization/ParameterConfigForm';
import { OptimizationResults } from '../../components/optimization/OptimizationResults';
import { OptimizationProgress } from '../../components/optimization/OptimizationProgress';
import { HeatMapVisualization } from '../../components/optimization/HeatMapVisualization';
import {
  OptimizationConfig,
  OptimizationStatus,
} from '../../types/optimization';
import { optimizationApi } from '../../services/optimizationApi';
import { Plus, Play, BarChart3, Grid3X3, RefreshCw, ChevronLeft } from 'lucide-react';

type ViewMode = 'list' | 'create' | 'results' | 'heatmap';

export default function OptimizationPage() {
  const { state, startOptimization, getResults } = useOptimization();
  const [configs, setConfigs] = useState<OptimizationConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedConfig, setSelectedConfig] = useState<OptimizationConfig | null>(null);
  const [startingId, setStartingId] = useState<string | null>(null);

  const loadConfigs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await optimizationApi.getAllConfigs();
      setConfigs(data as OptimizationConfig[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configurations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfigs();
  }, [loadConfigs]);

  const handleConfigCreated = () => {
    setViewMode('list');
    loadConfigs();
  };

  const handleStart = async (config: OptimizationConfig) => {
    try {
      setStartingId(config.id);
      await startOptimization(config.id);
      await loadConfigs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start optimization');
    } finally {
      setStartingId(null);
    }
  };

  const handleViewResults = async (config: OptimizationConfig) => {
    setSelectedConfig(config);
    await getResults(config.id);
    setViewMode('results');
  };

  const handleViewHeatmap = (config: OptimizationConfig) => {
    setSelectedConfig(config);
    setViewMode('heatmap');
  };

  const handleProgressComplete = () => {
    loadConfigs();
  };

  const getStatusBadge = (status: OptimizationStatus) => {
    const styles: Record<OptimizationStatus, string> = {
      [OptimizationStatus.DRAFT]: 'bg-gray-100 text-gray-600',
      [OptimizationStatus.PENDING]: 'bg-gray-100 text-gray-700',
      [OptimizationStatus.RUNNING]: 'bg-blue-100 text-blue-700',
      [OptimizationStatus.COMPLETED]: 'bg-green-100 text-green-700',
      [OptimizationStatus.FAILED]: 'bg-red-100 text-red-700',
      [OptimizationStatus.CANCELLED]: 'bg-yellow-100 text-yellow-700',
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const availableParameters = selectedConfig?.parameter_ranges
    ? Object.keys(selectedConfig.parameter_ranges)
    : [];

  // Running configs that have progress info
  const runningConfigs = configs.filter(
    (c) => c.status === OptimizationStatus.RUNNING || c.status === OptimizationStatus.PENDING,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          {viewMode !== 'list' && (
            <button
              onClick={() => { setViewMode('list'); setSelectedConfig(null); }}
              className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-1"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back to Configurations
            </button>
          )}
          <h1 className="text-2xl font-bold text-gray-900">
            {viewMode === 'list' && 'Parameter Optimization'}
            {viewMode === 'create' && 'New Configuration'}
            {viewMode === 'results' && `Results: ${selectedConfig?.name}`}
            {viewMode === 'heatmap' && `Heatmap: ${selectedConfig?.name}`}
          </h1>
          {viewMode === 'list' && (
            <p className="text-sm text-gray-500 mt-1">
              Create and manage parameter optimization configurations
            </p>
          )}
        </div>

        {viewMode === 'list' && (
          <div className="flex items-center gap-3">
            <button
              onClick={loadConfigs}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Refresh"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
            <button
              onClick={() => setViewMode('create')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
            >
              <Plus className="h-4 w-4" />
              New Config
            </button>
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-500 text-xs mt-1 hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Running optimizations progress */}
      {runningConfigs.map((config) => {
        const progress = state.activeOptimizations.get(config.id);
        if (!progress) return null;
        return (
          <OptimizationProgress
            key={config.id}
            configId={config.id}
            progress={progress}
            onComplete={handleProgressComplete}
          />
        );
      })}

      {/* View: Config List */}
      {viewMode === 'list' && (
        <div>
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              <span className="ml-3 text-gray-500">Loading configurations...</span>
            </div>
          ) : configs.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <Grid3X3 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No configurations yet</h3>
              <p className="text-gray-500 mb-6">
                Create your first optimization configuration to explore parameter combinations.
              </p>
              <button
                onClick={() => setViewMode('create')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
              >
                <Plus className="h-4 w-4" />
                Create Configuration
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {configs.map((config) => (
                <div
                  key={config.id}
                  className="bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-base font-semibold text-gray-900 truncate">
                          {config.name}
                        </h3>
                        {getStatusBadge(config.status)}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="font-medium text-gray-700">{config.ticker}</span>
                        <span>
                          {config.start_date.split('T')[0]} to {config.end_date.split('T')[0]}
                        </span>
                        <span>
                          {Object.keys(config.parameter_ranges || {}).length} parameters
                        </span>
                        <span>{config.total_combinations} combinations</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {(config.status === OptimizationStatus.DRAFT ||
                        config.status === OptimizationStatus.PENDING ||
                        config.status === OptimizationStatus.FAILED) && (
                        <button
                          onClick={() => handleStart(config)}
                          disabled={startingId === config.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium disabled:opacity-50"
                        >
                          <Play className="h-3.5 w-3.5" />
                          {startingId === config.id ? 'Starting...' : 'Start'}
                        </button>
                      )}
                      {config.status === OptimizationStatus.COMPLETED && (
                        <>
                          <button
                            onClick={() => handleViewResults(config)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                          >
                            <BarChart3 className="h-3.5 w-3.5" />
                            Results
                          </button>
                          <button
                            onClick={() => handleViewHeatmap(config)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm font-medium"
                          >
                            <Grid3X3 className="h-3.5 w-3.5" />
                            Heatmap
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* View: Create Config */}
      {viewMode === 'create' && (
        <ParameterConfigForm
          onConfigCreated={handleConfigCreated}
          onCancel={() => setViewMode('list')}
        />
      )}

      {/* View: Results */}
      {viewMode === 'results' && selectedConfig && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleViewHeatmap(selectedConfig)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm font-medium"
            >
              <Grid3X3 className="h-3.5 w-3.5" />
              View Heatmap
            </button>
          </div>
          <OptimizationResults
            results={state.results.get(selectedConfig.id) || []}
            loading={state.loading}
            configId={selectedConfig.id}
          />
        </div>
      )}

      {/* View: Heatmap */}
      {viewMode === 'heatmap' && selectedConfig && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleViewResults(selectedConfig)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              View Results
            </button>
          </div>
          <HeatMapVisualization
            configId={selectedConfig.id}
            availableParameters={availableParameters}
          />
        </div>
      )}
    </div>
  );
}
