// Mock Data Service - ONLY for testing purposes
// This should NEVER be used in production user interactions

export interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap?: number;
  pe?: number;
  dividend?: number;
  high52Week?: number;
  low52Week?: number;
}

export interface HistoricalData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjustedClose: number;
}

export interface CompanyInfo {
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  description: string;
  website: string;
  marketCap: number;
  employees: number;
}

class MockDataService {
  // Mock data fallbacks - ONLY for testing
  getMockQuote(symbol: string): StockQuote {
    const mockPrices: { [key: string]: number } = {
      AAPL: 195.5,
      MSFT: 420.75,
      GOOGL: 165.8,
      AMZN: 185.3,
      TSLA: 245.25,
      META: 485.4,
      NVDA: 875.6,
      ZIM: 8.75,
      INTC: 35.5,
      SPY: 580.25,
    };

    const price = mockPrices[symbol] || 100.0;
    const change = (Math.random() - 0.5) * 10;

    return {
      symbol,
      price,
      change,
      changePercent: (change / price) * 100,
      volume: Math.floor(Math.random() * 10000000) + 1000000,
    };
  }

  getMockHistoricalData(symbol: string, startDate: string, endDate: string): HistoricalData[] {
    const data: HistoricalData[] = [];
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));

    let currentPrice = this.getMockQuote(symbol).price;

    for (let i = 0; i <= days; i++) {
      const date = new Date(start);
      date.setDate(date.getDate() + i);

      // Skip weekends
      if (date.getDay() === 0 || date.getDay() === 6) continue;

      const priceChange = (Math.random() - 0.5) * 0.04; // ±2% daily change
      const open = currentPrice;
      const close = currentPrice * (1 + priceChange);
      const high = Math.max(open, close) * (1 + Math.random() * 0.02);
      const low = Math.min(open, close) * (1 - Math.random() * 0.02);
      const volume = Math.floor(Math.random() * 1000000) + 100000;

      data.push({
        date: date.toISOString().split('T')[0],
        open,
        high,
        low,
        close,
        volume,
        adjustedClose: close,
      });

      currentPrice = close;
    }

    return data;
  }

  getMockCompanyInfo(symbol: string): CompanyInfo {
    const mockInfo: { [key: string]: CompanyInfo } = {
      AAPL: {
        symbol: 'AAPL',
        name: 'Apple Inc.',
        sector: 'Technology',
        industry: 'Consumer Electronics',
        description:
          'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.',
        website: 'https://www.apple.com',
        marketCap: 3000000000000,
        employees: 164000,
      },
      MSFT: {
        symbol: 'MSFT',
        name: 'Microsoft Corporation',
        sector: 'Technology',
        industry: 'Software—Infrastructure',
        description:
          'Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.',
        website: 'https://www.microsoft.com',
        marketCap: 3000000000000,
        employees: 221000,
      },
      INTC: {
        symbol: 'INTC',
        name: 'Intel Corporation',
        sector: 'Technology',
        industry: 'Semiconductors',
        description:
          'Intel Corporation designs, manufactures, and sells computer, networking, and communications platforms worldwide.',
        website: 'https://www.intel.com',
        marketCap: 150000000000,
        employees: 131900,
      },
      ZIM: {
        symbol: 'ZIM',
        name: 'ZIM Integrated Shipping Services Ltd.',
        sector: 'Industrials',
        industry: 'Marine Shipping',
        description:
          'ZIM Integrated Shipping Services Ltd. provides container shipping and related services worldwide.',
        website: 'https://www.zim.com',
        marketCap: 2000000000,
        employees: 2000,
      },
    };

    return (
      mockInfo[symbol] || {
        symbol,
        name: `${symbol} Corporation`,
        sector: 'Unknown',
        industry: 'Unknown',
        description: `Information about ${symbol} is not available.`,
        website: '',
        marketCap: 0,
        employees: 0,
      }
    );
  }
}

export const mockDataService = new MockDataService();
