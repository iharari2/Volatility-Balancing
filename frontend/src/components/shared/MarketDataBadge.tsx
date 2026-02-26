import { useEffect, useState } from 'react';

export interface MarketDataBadgeProps {
  isFresh: boolean;
  isMarketHours: boolean;
  source: string;
  dataUpdatedAt: number; // React Query dataUpdatedAt (ms timestamp)
  compact?: boolean;     // if true, show only dot + elapsed time (no source chip)
}

const SOURCE_LABELS: Record<string, { label: string; className: string }> = {
  last_trade: { label: 'LIVE', className: 'text-green-600 font-semibold' },
  mid_quote:  { label: 'QUOTE', className: 'text-gray-500' },
  bid:        { label: 'BID', className: 'text-gray-500' },
  ask:        { label: 'ASK', className: 'text-gray-500' },
};

function getDotColor(isMarketHours: boolean, isFresh: boolean, elapsedMs: number): string {
  if (!isMarketHours) return 'bg-gray-400';
  if (elapsedMs > 120_000) return 'bg-red-500';
  if (elapsedMs > 60_000 || !isFresh) return 'bg-yellow-400';
  return 'bg-green-500';
}

function formatElapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

export default function MarketDataBadge({
  isFresh,
  isMarketHours,
  source,
  dataUpdatedAt,
  compact = false,
}: MarketDataBadgeProps) {
  const [elapsed, setElapsed] = useState(() =>
    dataUpdatedAt > 0 ? Date.now() - dataUpdatedAt : 0,
  );

  useEffect(() => {
    if (!dataUpdatedAt) return;
    setElapsed(Date.now() - dataUpdatedAt);
    const interval = setInterval(() => {
      setElapsed(Date.now() - dataUpdatedAt);
    }, 1000);
    return () => clearInterval(interval);
  }, [dataUpdatedAt]);

  const dotColor = getDotColor(isMarketHours, isFresh, elapsed);
  const sourceInfo = SOURCE_LABELS[source] ?? { label: source.toUpperCase(), className: 'text-gray-500' };

  return (
    <div className="inline-flex items-center gap-1.5 text-xs leading-none">
      <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
      {!compact && (
        <span className={`tracking-wide ${sourceInfo.className}`}>
          {sourceInfo.label}
        </span>
      )}
      {dataUpdatedAt > 0 && (
        <span className="text-gray-400">updated {formatElapsed(elapsed)}</span>
      )}
    </div>
  );
}
