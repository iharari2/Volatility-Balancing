interface Props {
  currentPct: number | null;
  minPct: number | null;
  maxPct: number | null;
  /** Show % labels below the bar. Default true. */
  showLabels?: boolean;
  /** Height of the bar in px. Default 10. */
  height?: number;
}

/**
 * Allocation bar with three zones:
 *   red (breach) | purple (safe zone) | red (breach)
 * A thin dark needle marks the current allocation %.
 */
export default function AllocationNeedleBar({
  currentPct,
  minPct,
  maxPct,
  showLabels = true,
  height = 10,
}: Props) {
  const min = minPct ?? 25;
  const max = maxPct ?? 75;
  const cur = currentPct ?? null;

  const needleColor =
    cur === null ? 'transparent'
    : cur < min || cur > max ? '#ef4444'
    : '#1e293b';

  return (
    <div style={{ width: '100%' }}>
      {/* Bar */}
      <div
        style={{
          position: 'relative',
          height,
          background: '#fee2e2',
          borderRadius: height / 2,
          overflow: 'hidden',
        }}
      >
        {/* Safe zone */}
        <div
          style={{
            position: 'absolute',
            left: `${min}%`,
            width: `${max - min}%`,
            top: 0,
            bottom: 0,
            background: '#ddd6fe',
          }}
        />
        {/* Needle */}
        {cur !== null && (
          <div
            style={{
              position: 'absolute',
              left: `${Math.min(Math.max(cur, 0), 100)}%`,
              top: -2,
              bottom: -2,
              width: 3,
              background: needleColor,
              borderRadius: 2,
              transform: 'translateX(-50%)',
            }}
          />
        )}
      </div>

      {/* Labels */}
      {showLabels && (
        <div style={{ position: 'relative', height: 14, marginTop: 2 }}>
          <span
            style={{
              position: 'absolute',
              left: `${min}%`,
              transform: 'translateX(-50%)',
              fontSize: 9,
              color: '#6366f1',
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            {min}%
          </span>
          <span
            style={{
              position: 'absolute',
              left: `${max}%`,
              transform: 'translateX(-50%)',
              fontSize: 9,
              color: '#6366f1',
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            {max}%
          </span>
          {cur !== null && (
            <span
              style={{
                position: 'absolute',
                left: `${Math.min(Math.max(cur, 2), 98)}%`,
                transform: 'translateX(-50%)',
                fontSize: 9,
                fontWeight: 800,
                color: needleColor,
                whiteSpace: 'nowrap',
                top: 2,
              }}
            >
              {cur.toFixed(1)}%
            </span>
          )}
        </div>
      )}
    </div>
  );
}
