// Optimization Progress Component
// Shows real-time progress of running optimizations

import React, { useEffect, useState } from 'react';
import { OptimizationProgress as ProgressType } from '../../types/optimization';

interface OptimizationProgressProps {
  configId: string;
  progress: ProgressType;
  onComplete?: () => void;
}

export const OptimizationProgress: React.FC<OptimizationProgressProps> = ({
  configId,
  progress,
  onComplete,
}) => {
  const [isVisible, setIsVisible] = useState(true);

  // Check if optimization is complete
  useEffect(() => {
    if (
      progress.status === 'completed' ||
      progress.status === 'failed' ||
      progress.status === 'cancelled'
    ) {
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        setIsVisible(false);
        onComplete?.();
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [progress.status, onComplete]);

  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'cancelled':
        return 'text-yellow-600 bg-yellow-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'pending':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'cancelled':
        return '⏹️';
      case 'running':
        return '🔄';
      case 'pending':
        return '⏳';
      default:
        return '❓';
    }
  };

  // Format time remaining
  const formatTimeRemaining = (timeString?: string): string => {
    if (!timeString) return 'Calculating...';

    try {
      const time = new Date(timeString);
      const now = new Date();
      const diff = time.getTime() - now.getTime();

      if (diff <= 0) return 'Almost done...';

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);

      if (minutes > 0) {
        return `${minutes}m ${seconds}s remaining`;
      } else {
        return `${seconds}s remaining`;
      }
    } catch {
      return 'Calculating...';
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border-l-4 border-blue-500">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{getStatusIcon(progress.status)}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Optimization Progress</h3>
              <p className="text-sm text-gray-500">Configuration ID: {configId.slice(0, 8)}...</p>
            </div>
          </div>

          <div
            className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
              progress.status,
            )}`}
          >
            {progress.status.toUpperCase()}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progress.progress_percentage.toFixed(1)}%</span>
          </div>

          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${Math.min(100, Math.max(0, progress.progress_percentage))}%` }}
            />
          </div>
        </div>

        {/* Progress Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Completed</div>
            <div className="text-2xl font-bold text-blue-600">
              {progress.completed_combinations}
            </div>
            <div className="text-xs text-gray-400">
              of {progress.total_combinations} combinations
            </div>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Remaining</div>
            <div className="text-2xl font-bold text-orange-600">
              {progress.total_combinations - progress.completed_combinations}
            </div>
            <div className="text-xs text-gray-400">combinations</div>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Estimated Time</div>
            <div className="text-lg font-bold text-green-600">
              {formatTimeRemaining(progress.estimated_completion_time)}
            </div>
            <div className="text-xs text-gray-400">remaining</div>
          </div>
        </div>

        {/* Current Combination */}
        {progress.current_combination && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-blue-900 mb-2">Currently Testing:</div>
            <div className="text-sm text-blue-800">
              {Object.entries(progress.current_combination.parameters).map(([key, value]) => (
                <span key={key} className="inline-block mr-4">
                  <span className="font-medium">{key}:</span> {value}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Status Messages */}
        {progress.status === 'completed' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Optimization Complete!</h3>
                <div className="mt-2 text-sm text-green-700">
                  All {progress.total_combinations} parameter combinations have been tested. You can
                  now view the results and analysis.
                </div>
              </div>
            </div>
          </div>
        )}

        {progress.status === 'failed' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Optimization Failed</h3>
                <div className="mt-2 text-sm text-red-700">
                  The optimization encountered an error. Please check the configuration and try
                  again.
                </div>
              </div>
            </div>
          </div>
        )}

        {progress.status === 'cancelled' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Optimization Cancelled</h3>
                <div className="mt-2 text-sm text-yellow-700">
                  The optimization was cancelled. {progress.completed_combinations} combinations
                  were completed.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 mt-4">
          {progress.status === 'completed' && (
            <button
              onClick={() => setIsVisible(false)}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              View Results
            </button>
          )}

          {(progress.status === 'failed' || progress.status === 'cancelled') && (
            <button
              onClick={() => setIsVisible(false)}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Dismiss
            </button>
          )}

          {progress.status === 'running' && (
            <button
              onClick={() => setIsVisible(false)}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Hide
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default OptimizationProgress;
