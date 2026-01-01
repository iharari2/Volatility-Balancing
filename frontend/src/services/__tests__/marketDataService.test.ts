// Test file demonstrating proper use of mock data for testing only
import { marketDataService } from '../marketDataService';
import { mockDataService } from '../mockDataService';

// Mock fetch for testing
global.fetch = jest.fn();

describe('MarketDataService', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  describe('getStockQuote', () => {
    it('should fetch real data when API is available', async () => {
      const mockResponse = {
        'Global Quote': {
          '01. symbol': 'AAPL',
          '05. price': '195.50',
          '09. change': '2.50',
          '10. change percent': '1.30%',
          '06. volume': '50000000',
        },
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await marketDataService.getStockQuote('AAPL');

      expect(result).toEqual({
        symbol: 'AAPL',
        price: 195.5,
        change: 2.5,
        changePercent: 1.3,
        volume: 50000000,
      });
    });

    it('should throw error when API is unavailable', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(marketDataService.getStockQuote('AAPL')).rejects.toThrow(
        'Failed to fetch real-time data for AAPL. Please check your internet connection and try again.',
      );
    });
  });

  describe('getHistoricalData', () => {
    it('should fetch real historical data when API is available', async () => {
      const mockResponse = {
        'Time Series (Daily)': {
          '2024-01-01': {
            '1. open': '190.00',
            '2. high': '195.00',
            '3. low': '189.00',
            '4. close': '194.50',
            '5. volume': '45000000',
            '5. adjusted close': '194.50',
          },
        },
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await marketDataService.getHistoricalData('AAPL', '2024-01-01', '2024-01-01');

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        date: '2024-01-01',
        open: 190.0,
        high: 195.0,
        low: 189.0,
        close: 194.5,
        volume: 45000000,
        adjustedClose: 194.5,
      });
    });

    it('should throw error when no data is found', async () => {
      const mockResponse = {
        'Time Series (Daily)': {},
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await expect(
        marketDataService.getHistoricalData('INVALID', '2024-01-01', '2024-01-01'),
      ).rejects.toThrow(
        'Failed to fetch historical data for INVALID. Please check your internet connection and try again.',
      );
    });
  });
});

describe('MockDataService', () => {
  describe('getMockQuote', () => {
    it('should return mock data for testing purposes only', () => {
      const result = mockDataService.getMockQuote('AAPL');

      expect(result.symbol).toBe('AAPL');
      expect(result.price).toBe(195.5);
      expect(typeof result.change).toBe('number');
      expect(typeof result.changePercent).toBe('number');
      expect(typeof result.volume).toBe('number');
    });
  });

  describe('getMockHistoricalData', () => {
    it('should generate mock historical data for testing', () => {
      const result = mockDataService.getMockHistoricalData('AAPL', '2024-01-01', '2024-01-07');

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);

      result.forEach((day) => {
        expect(day).toHaveProperty('date');
        expect(day).toHaveProperty('open');
        expect(day).toHaveProperty('high');
        expect(day).toHaveProperty('low');
        expect(day).toHaveProperty('close');
        expect(day).toHaveProperty('volume');
        expect(day).toHaveProperty('adjustedClose');
      });
    });
  });
});

// Example of how NOT to use mock data in production code
describe('Anti-pattern examples', () => {
  it('should NOT use mock data in production user interactions', () => {
    // ❌ WRONG: This should never be done in production code
    // const userQuote = mockDataService.getMockQuote('AAPL'); // DON'T DO THIS!

    // ✅ CORRECT: Always use real data service and handle errors properly
    const fetchRealData = async (symbol: string) => {
      try {
        return await marketDataService.getStockQuote(symbol);
      } catch (error) {
        // Show error to user, don't fall back to mock data
        throw new Error(`Unable to fetch data for ${symbol}. Please try again later.`);
      }
    };

    expect(fetchRealData).toBeDefined();
  });
});
