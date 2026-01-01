import { PortfolioPosition } from '../../../services/portfolioScopedApi';

interface PositionBaseline {
  baseline_price: number;
  baseline_qty: number;
  baseline_cash: number;
  baseline_total_value: number;
  baseline_stock_value: number;
  baseline_timestamp: string;
}

interface PositionListPanelProps {
  positions: PortfolioPosition[];
  baselines: Record<string, PositionBaseline>;
  selectedPositionId: string | null;
  onSelectPosition: (positionId: string) => void;
}

export default function PositionListPanel({
  positions,
  baselines,
  selectedPositionId,
  onSelectPosition,
}: PositionListPanelProps) {
  const getPositionMetrics = (position: PortfolioPosition) => {
    const baseline = baselines[position.id];
    const lastPrice = position.last_price ?? 0;
    const positionCash = position.cash || 0;
    const stockValue = lastPrice * position.qty;
    const totalValue = positionCash + stockValue;

    // % change from anchor
    const anchorChangePct =
      position.anchor_price && position.anchor_price > 0
        ? ((lastPrice - position.anchor_price) / position.anchor_price) * 100
        : null;

    // % position change vs baseline
    const positionChangePct = baseline
      ? baseline.baseline_total_value > 0
        ? ((totalValue - baseline.baseline_total_value) / baseline.baseline_total_value) * 100
        : null
      : null;

    // % stock change vs baseline
    const stockChangePct = baseline
      ? baseline.baseline_stock_value > 0
        ? ((stockValue - baseline.baseline_stock_value) / baseline.baseline_stock_value) * 100
        : null
      : null;

    return {
      totalValue,
      anchorChangePct,
      positionChangePct,
      stockChangePct,
    };
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h2 className="text-sm font-semibold text-gray-900">Positions</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {positions.length === 0 ? (
          <div className="p-4 text-sm text-gray-500 text-center">No positions</div>
        ) : (
          <div className="divide-y divide-gray-200">
            {positions.map((position) => {
              const metrics = getPositionMetrics(position);
              const isSelected = position.id === selectedPositionId;
              const asset = position.asset || position.ticker || 'N/A';

              return (
                <button
                  key={position.id}
                  onClick={() => onSelectPosition(position.id)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                    isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  }`}
                >
                  <div className="space-y-2">
                    {/* Asset & Status */}
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-gray-900">{asset}</span>
                      <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                        {position.status || 'RUNNING'}
                      </span>
                    </div>

                    {/* Qty & Cash */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500">Qty:</span>{' '}
                        <span className="font-medium text-gray-900">
                          {position.qty.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Cash:</span>{' '}
                        <span className="font-medium text-gray-900">
                          ${(position.cash || 0).toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {/* Total Value */}
                    <div className="text-xs">
                      <span className="text-gray-500">Total Value:</span>{' '}
                      <span className="font-semibold text-gray-900">
                        $
                        {metrics.totalValue.toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>

                    {/* % Changes */}
                    <div className="space-y-1 text-xs">
                      {metrics.anchorChangePct !== null && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">vs Anchor:</span>
                          <span
                            className={`font-medium ${
                              metrics.anchorChangePct >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {metrics.anchorChangePct >= 0 ? '+' : ''}
                            {metrics.anchorChangePct.toFixed(2)}%
                          </span>
                        </div>
                      )}
                      {metrics.positionChangePct !== null && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">vs Baseline (Pos):</span>
                          <span
                            className={`font-medium ${
                              metrics.positionChangePct >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {metrics.positionChangePct >= 0 ? '+' : ''}
                            {metrics.positionChangePct.toFixed(2)}%
                          </span>
                        </div>
                      )}
                      {metrics.stockChangePct !== null && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">vs Baseline (Stock):</span>
                          <span
                            className={`font-medium ${
                              metrics.stockChangePct >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {metrics.stockChangePct >= 0 ? '+' : ''}
                            {metrics.stockChangePct.toFixed(2)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}








