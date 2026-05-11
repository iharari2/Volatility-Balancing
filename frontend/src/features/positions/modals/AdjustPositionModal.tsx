import { useState, useMemo } from 'react';
import { X, TrendingUp, TrendingDown, Hash } from 'lucide-react';
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

type AdjustType = 'add' | 'remove' | 'set';

const ADJUST_OPTIONS: { type: AdjustType; label: string; description: string; icon: React.ReactNode; operation: 'BUY' | 'SELL' | 'SET_QTY' }[] = [
  {
    type: 'add',
    label: 'Add shares',
    description: 'Shares acquired outside the system (e.g. broker transfer, dividend reinvestment)',
    icon: <TrendingUp className="h-4 w-4" />,
    operation: 'BUY',
  },
  {
    type: 'remove',
    label: 'Remove shares',
    description: 'Shares removed outside the system (e.g. broker correction, partial transfer out)',
    icon: <TrendingDown className="h-4 w-4" />,
    operation: 'SELL',
  },
  {
    type: 'set',
    label: 'Set exact quantity',
    description: "Override quantity to match your broker's record exactly",
    icon: <Hash className="h-4 w-4" />,
    operation: 'SET_QTY',
  },
];

export default function AdjustPositionModal({
  position,
  currentPrice,
  onClose,
  onSave,
}: AdjustPositionModalProps) {
  const [adjustType, setAdjustType] = useState<AdjustType>('add');
  const [qty, setQty] = useState('');
  const [costPerShare, setCostPerShare] = useState('');
  const [reason, setReason] = useState('');

  const currentQty = position.qty ?? 0;

  const resultingQty = useMemo(() => {
    const n = parseFloat(qty);
    if (isNaN(n) || n <= 0) return null;
    if (adjustType === 'add') return currentQty + n;
    if (adjustType === 'remove') return Math.max(0, currentQty - n);
    return n; // set
  }, [adjustType, qty, currentQty]);

  const cashImpact = useMemo(() => {
    const n = parseFloat(qty);
    const price = parseFloat(costPerShare) || currentPrice;
    if (isNaN(n) || n <= 0) return null;
    if (adjustType === 'add') return -(n * price);
    if (adjustType === 'remove') return n * price;
    return null; // set qty has no implied cash movement
  }, [adjustType, qty, costPerShare, currentPrice]);

  const selectedOption = ADJUST_OPTIONS.find(o => o.type === adjustType)!;

  const isValid = () => {
    const n = parseFloat(qty);
    if (isNaN(n) || n <= 0) return false;
    if (adjustType === 'remove' && n > currentQty) return false;
    if (!reason.trim()) return false;
    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid()) return;

    const price = parseFloat(costPerShare) || undefined;

    onSave({
      operation: selectedOption.operation,
      qty: parseFloat(qty),
      price,
      reason: reason.trim(),
    });
  };

  const formatQty = (n: number) =>
    n.toLocaleString(undefined, { maximumFractionDigits: 4 });

  const formatCash = (n: number) =>
    n.toLocaleString(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 2 });

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 py-8">
        <div className="fixed inset-0 bg-gray-500/75" onClick={onClose} />

        <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Adjust Position</h3>
              <p className="text-sm text-gray-500 mt-0.5">
                {position.ticker} &middot; {formatQty(currentQty)} shares held
              </p>
            </div>
            <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
              <X className="h-5 w-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">

            {/* Step 1: What are you doing? */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">What changed?</label>
              <div className="space-y-2">
                {ADJUST_OPTIONS.map(opt => (
                  <label
                    key={opt.type}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      adjustType === opt.type
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="adjustType"
                      value={opt.type}
                      checked={adjustType === opt.type}
                      onChange={() => { setAdjustType(opt.type); setQty(''); }}
                      className="mt-0.5 h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                    />
                    <div className="flex-1 min-w-0">
                      <div className={`flex items-center gap-1.5 text-sm font-medium ${adjustType === opt.type ? 'text-primary-700' : 'text-gray-800'}`}>
                        {opt.icon}
                        {opt.label}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{opt.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Step 2: How many shares */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {adjustType === 'set' ? 'New total shares' : 'Number of shares'}
                <span className="text-red-500 ml-1">*</span>
              </label>
              <input
                type="number"
                step="0.0001"
                min="0.0001"
                max={adjustType === 'remove' ? currentQty : undefined}
                value={qty}
                onChange={e => setQty(e.target.value)}
                className="input w-full"
                placeholder={adjustType === 'set' ? currentQty.toString() : '0'}
                autoFocus
                required
              />
              {adjustType === 'remove' && parseFloat(qty) > currentQty && (
                <p className="mt-1 text-xs text-red-600">Cannot remove more than {formatQty(currentQty)} shares held</p>
              )}
              {/* Live preview */}
              {resultingQty !== null && (
                <p className="mt-1 text-xs text-gray-500">
                  Result: {formatQty(currentQty)} → <span className="font-medium text-gray-700">{formatQty(resultingQty)} shares</span>
                </p>
              )}
            </div>

            {/* Step 3: Cost per share (optional, only for add/remove) */}
            {adjustType !== 'set' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cost per share <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={costPerShare}
                    onChange={e => setCostPerShare(e.target.value)}
                    className="input w-full pl-7"
                    placeholder={currentPrice.toFixed(2)}
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  The price at which shares were acquired/sold. Used to adjust your cash balance.
                  {cashImpact !== null && (
                    <span className={`ml-1 font-medium ${cashImpact >= 0 ? 'text-green-600' : 'text-orange-600'}`}>
                      Cash {cashImpact >= 0 ? '+' : ''}{formatCash(cashImpact)}.
                    </span>
                  )}
                </p>
              </div>
            )}

            {/* Step 4: Reason */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reason <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={reason}
                onChange={e => setReason(e.target.value)}
                className="input w-full"
                placeholder="e.g. Reconcile with broker, DRIP reinvestment, partial transfer"
                required
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
                Cancel
              </button>
              <button
                type="submit"
                disabled={!isValid()}
                className="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
