import { useState } from 'react';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';

interface SetAnchorModalProps {
  position: PortfolioPosition;
  currentPrice: number;
  onClose: () => void;
  onSave: (anchorPrice: number) => void;
}

export default function SetAnchorModal({
  position,
  currentPrice,
  onClose,
  onSave,
}: SetAnchorModalProps) {
  const [anchorPrice, setAnchorPrice] = useState(
    position.anchor_price?.toFixed(2) || currentPrice.toFixed(2),
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const price = parseFloat(anchorPrice);
    if (isNaN(price) || price <= 0) {
      toast.error('Anchor price must be a positive number');
      return;
    }
    onSave(price);
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
                <h3 className="text-lg font-medium text-gray-900">Set Anchor Price</h3>
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
                    Current Anchor Price
                  </label>
                  <input
                    type="text"
                    value={
                      position.anchor_price ? `$${position.anchor_price.toFixed(2)}` : 'Not set'
                    }
                    disabled
                    className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Current Market Price
                  </label>
                  <input
                    type="text"
                    value={`$${currentPrice.toFixed(2)}`}
                    disabled
                    className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    New Anchor Price <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={anchorPrice}
                    onChange={(e) => setAnchorPrice(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder={currentPrice.toFixed(2)}
                    required
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    This will be used as the reference price for trigger calculations
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Set Anchor
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













