import { useState, useEffect, useMemo } from 'react';
import { exportToExcel } from '../../utils/exportExcel';
import { Download, Filter, Calendar } from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import AnalyticsKPIs from './AnalyticsKPIs';
import AnalyticsCharts from './AnalyticsCharts';
import AnalyticsEventTables from './AnalyticsEventTables';

// Analytics-specific time period presets
type AnalyticsPreset = '7d' | '30d' | '90d' | '1y' | 'all' | 'custom';

const analyticsPresets: { key: AnalyticsPreset; label: string; days: number | null }[] = [
  { key: '7d', label: '7D', days: 7 },
  { key: '30d', label: '30D', days: 30 },
  { key: '90d', label: '90D', days: 90 },
  { key: '1y', label: '1Y', days: 365 },
  { key: 'all', label: 'All', days: null },
];

type Resolution = 'daily' | 'weekly' | 'hourly';

function toISODate(d: Date) {
  return d.toISOString().slice(0, 10);
}

export default function AnalyticsPage() {
  const { positions, loading: portfolioLoading } = usePortfolio();
  const { selectedPortfolio, selectedPortfolioId, selectedTenantId } = useTenantPortfolio();
  const [selectedPositionId, setSelectedPositionId] = useState<string>('all');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<AnalyticsPreset>('30d');

  // Explicit date pickers (used when preset = 'custom' or when user edits them)
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>(toISODate(new Date()));

  // Resolution
  const [resolution, setResolution] = useState<Resolution>('daily');

  // Benchmark selector
  const [benchmarks, setBenchmarks] = useState<string[]>(['buy_hold', 'spy']);
  const [customTicker, setCustomTicker] = useState<string>('');
  const [customTickerInput, setCustomTickerInput] = useState<string>('');

  // Derive effective start/end from preset
  const { effectiveStartDate, effectiveEndDate } = useMemo(() => {
    if (selectedPreset === 'all') {
      return { effectiveStartDate: undefined, effectiveEndDate: undefined };
    }
    if (selectedPreset === 'custom') {
      return {
        effectiveStartDate: startDate || undefined,
        effectiveEndDate: endDate || undefined,
      };
    }
    const preset = analyticsPresets.find((p) => p.key === selectedPreset);
    const days = preset?.days;
    if (!days) return { effectiveStartDate: undefined, effectiveEndDate: undefined };
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    return {
      effectiveStartDate: toISODate(start),
      effectiveEndDate: toISODate(end),
    };
  }, [selectedPreset, startDate, endDate]);

  // Enforce hourly only for ≤30 day ranges
  const effectiveResolution = useMemo<Resolution>(() => {
    if (resolution !== 'hourly') return resolution;
    // Check day span
    if (!effectiveStartDate) return 'daily'; // "all" → force daily
    const start = new Date(effectiveStartDate);
    const end = effectiveEndDate ? new Date(effectiveEndDate) : new Date();
    const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
    return diffDays <= 30 ? 'hourly' : 'daily';
  }, [resolution, effectiveStartDate, effectiveEndDate]);

  const handlePresetClick = (preset: AnalyticsPreset) => {
    setSelectedPreset(preset);
    if (preset !== 'custom') {
      // Reset custom date inputs to reflect new preset visually
      if (preset === 'all') {
        setStartDate('');
        setEndDate(toISODate(new Date()));
      } else {
        const p = analyticsPresets.find((x) => x.key === preset);
        if (p?.days) {
          const s = new Date();
          s.setDate(s.getDate() - p.days);
          setStartDate(toISODate(s));
          setEndDate(toISODate(new Date()));
        }
      }
    }
  };

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    if (field === 'start') setStartDate(value);
    else setEndDate(value);
    setSelectedPreset('custom');
  };

  const toggleBenchmark = (bm: string) => {
    setBenchmarks((prev) =>
      prev.includes(bm) ? prev.filter((x) => x !== bm) : [...prev, bm],
    );
  };

  const applyCustomTicker = () => {
    const t = customTickerInput.trim().toUpperCase();
    if (t) {
      setCustomTicker(t);
      if (!benchmarks.includes('custom')) setBenchmarks((prev) => [...prev, 'custom']);
    } else {
      setCustomTicker('');
      setBenchmarks((prev) => prev.filter((x) => x !== 'custom'));
    }
  };

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!selectedTenantId || !selectedPortfolioId) {
        setAnalyticsData(null);
        setAnalyticsError(null);
        return;
      }

      setLoadingAnalytics(true);
      setAnalyticsError(null);
      try {
        const { portfolioScopedApi } = await import('../../services/portfolioScopedApi');
        const positionFilter = selectedPositionId !== 'all' ? selectedPositionId : undefined;
        const data = await portfolioScopedApi.getAnalytics(
          selectedTenantId,
          selectedPortfolioId,
          0,
          positionFilter,
          effectiveStartDate,
          effectiveEndDate,
          effectiveResolution,
          benchmarks,
          customTicker || undefined,
        );
        setAnalyticsData(data);
      } catch (error: any) {
        console.error('Error fetching analytics:', error);
        setAnalyticsError(
          error?.message ||
            error?.detail ||
            error?.response?.data?.detail ||
            'Failed to load analytics data',
        );
        setAnalyticsData(null);
      } finally {
        setLoadingAnalytics(false);
      }
    };

    fetchAnalytics();
  }, [
    selectedTenantId,
    selectedPortfolioId,
    selectedPositionId,
    effectiveStartDate,
    effectiveEndDate,
    effectiveResolution,
    benchmarks,
    customTicker,
  ]);

  const filteredPositions = useMemo(() => {
    if (selectedPositionId === 'all') return positions;
    return positions.filter((p) => p.id === selectedPositionId);
  }, [positions, selectedPositionId]);

  const handleExport = async () => {
    if (!selectedTenantId || !selectedPortfolioId) return;
    const positionFilter = selectedPositionId !== 'all' ? selectedPositionId : undefined;
    const params = new URLSearchParams({ tenant_id: selectedTenantId, portfolio_id: selectedPortfolioId });
    if (positionFilter) params.set('position_id', positionFilter);
    if (effectiveStartDate) params.set('start_date', effectiveStartDate);
    if (effectiveEndDate) params.set('end_date', effectiveEndDate);
    if (effectiveResolution) params.set('resolution', effectiveResolution);
    await exportToExcel(`/v1/excel/analytics/export?${params.toString()}`, 'analytics.xlsx');
  };

  if (!selectedPortfolio) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">Please select a portfolio to view analytics</p>
      </div>
    );
  }

  if (portfolioLoading || loadingAnalytics) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
          <p className="text-sm text-gray-500 mt-1">
            {selectedPortfolio.name} •{' '}
            {selectedPositionId === 'all'
              ? 'All Cells'
              : positions.find((p) => p.id === selectedPositionId)?.ticker || 'Selected Cell'}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Time Period Presets */}
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            <Calendar className="h-4 w-4 text-gray-400 ml-2" />
            {analyticsPresets.map((preset) => (
              <button
                key={preset.key}
                onClick={() => handlePresetClick(preset.key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  selectedPreset === preset.key
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {preset.label}
              </button>
            ))}
            <button
              onClick={() => setSelectedPreset('custom')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                selectedPreset === 'custom'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Custom
            </button>
          </div>

          {/* Position Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={selectedPositionId}
              onChange={(e) => setSelectedPositionId(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none text-sm bg-white"
            >
              <option value="all">All Cells</option>
              {positions.map((pos) => (
                <option key={pos.id} value={pos.id}>
                  {pos.ticker || pos.asset} Cell
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleExport}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Custom date pickers — visible when preset = 'custom' or always for refinement */}
      <div className="flex flex-wrap items-center gap-4 bg-gray-50 rounded-lg p-3 border border-gray-200">
        {/* Date Range */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 font-medium">From</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => handleDateChange('start', e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500"
          />
          <label className="text-xs text-gray-500 font-medium">To</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => handleDateChange('end', e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="h-4 w-px bg-gray-300" />

        {/* Resolution */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 font-medium">Resolution</label>
          <div className="flex border border-gray-300 rounded overflow-hidden text-xs">
            {(['daily', 'weekly', 'hourly'] as Resolution[]).map((r) => {
              const disabled = r === 'hourly' && effectiveResolution !== 'hourly' && resolution === 'hourly';
              return (
                <button
                  key={r}
                  onClick={() => setResolution(r)}
                  disabled={disabled}
                  className={`px-3 py-1 font-medium transition-colors capitalize ${
                    effectiveResolution === r
                      ? 'bg-blue-600 text-white'
                      : disabled
                        ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                        : 'bg-white text-gray-600 hover:bg-gray-50'
                  }`}
                  title={r === 'hourly' ? 'Available for ≤30 day ranges only' : undefined}
                >
                  {r}
                </button>
              );
            })}
          </div>
          {resolution === 'hourly' && effectiveResolution !== 'hourly' && (
            <span className="text-xs text-amber-600">Range too wide — switched to daily</span>
          )}
        </div>

        <div className="h-4 w-px bg-gray-300" />

        {/* Benchmark Selector */}
        <div className="flex items-center gap-2 flex-wrap">
          <label className="text-xs text-gray-500 font-medium">Benchmarks</label>
          {[
            { key: 'buy_hold', label: 'Buy & Hold' },
            { key: 'spy', label: 'S&P 500' },
          ].map((bm) => (
            <label key={bm.key} className="flex items-center gap-1 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={benchmarks.includes(bm.key)}
                onChange={() => toggleBenchmark(bm.key)}
                className="rounded"
              />
              {bm.label}
            </label>
          ))}
          <div className="flex items-center gap-1">
            <label className="flex items-center gap-1 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={benchmarks.includes('custom')}
                onChange={() => {
                  if (benchmarks.includes('custom')) {
                    setBenchmarks((p) => p.filter((x) => x !== 'custom'));
                    setCustomTicker('');
                  } else if (customTicker) {
                    setBenchmarks((p) => [...p, 'custom']);
                  }
                }}
                className="rounded"
              />
              Custom:
            </label>
            <input
              type="text"
              value={customTickerInput}
              onChange={(e) => setCustomTickerInput(e.target.value.toUpperCase())}
              onBlur={applyCustomTicker}
              onKeyDown={(e) => e.key === 'Enter' && applyCustomTicker()}
              placeholder="QQQ"
              className="w-16 text-xs border border-gray-300 rounded px-1 py-0.5 focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Error Display */}
      {analyticsError && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Analytics Data Unavailable</h3>
              <p className="mt-1 text-sm text-yellow-700">{analyticsError}</p>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <AnalyticsKPIs positions={filteredPositions} analyticsData={analyticsData} />

      {/* Charts */}
      <AnalyticsCharts
        positions={filteredPositions}
        analyticsData={analyticsData}
        activeBenchmarks={benchmarks}
        customTicker={customTicker}
      />

      {/* Event Tables */}
      <AnalyticsEventTables events={analyticsData?.events || []} />
    </div>
  );
}
