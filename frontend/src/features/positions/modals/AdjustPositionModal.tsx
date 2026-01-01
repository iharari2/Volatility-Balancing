import { useState } from 'react';
import { X } from 'lucide-react';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';

interface AdjustPositionModalProps {
  position: PortfolioPosition;
  currentPrice: number;
  onClose: () => void;
  onSave: (data: {
    operation: 'BUY' | 'SELL' | 'SET_QTY';
    qty: number;
    price?: number;
    reason: string;
  }) => void;
}

export default function AdjustPositionModal({
  position,
  currentPrice,
  onClose,
  onSave,
}: AdjustPositionModalProps) {
  const [operation, setOperation] = useState<'BUY' | 'SELL' | 'SET_QTY'>('BUY');
  const [qty, setQty] = useState('');
  const [price, setPrice] = useState(currentPrice.toFixed(2));
  const [reason, setReason] = useState('');
  const [confirmManual, setConfirmManual] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!qty || parseFloat(qty) <= 0) {
      alert('Quantity is required and must be > 0');
      return;
    }
    if (!reason.trim()) {
      alert('Reason is required');
      return;
    }
    if (!confirmManual) {
      alert('Please confirm this is a manual correction');
      return;
    }

    onSave({
      operation,
      qty: parseFloat(qty),
      price: price ? parseFloat(price) : undefined,
      reason: reason.trim(),
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Manual Adjustment</h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Asset</label>
                  <input
                    type="text"
                    value={position.ticker}
                    disabled
                    className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Operation <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={operation}
                    onChange={(e) => setOperation(e.target.value as 'BUY' | 'SELL' | 'SET_QTY')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                    <option value="SET_QTY">Set Qty</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Quantity <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="100"
                    required
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Current position: {position.qty.toLocaleString()} shares
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Price (optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder={currentPrice.toFixed(2)}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Defaults to current market price if not provided
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Reason <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    rows={3}
                    placeholder="e.g., align with broker"
                    required
                  />
                </div>

                <div className="flex items-start">
                  <input
                    type="checkbox"
                    id="confirm-manual"
                    checked={confirmManual}
                    onChange={(e) => setConfirmManual(e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    required
                  />
                  <label htmlFor="confirm-manual" className="ml-2 block text-sm text-gray-700">
                    <span className="text-red-500">*</span> This is a manual correction
                  </label>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Apply Adjustment
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}













