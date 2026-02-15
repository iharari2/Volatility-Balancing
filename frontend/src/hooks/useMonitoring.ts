import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { monitoringApi } from '../lib/api';

export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system-status'],
    queryFn: monitoringApi.getSystemStatus,
    refetchInterval: 30000,
  });
};

export const useAlerts = (status?: 'active' | 'acknowledged' | 'resolved') => {
  return useQuery({
    queryKey: ['alerts', status],
    queryFn: () => monitoringApi.getAlerts(status),
    refetchInterval: 30000,
  });
};

export const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => monitoringApi.acknowledgeAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['system-status'] });
    },
  });
};

export const useResolveAlert = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => monitoringApi.resolveAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['system-status'] });
    },
  });
};

export const useWebhookConfig = () => {
  return useQuery({
    queryKey: ['webhook-config'],
    queryFn: monitoringApi.getWebhookConfig,
  });
};

export const useSetWebhookConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string | null) => monitoringApi.setWebhookConfig(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhook-config'] });
    },
  });
};
