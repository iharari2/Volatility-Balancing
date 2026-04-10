import { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import {
  ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, Brush,
} from 'recharts';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { WorkspaceProvider, useWorkspace } from '../workspace/WorkspaceContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { getPositionPerformance, type PerformanceData } from '../../api/performance';
import AllocationNeedleBar from '../../components/shared/AllocationNeedleBar';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import PositionCellList from '../workspace/components/LeftPanel/PositionCellList';
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

function PositionHeader({ position }: { position: ReturnType<typeof useWorkspace>['selectedPosition'] }) {
  if (!position) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between">
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
      <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-gray-100">
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

  useEffect(() => { loadPerf(); }, [positionId, ctxPortfolioId, selectedTenantId, perfWindow]);

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

        {/* Left: compact position list */}
        <div className="w-52 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col">
          <div className="px-3 py-2 border-b border-gray-100 text-[10px] font-bold text-gray-400 uppercase tracking-wide">
            Positions
          </div>
          <PositionCellList />
        </div>

        {/* Right: detail */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">

          {positionsLoading ? (
            <LoadingSpinner message="Loading position..." />
          ) : !selectedPosition ? (
            <div className="text-center text-gray-400 py-12">Position not found</div>
          ) : (
            <>
              <PositionHeader position={selectedPosition} />

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
