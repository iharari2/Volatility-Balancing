import React, { useState, useEffect } from 'react';
import { simulationProgressApi } from '../lib/api';
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';

interface SimulationProgressBarProps {
  simulationId: string | null;
  onComplete?: () => void;
  onError?: (error: string) => void;
  className?: string;
  show?: boolean;
}

interface ProgressData {
  simulation_id: string;
  status: string;
  progress: number;
  message: string;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  start_time?: string;
  end_time?: string;
  error?: string;
}

export default function SimulationProgressBar({
  simulationId,
  onComplete,
  onError,
  className = '',
  show = true,
}: SimulationProgressBarProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!simulationId) {
      setProgress(null);
      setIsPolling(false);
      setError(null);
      return;
    }

    setIsPolling(true);
    setError(null);

    // Simulate realistic progress when no real progress data is available
    let progressValue = 0.1; // Start at 10%
    const progressMessages = [
      'Initializing simulation...',
      'Fetching market data...',
      'Processing historical prices...',
      'Calculating volatility triggers...',
      'Running algorithm simulation...',
      'Generating trade analysis...',
      'Computing performance metrics...',
      'Finalizing results...',
    ];

    let messageIndex = 0;
    let hasRealProgress = false;
    const progressInterval = setInterval(() => {
      // Only use simulated progress if we don't have real progress data
      if (!hasRealProgress && progressValue < 0.9) {
        progressValue += 0.1;
        messageIndex = Math.min(
          Math.floor(progressValue * progressMessages.length),
          progressMessages.length - 1,
        );

        setProgress({
          simulation_id: simulationId,
          status: 'processing',
          progress: progressValue,
          message: progressMessages[messageIndex],
          current_step: 'simulation',
          total_steps: 8,
          completed_steps: Math.floor(progressValue * 8),
          start_time: new Date().toISOString(),
        });
      }
    }, 500); // Update every 500ms for simulated progress

    const pollProgress = async () => {
      try {
        const progressData = await simulationProgressApi.getProgress(simulationId);
        if (progressData) {
          // Stop simulated progress and use real progress data
          hasRealProgress = true;
          clearInterval(progressInterval);
          setProgress(progressData);

          if (progressData.status === 'completed') {
            setIsPolling(false);
            onComplete?.();
          } else if (progressData.status === 'error') {
            setIsPolling(false);
            setError(progressData.error || 'Unknown error');
            onError?.(progressData.error || 'Unknown error');
          }
        }
      } catch (err) {
        // If no real progress data, continue with simulated progress
        console.log('No real progress data available, using simulated progress');
      }
    };

    // Poll for real progress data more frequently for better responsiveness
    const pollInterval = setInterval(pollProgress, 500);

    return () => {
      clearInterval(progressInterval);
      clearInterval(pollInterval);
      setIsPolling(false);
    };
  }, [simulationId, onComplete, onError]);

  // Show progress bar if show prop is true
  if (!show) {
    return null;
  }

  // Show loading state when simulationId exists but progress data hasn't been fetched yet
  if (!progress) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            <h3 className="text-lg font-semibold text-gray-900">Running Simulation...</h3>
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-500 h-2.5 rounded-full animate-pulse"
            style={{ width: '30%' }}
          ></div>
        </div>
        <div className="flex justify-between text-sm text-gray-600 mt-2">
          <span>Processing simulation data...</span>
          <span>30%</span>
        </div>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (progress.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'initializing':
      case 'fetching_data':
      case 'processing':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (progress.status) {
      case 'completed':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'initializing':
      case 'fetching_data':
      case 'processing':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return '';

    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.round((end.getTime() - start.getTime()) / 1000);

    if (duration < 60) return `${duration}s`;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <h3 className="text-sm font-medium text-gray-900">
            {progress.status === 'completed'
              ? 'Simulation Complete'
              : progress.status === 'error'
              ? 'Simulation Error'
              : 'Running Simulation'}
          </h3>
        </div>
        <div className="text-xs text-gray-500">
          {formatDuration(progress.start_time, progress.end_time)}
        </div>
      </div>

      <div className="mb-3">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>{progress.message}</span>
          <span>{Math.round(progress.progress * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
            style={{ width: `${progress.progress * 100}%` }}
          />
        </div>
      </div>

      <div className="flex justify-between text-xs text-gray-500">
        <span>
          Step {progress.completed_steps} of {progress.total_steps}
        </span>
        <span className="capitalize">{progress.current_step.replace('_', ' ')}</span>
      </div>

      {error && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      {progress.status === 'completed' && (
        <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
          Simulation completed successfully! Results are now available.
        </div>
      )}
    </div>
  );
}
