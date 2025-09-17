import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { positionsApi } from '../lib/api';
import { Position, CreatePositionRequest } from '../types';

export const usePositions = () => {
  return useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await positionsApi.list();
      return response.positions;
    },
  });
};

export const usePosition = (id: string) => {
  return useQuery({
    queryKey: ['position', id],
    queryFn: () => positionsApi.get(id),
    enabled: !!id,
  });
};

export const useCreatePosition = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePositionRequest) => positionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
  });
};

export const useSetAnchorPrice = (positionId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (price: number) => positionsApi.setAnchor(positionId, price),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['evaluation', positionId] });
    },
  });
};

export const useEvaluatePosition = (positionId: string, currentPrice: number) => {
  return useQuery({
    queryKey: ['evaluation', positionId, currentPrice],
    queryFn: () => positionsApi.evaluate(positionId, currentPrice),
    enabled: !!positionId && !!currentPrice,
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  });
};

export const usePositionEvents = (positionId: string) => {
  return useQuery({
    queryKey: ['events', positionId],
    queryFn: () => positionsApi.getEvents(positionId),
    enabled: !!positionId,
  });
};

export const useAutoSizeOrder = (positionId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      currentPrice,
      idempotencyKey,
    }: {
      currentPrice: number;
      idempotencyKey?: string;
    }) => positionsApi.autoSize(positionId, currentPrice, idempotencyKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders', positionId] });
      queryClient.invalidateQueries({ queryKey: ['position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['evaluation', positionId] });
    },
  });
};
