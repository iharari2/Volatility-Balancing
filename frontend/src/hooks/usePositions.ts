import { useQuery, useMutation } from '@tanstack/react-query';
import { positionsApi, enhancedPositionsApi } from '../lib/api';

// Re-export types from PortfolioContext for backwards compatibility
export type { Position, PositionConfig } from '../contexts/PortfolioContext';

// Position interface for API responses (different from PortfolioContext.Position)
interface ApiPosition {
  id: string;
  ticker: string;
  asset?: string;
  qty: number;
  cash: number;
  anchor_price: number | null;
  created_at?: string;
  order_policy?: {
    trigger_threshold_pct: number;
    rebalance_ratio: number;
    commission_rate: number;
    min_notional: number;
    allow_after_hours: boolean;
  };
  guardrails?: {
    min_stock_alloc_pct: number;
    max_stock_alloc_pct: number;
    max_orders_per_day: number;
  };
}

// Hook for fetching all positions using react-query
export const usePositions = () => {
  return useQuery({
    queryKey: ['positions'],
    queryFn: async (): Promise<ApiPosition[]> => {
      try {
        const response = await positionsApi.list();
        // API returns { positions: Position[] }
        const positions = response.positions ?? [];
        return positions.map((p: any) => ({
          ...p,
          ticker: p.ticker || p.asset || '',
          anchor_price: p.anchor_price ?? null,
        })) as ApiPosition[];
      } catch {
        return [];
      }
    },
    staleTime: 30000,
  });
};

// Event interface
interface PositionEvent {
  id: string;
  position_id: string;
  type: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

interface PositionEventsResponse {
  events: PositionEvent[];
}

// Hook for fetching position events
export const usePositionEvents = (positionId: string) => {
  return useQuery({
    queryKey: ['positions', positionId, 'events'],
    queryFn: async (): Promise<PositionEventsResponse> => {
      if (!positionId) return { events: [] };
      try {
        // API returns { position_id: string, events: Event[] }
        const response = await positionsApi.getEvents(positionId);
        const events = (response.events ?? []).map((e: any) => ({
          ...e,
          timestamp: e.timestamp || e.ts || new Date().toISOString(),
        })) as PositionEvent[];
        return { events };
      } catch {
        return { events: [] };
      }
    },
    enabled: !!positionId,
    staleTime: 30000,
  });
};

// Evaluate position hook
export const useEvaluatePosition = (positionId: string, currentPrice: number) => {
  return useQuery({
    queryKey: ['positions', positionId, 'evaluate', currentPrice],
    queryFn: () => positionsApi.evaluate(positionId, currentPrice),
    enabled: !!positionId && currentPrice > 0,
    staleTime: 10000,
  });
};

// Evaluate position with market data hook
export const useEvaluatePositionWithMarketData = (positionId: string) => {
  return useQuery({
    queryKey: ['positions', positionId, 'evaluate', 'market'],
    queryFn: () => enhancedPositionsApi.evaluateWithMarketData(positionId),
    enabled: !!positionId,
    staleTime: 10000,
  });
};

// Auto-size order mutation hook
export const useAutoSizeOrder = (positionId: string) => {
  return useMutation({
    mutationFn: (params: { currentPrice: number; idempotencyKey?: string }) =>
      positionsApi.autoSize(positionId, params.currentPrice, params.idempotencyKey),
  });
};

// Auto-size order with market data mutation hook
export const useAutoSizeOrderWithMarketData = (positionId: string) => {
  return useMutation({
    mutationFn: (idempotencyKey?: string) =>
      enhancedPositionsApi.autoSizeWithMarketData(positionId, idempotencyKey),
  });
};

// Single position hook
export const usePosition = (positionId: string) => {
  return useQuery({
    queryKey: ['position', positionId],
    queryFn: () => positionsApi.get(positionId),
    enabled: !!positionId,
    staleTime: 30000,
  });
};

// Set anchor price mutation hook
export const useSetAnchorPrice = (positionId: string) => {
  return useMutation({
    mutationFn: (price: number) => positionsApi.setAnchor(positionId, price),
  });
};

// Create position mutation hook
export const useCreatePosition = () => {
  return useMutation({
    mutationFn: (data: { ticker: string; qty: number; cash: number; anchor_price?: number }) =>
      positionsApi.create(data),
  });
};

// Delete position mutation hook
export const useDeletePosition = () => {
  return useMutation({
    mutationFn: (positionId: string) => positionsApi.delete(positionId),
  });
};

// Re-export the PortfolioContext hook as well
export { usePortfolio } from '../contexts/PortfolioContext';
