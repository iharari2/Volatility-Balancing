import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface Trade {
  id: string;
  time: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  qty: number;
  price: number;
  commission: number;
  order_id?: string;
}

export default function RecentTradesTable() {
  const { selectedPortfolioId } = useTenantPortfolio();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedPortfolioId) {
      setLoading(false);
      return;
    }

    // TODO: Fetch recent trades from API
    // For now, use mock data
    const mockTrades: Trade[] = [
      {
        id: '1',
        time: '10:03',
        symbol: 'AAPL',
        action: 'BUY',
        qty: 10,
        price: 196.4,
        commission: 1.96,
        order_id: 'ORD-123',
      },
    ];
    setTrades(mockTrades);
    setLoading(false);
  }, [selectedPortfolioId]);

  if (loading) {
    return <p className="text-sm text-gray-500">Loading trades...</p>;
  }

  if (trades.length === 0) {
    return <p className="text-sm text-gray-500">No recent trades</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Symbol
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Action
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Qty
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Price
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Commission
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {trades.map((trade) => (
            <tr key={trade.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{trade.time}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                {trade.symbol}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                <span
                  className={`badge ${trade.action === 'BUY' ? 'badge-success' : 'badge-danger'}`}
                >
                  {trade.action}
                </span>
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{trade.qty}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                ${trade.price.toFixed(2)}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                ${trade.commission.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4 text-right">
        <Link to="/audit" className="text-sm text-primary-600 hover:text-primary-900 font-medium">
          View All →
        </Link>
      </div>
    </div>
  );
}







