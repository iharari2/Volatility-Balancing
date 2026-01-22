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
        hasAllOHLC: data.open !== undefined && data.high !== undefined &&
                    data.low !== undefined && data.close !== undefined
      });
      return data;
    },
    enabled: !!ticker,
    refetchInterval: 30000, // Refetch every 30 seconds to reduce rate limits
    staleTime: 15000, // Allow brief caching between polls
    gcTime: 300000, // Cache for 5 minutes
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
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
