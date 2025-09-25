// Parameter Optimization API Service
// Handles all API calls for the optimization system

import { API_BASE_URL } from './api';
import {
  CreateConfigRequest,
  ConfigResponse,
  StartResponse,
  ProgressResponse,
  ResultsResponse,
  HeatmapData,
  MetricsResponse,
  ParameterTypeInfo,
  ParameterTypesResponse,
  OptimizationResult,
  OptimizationConfig,
  OptimizationProgress,
  OptimizationMetric,
  ParameterType,
} from '../types/optimization';

class OptimizationApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/optimization`;
  }

  // Configuration Management
  async createConfig(config: CreateConfigRequest): Promise<ConfigResponse> {
    const response = await fetch(`${this.baseUrl}/configs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to create config: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  async getConfig(id: string): Promise<ConfigResponse> {
    const response = await fetch(`${this.baseUrl}/configs/${id}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get config: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  async getAllConfigs(): Promise<ConfigResponse[]> {
    const response = await fetch(`${this.baseUrl}/configs`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get configs: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  // Optimization Control
  async startOptimization(id: string): Promise<StartResponse> {
    const response = await fetch(`${this.baseUrl}/configs/${id}/start`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to start optimization: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  async getProgress(id: string): Promise<ProgressResponse> {
    const response = await fetch(`${this.baseUrl}/configs/${id}/progress`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get progress: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  // Results and Analysis
  async getResults(id: string): Promise<OptimizationResult[]> {
    const response = await fetch(`${this.baseUrl}/configs/${id}/results`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get results: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  async getHeatmap(
    id: string,
    xParameter: string,
    yParameter: string,
    metric: OptimizationMetric,
  ): Promise<HeatmapData> {
    const params = new URLSearchParams({
      x_parameter: xParameter,
      y_parameter: yParameter,
      metric: metric,
    });

    const response = await fetch(`${this.baseUrl}/configs/${id}/heatmap?${params}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get heatmap: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    return response.json();
  }

  // Metadata
  async getMetrics(): Promise<OptimizationMetric[]> {
    const response = await fetch(`${this.baseUrl}/metrics`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get metrics: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    const data: MetricsResponse = await response.json();
    // Extract just the value properties from the response objects
    return data.metrics.map((metric) => metric.value as OptimizationMetric);
  }

  async getParameterTypes(): Promise<ParameterTypeInfo[]> {
    const response = await fetch(`${this.baseUrl}/parameter-types`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to get parameter types: ${response.status} ${error.detail || response.statusText}`,
      );
    }

    const data: ParameterTypesResponse = await response.json();
    return data.parameter_types;
  }

  // Utility Methods
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/metrics`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Polling for progress updates
  async pollProgress(
    id: string,
    onUpdate: (progress: ProgressResponse) => void,
    interval: number = 2000,
  ): Promise<void> {
    const poll = async () => {
      try {
        const progress = await this.getProgress(id);
        onUpdate(progress);

        // Continue polling if optimization is still running
        if (progress.status === 'running' || progress.status === 'pending') {
          setTimeout(poll, interval);
        }
      } catch (error) {
        console.error('Error polling progress:', error);
        // Stop polling on error
      }
    };

    poll();
  }

  // Cancel polling (if needed)
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

  startPolling(
    id: string,
    onUpdate: (progress: ProgressResponse) => void,
    interval: number = 2000,
  ): void {
    this.stopPolling(id); // Stop any existing polling

    const poll = async () => {
      try {
        const progress = await this.getProgress(id);
        onUpdate(progress);

        // Continue polling if optimization is still running
        if (progress.status === 'running' || progress.status === 'pending') {
          const timeoutId = setTimeout(poll, interval);
          this.pollingIntervals.set(id, timeoutId);
        }
      } catch (error) {
        console.error('Error polling progress:', error);
        this.pollingIntervals.delete(id);
      }
    };

    poll();
  }

  stopPolling(id: string): void {
    const timeoutId = this.pollingIntervals.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.pollingIntervals.delete(id);
    }
  }

  stopAllPolling(): void {
    this.pollingIntervals.forEach((timeoutId) => clearTimeout(timeoutId));
    this.pollingIntervals.clear();
  }
}

// Export singleton instance
export const optimizationApi = new OptimizationApiService();
export default optimizationApi;
