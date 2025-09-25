// Optimization Context
// Provides state management for the Parameter Optimization System

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import {
  OptimizationState,
  OptimizationContextType,
  OptimizationConfig,
  OptimizationProgress,
  OptimizationResult,
  HeatmapData,
  CreateConfigRequest,
  OptimizationMetric,
  ParameterType,
  ParameterTypeInfo,
} from '../types/optimization';
import { optimizationApi } from '../services/optimizationApi';

// Initial state
const initialState: OptimizationState = {
  configs: [],
  activeOptimizations: new Map(),
  results: new Map(),
  heatmapData: new Map(),
  loading: false,
  error: null,
};

// Action types
type OptimizationAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_CONFIGS'; payload: OptimizationConfig[] }
  | { type: 'ADD_CONFIG'; payload: OptimizationConfig }
  | { type: 'UPDATE_CONFIG'; payload: OptimizationConfig }
  | { type: 'SET_PROGRESS'; payload: { id: string; progress: OptimizationProgress } }
  | { type: 'SET_RESULTS'; payload: { id: string; results: OptimizationResult[] } }
  | { type: 'SET_HEATMAP'; payload: { id: string; heatmap: HeatmapData } }
  | { type: 'REMOVE_OPTIMIZATION'; payload: string };

// Reducer
function optimizationReducer(
  state: OptimizationState,
  action: OptimizationAction,
): OptimizationState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'SET_CONFIGS':
      return { ...state, configs: action.payload };

    case 'ADD_CONFIG':
      return { ...state, configs: [...state.configs, action.payload] };

    case 'UPDATE_CONFIG':
      return {
        ...state,
        configs: state.configs.map((config) =>
          config.id === action.payload.id ? action.payload : config,
        ),
      };

    case 'SET_PROGRESS':
      const newActiveOptimizations = new Map(state.activeOptimizations);
      newActiveOptimizations.set(action.payload.id, action.payload.progress);
      return { ...state, activeOptimizations: newActiveOptimizations };

    case 'SET_RESULTS':
      const newResults = new Map(state.results);
      newResults.set(action.payload.id, action.payload.results);
      return { ...state, results: newResults };

    case 'SET_HEATMAP':
      const newHeatmapData = new Map(state.heatmapData);
      newHeatmapData.set(action.payload.id, action.payload.heatmap);
      return { ...state, heatmapData: newHeatmapData };

    case 'REMOVE_OPTIMIZATION':
      const updatedActiveOptimizations = new Map(state.activeOptimizations);
      updatedActiveOptimizations.delete(action.payload);
      return { ...state, activeOptimizations: updatedActiveOptimizations };

    default:
      return state;
  }
}

// Context
const OptimizationContext = createContext<OptimizationContextType | undefined>(undefined);

// Provider component
interface OptimizationProviderProps {
  children: ReactNode;
}

export function OptimizationProvider({ children }: OptimizationProviderProps) {
  const [state, dispatch] = useReducer(optimizationReducer, initialState);

  // Action creators
  const createConfig = useCallback(async (config: CreateConfigRequest) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      const newConfig = await optimizationApi.createConfig(config);
      dispatch({ type: 'ADD_CONFIG', payload: newConfig });
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to create config',
      });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const getConfig = useCallback(async (id: string): Promise<OptimizationConfig | null> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      const config = await optimizationApi.getConfig(id);
      dispatch({ type: 'UPDATE_CONFIG', payload: config });
      return config;
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to get config',
      });
      return null;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const startOptimization = useCallback(async (id: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      await optimizationApi.startOptimization(id);

      // Start polling for progress updates
      optimizationApi.startPolling(id, (progress) => {
        dispatch({ type: 'SET_PROGRESS', payload: { id, progress } });
      });

      // Update config status
      const config = await optimizationApi.getConfig(id);
      dispatch({ type: 'UPDATE_CONFIG', payload: config });
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to start optimization',
      });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const getProgress = useCallback(async (id: string): Promise<OptimizationProgress | null> => {
    try {
      const progress = await optimizationApi.getProgress(id);
      dispatch({ type: 'SET_PROGRESS', payload: { id, progress } });
      return progress;
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to get progress',
      });
      return null;
    }
  }, []);

  const getResults = useCallback(async (id: string): Promise<OptimizationResult[]> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      const results = await optimizationApi.getResults(id);
      dispatch({ type: 'SET_RESULTS', payload: { id, results } });
      return results;
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to get results',
      });
      return [];
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const getHeatmap = useCallback(
    async (
      id: string,
      x: string,
      y: string,
      metric: OptimizationMetric,
    ): Promise<HeatmapData | null> => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        dispatch({ type: 'CLEAR_ERROR' });

        const heatmap = await optimizationApi.getHeatmap(id, x, y, metric);
        dispatch({ type: 'SET_HEATMAP', payload: { id, heatmap } });
        return heatmap;
      } catch (error) {
        dispatch({
          type: 'SET_ERROR',
          payload: error instanceof Error ? error.message : 'Failed to get heatmap',
        });
        return null;
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    },
    [],
  );

  const getMetrics = useCallback(async (): Promise<OptimizationMetric[]> => {
    try {
      return await optimizationApi.getMetrics();
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to get metrics',
      });
      return [];
    }
  }, []);

  const getParameterTypes = useCallback(async (): Promise<ParameterTypeInfo[]> => {
    try {
      return await optimizationApi.getParameterTypes();
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to get parameter types',
      });
      return [];
    }
  }, []);

  const refreshProgress = useCallback(async (id: string) => {
    try {
      const progress = await optimizationApi.getProgress(id);
      dispatch({ type: 'SET_PROGRESS', payload: { id, progress } });
    } catch (error) {
      console.error('Error refreshing progress:', error);
    }
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const value: OptimizationContextType = {
    state,
    createConfig,
    getConfig,
    startOptimization,
    getProgress,
    getResults,
    getHeatmap,
    getMetrics,
    getParameterTypes,
    refreshProgress,
    clearError,
  };

  return <OptimizationContext.Provider value={value}>{children}</OptimizationContext.Provider>;
}

// Hook to use the context
export function useOptimization() {
  const context = useContext(OptimizationContext);
  if (context === undefined) {
    throw new Error('useOptimization must be used within an OptimizationProvider');
  }
  return context;
}

export default OptimizationContext;
