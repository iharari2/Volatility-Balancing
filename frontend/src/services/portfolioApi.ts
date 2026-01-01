const API_BASE = '/api';

export interface BackendPosition {
  id: string;
  ticker: string;
  qty: number;
  cash: number;
  anchor_price: number | null;
  order_policy: {
    trigger_threshold_pct: number;
    rebalance_ratio: number;
    commission_rate: number;
    min_notional: number;
    allow_after_hours: boolean;
  };
  guardrails: {
    min_stock_alloc_pct: number;
    max_stock_alloc_pct: number;
    max_orders_per_day: number;
  };
}

export interface CreatePositionRequest {
  ticker: string;
  qty: number;
  cash: number;
  anchor_price?: number;
  order_policy?: {
    trigger_threshold_pct?: number;
    rebalance_ratio?: number;
    commission_rate?: number;
    min_notional?: number;
    allow_after_hours?: boolean;
  };
  guardrails?: {
    min_stock_alloc_pct?: number;
    max_stock_alloc_pct?: number;
    max_orders_per_day?: number;
  };
}

export interface CreatePositionResponse {
  id: string;
  ticker: string;
  qty: number;
  cash: number;
  anchor_price: number | null;
  order_policy: {
    trigger_threshold_pct: number;
    rebalance_ratio: number;
    commission_rate: number;
    min_notional: number;
    allow_after_hours: boolean;
  };
  guardrails: {
    min_stock_alloc_pct: number;
    max_stock_alloc_pct: number;
    max_orders_per_day: number;
  };
}

class PortfolioApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API request failed: ${response.status} ${errorText}`);
    }

    return response.json();
  }

  async getPositions(): Promise<BackendPosition[]> {
    const response = await this.request<{ positions: BackendPosition[] }>('/positions');
    return response.positions;
  }

  async createPosition(position: CreatePositionRequest): Promise<CreatePositionResponse> {
    return this.request<CreatePositionResponse>('/positions', {
      method: 'POST',
      body: JSON.stringify(position),
    });
  }

  async updatePosition(
    positionId: string,
    position: Partial<CreatePositionRequest>,
  ): Promise<CreatePositionResponse> {
    // The backend POST endpoint handles updates for existing positions with the same ticker
    // We just need to send the update data directly
    return this.createPosition(position as CreatePositionRequest);
  }

  async deletePosition(positionId: string): Promise<void> {
    await this.request(`/positions/${positionId}`, {
      method: 'DELETE',
    });
  }

  async getPosition(positionId: string): Promise<BackendPosition> {
    return this.request<BackendPosition>(`/positions/${positionId}`);
  }

  async clearAllPositions(): Promise<void> {
    await this.request('/clear-positions', {
      method: 'POST',
    });
  }
}

export const portfolioApi = new PortfolioApiService();
