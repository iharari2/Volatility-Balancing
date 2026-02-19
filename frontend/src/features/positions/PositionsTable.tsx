import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import { exportToExcel } from '../../utils/exportExcel';
import toast from 'react-hot-toast';

interface PositionsTableProps {
  positions: any[];
  cashBalance: number;
  onExport?: () => void;
}

export default function PositionsTable({ positions, cashBalance, onExport }: PositionsTableProps) {
  const { selectedPortfolio } = useTenantPortfolio();

  // Calculate total portfolio value
  const totalStockValue = positions.reduce((sum, pos) => sum + pos.marketValue, 0);
  const totalPortfolioValue = totalStockValue + cashBalance;

  const handleExport = async () => {
    if (onExport) {
      onExport();
    } else {
      try {
        await exportToExcel(
          '/v1/excel/trading/export?format=xlsx',
          `positions_${new Date().toISOString().split('T')[0]}.xlsx`,
        );
        toast.success('Positions exported');
      } catch (err) {
        toast.error(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={handleExport}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <Download className="h-5 w-5 mr-2" />
          Export Positions Excel
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Asset
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Qty
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Value
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Weight%
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                P&L
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {/* Cash Row */}
            <tr className="bg-gray-50">
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                Cash
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">—</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">—</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                ${cashBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                {totalPortfolioValue > 0
                  ? ((cashBalance / totalPortfolioValue) * 100).toFixed(1)
                  : '0.0'}
                %
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">—</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                <button className="text-primary-600 hover:text-primary-900 mr-2">Deposit</button>
                <button className="text-primary-600 hover:text-primary-900">Withdraw</button>
              </td>
            </tr>

            {/* Position Rows */}
            {positions.map((position) => {
              const weightPercent =
                totalPortfolioValue > 0 ? (position.marketValue / totalPortfolioValue) * 100 : 0;
              return (
                <tr key={position.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{position.ticker}</div>
                  </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                {(position.units || position.qty || 0).toLocaleString()}
              </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    ${(position.currentPrice || 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    $
                    {(position.marketValue || 0).toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {weightPercent.toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    <span
                      className={(position.pnlPercent || 0) >= 0 ? 'text-green-600' : 'text-red-600'}
                    >
                      {(position.pnlPercent || 0) >= 0 ? '+' : ''}
                      {(position.pnlPercent || 0).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                    <button
                      className="text-primary-600 hover:text-primary-900 mr-3"
                      title="Adjust position"
                    >
                      Adjust
                    </button>
                    <Link
                      to={`/positions/${position.id}`}
                      className="text-primary-600 hover:text-primary-900"
                      title="View details"
                    >
                      Details
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

















