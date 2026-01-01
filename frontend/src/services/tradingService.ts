// Trading Service API client for continuous trading
const API_BASE = '/api';

export interface TradingStatus {
  position_id: string;
  is_running: boolean;
  is_paused: boolean;
  start_time: string | null;
  last_check: string | null;
  total_checks: number;
  total_trades: number;
  total_errors: number;
  last_error: string | null;
}

export interface StartTradingRequest {
  polling_interval_seconds?: number;
}

class TradingService {
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

  async startTrading(
    positionId: string,
    pollingIntervalSeconds: number = 300
  ): Promise<{ message: string; position_id: string; status: string }> {
    return this.request(`/trading/start/${positionId}`, {
      method: 'POST',
      body: JSON.stringify({ polling_interval_seconds: pollingIntervalSeconds }),
    });
  }

  async stopTrading(positionId: string): Promise<{ message: string; position_id: string; status: string }> {
    return this.request(`/trading/stop/${positionId}`, {
      method: 'POST',
    });
  }

  async pauseTrading(positionId: string): Promise<{ message: string; position_id: string; status: string }> {
    return this.request(`/trading/pause/${positionId}`, {
      method: 'POST',
    });
  }

  async resumeTrading(positionId: string): Promise<{ message: string; position_id: string; status: string }> {
    return this.request(`/trading/resume/${positionId}`, {
      method: 'POST',
    });
  }

  async getTradingStatus(positionId: string): Promise<TradingStatus> {
    return this.request(`/trading/status/${positionId}`);
  }

  async listActiveTrading(): Promise<{ active_positions: TradingStatus[]; count: number }> {
    return this.request('/trading/active');
  }
}

export const tradingService = new TradingService();

































