import { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import {
  ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, Brush,
} from 'recharts';
import { ArrowLeft, RefreshCw, Moon, Sun } from 'lucide-react';
import toast from 'react-hot-toast';
import { WorkspaceProvider, useWorkspace } from '../workspace/WorkspaceContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { getPositionPerformance, type PerformanceData } from '../../api/performance';
import { getPositionCockpit, type CockpitResponse } from '../../api/cockpit';
import { portfolioScopedApi, type PortfolioConfig } from '../../services/portfolioScopedApi';
import AllocationNeedleBar from '../../components/shared/AllocationNeedleBar';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import StrategyTab from '../workspace/components/tabs/StrategyTab';
import EventsTab from '../workspace/components/tabs/EventsTab';
import OrdersTab from '../workspace/components/tabs/OrdersTab';

// ── helpers ──────────────────────────────────────────────────────────────────

function fmt$(n: number | null | undefined, dec = 2) {
  if (n == null) return '—';
  return '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
function fmtPct(n: number | null | undefined, dec = 2) {
  if (n == null) return '—';
  return (n >= 0 ? '+' : '') + n.toFixed(dec) + '%';
}
function clr(n: number | null | undefined) {
  if (n == null) return '';
  return n >= 0 ? 'text-green-600' : 'text-red-500';
}
function fmtTs(ts: string) {
  const d = new Date(ts);
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}
function fmtTsShort(ts: string) {
  const d = new Date(ts);
  return d.toLocaleString('en-US', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}

// ── Market snapshot bar ───────────────────────────────────────────────────────

type SessionLabel = 'OPEN' | 'PRE' | 'AH' | 'CLOSED' | 'UNKNOWN';

function sessionFromPolicy(policy: string | null | undefined): SessionLabel {
  if (!policy) return 'UNKNOWN';
  const p = policy.toUpperCase();
  if (p.includes('AFTER') || p.includes('AH')) return 'AH';
  if (p.includes('PRE')) return 'PRE';
  if (p.includes('OPEN') || p.includes('REG') || p.includes('REGULAR')) return 'OPEN';
  if (p.includes('CLOSE')) return 'CLOSED';
  return 'UNKNOWN';
}

const SESSION_STYLES: Record<SessionLabel, string> = {
  OPEN:    'bg-green-100 text-green-700',
  PRE:     'bg-blue-100 text-blue-700',
  AH:      'bg-violet-100 text-violet-700',
  CLOSED:  'bg-gray-100 text-gray-500',
  UNKNOWN: 'bg-gray-100 text-gray-400',
};

function MarketSnapshotBar({ cockpit, afterHoursEnabled, onToggleAfterHours, toggling }: {
  cockpit: CockpitResponse | null;
  afterHoursEnabled: boolean;
  onToggleAfterHours: () => void;
  toggling: boolean;
}) {
  const q = cockpit?.recent_quotes?.[0] ?? null;
  const session: SessionLabel = sessionFromPolicy(q?.price_policy);
  const effectivePrice = q?.effective_price ?? null;
  const closePrice = q?.close ?? null;
  const extendedMove = (effectivePrice != null && closePrice != null && session !== 'OPEN')
    ? effectivePrice - closePrice : null;
  const extendedMovePct = (extendedMove != null && closePrice && closePrice !== 0)
    ? (extendedMove / closePrice) * 100 : null;

  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 px-4 py-2.5 bg-slate-50 border-t border-gray-100 text-xs">

      {/* Session badge */}
      <div className="flex items-center gap-1.5">
        <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${SESSION_STYLES[session]}`}>
          {session === 'AH' ? 'After-Hours' : session === 'PRE' ? 'Pre-Market' : session === 'OPEN' ? 'Market Open' : session === 'CLOSED' ? 'Closed' : '—'}
        </span>
      </div>

      {/* Effective price (AH/PRE only) */}
      {effectivePrice != null && session !== 'OPEN' && (
        <div className="flex items-center gap-1.5">
          <span className="text-gray-400 text-[10px] uppercase font-semibold">Effective</span>
          <span className="font-bold text-slate-800">${effectivePrice.toFixed(2)}</span>
          {extendedMovePct != null && (
            <span className={`text-[10px] font-semibold ${extendedMovePct >= 0 ? 'text-green-600' : 'text-red-500'}`}>
              ({extendedMovePct >= 0 ? '+' : ''}{extendedMovePct.toFixed(2)}% ext)
            </span>
          )}
        </div>
      )}

      {/* OHLC */}
      {q && (
        <div className="flex items-center gap-3 text-gray-500">
          {[
            { l: 'O', v: q.open },
            { l: 'H', v: q.high },
            { l: 'L', v: q.low },
            { l: 'C', v: q.close },
          ].map(({ l, v }) => v != null && (
            <span key={l}>
              <span className="text-gray-400 font-semibold">{l} </span>
              <span className="font-semibold text-slate-700">${v.toFixed(2)}</span>
            </span>
          ))}
          {q.volume != null && (
            <span className="text-gray-400">
              Vol {(q.volume / 1_000_000).toFixed(1)}M
            </span>
          )}
        </div>
      )}

      {!q && <span className="text-gray-400 italic">No market data available</span>}

      {/* After-hours toggle */}
      <div className="ml-auto flex items-center gap-2">
        <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">After-hours trading</span>
        <button
          onClick={onToggleAfterHours}
          disabled={toggling}
          title={afterHoursEnabled ? 'Disable after-hours trading' : 'Enable after-hours trading'}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 ${
            afterHoursEnabled ? 'bg-violet-500' : 'bg-gray-300'
          }`}
        >
          <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
            afterHoursEnabled ? 'translate-x-4' : 'translate-x-0.5'
          }`} />
        </button>
        {afterHoursEnabled
          ? <Moon className="h-3.5 w-3.5 text-violet-500" />
          : <Sun className="h-3.5 w-3.5 text-amber-400" />}
      </div>
    </div>
  );
}

// ── Chart ─────────────────────────────────────────────────────────────────────

function PerformanceChart({ data, window, onWindowChange }:
  { data: PerformanceData; window: string; onWindowChange: (w: string) => void }) {

  // Merge price + value series by timestamp
  const merged = useMemo(() => {
    const map = new Map<string, { timestamp: string; price?: number; value?: number }>();
    for (const p of data.price_series) {
      map.set(p.timestamp, { timestamp: p.timestamp, price: p.price });
    }
    for (const v of data.value_series) {
      const existing = map.get(v.timestamp) ?? { timestamp: v.timestamp };
      existing.value = v.value;
      map.set(v.timestamp, existing);
    }
    return Array.from(map.values()).sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  }, [data]);

  // Build a set of trade timestamps for custom dot rendering
  const tradeSet = useMemo(() => new Map(
    data.trade_markers.map((t) => [t.timestamp, t])
  ), [data.trade_markers]);

  // Custom dot for BUY/SELL markers on the price line
  const PriceDot = (props: any) => {
    const { cx, cy, payload } = props;
    const trade = tradeSet.get(payload.timestamp);
    if (!trade || cx == null || cy == null) return null;
    const isBuy = trade.side === 'BUY';
    return (
      <g>
        <circle cx={cx} cy={cy} r={6} fill={isBuy ? '#16a34a' : '#dc2626'} opacity={0.9} />
        <text x={cx + 8} y={cy - 4} fontSize={9} fill={isBuy ? '#16a34a' : '#dc2626'} fontWeight="700">
          {isBuy ? '▲' : '▼'} {trade.side} {trade.qty.toFixed(0)}
        </text>
      </g>
    );
  };

  const anchor = data.anchor;
  const hasData = merged.length > 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-slate-800">Performance Chart</h3>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1 text-indigo-600">
              <svg width="16" height="3"><line x1="0" y1="1.5" x2="16" y2="1.5" stroke="#6366f1" strokeWidth="2" /></svg>
              Ticker price
            </span>
            <span className="flex items-center gap-1 text-amber-500">
              <svg width="16" height="3"><line x1="0" y1="1.5" x2="16" y2="1.5" stroke="#f59e0b" strokeWidth="2" strokeDasharray="4 2" /></svg>
              Position value
            </span>
            <span className="flex items-center gap-1 text-green-600 text-[10px]">● BUY</span>
            <span className="flex items-center gap-1 text-red-500 text-[10px]">● SELL</span>
          </div>
          <select
            value={window}
            onChange={(e) => onWindowChange(e.target.value)}
            className="border border-gray-200 rounded px-2 py-1 text-xs text-slate-600"
          >
            {['1d', '7d', '30d', 'all'].map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </div>
      </div>

      {!hasData ? (
        <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
          No evaluation data for this window yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={merged} margin={{ top: 10, right: 60, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={fmtTsShort}
              tick={{ fontSize: 9, fill: '#94a3b8' }}
              minTickGap={60}
            />
            {/* Left axis: ticker price */}
            <YAxis
              yAxisId="left"
              domain={['auto', 'auto']}
              tick={{ fontSize: 9, fill: '#6366f1' }}
              tickFormatter={(v) => `$${v.toFixed(2)}`}
              width={55}
            />
            {/* Right axis: position value */}
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={['auto', 'auto']}
              tick={{ fontSize: 9, fill: '#f59e0b' }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
              width={45}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                return (
                  <div className="bg-white border border-gray-200 rounded shadow-lg p-2 text-xs">
                    <div className="text-gray-400 mb-1">{fmtTs(label)}</div>
                    {payload.map((p: any) => (
                      <div key={p.name} style={{ color: p.color }}>
                        {p.name}: {p.name === 'price' ? `$${p.value?.toFixed(2)}` : `$${p.value?.toLocaleString()}`}
                      </div>
                    ))}
                  </div>
                );
              }}
            />

            {/* Anchor + trigger reference lines */}
            {anchor.price && (
              <ReferenceLine yAxisId="left" y={anchor.price} stroke="#a5b4fc" strokeDasharray="5 3"
                label={{ value: `Anchor $${anchor.price.toFixed(2)}`, position: 'insideTopLeft', fontSize: 9, fill: '#a5b4fc' }} />
            )}
            {anchor.trigger_up_price && (
              <ReferenceLine yAxisId="left" y={anchor.trigger_up_price} stroke="#fcd34d" strokeDasharray="3 3" opacity={0.8}
                label={{ value: `+${anchor.trigger_up_pct}% $${anchor.trigger_up_price.toFixed(2)}`, position: 'insideTopRight', fontSize: 8, fill: '#f59e0b' }} />
            )}
            {anchor.trigger_down_price && (
              <ReferenceLine yAxisId="left" y={anchor.trigger_down_price} stroke="#fcd34d" strokeDasharray="3 3" opacity={0.8}
                label={{ value: `${anchor.trigger_down_pct}% $${anchor.trigger_down_price.toFixed(2)}`, position: 'insideBottomRight', fontSize: 8, fill: '#f59e0b' }} />
            )}

            {/* Vertical drop lines for each trade */}
            {data.trade_markers.map((t) => (
              <ReferenceLine
                key={`tl-${t.timestamp}`}
                yAxisId="left"
                x={t.timestamp}
                stroke={t.side === 'BUY' ? '#16a34a' : '#dc2626'}
                strokeWidth={1}
                strokeDasharray="2 2"
                opacity={0.35}
              />
            ))}

            {/* Ticker price line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="price"
              stroke="#6366f1"
              strokeWidth={2}
              dot={<PriceDot />}
              activeDot={{ r: 4, fill: '#6366f1' }}
              name="price"
              connectNulls
            />
            {/* Position value line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="value"
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
              activeDot={{ r: 3, fill: '#f59e0b' }}
              name="value"
              connectNulls
            />

            <Brush dataKey="timestamp" height={18} tickFormatter={fmtTsShort}
              travellerWidth={6} stroke="#e2e8f0" fill="#f8fafc" />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── Position header ───────────────────────────────────────────────────────────

function PositionHeader({ position, cockpit, afterHoursEnabled, onToggleAfterHours, toggling }: {
  position: ReturnType<typeof useWorkspace>['selectedPosition'];
  cockpit: CockpitResponse | null;
  afterHoursEnabled: boolean;
  onToggleAfterHours: () => void;
  toggling: boolean;
}) {
  if (!position) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="flex items-start justify-between p-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-slate-900">{position.asset_symbol}</h1>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              position.status === 'RUNNING' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
            }`}>
              {position.status === 'RUNNING' ? '● Running' : '⏸ Paused'}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-black text-slate-900">
            {position.last_price != null ? `$${position.last_price.toFixed(2)}` : '—'}
          </div>
          {position.pct_from_anchor != null && (
            <div className={`text-sm font-semibold ${position.pct_from_anchor >= 0 ? 'text-green-600' : 'text-red-500'}`}>
              {fmtPct(position.pct_from_anchor)} from anchor
            </div>
          )}
          <div className="text-xs text-gray-400 mt-1">
            anchor {position.anchor_price != null ? `$${position.anchor_price.toFixed(2)}` : '—'}
          </div>
        </div>
      </div>

      {/* Stat chips */}
      <div className="flex flex-wrap gap-4 px-4 pb-4 pt-0 border-b border-gray-100">
        {[
          { label: 'Total Value', value: fmt$(position.total_value), sub: 'stock + cash' },
          { label: 'Stock Value', value: fmt$(position.stock_value), sub: `${position.qty.toFixed(4)} shares` },
          { label: 'Cash', value: fmt$(position.cash), sub: position.stock_pct != null ? `${(100 - position.stock_pct).toFixed(1)}% of cell` : '' },
          { label: 'P&L vs Baseline', value: fmtPct(position.position_vs_baseline_pct), color: clr(position.position_vs_baseline_pct) },
          { label: 'Avg Cost', value: position.avg_cost != null ? `$${position.avg_cost.toFixed(2)}` : '—', sub: '' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="flex flex-col min-w-[90px]">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">{label}</span>
            <span className={`text-sm font-bold mt-0.5 ${color ?? 'text-slate-900'}`}>{value}</span>
            {sub && <span className="text-[10px] text-gray-400">{sub}</span>}
          </div>
        ))}
      </div>

      {/* Market snapshot + after-hours toggle */}
      <MarketSnapshotBar
        cockpit={cockpit}
        afterHoursEnabled={afterHoursEnabled}
        onToggleAfterHours={onToggleAfterHours}
        toggling={toggling}
      />
    </div>
  );
}

