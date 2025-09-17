import {
  Position,
  Order,
  Event,
  EvaluationResult,
  CreatePositionRequest,
  CreateOrderRequest,
  FillOrderRequest,
} from '../types';

const API_BASE = '/api'; // This will use the Vite proxy
// Alternative: const API_BASE = 'http://localhost:8000/v1'; // Direct connection

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

// Positions API
export const positionsApi = {
  create: (data: CreatePositionRequest) =>
    request<Position>('/positions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  list: () => request<{ positions: Position[] }>('/positions'),

  get: (id: string) => request<Position>(`/positions/${id}`),

  setAnchor: (id: string, price: number) =>
    request<{ position_id: string; anchor_price: number; message: string }>(
      `/positions/${id}/anchor?price=${price}`,
      { method: 'POST' },
    ),

  evaluate: (id: string, currentPrice: number) =>
    request<EvaluationResult>(`/positions/${id}/evaluate?current_price=${currentPrice}`, {
      method: 'POST',
    }),

  getEvents: (id: string, limit = 100) =>
    request<{ position_id: string; events: Event[] }>(`/positions/${id}/events?limit=${limit}`),

  autoSize: (id: string, currentPrice: number, idempotencyKey?: string) =>
    request<{
      position_id: string;
      current_price: number;
      order_submitted: boolean;
      order_id?: string;
      order_details?: any;
      sizing_details?: any;
      evaluation: EvaluationResult;
      reason?: string;
      rejections?: string[];
    }>(`/positions/${id}/orders/auto-size?current_price=${currentPrice}`, {
      method: 'POST',
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),
};

// Orders API
export const ordersApi = {
  create: (positionId: string, data: CreateOrderRequest, idempotencyKey?: string) =>
    request<{
      order_id: string;
      position_id: string;
      side: string;
      qty: number;
      price: number;
      status: string;
    }>(`/positions/${positionId}/orders`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),

  fill: (orderId: string, data: FillOrderRequest) =>
    request<{ order_id: string; status: string; qty: number; price: number; commission: number }>(
      `/orders/${orderId}/fill`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      },
    ),

  list: (positionId: string, limit = 100) =>
    request<{ position_id: string; orders: Order[] }>(
      `/positions/${positionId}/orders?limit=${limit}`,
    ),

  autoSize: (positionId: string, currentPrice: number, idempotencyKey?: string) =>
    request<{
      position_id: string;
      current_price: number;
      order_submitted: boolean;
      order_id?: string;
      order_details?: any;
      sizing_details?: any;
      evaluation: EvaluationResult;
      reason?: string;
      rejections?: string[];
    }>(`/positions/${positionId}/orders/auto-size?current_price=${currentPrice}`, {
      method: 'POST',
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),
};

// Health API
export const healthApi = {
  check: () => request<{ status: string; timestamp: string }>('/health'),
};

export { ApiError };
