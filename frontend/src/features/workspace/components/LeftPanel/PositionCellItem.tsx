import { TrendingUp, TrendingDown, Pause, Play } from 'lucide-react';
import { PositionSummaryItem } from '../../../../api/cockpit';

interface PositionCellItemProps {
  position: PositionSummaryItem;
  isSelected: boolean;
  onClick: () => void;
}

const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
};

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
};

export default function PositionCellItem({ position, isSelected, onClick }: PositionCellItemProps) {
  const isRunning = position.status === 'RUNNING';
  const pnlValue = position.position_vs_baseline_pct ?? 0;
  const isPnlPositive = pnlValue >= 0;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-3 transition-all ${
        isSelected
          ? 'bg-primary-50 border-l-4 border-primary-500'
          : 'hover:bg-gray-50 border-l-4 border-transparent'
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        {/* Ticker */}
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-900 text-sm">{position.asset_symbol}</span>
          {isRunning ? (
            <Play className="h-3 w-3 text-success-500" />
          ) : (
            <Pause className="h-3 w-3 text-gray-400" />
          )}
        </div>

        {/* Status Badge */}
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
            isRunning ? 'bg-success-100 text-success-700' : 'bg-gray-100 text-gray-600'
          }`}
        >
          {position.status || 'RUNNING'}
        </span>
      </div>

      <div className="flex items-center justify-between">
        {/* Total Value */}
        <span className="text-sm font-semibold text-gray-700">
          {formatCurrency(position.total_value)}
        </span>

        {/* P&L */}
        <span
          className={`flex items-center text-xs font-semibold ${
            isPnlPositive ? 'text-success-600' : 'text-danger-600'
          }`}
        >
          {isPnlPositive ? (
            <TrendingUp className="h-3 w-3 mr-0.5" />
          ) : (
            <TrendingDown className="h-3 w-3 mr-0.5" />
          )}
          {formatPercent(pnlValue)}
        </span>
      </div>

      {/* Stock Allocation Bar */}
      <div className="mt-2">
        <div className="flex justify-between text-[10px] text-gray-500 mb-1">
          <span>Stock {position.stock_pct?.toFixed(0) ?? 0}%</span>
          <span>Cash {(100 - (position.stock_pct ?? 0)).toFixed(0)}%</span>
        </div>
        <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all"
            style={{ width: `${position.stock_pct ?? 50}%` }}
          />
        </div>
      </div>
    </button>
  );
}
