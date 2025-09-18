import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dividendApi } from '../lib/api';

export const useDividendPositionStatus = (positionId: string) => {
  return useQuery({
    queryKey: ['dividends', 'position', positionId],
    queryFn: () => dividendApi.getPositionStatus(positionId),
    enabled: !!positionId,
  });
};

export const useDividendMarketInfo = (ticker: string) => {
  return useQuery({
    queryKey: ['dividends', 'market', ticker],
    queryFn: () => dividendApi.getMarketInfo(ticker),
    enabled: !!ticker,
  });
};

export const useUpcomingDividends = (ticker: string) => {
  return useQuery({
    queryKey: ['dividends', 'upcoming', ticker],
    queryFn: () => dividendApi.getUpcoming(ticker),
    enabled: !!ticker,
  });
};

export const useAnnounceDividend = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      ticker: string;
      ex_date: string;
      pay_date: string;
      dps: number;
      currency: string;
      withholding_tax_rate: number;
    }) => dividendApi.announce(data),
    onSuccess: (_, variables) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['dividends', 'market', variables.ticker] });
      queryClient.invalidateQueries({ queryKey: ['dividends', 'upcoming', variables.ticker] });
      queryClient.invalidateQueries({ queryKey: ['dividends', 'position'] });
    },
  });
};

export const useProcessExDividend = (positionId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => dividendApi.processExDividend(positionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dividends', 'position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
  });
};

export const useProcessDividendPayment = (positionId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (receivableId: string) => dividendApi.processPayment(positionId, receivableId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dividends', 'position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
  });
};
