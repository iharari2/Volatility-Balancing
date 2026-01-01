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
    queryFn: async () => {
      const data = await marketApi.getPrice(ticker);
      console.log(`[useMarketPrice ${ticker}] Received data:`, {
        price: data.price,
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
        timestamp: data.timestamp,
        hasAllOHLC: data.open !== undefined && data.high !== undefined && 
                    data.low !== undefined && data.close !== undefined
      });
      return data;
    },
    enabled: !!ticker,
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
    staleTime: 0, // Always consider data stale, force fresh fetch
    gcTime: 0, // Don't cache (cacheTime renamed to gcTime in v5)
    refetchOnMount: 'always', // Always refetch when component mounts
    refetchOnWindowFocus: true, // Refetch when window regains focus
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
