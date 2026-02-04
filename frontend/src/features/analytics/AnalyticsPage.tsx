import { useState, useEffect, useMemo } from 'react';
import { Download, Filter, Calendar } from 'lucide-react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import AnalyticsKPIs from './AnalyticsKPIs';
import AnalyticsCharts from './AnalyticsCharts';
import AnalyticsEventTables from './AnalyticsEventTables';

// Analytics-specific time period presets
type AnalyticsPreset = '7d' | '30d' | '90d' | '1y' | 'all';

const analyticsPresets: { key: AnalyticsPreset; label: string; days: number | null }[] = [
  { key: '7d', label: '7D', days: 7 },
  { key: '30d', label: '30D', days: 30 },
  { key: '90d', label: '90D', days: 90 },
  { key: '1y', label: '1Y', days: 365 },
  { key: 'all', label: 'All', days: null },
];

export default function AnalyticsPage() {
  const { positions, loading: portfolioLoading } = usePortfolio();
  const { selectedPortfolio, selectedPortfolioId, selectedTenantId } = useTenantPortfolio();
  const [selectedPositionId, setSelectedPositionId] = useState<string>('all');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<AnalyticsPreset>('30d');

  // Calculate days from preset
  const days = useMemo(() => {
    const preset = analyticsPresets.find((p) => p.key === selectedPreset);
    return preset?.days ?? 365; // Default to 1 year for "all"
  }, [selectedPreset]);

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
        // Pass selectedPositionId to filter analytics by position
        const positionFilter = selectedPositionId !== 'all' ? selectedPositionId : undefined;
        const data = await portfolioScopedApi.getAnalytics(selectedTenantId, selectedPortfolioId, days, positionFilter);
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
  }, [selectedTenantId, selectedPortfolioId, selectedPositionId, days]);

  const filteredPositions = useMemo(() => {
    if (selectedPositionId === 'all') return positions;
    return positions.filter((p) => p.id === selectedPositionId);
  }, [positions, selectedPositionId]);

  const handleExport = () => {
    const positionParam = selectedPositionId !== 'all' ? `&positionId=${selectedPositionId}` : '';
    window.open(`/api/v1/excel/analytics/export?format=xlsx${positionParam}`, '_blank');
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
        <div className="flex items-center gap-3">
          {/* Time Period Selector */}
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            <Calendar className="h-4 w-4 text-gray-400 ml-2" />
            {analyticsPresets.map((preset) => (
              <button
                key={preset.key}
                onClick={() => setSelectedPreset(preset.key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  selectedPreset === preset.key
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {preset.label}
              </button>
            ))}
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
      <AnalyticsCharts positions={filteredPositions} analyticsData={analyticsData} />

      {/* Event Tables (ANA-7) */}
      <AnalyticsEventTables events={analyticsData?.events || []} />
    </div>
  );
}







