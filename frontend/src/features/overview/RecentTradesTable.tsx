import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioApi, ordersApi } from '../../lib/api';
import { TradeRow } from '../../types/orders';

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
  const { selectedTenantId, selectedPortfolioId } = useTenantPortfolio();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedTenantId || !selectedPortfolioId) {
      setTrades([]);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchTrades() {
      setLoading(true);
      try {
        const positions = await portfolioApi.getPositions(selectedTenantId!, selectedPortfolioId!);

        const allTrades: (TradeRow & { asset: string })[] = [];
        await Promise.all(
          positions.map(async (pos) => {
            try {
              const resp = await ordersApi.listTrades(
                selectedTenantId!,
                selectedPortfolioId!,
                pos.id,
                20,
              );
              for (const t of resp.trades) {
                allTrades.push({ ...t, asset: pos.asset });
              }
            } catch {
              // skip positions with no trades
            }
          }),
        );

        if (cancelled) return;

        allTrades.sort(
          (a, b) => new Date(b.executed_at).getTime() - new Date(a.executed_at).getTime(),
        );

        const mapped: Trade[] = allTrades.slice(0, 10).map((t) => {
          const dt = new Date(t.executed_at);
          return {
            id: t.id,
            time: dt.toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            }),
            symbol: t.asset,
            action: t.side as 'BUY' | 'SELL',
            qty: t.qty,
            price: t.price,
            commission: t.commission,
            order_id: t.order_id,
          };
        });

        setTrades(mapped);
      } catch (err) {
        console.error('Failed to fetch recent trades:', err);
        setTrades([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchTrades();
    return () => {
      cancelled = true;
    };
  }, [selectedTenantId, selectedPortfolioId]);

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
