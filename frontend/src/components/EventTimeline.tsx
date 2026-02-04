import { useState, useMemo } from 'react';
import { Event } from '../types';
import { format } from 'date-fns';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Target,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  Filter,
  X,
} from 'lucide-react';
import DateRangeFilter, { DateRange } from './shared/DateRangeFilter';
import EventTypeFilter, { filterEventsByType, getUniqueEventTypes } from './shared/EventTypeFilter';

interface EventTimelineProps {
  events: Event[];
  showFilters?: boolean;
  onFilterChange?: (filters: { dateRange: DateRange; eventTypes: string[] }) => void;
}

const getEventIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case 'position_created':
      return Activity;
    case 'anchor_set':
      return Target;
    case 'trigger_detected':
      return AlertCircle;
    case 'order_submitted':
      return TrendingUp;
    case 'order_filled':
      return CheckCircle;
    case 'order_cancelled':
    case 'order_rejected':
      return XCircle;
    default:
      return Info;
  }
};

const getEventColor = (type: string) => {
  switch (type.toLowerCase()) {
    case 'position_created':
      return 'text-primary-600 bg-primary-100';
    case 'anchor_set':
      return 'text-warning-600 bg-warning-100';
    case 'trigger_detected':
      return 'text-danger-600 bg-danger-100';
    case 'order_submitted':
      return 'text-primary-600 bg-primary-100';
    case 'order_filled':
      return 'text-success-600 bg-success-100';
    case 'order_cancelled':
    case 'order_rejected':
      return 'text-danger-600 bg-danger-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

export default function EventTimeline({ events, showFilters = false, onFilterChange }: EventTimelineProps) {
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });
  const [selectedEventTypes, setSelectedEventTypes] = useState<string[]>([]);
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  // Get unique event types from the events for dynamic filtering
  const availableEventTypes = useMemo(() => getUniqueEventTypes(events), [events]);

  // Apply filters locally
  const filteredEvents = useMemo(() => {
    let result = events;

    // Apply date range filter
    if (dateRange.startDate || dateRange.endDate) {
      result = result.filter((event) => {
        const eventDate = new Date(event.ts);
        if (dateRange.startDate && eventDate < new Date(dateRange.startDate)) return false;
        if (dateRange.endDate && eventDate > new Date(dateRange.endDate)) return false;
        return true;
      });
    }

    // Apply event type filter
    if (selectedEventTypes.length > 0) {
      result = filterEventsByType(result, selectedEventTypes);
    }

    return result;
  }, [events, dateRange, selectedEventTypes]);

  const handleDateRangeChange = (range: DateRange) => {
    setDateRange(range);
    onFilterChange?.({ dateRange: range, eventTypes: selectedEventTypes });
  };

  const handleEventTypesChange = (types: string[]) => {
    setSelectedEventTypes(types);
    onFilterChange?.({ dateRange, eventTypes: types });
  };

  const handleClearFilters = () => {
    setDateRange({ startDate: null, endDate: null });
    setSelectedEventTypes([]);
    onFilterChange?.({ dateRange: { startDate: null, endDate: null }, eventTypes: [] });
  };

  const hasActiveFilters = dateRange.startDate || dateRange.endDate || selectedEventTypes.length > 0;

  if (events.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Events Yet</h3>
          <p className="text-gray-500">
            Events will appear here as you interact with the position.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Event Timeline</h3>
        {showFilters && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded border transition-colors ${
                showFilterPanel || hasActiveFilters
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Filter className="h-4 w-4" />
              Filters
              {hasActiveFilters && (
                <span className="bg-primary-600 text-white px-1.5 py-0.5 rounded-full text-xs">
                  {(dateRange.startDate || dateRange.endDate ? 1 : 0) + (selectedEventTypes.length > 0 ? 1 : 0)}
                </span>
              )}
            </button>
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1 px-2 py-1.5 text-sm text-gray-500 hover:text-gray-700"
              >
                <X className="h-3 w-3" />
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {showFilters && showFilterPanel && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4">
          <DateRangeFilter value={dateRange} onChange={handleDateRangeChange} compact />
          <EventTypeFilter
            selectedTypes={selectedEventTypes}
            onChange={handleEventTypesChange}
            availableTypes={availableEventTypes.length > 0 ? availableEventTypes : undefined}
            compact
          />
        </div>
      )}

      {hasActiveFilters && (
        <div className="mb-4 text-sm text-gray-500">
          Showing {filteredEvents.length} of {events.length} events
        </div>
      )}

      {filteredEvents.length === 0 ? (
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Matching Events</h3>
          <p className="text-gray-500">
            No events match your current filters. Try adjusting or clearing filters.
          </p>
        </div>
      ) : (
        <div className="flow-root">
          <ul className="-mb-8">
            {filteredEvents.map((event, eventIdx) => {
              const Icon = getEventIcon(event.type);
              const colorClasses = getEventColor(event.type);

              return (
                <li key={event.id}>
                  <div className="relative pb-8">
                    {eventIdx !== filteredEvents.length - 1 ? (
                      <span
                        className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                        aria-hidden="true"
                      />
                    ) : null}
                    <div className="relative flex space-x-3">
                      <div>
                        <span
                          className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${colorClasses}`}
                        >
                          <Icon className="h-4 w-4" />
                        </span>
                      </div>
                      <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="text-sm font-medium text-gray-900">
                              {event.type.replace(/_/g, ' ').toUpperCase()}
                            </h4>
                            <span className="text-xs text-gray-500">
                              {format(new Date(event.ts), 'MMM d, yyyy h:mm:ss a')}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{event.message}</p>

                          {event.inputs && Object.keys(event.inputs).length > 0 && (
                            <div className="mt-2">
                              <details className="text-xs">
                                <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                                  View Inputs
                                </summary>
                                <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                  {JSON.stringify(event.inputs, null, 2)}
                                </pre>
                              </details>
                            </div>
                          )}

                          {event.outputs && Object.keys(event.outputs).length > 0 && (
                            <div className="mt-2">
                              <details className="text-xs">
                                <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                                  View Outputs
                                </summary>
                                <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                  {JSON.stringify(event.outputs, null, 2)}
                                </pre>
                              </details>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}


