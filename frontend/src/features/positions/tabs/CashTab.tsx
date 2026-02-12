import { useState } from 'react';
import toast from 'react-hot-toast';
import { portfolioScopedApi, PortfolioPosition } from '../../../services/portfolioScopedApi';

// Cash summary interface (calculated from positions)
interface CashSummary {
  cash_balance: number;
  reserved_cash: number;
  available_cash: number;
}
import DepositModal from '../modals/DepositModal';
import WithdrawModal from '../modals/WithdrawModal';

interface CashTabProps {
  tenantId: string;
  portfolioId: string;
  cash: CashSummary | null;
  positions: PortfolioPosition[]; // Positions contain cash
  onRefresh: () => void;
  onCopyTraceId: (traceId: string) => void;
  copiedTraceId: string | null;
}

export default function CashTab({
  tenantId,
  portfolioId,
  cash,
  positions,
  onRefresh,
  onCopyTraceId,
  copiedTraceId,
}: CashTabProps) {
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<PortfolioPosition | null>(null);

  const handleDeposit = async (amount: number, reason: string, positionId?: string) => {
    try {
      const result = await portfolioScopedApi.depositCash(tenantId, portfolioId, {
        amount,
        reason,
        position_id: positionId,
      });
      if (result.trace_id) {
        onCopyTraceId(result.trace_id);
      }
      setShowDepositModal(false);
      setSelectedPosition(null);
      onRefresh();
    } catch (error) {
      console.error('Error depositing cash:', error);
      toast.error('Failed to deposit cash');
    }
  };

  const handleWithdraw = async (amount: number, reason: string, positionId?: string) => {
    try {
      const result = await portfolioScopedApi.withdrawCash(tenantId, portfolioId, {
        amount,
        reason,
        position_id: positionId,
      });
      if (result.trace_id) {
        onCopyTraceId(result.trace_id);
      }
      setShowWithdrawModal(false);
      setSelectedPosition(null);
      onRefresh();
    } catch (error) {
      console.error('Error withdrawing cash:', error);
      toast.error('Failed to withdraw cash');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Cash Management</h3>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">Cash Balance</label>
            <div className="mt-1 text-2xl font-semibold text-gray-900">
              $
              {(cash?.cash_balance || 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <p className="mt-1 text-sm text-gray-500">Total cash in portfolio</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Reserved Cash</label>
            <div className="mt-1 text-2xl font-semibold text-gray-500">
              $
              {(cash?.reserved_cash || 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <p className="mt-1 text-sm text-gray-500">Pending orders</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Available Cash</label>
            <div className="mt-1 text-2xl font-semibold text-green-600">
              $
              {(cash?.available_cash || 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <p className="mt-1 text-sm text-gray-500">Available for trading</p>
          </div>
        </div>
      </div>

      {/* Positions Cash Table */}
      <div className="border-t border-gray-200 pt-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Position Cash Balances</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cash Balance
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {positions.map((position) => {
                const ticker = position.asset || position.ticker || 'N/A';
                const positionCash = position.cash || 0;
                return (
                  <tr key={position.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      {ticker}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      $
                      {positionCash.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedPosition(position);
                            setShowDepositModal(true);
                          }}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          Deposit
                        </button>
                        <button
                          onClick={() => {
                            setSelectedPosition(position);
                            setShowWithdrawModal(true);
                          }}
                          className="text-primary-600 hover:text-primary-900"
                          disabled={positionCash <= 0}
                        >
                          Withdraw
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {positions.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-sm text-gray-500">
                    No positions found. Add positions to manage cash.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      {showDepositModal && (
        <DepositModal
          position={selectedPosition}
          onClose={() => {
            setShowDepositModal(false);
            setSelectedPosition(null);
          }}
          onSave={(amount, reason) => handleDeposit(amount, reason, selectedPosition?.id)}
        />
      )}

      {showWithdrawModal && selectedPosition && (
        <WithdrawModal
          position={selectedPosition}
          availableCash={selectedPosition.cash || 0}
          onClose={() => {
            setShowWithdrawModal(false);
            setSelectedPosition(null);
          }}
          onSave={(amount, reason) => handleWithdraw(amount, reason, selectedPosition.id)}
        />
      )}
    </div>
  );
}