// ── Trigger cards ─────────────────────────────────────────────────────────────

function TriggerCards({ position, perfData }: {
  position: ReturnType<typeof useWorkspace>['selectedPosition'];
  perfData: PerformanceData | null;
}) {
  if (!position) return null;
  const up = position.trigger_up_pct ?? 3;
  const dn = Math.abs(position.trigger_down_pct ?? -3);
  const pct = position.pct_from_anchor ?? 0;
  const upProgress = Math.min(pct > 0 ? (pct / up) * 100 : 0, 100);
  const dnProgress = Math.min(pct < 0 ? (Math.abs(pct) / dn) * 100 : 0, 100);

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Up trigger */}
      <div className="bg-white border border-gray-200 rounded-lg p-3">
        <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">▲ Upside trigger</div>
        <div className={`text-xl font-black mt-1 ${upProgress >= 100 ? 'text-amber-500' : 'text-green-600'}`}>
          {pct > 0 ? fmtPct(pct) : '0.00%'}
        </div>
        <div className="text-xs text-gray-400">of +{up}% threshold</div>
        <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${upProgress >= 80 ? 'bg-amber-400' : 'bg-indigo-300'}`}
               style={{ width: `${upProgress}%` }} />
        </div>
        {perfData?.anchor.trigger_up_price && (
          <div className="text-[10px] text-gray-400 mt-1">
            fires at ${perfData.anchor.trigger_up_price.toFixed(2)}
          </div>
        )}
      </div>
      {/* Down trigger */}
      <div className="bg-white border border-gray-200 rounded-lg p-3">
        <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">▼ Downside trigger</div>
        <div className={`text-xl font-black mt-1 ${dnProgress >= 100 ? 'text-amber-500' : 'text-red-500'}`}>
          {pct < 0 ? fmtPct(pct) : '0.00%'}
        </div>
        <div className="text-xs text-gray-400">of -{dn}% threshold</div>
        <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${dnProgress >= 80 ? 'bg-amber-400' : 'bg-indigo-300'}`}
               style={{ width: `${dnProgress}%` }} />
        </div>
        {perfData?.anchor.trigger_down_price && (
          <div className="text-[10px] text-gray-400 mt-1">
            fires at ${perfData.anchor.trigger_down_price.toFixed(2)}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main inner component ──────────────────────────────────────────────────────

type DetailTab = 'chart' | 'events' | 'orders' | 'strategy';

function PositionDetailInner() {
  const { positionId } = useParams<{ positionId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const portfolioId = searchParams.get('portfolio');

  const { positions, positionsLoading, selectedPosition, setSelectedPositionId, portfolioId: ctxPortfolioId } = useWorkspace();
  const { selectedTenantId } = useTenantPortfolio();

  const [activeTab, setActiveTab] = useState<DetailTab>('chart');
  const [perfWindow, setPerfWindow] = useState('7d');
  const [perfData, setPerfData] = useState<PerformanceData | null>(null);
  const [perfLoading, setPerfLoading] = useState(false);
  const [cockpit, setCockpit] = useState<CockpitResponse | null>(null);
  const [afterHoursEnabled, setAfterHoursEnabled] = useState(false);
  const [currentConfig, setCurrentConfig] = useState<PortfolioConfig | null>(null);
  const [toggling, setToggling] = useState(false);

  // Sync selected position from URL
  useEffect(() => {
    if (positionId) setSelectedPositionId(positionId);
  }, [positionId, setSelectedPositionId]);

  // Load performance data
  const loadPerf = async () => {
    if (!selectedTenantId || !ctxPortfolioId || !positionId) return;
    setPerfLoading(true);
    try {
      const d = await getPositionPerformance(selectedTenantId, ctxPortfolioId, positionId, perfWindow);
      setPerfData(d);
    } catch (e) {
      console.error('Failed to load performance data', e);
    } finally {
      setPerfLoading(false);
    }
  };

  // Load cockpit (market snapshot) + portfolio config (after-hours setting)
  const loadMeta = async () => {
    if (!ctxPortfolioId || !positionId || !selectedTenantId) return;
    try {
      const [ck, cfg] = await Promise.all([
        getPositionCockpit(ctxPortfolioId, positionId, '1d'),
        portfolioScopedApi.getConfig(selectedTenantId, ctxPortfolioId),
      ]);
      setCockpit(ck);
      setCurrentConfig(cfg);
      setAfterHoursEnabled(cfg.market_hours_policy === 'market-plus-after-hours');
    } catch (e) {
      console.error('Failed to load cockpit/config', e);
    }
  };

  useEffect(() => { loadPerf(); }, [positionId, ctxPortfolioId, selectedTenantId, perfWindow]);
  useEffect(() => { loadMeta(); }, [positionId, ctxPortfolioId, selectedTenantId]);

  const handleToggleAfterHours = async () => {
    if (!selectedTenantId || !ctxPortfolioId || !currentConfig) return;
    setToggling(true);
    const newPolicy = afterHoursEnabled ? 'market-open-only' : 'market-plus-after-hours';
    try {
      await portfolioScopedApi.updateConfig(selectedTenantId, ctxPortfolioId, {
        ...currentConfig,
        market_hours_policy: newPolicy,
      });
      setAfterHoursEnabled(!afterHoursEnabled);
      setCurrentConfig({ ...currentConfig, market_hours_policy: newPolicy });
      toast.success(`After-hours trading ${newPolicy === 'market-plus-after-hours' ? 'enabled' : 'disabled'}`);
    } catch (e) {
      toast.error('Failed to update after-hours setting');
    } finally {
      setToggling(false);
    }
  };

  const tabs: { id: DetailTab; label: string }[] = [
    { id: 'chart', label: 'Performance' },
    { id: 'events', label: 'Events' },
    { id: 'orders', label: 'Orders' },
    { id: 'strategy', label: 'Strategy' },
  ];

  return (
    <div className="h-screen flex flex-col bg-slate-50 overflow-hidden">

      {/* Top bar */}
      <div className="bg-slate-900 text-slate-200 flex items-center justify-between px-5 h-11 flex-shrink-0">
        <div className="flex items-center gap-3 text-sm">
          <button onClick={() => navigate('/')} className="flex items-center gap-1.5 text-slate-400 hover:text-white text-xs">
            <ArrowLeft className="h-4 w-4" /> Dashboard
          </button>
          <span className="text-slate-600">›</span>
          <span className="font-semibold text-white">
            {selectedPosition?.asset_symbol ?? positionId}
          </span>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">

        {/* Left: compact position nav */}
        <div className="w-52 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col overflow-y-auto">
          <div className="px-3 py-2 border-b border-gray-100 text-[10px] font-bold text-gray-400 uppercase tracking-wide flex-shrink-0">
            Positions
          </div>
          {positions.map((p) => {
            const isActive = p.position_id === positionId;
            const pnlColor = p.position_vs_baseline_pct == null ? 'text-gray-400'
              : p.position_vs_baseline_pct >= 0 ? 'text-green-600' : 'text-red-500';
            return (
              <button
                key={p.position_id}
                onClick={() => navigate(`/positions/${p.position_id}?portfolio=${ctxPortfolioId}`)}
                className={`w-full text-left px-3 py-2.5 border-b border-gray-100 transition-colors ${
                  isActive ? 'bg-indigo-50 border-l-[3px] border-l-indigo-500' : 'hover:bg-slate-50 border-l-[3px] border-l-transparent'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm text-slate-900">{p.asset_symbol}</span>
                  <span className={`text-xs font-semibold ${pnlColor}`}>
                    {p.position_vs_baseline_pct != null ? fmtPct(p.position_vs_baseline_pct) : '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-gray-500 mb-1.5">
                  <span>${p.total_value.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
                  <span className={`px-1 rounded text-[9px] font-bold ${p.status === 'RUNNING' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                    {p.status ?? 'UNKNOWN'}
                  </span>
                </div>
                {/* mini allocation bar */}
                <div className="h-1 bg-red-100 rounded-full relative overflow-hidden">
                  {p.guardrail_min_pct != null && p.guardrail_max_pct != null && (
                    <div className="absolute top-0 bottom-0 bg-violet-200 rounded-full"
                      style={{ left: `${p.guardrail_min_pct}%`, width: `${p.guardrail_max_pct - p.guardrail_min_pct}%` }} />
                  )}
                  {p.stock_pct != null && (
                    <div className="absolute top-[-1px] bottom-[-1px] w-[3px] bg-slate-700 rounded"
                      style={{ left: `${Math.min(Math.max(p.stock_pct, 0), 100)}%`, transform: 'translateX(-50%)' }} />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Right: detail */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">

          {positionsLoading ? (
            <LoadingSpinner message="Loading position..." />
          ) : !selectedPosition ? (
            <div className="text-center text-gray-400 py-12">Position not found</div>
          ) : (
            <>
              <PositionHeader
                position={selectedPosition}
                cockpit={cockpit}
                afterHoursEnabled={afterHoursEnabled}
                onToggleAfterHours={handleToggleAfterHours}
                toggling={toggling}
              />

              {/* Two-column: chart+tabs | right column */}
              <div className="grid grid-cols-[1fr_280px] gap-3">

                {/* Left: tabs */}
                <div className="space-y-3">
                  {/* Tab bar */}
                  <div className="flex gap-1 border-b border-gray-200">
                    {tabs.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id)}
                        className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
                          activeTab === t.id
                            ? 'border-indigo-500 text-indigo-600'
                            : 'border-transparent text-gray-500 hover:text-slate-700'
                        }`}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {activeTab === 'chart' && (
                    perfLoading ? (
                      <div className="bg-white border border-gray-200 rounded-lg p-8">
                        <LoadingSpinner message="Loading performance data..." />
                      </div>
                    ) : perfData ? (
                      <PerformanceChart data={perfData} window={perfWindow} onWindowChange={setPerfWindow} />
                    ) : (
                      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-400 text-sm">
                        No performance data available yet
                      </div>
                    )
                  )}
                  {activeTab === 'events' && <EventsTab />}
                  {activeTab === 'orders' && <OrdersTab />}
                  {activeTab === 'strategy' && <StrategyTab />}
                </div>

                {/* Right column: allocation + triggers */}
                <div className="space-y-3">
                  {/* Allocation */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h3 className="text-xs font-bold text-slate-800 mb-4">Allocation</h3>
                    <AllocationNeedleBar
                      currentPct={selectedPosition.stock_pct}
                      minPct={selectedPosition.guardrail_min_pct ?? perfData?.guardrails.min_stock_pct ?? null}
                      maxPct={selectedPosition.guardrail_max_pct ?? perfData?.guardrails.max_stock_pct ?? null}
                      height={14}
                      showLabels={true}
                    />
                    <div className="mt-3 text-xs text-gray-500 bg-slate-50 rounded p-2">
                      {selectedPosition.stock_pct != null &&
                       selectedPosition.guardrail_min_pct != null &&
                       selectedPosition.guardrail_max_pct != null ? (
                        selectedPosition.stock_pct < selectedPosition.guardrail_min_pct ||
                        selectedPosition.stock_pct > selectedPosition.guardrail_max_pct
                          ? <span className="text-red-600 font-semibold">⚠ Guardrail breach</span>
                          : <span className="text-green-600">✓ Within guardrails</span>
                      ) : '—'}
                    </div>
                  </div>

                  {/* Trigger cards */}
                  <TriggerCards position={selectedPosition} perfData={perfData} />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Export wrapped in WorkspaceProvider ───────────────────────────────────────

export default function PositionDetailPageV2() {
  return (
    <WorkspaceProvider>
      <PositionDetailInner />
    </WorkspaceProvider>
  );
}
