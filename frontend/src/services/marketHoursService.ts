export type MarketStatus = 'PRE_MARKET' | 'OPEN' | 'AFTER_HOURS' | 'CLOSED';

export interface MarketHoursState {
  status: MarketStatus;
  isOpen: boolean;
  nextOpen?: string; // ISO timestamp
  nextClose?: string; // ISO timestamp
  currentTime: string; // ISO timestamp
}

class MarketHoursService {
  private cache: MarketHoursState | null = null;
  private cacheExpiry: number = 0;
  private readonly CACHE_TTL = 60000; // 1 minute

  async getMarketState(): Promise<MarketHoursState> {
    const now = Date.now();
    if (this.cache && now < this.cacheExpiry) {
      return this.cache;
    }

    try {
      const response = await fetch('/api/market/state');
      if (response.ok) {
        const data = await response.json();
        this.cache = data as MarketHoursState;
        this.cacheExpiry = now + this.CACHE_TTL;
        return data as MarketHoursState;
      }
    } catch (error) {
      console.error('Error fetching market state:', error);
    }

    // Fallback: Calculate based on current time (US market hours)
    return this.calculateMarketState();
  }

  private calculateMarketState(): MarketHoursState {
    const now = new Date();
    const utc = now.getTime() + now.getTimezoneOffset() * 60000;
    const est = new Date(utc + -5 * 3600000); // EST is UTC-5
    const hour = est.getHours();
    const day = est.getDay(); // 0 = Sunday, 6 = Saturday

    // Market is closed on weekends
    if (day === 0 || day === 6) {
      return {
        status: 'CLOSED',
        isOpen: false,
        currentTime: now.toISOString(),
      };
    }

    // Pre-market: 4:00 AM - 9:30 AM EST
    if (hour >= 4 && hour < 9) {
      return {
        status: 'PRE_MARKET',
        isOpen: false,
        currentTime: now.toISOString(),
      };
    }

    // Market open: 9:30 AM - 4:00 PM EST
    if (hour >= 9 && hour < 16) {
      return {
        status: 'OPEN',
        isOpen: true,
        currentTime: now.toISOString(),
      };
    }

    // After-hours: 4:00 PM - 8:00 PM EST
    if (hour >= 16 && hour < 20) {
      return {
        status: 'AFTER_HOURS',
        isOpen: false,
        currentTime: now.toISOString(),
      };
    }

    // Closed: 8:00 PM - 4:00 AM EST
    return {
      status: 'CLOSED',
      isOpen: false,
      currentTime: now.toISOString(),
    };
  }

  getStatusLabel(status: MarketStatus): string {
    switch (status) {
      case 'PRE_MARKET':
        return 'Pre-Market';
      case 'OPEN':
        return 'Market Open';
      case 'AFTER_HOURS':
        return 'After-Hours';
      case 'CLOSED':
        return 'Market Closed';
    }
  }

  getStatusColor(status: MarketStatus): string {
    switch (status) {
      case 'OPEN':
        return 'bg-green-100 text-green-800';
      case 'PRE_MARKET':
      case 'AFTER_HOURS':
        return 'bg-yellow-100 text-yellow-800';
      case 'CLOSED':
        return 'bg-gray-100 text-gray-800';
    }
  }
}

export const marketHoursService = new MarketHoursService();

