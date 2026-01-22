import { useMutation, useQuery } from '@tanstack/react-query';
import { simulationApi } from '../lib/api';
import { SimulationConfig } from '../components/SimulationControls';

export const useRunSimulation = () => {
  return useMutation({
    mutationFn: async (config: SimulationConfig) => {
      try {
        const response = await simulationApi.runSimulation(config);
        return response;
      } catch (error) {
        // Log the actual error for debugging
        console.error('Simulation API failed:', error);
        const err = error as Error & { status?: number };
        console.error('Error details:', {
          message: err.message,
          status: err.status,
          config: config,
        });
        throw error; // Re-throw to see the actual error
      }
    },
  });
};

export const useSimulationHistory = () => {
  return useQuery({
    queryKey: ['simulation-history'],
    queryFn: async () => {
      // This would fetch saved simulation results
      // For now, return empty array
      return [];
    },
  });
};

export const useVolatilityData = (ticker: string, windowMinutes: number = 60) => {
  return useQuery({
    queryKey: ['volatility', ticker, windowMinutes],
    queryFn: async () => {
      const response = await simulationApi.getVolatility(ticker, windowMinutes);
      return response;
    },
    enabled: !!ticker,
  });
};

export const useHistoricalData = (ticker: string, startDate: string, endDate: string) => {
  return useQuery({
    queryKey: ['historical-data', ticker, startDate, endDate],
    queryFn: async () => {
      const response = await simulationApi.getHistoricalData(ticker, startDate, endDate);
      return response;
    },
    enabled: !!ticker && !!startDate && !!endDate,
  });
};
