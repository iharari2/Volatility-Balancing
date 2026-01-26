/**
 * Position History API
 *
 * Fetches historical data for position performance tracking over multiple days.
 */

const TENANT_ID = 'default';

export interface PerformancePoint {
  timestamp: string;
  total_value: number;
  stock_value: number;
  cash: number;
  qty: number;
  allocation_pct: number;
}

export interface PerformanceSeriesResponse {
  position_id: string;
  interval: string;
  start_time: string | null;
  end_time: string | null;
  points: PerformancePoint[];
  total_points: number;
}

export interface DailySummary {
  date: string;
  open_value: number | null;
  close_value: number | null;
  high_value: number | null;
  low_value: number | null;
  daily_return_pct: number | null;
  evaluation_count: number;
  trade_count: number;
}

export interface DailySummariesResponse {
  position_id: string;
  days: DailySummary[];
  total_days: number;
}

export interface PositionSnapshotResponse {
  position_id: string;
  as_of: string;
  total_value: number | null;
  stock_value: number | null;
  cash: number | null;
  qty: number | null;
  allocation_pct: number | null;
  market_price: number | null;
  found: boolean;
}

async function request<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Get performance time series for charting
 */
export function getPerformanceSeries(
  portfolioId: string,
  positionId: string,
  options?: {
    startDate?: string;
    endDate?: string;
    interval?: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d';
    mode?: 'LIVE' | 'SIMULATION';
  }
): Promise<PerformanceSeriesResponse> {
  const params = new URLSearchParams();
  if (options?.startDate) params.set('start_date', options.startDate);
  if (options?.endDate) params.set('end_date', options.endDate);
  if (options?.interval) params.set('interval', options.interval);
  if (options?.mode) params.set('mode', options.mode);

  const queryString = params.toString();
  const url = `/v1/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/history/performance${queryString ? `?${queryString}` : ''}`;

  return request<PerformanceSeriesResponse>(url);
}

/**
 * Get daily summaries for a position
 */
export function getDailySummaries(
  portfolioId: string,
  positionId: string,
  options?: {
    startDate?: string;
    endDate?: string;
    mode?: 'LIVE' | 'SIMULATION';
  }
): Promise<DailySummariesResponse> {
  const params = new URLSearchParams();
  if (options?.startDate) params.set('start_date', options.startDate);
  if (options?.endDate) params.set('end_date', options.endDate);
  if (options?.mode) params.set('mode', options.mode);

  const queryString = params.toString();
  const url = `/v1/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/history/daily${queryString ? `?${queryString}` : ''}`;

  return request<DailySummariesResponse>(url);
}

/**
 * Get position snapshot at a specific point in time
 */
export function getPositionSnapshot(
  portfolioId: string,
  positionId: string,
  options?: {
    asOf?: string;
    mode?: 'LIVE' | 'SIMULATION';
  }
): Promise<PositionSnapshotResponse> {
  const params = new URLSearchParams();
  if (options?.asOf) params.set('as_of', options.asOf);
  if (options?.mode) params.set('mode', options.mode);

  const queryString = params.toString();
  const url = `/v1/tenants/${TENANT_ID}/portfolios/${portfolioId}/positions/${positionId}/history/snapshot${queryString ? `?${queryString}` : ''}`;

  return request<PositionSnapshotResponse>(url);
}
