import { useState, useMemo } from 'react';
import { Calendar, X } from 'lucide-react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

export interface DateRange {
  startDate: string | null;
  endDate: string | null;
}

export type DatePreset = 'today' | 'last24h' | 'last7d' | 'last30d' | 'custom' | 'all';

interface DateRangeFilterProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  showPresets?: boolean;
  className?: string;
  compact?: boolean;
}

const presets: { key: DatePreset; label: string }[] = [
  { key: 'all', label: 'All Time' },
  { key: 'today', label: 'Today' },
  { key: 'last24h', label: 'Last 24h' },
  { key: 'last7d', label: 'Last 7 days' },
  { key: 'last30d', label: 'Last 30 days' },
  { key: 'custom', label: 'Custom' },
];

function getPresetRange(preset: DatePreset): DateRange {
  const now = new Date();
  switch (preset) {
    case 'today':
      return {
        startDate: format(startOfDay(now), "yyyy-MM-dd'T'HH:mm"),
        endDate: format(endOfDay(now), "yyyy-MM-dd'T'HH:mm"),
      };
    case 'last24h':
      return {
        startDate: format(subDays(now, 1), "yyyy-MM-dd'T'HH:mm"),
        endDate: format(now, "yyyy-MM-dd'T'HH:mm"),
      };
    case 'last7d':
      return {
        startDate: format(subDays(now, 7), "yyyy-MM-dd'T'HH:mm"),
        endDate: format(now, "yyyy-MM-dd'T'HH:mm"),
      };
    case 'last30d':
      return {
        startDate: format(subDays(now, 30), "yyyy-MM-dd'T'HH:mm"),
        endDate: format(now, "yyyy-MM-dd'T'HH:mm"),
      };
    case 'all':
    case 'custom':
    default:
      return { startDate: null, endDate: null };
  }
}

function detectPreset(range: DateRange): DatePreset {
  if (!range.startDate && !range.endDate) return 'all';

  const now = new Date();
  const startDate = range.startDate ? new Date(range.startDate) : null;

  if (!startDate) return 'custom';

  const diffHours = (now.getTime() - startDate.getTime()) / (1000 * 60 * 60);

  if (diffHours <= 25 && diffHours >= 23) return 'last24h';
  if (diffHours <= 169 && diffHours >= 167) return 'last7d';
  if (diffHours <= 721 && diffHours >= 719) return 'last30d';

  // Check if it's "today"
  const todayStart = startOfDay(now);
  if (startDate.getTime() >= todayStart.getTime() && startDate.getTime() <= now.getTime()) {
    return 'today';
  }

  return 'custom';
}

export default function DateRangeFilter({
  value,
  onChange,
  showPresets = true,
  className = '',
  compact = false,
}: DateRangeFilterProps) {
  const [showCustom, setShowCustom] = useState(false);

  const activePreset = useMemo(() => detectPreset(value), [value]);

  const handlePresetClick = (preset: DatePreset) => {
    if (preset === 'custom') {
      setShowCustom(true);
      return;
    }
    setShowCustom(false);
    onChange(getPresetRange(preset));
  };

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...value, startDate: e.target.value || null });
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...value, endDate: e.target.value || null });
  };

  const handleClear = () => {
    setShowCustom(false);
    onChange({ startDate: null, endDate: null });
  };

  const hasFilter = value.startDate || value.endDate;

  if (compact) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <Calendar className="h-4 w-4 text-gray-400" />
        <select
          value={activePreset}
          onChange={(e) => handlePresetClick(e.target.value as DatePreset)}
          className="text-sm border border-gray-300 rounded px-2 py-1 bg-white"
        >
          {presets.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
        {(activePreset === 'custom' || showCustom) && (
          <>
            <input
              type="datetime-local"
              value={value.startDate || ''}
              onChange={handleStartDateChange}
              className="text-sm border border-gray-300 rounded px-2 py-1"
              placeholder="Start"
            />
            <span className="text-gray-400">to</span>
            <input
              type="datetime-local"
              value={value.endDate || ''}
              onChange={handleEndDateChange}
              className="text-sm border border-gray-300 rounded px-2 py-1"
              placeholder="End"
            />
          </>
        )}
        {hasFilter && (
          <button
            onClick={handleClear}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
            title="Clear filter"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {showPresets && (
        <div className="flex flex-wrap gap-2">
          {presets.map((p) => (
            <button
              key={p.key}
              onClick={() => handlePresetClick(p.key)}
              className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                activePreset === p.key
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      {(activePreset === 'custom' || showCustom || !showPresets) && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">From:</label>
            <input
              type="datetime-local"
              value={value.startDate || ''}
              onChange={handleStartDateChange}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">To:</label>
            <input
              type="datetime-local"
              value={value.endDate || ''}
              onChange={handleEndDateChange}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          {hasFilter && (
            <button
              onClick={handleClear}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 rounded border border-gray-300 hover:bg-gray-50"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}
        </div>
      )}

      {hasFilter && (
        <div className="text-xs text-gray-500">
          Filtering:{' '}
          {value.startDate && format(new Date(value.startDate), 'MMM d, yyyy HH:mm')}
          {value.startDate && value.endDate && ' - '}
          {value.endDate && format(new Date(value.endDate), 'MMM d, yyyy HH:mm')}
        </div>
      )}
    </div>
  );
}

// Helper to convert DateRange to API query params
export function dateRangeToParams(range: DateRange): Record<string, string> {
  const params: Record<string, string> = {};
  if (range.startDate) {
    params.start_date = new Date(range.startDate).toISOString();
  }
  if (range.endDate) {
    params.end_date = new Date(range.endDate).toISOString();
  }
  return params;
}

// Helper to get default date range (last 7 days)
export function getDefaultDateRange(): DateRange {
  return getPresetRange('last7d');
}
