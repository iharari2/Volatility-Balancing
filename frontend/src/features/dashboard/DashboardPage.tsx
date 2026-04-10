import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RefreshCw, TrendingUp, TrendingDown, Minus, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useWorkspace, WorkspaceProvider } from '../workspace/WorkspaceContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioApi } from '../../lib/api';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import AllocationNeedleBar from '../../components/shared/AllocationNeedleBar';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import AddPositionModal from '../positions/modals/AddPositionModal';
import type { PositionSummaryItem } from '../../api/cockpit';

// ── helpers ──────────────────────────────────────────────────────────────────

function fmt$(n: number | null | undefined, dec = 0) {
  if (n == null) return '—';
  return '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
function fmtPct(n: number | null | undefined, dec = 1) {
  if (n == null) return '—';
  return (n >= 0 ? '+' : '') + n.toFixed(dec) + '%';
}
function clr(n: number | null | undefined) {
  if (n == null) return 'text-gray-400';
  return n >= 0 ? 'text-green-600' : 'text-red-500';
}

// ── Alert strip ───────────────────────────────────────────────────────────────

function AlertStrip({ positions }: { positions: PositionSummaryItem[] }) {
  const [dismissed, setDismissed] = useState<string[]>([]);

  const alerts = positions.flatMap((p) => {
    const msgs: { id: string; msg: string; level: 'warn' | 'danger' }[] = [];
    const { stock_pct, guardrail_min_pct, guardrail_max_pct, asset_symbol, pct_from_anchor,
            trigger_up_pct, trigger_down_pct } = p;

    if (stock_pct != null && guardrail_max_pct != null && stock_pct > guardrail_max_pct) {
      msgs.push({ id: `${p.position_id}-over`, level: 'danger',
        msg: `${asset_symbol} allocation ${stock_pct.toFixed(1)}% exceeds upper guardrail (${guardrail_max_pct}%)` });
    } else if (stock_pct != null && guardrail_max_pct != null && stock_pct > guardrail_max_pct * 0.95) {
      msgs.push({ id: `${p.position_id}-near-over`, level: 'warn',
        msg: `${asset_symbol} allocation ${stock_pct.toFixed(1)}% approaching upper guardrail (${guardrail_max_pct}%)` });
    }
    if (stock_pct != null && guardrail_min_pct != null && stock_pct < guardrail_min_pct) {
      msgs.push({ id: `${p.position_id}-under`, level: 'danger',
        msg: `${asset_symbol} allocation ${stock_pct.toFixed(1)}% below lower guardrail (${guardrail_min_pct}%)` });
    }
    if (pct_from_anchor != null && trigger_up_pct != null && pct_from_anchor >= trigger_up_pct) {
      msgs.push({ id: `${p.position_id}-trig-up`, level: 'warn',
        msg: `${asset_symbol} price +${pct_from_anchor.toFixed(2)}% from anchor — trigger fired` });
    }
    if (pct_from_anchor != null && trigger_down_pct != null && pct_from_anchor <= trigger_down_pct) {
      msgs.push({ id: `${p.position_id}-trig-dn`, level: 'warn',
        msg: `${asset_symbol} price ${pct_from_anchor.toFixed(2)}% from anchor — trigger fired` });
    }
    return msgs;
  }).filter((a) => !dismissed.includes(a.id));

  if (!alerts.length) return null;

  return (
    <div className="space-y-1 mb-3">
      {alerts.map((a) => (
        <div key={a.id}
          className={`flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-sm font-medium border ${
            a.level === 'danger'
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}
        >
          <span>{a.level === 'danger' ? '🚨' : '⚠️'} {a.msg}</span>
          <button onClick={() => setDismissed((d) => [...d, a.id])} className="text-current opacity-60 hover:opacity-100">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Trigger distance cell ─────────────────────────────────────────────────────

function TriggerDistanceCell({ pct_from_anchor, trigger_up_pct, trigger_down_pct, anchor_price, last_price }:
  { pct_from_anchor: number | null; trigger_up_pct: number | null; trigger_down_pct: number | null;
    anchor_price: number | null; last_price: number | null }) {
  const up = trigger_up_pct ?? 3;
  const dn = Math.abs(trigger_down_pct ?? -3);
  const pct = pct_from_anchor ?? 0;

  const upProgress = Math.min(Math.max(pct > 0 ? (pct / up) * 100 : 0, 0), 100);
  const dnProgress = Math.min(Math.max(pct < 0 ? (Math.abs(pct) / dn) * 100 : 0, 0), 100);

  const upNear = upProgress >= 80;
  const dnNear = dnProgress >= 80;

  return (
    <div className="space-y-1 min-w-[110px]">
      <div className="flex items-center gap-1.5 text-xs">
        <span className="text-gray-400 w-3">▲</span>
        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${upNear ? 'bg-amber-400' : 'bg-indigo-300'}`}
               style={{ width: `${upProgress}%` }} />
        </div>
        <span className={`min-w-[52px] text-right font-mono text-[11px] ${upNear ? 'text-amber-600 font-bold' : 'text-green-600'}`}>
          {pct > 0 ? `+${pct.toFixed(2)}` : '0.00'}% / {up}%
        </span>
      </div>
      <div className="flex items-center gap-1.5 text-xs">
        <span className="text-gray-400 w-3">▼</span>
        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${dnNear ? 'bg-amber-400' : 'bg-indigo-300'}`}
               style={{ width: `${dnProgress}%` }} />
        </div>
        <span className={`min-w-[52px] text-right font-mono text-[11px] ${dnNear ? 'text-amber-600 font-bold' : 'text-red-500'}`}>
          {pct < 0 ? `${pct.toFixed(2)}` : '0.00'}% / -{dn}%
        </span>
      </div>
      {anchor_price && last_price && (
        <div className="text-[10px] text-gray-400">
          anchor ${anchor_price.toFixed(2)} · now ${last_price.toFixed(2)}
        </div>
      )}
    </div>
  );
}

// ── Last action cell ──────────────────────────────────────────────────────────

function LastActionCell({ action }: { action: PositionSummaryItem['last_action'] }) {
  if (!action?.action) return <span className="text-gray-400 text-xs">—</span>;
  const a = action.action.toUpperCase();
  const pill =
    a === 'BUY'  ? 'bg-green-100 text-green-700' :
    a === 'SELL' ? 'bg-red-100 text-red-700' :
    a === 'HOLD' ? 'bg-gray-100 text-gray-600' : 'bg-gray-100 text-gray-600';
  const icon = a === 'BUY' ? '▲' : a === 'SELL' ? '▼' : '—';
  const ts = action.timestamp ? new Date(action.timestamp) : null;
  const label = ts ? ts.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div>
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${pill}`}>
        {icon} {a}
      </span>
      {label && <div className="text-[10px] text-gray-400 mt-0.5">{label}</div>}
      {action.reason && <div className="text-[10px] text-gray-400">{action.reason}</div>}
    </div>
  );
}

// ── Dashboard inner (uses useWorkspace) ───────────────────────────────────────

function DashboardInner() {
  const navigate = useNavigate();
  const { positions, positionsLoading, portfolioId, refreshPositions } = useWorkspace();
  const { selectedTenantId, selectedPortfolio, portfolios, setSelectedPortfolioId, refreshPortfolios } = useTenantPortfolio();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  // Auto-refresh every 60s
  useEffect(() => {
    const id = setInterval(() => refreshPositions(), 60_000);
    return () => clearInterval(id);
  }, [refreshPositions]);

  // Market status
  useEffect(() => {
    const update = async () => setMarketStatus((await marketHoursService.getMarketState()).status);
    update();
    const id = setInterval(update, 60_000);
    return () => clearInterval(id);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshPositions();
    setIsRefreshing(false);
  };

  const handleAddPosition = async (data: {
    ticker: string; qty: number; dollarValue: number;
    inputMode: 'qty' | 'dollar'; currentPrice: number;
    startingCash: { currency: string; amount: number };
  }) => {
    if (!selectedTenantId || !portfolioId) { toast.error('No portfolio selected'); return; }
    const finalQty = data.inputMode === 'qty' ? data.qty : data.dollarValue / data.currentPrice;
    await portfolioApi.createPosition(selectedTenantId, portfolioId, {
      asset: data.ticker, qty: finalQty,
      anchor_price: data.currentPrice, avg_cost: data.currentPrice,
      starting_cash: data.startingCash,
    });
    setShowAddModal(false);
    await refreshPositions();
    await refreshPortfolios();
    toast.success(`${data.ticker} position added`);
  };

  // KPIs
  const totalValue = positions.reduce((s, p) => s + p.total_value, 0);
  const totalCash  = positions.reduce((s, p) => s + p.cash, 0);
  const totalPnlPct = positions.length
    ? positions.reduce((s, p) => s + (p.position_vs_baseline_pct ?? 0), 0) / positions.length
    : null;
  const running = positions.filter((p) => p.status === 'RUNNING').length;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">

      {/* ── Top bar ── */}
      <div className="bg-slate-900 text-slate-200 flex items-center justify-between px-5 h-11 flex-shrink-0">
        <div className="flex items-center gap-3">
          <span className="font-bold text-white text-sm">⚡ Volatility Balancer</span>
          {/* Portfolio switcher */}
          {portfolios.length > 1 && (
            <select
              value={portfolioId ?? ''}
              onChange={(e) => setSelectedPortfolioId(e.target.value)}
              className="bg-slate-800 text-slate-200 text-xs border border-slate-700 rounded px-2 py-1"
            >
              {portfolios.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
          {portfolios.length === 1 && (
            <span className="text-slate-400 text-xs">{selectedPortfolio?.name}</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1 rounded-full">
            <span className={`w-2 h-2 rounded-full ${marketStatus === 'OPEN' ? 'bg-green-400 shadow-[0_0_6px_#4ade80]' : 'bg-slate-500'}`} />
            {marketStatus === 'OPEN' ? 'Market Open' : 'Market Closed'}
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="text-slate-400 hover:text-white disabled:opacity-40"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">

        {/* ── Left sidebar: portfolio summary ── */}
        <div className="w-52 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col py-3 px-3 gap-3">
          {/* Portfolio card */}
          {selectedPortfolio && (
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
              <div className="text-xs font-semibold text-indigo-700 mb-1">{selectedPortfolio.name}</div>
              <div className="text-xl font-black text-slate-900">{fmt$(totalValue)}</div>
              <div className="text-xs text-slate-500 mt-1">
                {positions.length} position{positions.length !== 1 ? 's' : ''} ·{' '}
                <span className={totalPnlPct == null ? '' : clr(totalPnlPct)}>
                  {totalPnlPct == null ? '—' : fmtPct(totalPnlPct)}
                </span>
              </div>
            </div>
          )}
          {/* Nav links */}
          <nav className="flex flex-col gap-0.5 text-xs font-medium">
            {[
              { label: '🏠 Dashboard', path: '/', active: true },
              { label: '📊 Analytics', path: '/analytics' },
              { label: '📋 Orders', path: '/?tab=orders' },
              { label: '💰 Dividends', path: '/?tab=dividends' },
              { label: '⚙️ Strategy', path: '/?tab=strategy' },
              { label: '📁 Portfolios', path: '/portfolios' },
            ].map(({ label, path, active }) => (
              <a key={path} href={path}
                className={`px-3 py-1.5 rounded-md transition-colors ${active ? 'bg-indigo-50 text-indigo-700' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'}`}>
                {label}
              </a>
            ))}
          </nav>
        </div>

        {/* ── Main content ── */}
        <div className="flex-1 overflow-y-auto p-4">

          {/* Alert strip */}
          {!positionsLoading && <AlertStrip positions={positions} />}

          {/* KPI row */}
          <div className="grid grid-cols-5 gap-3 mb-4">
            {[
              { label: 'Total AUM', value: fmt$(totalValue), sub: `${positions.length} positions` },
              { label: 'Total Cash', value: fmt$(totalCash), sub: `${totalValue > 0 ? ((totalCash / totalValue) * 100).toFixed(1) : '—'}% of AUM` },
              { label: 'Avg P&L', value: fmtPct(totalPnlPct), sub: 'vs baseline', color: clr(totalPnlPct) },
              { label: 'Running', value: String(running), sub: `of ${positions.length} positions` },
              { label: 'Last Refresh', value: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }), sub: 'auto every 60s' },
            ].map(({ label, value, sub, color }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">{label}</div>
                <div className={`text-xl font-black mt-1 ${color ?? 'text-slate-900'}`}>{value}</div>
                <div className="text-[11px] text-gray-400 mt-0.5">{sub}</div>
              </div>
            ))}
          </div>

          {/* Positions table */}
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-bold text-slate-800">Positions</h2>
            <button
              onClick={() => setShowAddModal(true)}
              disabled={!portfolioId}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-40"
            >
              <Plus className="h-3.5 w-3.5" /> Add Position
            </button>
          </div>

          {positionsLoading ? (
            <div className="bg-white border border-gray-200 rounded-lg p-12">
              <LoadingSpinner message="Loading positions..." />
            </div>
          ) : positions.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-gray-400">
              <div className="text-4xl mb-3">📭</div>
              <div className="font-semibold text-gray-600">No positions yet</div>
              <div className="text-sm mt-1">Add a position to start trading</div>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden mb-4">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-gray-200">
                    {['Asset', 'Status', 'Price', 'Qty', 'Stock Value', 'Cash', 'Total', 'P&L vs Baseline',
                      'Allocation (min / now / max)', 'Trigger Distance', 'Last Action'].map((h) => (
                      <th key={h} className="px-3 py-2 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {positions.map((p) => (
                    <tr
                      key={p.position_id}
                      onClick={() => navigate(`/positions/${p.position_id}?portfolio=${portfolioId}`)}
                      className="border-b border-gray-100 hover:bg-indigo-50/30 cursor-pointer transition-colors"
                    >
                      {/* Asset */}
                      <td className="px-3 py-3">
                        <div className="font-bold text-sm text-slate-900">{p.asset_symbol}</div>
                      </td>

                      {/* Status */}
                      <td className="px-3 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          p.status === 'RUNNING' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${p.status === 'RUNNING' ? 'bg-green-500' : 'bg-amber-500'}`} />
                          {p.status ?? 'UNKNOWN'}
                        </span>
                      </td>

                      {/* Price */}
                      <td className="px-3 py-3">
                        <div className="font-bold text-sm">{p.last_price != null ? `$${p.last_price.toFixed(2)}` : '—'}</div>
                        {p.pct_from_anchor != null && (
                          <div className={`text-[10px] ${clr(p.pct_from_anchor)}`}>{fmtPct(p.pct_from_anchor)} from anchor</div>
                        )}
                        {p.anchor_price != null && (
                          <div className="text-[10px] text-gray-400">anchor ${p.anchor_price.toFixed(2)}</div>
                        )}
                      </td>

                      {/* Qty */}
                      <td className="px-3 py-3 text-sm">{p.qty.toFixed(2)}</td>

                      {/* Stock value */}
                      <td className="px-3 py-3 text-sm font-semibold">{fmt$(p.stock_value)}</td>

                      {/* Cash */}
                      <td className="px-3 py-3 text-sm">{fmt$(p.cash)}</td>

                      {/* Total */}
                      <td className="px-3 py-3 text-sm font-bold">{fmt$(p.total_value)}</td>

                      {/* P&L */}
                      <td className="px-3 py-3">
                        <span className={`text-sm font-semibold ${clr(p.position_vs_baseline_pct)}`}>
                          {fmtPct(p.position_vs_baseline_pct)}
                        </span>
                      </td>

                      {/* Allocation bar */}
                      <td className="px-3 py-3" style={{ minWidth: 160 }}>
                        <AllocationNeedleBar
                          currentPct={p.stock_pct}
                          minPct={p.guardrail_min_pct}
                          maxPct={p.guardrail_max_pct}
                          height={10}
                          showLabels={true}
                        />
                      </td>

                      {/* Trigger distance */}
                      <td className="px-3 py-3">
                        <TriggerDistanceCell
                          pct_from_anchor={p.pct_from_anchor}
                          trigger_up_pct={p.trigger_up_pct}
                          trigger_down_pct={p.trigger_down_pct}
                          anchor_price={p.anchor_price}
                          last_price={p.last_price}
                        />
                      </td>

                      {/* Last action */}
                      <td className="px-3 py-3">
                        <LastActionCell action={p.last_action} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Strategy snapshot */}
          {positions.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-bold text-slate-800 mb-3">Strategy Snapshot</h3>
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    {['Asset', 'Trigger ▲', 'Trigger ▼', 'Guard Min', 'Guard Max', 'Auto-trade'].map((h) => (
                      <th key={h} className="pb-2 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wide pr-6">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {positions.map((p) => (
                    <tr key={p.position_id} className="border-b border-gray-50">
                      <td className="py-2 font-bold pr-6">{p.asset_symbol}</td>
                      <td className="py-2 pr-6 text-green-600">{p.trigger_up_pct != null ? `+${p.trigger_up_pct}%` : '—'}</td>
                      <td className="py-2 pr-6 text-red-500">{p.trigger_down_pct != null ? `${p.trigger_down_pct}%` : '—'}</td>
                      <td className="py-2 pr-6 text-indigo-600">{p.guardrail_min_pct != null ? `${p.guardrail_min_pct}%` : '—'}</td>
                      <td className="py-2 pr-6 text-indigo-600">{p.guardrail_max_pct != null ? `${p.guardrail_max_pct}%` : '—'}</td>
                      <td className="py-2">
                        <span className={`font-bold text-xs ${p.status === 'RUNNING' ? 'text-green-600' : 'text-amber-600'}`}>
                          {p.status === 'RUNNING' ? 'ON' : 'PAUSED'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showAddModal && (
        <AddPositionModal onClose={() => setShowAddModal(false)} onSave={handleAddPosition} />
      )}
    </div>
  );
}

// ── Export wrapped in WorkspaceProvider ───────────────────────────────────────

export default function DashboardPage() {
  return (
    <WorkspaceProvider>
      <DashboardInner />
    </WorkspaceProvider>
  );
}
