import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';
import { portfolioScopedApi } from '../../../services/portfolioScopedApi';

interface EditPositionModalProps {
  position: PortfolioPosition;
  tenantId: string;
  portfolioId: string;
  onClose: () => void;
  onSave: () => void;
}

export default function EditPositionModal({
  position,
  tenantId,
  portfolioId,
  onClose,
  onSave,
}: EditPositionModalProps) {
  const [qty, setQty] = useState(position.qty.toString());
  const [cash, setCash] = useState((position.cash || 0).toString());
  const [anchorPrice, setAnchorPrice] = useState(
    position.anchor_price ? position.anchor_price.toString() : '',
  );
  const [avgCost, setAvgCost] = useState(position.avg_cost ? position.avg_cost.toString() : '');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const ticker = position.asset || position.ticker || '';

      // Update quantity if changed
      const newQty = parseFloat(qty);
      if (newQty !== position.qty) {
        await portfolioScopedApi.adjustPosition(tenantId, portfolioId, ticker, {
          operation: 'SET_QTY',
          qty: newQty,
          reason: 'Manual quantity update',
        });
      }

      // Update anchor price if changed
      if (anchorPrice && parseFloat(anchorPrice) !== position.anchor_price) {
        await portfolioScopedApi.setAnchor(tenantId, portfolioId, ticker, parseFloat(anchorPrice));
      }

      // Note: Cash and avg_cost updates would need new endpoints or use adjustPosition
      // For now, we'll just update qty and anchor_price

      onSave();
      onClose();
    } catch (error: any) {
      console.error('Error updating position:', error);
      alert(`Failed to update position: ${error.message || 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
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
                <h3 className="text-lg font-medium text-gray-900">
                  Edit Position: {position.asset || position.ticker}
                </h3>
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
                  <label className="block text-sm font-medium text-gray-700">
                    Quantity <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Cash</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={cash}
                    onChange={(e) => setCash(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    disabled
                    title="Cash editing will be available after migration"
                  />
                  <p className="mt-1 text-xs text-gray-500">Cash editing via API coming soon</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Anchor Price</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={anchorPrice}
                    onChange={(e) => setAnchorPrice(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Average Cost</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={avgCost}
                    onChange={(e) => setAvgCost(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    disabled
                    title="Average cost editing not yet implemented"
                  />
                  <p className="mt-1 text-xs text-gray-500">Average cost editing coming soon</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={saving}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
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








