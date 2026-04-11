import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, RefreshCw } from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { exportToExcel } from '../../utils/exportExcel';
import AnalyticsKPIs from './AnalyticsKPIs';
import AnalyticsCharts from './AnalyticsCharts';
import AnalyticsEventTables from './AnalyticsEventTables';

// ── types ─────────────────────────────────────────────────────────────────────

type AnalyticsPreset = '7d' | '30d' | '90d' | '1y' | 'all' | 'custom';
type Resolution = 'daily' | 'weekly' | 'hourly';

const PRESETS: { key: AnalyticsPreset; label: string; days: number | null }[] = [
  { key: '7d',  label: '7D',   days: 7   },
  { key: '30d', label: '30D',  days: 30  },
  { key: '90d', label: '90D',  days: 90  },
  { key: '1y',  label: '1Y',   days: 365 },
  { key: 'all', label: 'All',  days: null },
];

function toISODate(d: Date) {
  return d.toISOString().slice(0, 10);
}

// ── main ──────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const navigate = useNavigate();
  const { positions, loading: portfolioLoading } = usePortfolio();
  const { selectedPortfolio, selectedPortfolioId, selectedTenantId, portfolios, setSelectedPortfolioId } = useTenantPortfolio();

  // Filters
  const [selectedPositionId, setSelectedPositionId] = useState<string>('all');
  const [selectedPreset, setSelectedPreset] = useState<AnalyticsPreset>('30d');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>(toISODate(new Date()));
  const [resolution, setResolution] = useState<Resolution>('daily');
  const [benchmarks, setBenchmarks] = useState<string[]>(['buy_hold', 'spy']);
  const [customTicker, setCustomTicker] = useState<string>('');
  const [customTickerInput, setCustomTickerInput] = useState<string>('');

  // Data
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // ── derived dates ────────────────────────────────────────────────────────────

  const { effectiveStartDate, effectiveEndDate } = useMemo(() => {
    if (selectedPreset === 'all') return { effectiveStartDate: undefined, effectiveEndDate: undefined };
    if (selectedPreset === 'custom') return { effectiveStartDate: startDate || undefined, effectiveEndDate: endDate || undefined };
    const preset = PRESETS.find((p) => p.key === selectedPreset);
    if (!preset?.days) return { effectiveStartDate: undefined, effectiveEndDate: undefined };
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - preset.days);
    return { effectiveStartDate: toISODate(start), effectiveEndDate: toISODate(end) };
  }, [selectedPreset, startDate, endDate]);

  const effectiveResolution = useMemo<Resolution>(() => {
    if (resolution !== 'hourly') return resolution;
    if (!effectiveStartDate) return 'daily';
    const diffDays = (new Date(effectiveEndDate ?? new Date()).getTime() - new Date(effectiveStartDate).getTime()) / 86400000;
    return diffDays <= 30 ? 'hourly' : 'daily';
  }, [resolution, effectiveStartDate, effectiveEndDate]);

  // ── handlers ─────────────────────────────────────────────────────────────────

  const handlePresetClick = (preset: AnalyticsPreset) => {
    setSelectedPreset(preset);
    if (preset !== 'custom') {
      if (preset === 'all') { setStartDate(''); setEndDate(toISODate(new Date())); }
      else {
        const p = PRESETS.find((x) => x.key === preset);
        if (p?.days) { const s = new Date(); s.setDate(s.getDate() - p.days); setStartDate(toISODate(s)); setEndDate(toISODate(new Date())); }
      }
    }
  };

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    if (field === 'start') setStartDate(value); else setEndDate(value);
    setSelectedPreset('custom');
  };

  const toggleBenchmark = (bm: string) =>
    setBenchmarks((prev) => prev.includes(bm) ? prev.filter((x) => x !== bm) : [...prev, bm]);

  const applyCustomTicker = () => {
    const t = customTickerInput.trim().toUpperCase();
    if (t) { setCustomTicker(t); if (!benchmarks.includes('custom')) setBenchmarks((p) => [...p, 'custom']); }
    else { setCustomTicker(''); setBenchmarks((p) => p.filter((x) => x !== 'custom')); }
  };

  // ── data fetch ───────────────────────────────────────────────────────────────

  useEffect(() => {
    const fetch = async () => {
      if (!selectedTenantId || !selectedPortfolioId) { setAnalyticsData(null); return; }
      setLoadingAnalytics(true);
      setAnalyticsError(null);
      try {
        const { portfolioScopedApi } = await import('../../services/portfolioScopedApi');
        const data = await portfolioScopedApi.getAnalytics(
          selectedTenantId, selectedPortfolioId, 0,
          selectedPositionId !== 'all' ? selectedPositionId : undefined,
          effectiveStartDate, effectiveEndDate, effectiveResolution,
          benchmarks, customTicker || undefined,
        );
        setAnalyticsData(data);
      } catch (err: any) {
        setAnalyticsError(err?.message || 'Failed to load analytics data');
        setAnalyticsData(null);
      } finally {
        setLoadingAnalytics(false);
      }
    };
    fetch();
  }, [selectedTenantId, selectedPortfolioId, selectedPositionId, effectiveStartDate, effectiveEndDate, effectiveResolution, benchmarks, customTicker]);

  const filteredPositions = useMemo(
    () => selectedPositionId === 'all' ? positions : positions.filter((p) => p.id === selectedPositionId),
    [positions, selectedPositionId],
  );

  const handleExport = async () => {
    if (!selectedTenantId || !selectedPortfolioId) return;
    const params = new URLSearchParams({ tenant_id: selectedTenantId, portfolio_id: selectedPortfolioId });
    if (selectedPositionId !== 'all') params.set('position_id', selectedPositionId);
    if (effectiveStartDate) params.set('start_date', effectiveStartDate);
    if (effectiveEndDate) params.set('end_date', effectiveEndDate);
    if (effectiveResolution) params.set('resolution', effectiveResolution);
    await exportToExcel(`/v1/excel/analytics/export?${params.toString()}`, 'analytics.xlsx');
  };

  // ── render ───────────────────────────────────────────────────────────────────

  return (
    <div className="h-screen flex flex-col bg-slate-50 overflow-hidden">

      {/* ── Top bar ── */}
      <div className="bg-slate-900 text-slate-200 flex items-center justify-between px-5 h-11 flex-shrink-0">
        <div className="flex items-center gap-3 text-sm">
          <button onClick={() => navigate('/')} className="flex items-center gap-1.5 text-slate-400 hover:text-white text-xs">
            <ArrowLeft className="h-4 w-4" /> Dashboard
          </button>
          <span className="text-slate-600">›</span>
          <span className="font-semibold text-white">Analytics</span>
          {selectedPortfolio && <span className="text-slate-400 text-xs">— {selectedPortfolio.name}</span>}
        </div>
        <div className="flex items-center gap-2">
          {/* Portfolio switcher */}
          {portfolios.length > 1 && (
            <select
              value={selectedPortfolioId ?? ''}
              onChange={(e) => setSelectedPortfolioId(e.target.value)}
              className="bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1 focus:outline-none"
            >
              {portfolios.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          )}
          <button
            onClick={handleExport}
            disabled={!analyticsData}
            className="flex items-center gap-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-white text-xs font-semibold px-3 py-1.5 rounded transition-colors"
          >
            <Download className="h-3.5 w-3.5" /> Export
          </button>
        </div>
      </div>

      {/* ── Controls bar ── */}
      <div className="bg-white border-b border-gray-200 px-5 py-2.5 flex flex-wrap items-center gap-x-5 gap-y-2 flex-shrink-0">

        {/* Time presets */}
        <div className="flex items-center gap-1">
          {PRESETS.map((p) => (
            <button key={p.key} onClick={() => handlePresetClick(p.key)}
              className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
                selectedPreset === p.key ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}>
              {p.label}
            </button>
          ))}
          <button onClick={() => setSelectedPreset('custom')}
            className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
              selectedPreset === 'custom' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}>
            Custom
          </button>
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Date range */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-400 font-medium">From</span>
          <input type="date" value={startDate} onChange={(e) => handleDateChange('start', e.target.value)}
            className="border border-gray-200 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-indigo-400" />
          <span className="text-gray-400 font-medium">To</span>
          <input type="date" value={endDate} onChange={(e) => handleDateChange('end', e.target.value)}
            className="border border-gray-200 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-indigo-400" />
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Resolution */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-gray-400 font-medium">Res</span>
          <div className="flex border border-gray-200 rounded overflow-hidden">
            {(['daily', 'weekly', 'hourly'] as Resolution[]).map((r) => {
              const disabled = r === 'hourly' && resolution === 'hourly' && effectiveResolution !== 'hourly';
              return (
                <button key={r} onClick={() => setResolution(r)} disabled={disabled}
                  className={`px-2.5 py-1 font-medium capitalize transition-colors ${
                    effectiveResolution === r ? 'bg-indigo-600 text-white'
                    : disabled ? 'bg-gray-50 text-gray-300 cursor-not-allowed'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                  }`}>
                  {r}
                </button>
              );
            })}
          </div>
          {resolution === 'hourly' && effectiveResolution !== 'hourly' && (
            <span className="text-amber-500 text-[10px]">Range too wide</span>
          )}
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Position filter */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-gray-400 font-medium">Position</span>
          <select value={selectedPositionId} onChange={(e) => setSelectedPositionId(e.target.value)}
            className="border border-gray-200 rounded px-2 py-1 text-xs bg-white focus:ring-1 focus:ring-indigo-400">
            <option value="all">All</option>
            {positions.map((p) => <option key={p.id} value={p.id}>{p.ticker || p.asset}</option>)}
          </select>
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Benchmarks */}
        <div className="flex items-center gap-3 text-xs">
          <span className="text-gray-400 font-medium">vs</span>
          {[{ key: 'buy_hold', label: 'Buy & Hold' }, { key: 'spy', label: 'S&P 500' }].map((bm) => (
            <label key={bm.key} className="flex items-center gap-1 cursor-pointer">
              <input type="checkbox" checked={benchmarks.includes(bm.key)} onChange={() => toggleBenchmark(bm.key)} className="rounded accent-indigo-600" />
              <span className="text-gray-700">{bm.label}</span>
            </label>
          ))}
          <label className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={benchmarks.includes('custom')}
              onChange={() => {
                if (benchmarks.includes('custom')) { setBenchmarks((p) => p.filter((x) => x !== 'custom')); setCustomTicker(''); }
                else if (customTicker) setBenchmarks((p) => [...p, 'custom']);
              }}
              className="rounded accent-indigo-600" />
            <span className="text-gray-700">Custom:</span>
          </label>
          <input type="text" value={customTickerInput} placeholder="QQQ"
            onChange={(e) => setCustomTickerInput(e.target.value.toUpperCase())}
            onBlur={applyCustomTicker}
            onKeyDown={(e) => e.key === 'Enter' && applyCustomTicker()}
            className="w-14 border border-gray-200 rounded px-1.5 py-0.5 text-xs focus:ring-1 focus:ring-indigo-400" />
        </div>

        {/* Loading spinner */}
        {loadingAnalytics && <RefreshCw className="h-3.5 w-3.5 text-indigo-400 animate-spin ml-auto" />}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">

        {!selectedPortfolio ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-gray-400 text-sm">
            Select a portfolio to view analytics
          </div>
        ) : analyticsError ? (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
            <span className="font-semibold">Analytics unavailable: </span>{analyticsError}
          </div>
        ) : null}

        {selectedPortfolio && !portfolioLoading && (
          <>
            <AnalyticsKPIs positions={filteredPositions} analyticsData={analyticsData} />
            <AnalyticsCharts
              positions={filteredPositions}
              analyticsData={analyticsData}
              activeBenchmarks={benchmarks}
              customTicker={customTicker}
            />
            <AnalyticsEventTables events={analyticsData?.events || []} />
          </>
        )}

        {portfolioLoading && (
          <div className="text-center py-12 text-gray-400 text-sm">Loading portfolio data...</div>
        )}
      </div>
    </div>
  );
}
