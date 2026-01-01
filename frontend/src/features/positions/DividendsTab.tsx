import { useState, useEffect } from 'react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface DividendReceivable {
  id: string;
  ticker: string;
  ex_date: string;
  pay_date: string;
  gross_amount: number;
  net_amount: number;
  status: string;
}

interface DividendHistory {
  id: string;
  ticker: string;
  ex_date: string;
  pay_date: string;
  dps: number;
  currency: string;
  status: string;
}

export default function DividendsTab() {
  const { positions } = usePortfolio();
  const { selectedPortfolioId } = useTenantPortfolio();
  const [receivables, setReceivables] = useState<DividendReceivable[]>([]);
  const [history, setHistory] = useState<DividendHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedPortfolioId) {
      setLoading(false);
      return;
    }

    // TODO: Fetch dividends from API
    // For now, use mock data
    const mockReceivables: DividendReceivable[] = [];
    const mockHistory: DividendHistory[] = [];

    setReceivables(mockReceivables);
    setHistory(mockHistory);
    setLoading(false);
  }, [selectedPortfolioId, positions]);

  if (loading) {
    return <p className="text-sm text-gray-500">Loading dividends...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Dividend Management</h3>
      </div>

      {/* Upcoming Dividends */}
      <div>
        <h4 className="text-md font-medium text-gray-900 mb-4">Upcoming Dividends</h4>
        {receivables.length === 0 ? (
          <p className="text-sm text-gray-500">No upcoming dividends</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Ticker
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Ex-Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Pay Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Gross Amount
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Net Amount
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {receivables.map((div) => (
                  <tr key={div.id}>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.ticker}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.ex_date}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.pay_date}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      ${div.gross_amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      ${div.net_amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        {div.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Dividend History */}
      <div>
        <h4 className="text-md font-medium text-gray-900 mb-4">Dividend History</h4>
        {history.length === 0 ? (
          <p className="text-sm text-gray-500">No dividend history</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Ticker
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Ex-Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Pay Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    DPS
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Currency
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {history.map((div) => (
                  <tr key={div.id}>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.ticker}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.ex_date}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.pay_date}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">${div.dps.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{div.currency}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        {div.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

