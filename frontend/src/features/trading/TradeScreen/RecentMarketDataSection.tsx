import { PortfolioPosition } from '../../../services/portfolioScopedApi';
import { useState, useEffect } from 'react';

interface RecentMarketDataSectionProps {
  position: PortfolioPosition;
}

export default function RecentMarketDataSection({ position }: RecentMarketDataSectionProps) {
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMarketData = async () => {
      try {
        const asset = position.asset || position.ticker;
        if (!asset) return;

        // Fetch recent market data - adjust endpoint as needed
        const response = await fetch(`/api/v1/market-data/${asset}/latest`);
        if (response.ok) {
          const data = await response.json();
          setMarketData(data);
        }
      } catch (error) {
        console.error('Error loading market data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMarketData();
    const interval = setInterval(loadMarketData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [position]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Market Data</h2>
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Market Data</h2>
      {marketData ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <dt className="text-sm text-gray-500">Last Price</dt>
            <dd className="text-lg font-semibold text-gray-900 mt-1">
              ${(position.last_price || 0).toFixed(2)}
            </dd>
          </div>
          {marketData.open && (
            <div>
              <dt className="text-sm text-gray-500">Open</dt>
              <dd className="text-lg font-semibold text-gray-900 mt-1">
                ${marketData.open.toFixed(2)}
              </dd>
            </div>
          )}
          {marketData.high && (
            <div>
              <dt className="text-sm text-gray-500">High</dt>
              <dd className="text-lg font-semibold text-gray-900 mt-1">
                ${marketData.high.toFixed(2)}
              </dd>
            </div>
          )}
          {marketData.low && (
            <div>
              <dt className="text-sm text-gray-500">Low</dt>
              <dd className="text-lg font-semibold text-gray-900 mt-1">
                ${marketData.low.toFixed(2)}
              </dd>
            </div>
          )}
        </div>
      ) : (
        <div className="text-sm text-gray-500">Market data not available</div>
      )}
    </div>
  );
}








