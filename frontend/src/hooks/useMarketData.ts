import { useQuery } from '@tanstack/react-query';
import { marketApi } from '../lib/api';

export const useMarketStatus = () => {
  return useQuery({
    queryKey: ['market', 'status'],
    queryFn: marketApi.getStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useMarketPrice = (ticker: string) => {
  return useQuery({
    queryKey: ['market', 'price', ticker],
    queryFn: () => marketApi.getPrice(ticker),
    enabled: !!ticker,
    refetchInterval: 30000,
    staleTime: 15000,
    gcTime: 300000,
    refetchOnWindowFocus: false,
  });
};

export const useHistoricalData = (
  ticker: string,
  startDate: string,
  endDate: string,
  marketHoursOnly = false,
) => {
  return useQuery({
    queryKey: ['market', 'historical', ticker, startDate, endDate, marketHoursOnly],
    queryFn: () => marketApi.getHistoricalData(ticker, startDate, endDate, marketHoursOnly),
    enabled: !!ticker && !!startDate && !!endDate,
  });
};
