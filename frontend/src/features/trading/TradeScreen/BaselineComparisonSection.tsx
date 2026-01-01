import { PortfolioPosition } from '../../../services/portfolioScopedApi';

interface PositionBaseline {
  baseline_price: number;
  baseline_qty: number;
  baseline_cash: number;
  baseline_total_value: number;
  baseline_stock_value: number;
  baseline_timestamp: string;
}

interface BaselineComparisonSectionProps {
  position: PortfolioPosition;
  baseline: PositionBaseline;
}

export default function BaselineComparisonSection({
  position,
  baseline,
}: BaselineComparisonSectionProps) {
  const lastPrice = position.last_price ?? 0;
  const positionCash = position.cash || 0;
  const stockValue = lastPrice * position.qty;
  const totalValue = positionCash + stockValue;

  const priceChange = lastPrice - baseline.baseline_price;
  const priceChangePct =
    baseline.baseline_price > 0 ? (priceChange / baseline.baseline_price) * 100 : 0;
  const qtyChange = position.qty - baseline.baseline_qty;
  const cashChange = positionCash - baseline.baseline_cash;
  const totalValueChange = totalValue - baseline.baseline_total_value;
  const totalValueChangePct =
    baseline.baseline_total_value > 0
      ? (totalValueChange / baseline.baseline_total_value) * 100
      : 0;
  const stockValueChange = stockValue - baseline.baseline_stock_value;
  const stockValueChangePct =
    baseline.baseline_stock_value > 0
      ? (stockValueChange / baseline.baseline_stock_value) * 100
      : 0;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Baseline Comparison</h2>
      <div className="text-xs text-gray-500 mb-4">
        Baseline: {new Date(baseline.baseline_timestamp).toLocaleString()}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <dt className="text-sm text-gray-500">Price Change</dt>
          <dd
            className={`text-lg font-semibold mt-1 ${
              priceChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)} ({priceChangePct >= 0 ? '+' : ''}
            {priceChangePct.toFixed(2)}%)
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Quantity Change</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {qtyChange >= 0 ? '+' : ''}
            {qtyChange.toFixed(4)} shares
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Cash Change</dt>
          <dd
            className={`text-lg font-semibold mt-1 ${
              cashChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {cashChange >= 0 ? '+' : ''}${cashChange.toFixed(2)}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Stock Value Change</dt>
          <dd
            className={`text-lg font-semibold mt-1 ${
              stockValueChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {stockValueChange >= 0 ? '+' : ''}${stockValueChange.toFixed(2)} (
            {stockValueChangePct >= 0 ? '+' : ''}
            {stockValueChangePct.toFixed(2)}%)
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Total Value Change</dt>
          <dd
            className={`text-lg font-semibold mt-1 ${
              totalValueChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {totalValueChange >= 0 ? '+' : ''}${totalValueChange.toFixed(2)} (
            {totalValueChangePct >= 0 ? '+' : ''}
            {totalValueChangePct.toFixed(2)}%)
          </dd>
        </div>
      </div>
    </div>
  );
}








