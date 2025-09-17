import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersApi } from '../lib/api';
import { CreateOrderRequest, FillOrderRequest } from '../types';

export const useOrders = (positionId: string) => {
  return useQuery({
    queryKey: ['orders', positionId],
    queryFn: () => ordersApi.list(positionId),
    enabled: !!positionId,
  });
};

export const useCreateOrder = (positionId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, idempotencyKey }: { data: CreateOrderRequest; idempotencyKey?: string }) =>
      ordersApi.create(positionId, data, idempotencyKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders', positionId] });
      queryClient.invalidateQueries({ queryKey: ['position', positionId] });
    },
  });
};

export const useFillOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: FillOrderRequest }) =>
      ordersApi.fill(orderId, data),
    onSuccess: (_, { orderId }) => {
      // Invalidate all order-related queries
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['position'] });
    },
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
    }) => ordersApi.autoSize(positionId, currentPrice, idempotencyKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders', positionId] });
      queryClient.invalidateQueries({ queryKey: ['position', positionId] });
      queryClient.invalidateQueries({ queryKey: ['evaluation', positionId] });
    },
  });
};


