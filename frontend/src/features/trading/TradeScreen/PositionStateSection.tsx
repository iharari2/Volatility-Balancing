import { PortfolioPosition } from '../../../services/portfolioScopedApi';

interface PositionStateSectionProps {
  position: PortfolioPosition;
}

export default function PositionStateSection({ position }: PositionStateSectionProps) {
  const lastPrice = position.last_price ?? 0;
  const positionCash = position.cash || 0;
  const stockValue = lastPrice * position.qty;
  const totalValue = positionCash + stockValue;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Position State</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <dt className="text-sm text-gray-500">Quantity</dt>
          <dd className="text-xl font-semibold text-gray-900 mt-1">
            {position.qty.toLocaleString()} shares
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Cash</dt>
          <dd className="text-xl font-semibold text-gray-900 mt-1">
            $
            {positionCash.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Stock Value</dt>
          <dd className="text-xl font-semibold text-gray-900 mt-1">
            $
            {stockValue.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Total Value</dt>
          <dd className="text-xl font-semibold text-gray-900 mt-1">
            $
            {totalValue.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Anchor Price</dt>
          <dd className="text-lg font-medium text-gray-900 mt-1">
            {position.anchor_price ? `$${position.anchor_price.toFixed(2)}` : 'Not set'}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Last Price</dt>
          <dd className="text-lg font-medium text-gray-900 mt-1">
            {lastPrice > 0 ? `$${lastPrice.toFixed(2)}` : 'N/A'}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Avg Cost</dt>
          <dd className="text-lg font-medium text-gray-900 mt-1">
            {position.avg_cost ? `$${position.avg_cost.toFixed(2)}` : 'N/A'}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Status</dt>
          <dd className="text-lg font-medium text-gray-900 mt-1">
            <span className="px-2 py-1 rounded bg-gray-100 text-gray-700">
              {position.status || 'RUNNING'}
            </span>
          </dd>
        </div>
      </div>
    </div>
  );
}








