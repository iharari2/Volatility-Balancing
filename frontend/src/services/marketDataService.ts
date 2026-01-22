// Market Data Service for fetching real-time stock data
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

class MarketDataService {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    // Using Alpha Vantage API (free tier available)
    this.apiKey = import.meta.env.VITE_ALPHA_VANTAGE_API_KEY || 'demo';
    this.baseUrl = 'https://www.alphavantage.co/query';

    if (this.apiKey === 'demo') {
      console.info(
        'MarketData: Using demo API key. Set VITE_ALPHA_VANTAGE_API_KEY for production.',
      );
    }
  }

  // Fetch current stock quote
  async getStockQuote(symbol: string): Promise<StockQuote> {
    try {
      const response = await fetch(
        `${this.baseUrl}?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${this.apiKey}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data['Global Quote']) {
        const quote = data['Global Quote'];
        return {
          symbol: quote['01. symbol'],
          price: parseFloat(quote['05. price']),
          change: parseFloat(quote['09. change']),
          changePercent: parseFloat(quote['10. change percent'].replace('%', '')),
          volume: parseInt(quote['06. volume']),
        };
      }
      throw new Error('Invalid API response - no Global Quote data');
    } catch (error) {
      console.error(`Error fetching quote for ${symbol}:`, error);
      throw new Error(
        `Failed to fetch real-time data for ${symbol}. Please check your internet connection and try again.`,
      );
    }
  }

  // Fetch historical data for simulation
  async getHistoricalData(
    symbol: string,
    startDate: string,
    endDate: string,
  ): Promise<HistoricalData[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}?function=TIME_SERIES_DAILY&symbol=${symbol}&outputsize=full&apikey=${this.apiKey}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data['Time Series (Daily)']) {
        const timeSeries = data['Time Series (Daily)'];
        const historicalData: HistoricalData[] = [];

        const start = new Date(startDate);
        const end = new Date(endDate);

        for (const [date, values] of Object.entries(timeSeries) as [string, Record<string, string>][]) {
          const dataDate = new Date(date);
          if (dataDate >= start && dataDate <= end) {
            historicalData.push({
              date,
              open: parseFloat(values['1. open']),
              high: parseFloat(values['2. high']),
              low: parseFloat(values['3. low']),
              close: parseFloat(values['4. close']),
              volume: parseInt(values['5. volume']),
              adjustedClose: parseFloat(values['5. adjusted close']),
            });
          }
        }

        if (historicalData.length === 0) {
          throw new Error(`No historical data found for ${symbol} in the specified date range`);
        }

        return historicalData.sort(
          (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
        );
      }
      throw new Error('Invalid API response - no Time Series data');
    } catch (error) {
      console.error(`Error fetching historical data for ${symbol}:`, error);
      throw new Error(
        `Failed to fetch historical data for ${symbol}. Please check your internet connection and try again.`,
      );
    }
  }

  // Fetch company information
  async getCompanyInfo(symbol: string): Promise<CompanyInfo> {
    try {
      const response = await fetch(
        `${this.baseUrl}?function=OVERVIEW&symbol=${symbol}&apikey=${this.apiKey}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.Symbol) {
        return {
          symbol: data.Symbol,
          name: data.Name,
          sector: data.Sector,
          industry: data.Industry,
          description: data.Description,
          website: data.Website,
          marketCap: parseInt(data.MarketCapitalization) || 0,
          employees: parseInt(data.FullTimeEmployees) || 0,
        };
      }
      throw new Error('Invalid API response - no company data');
    } catch (error) {
      console.error(`Error fetching company info for ${symbol}:`, error);
      throw new Error(
        `Failed to fetch company information for ${symbol}. Please check your internet connection and try again.`,
      );
    }
  }

  // Note: Mock data functions have been moved to mockDataService.ts
  // This service only provides real market data and throws errors when data is unavailable
}

export const marketDataService = new MarketDataService();
