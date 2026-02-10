import { useState, useRef, useEffect } from 'react';
import { Filter, X, ChevronDown, Check } from 'lucide-react';

export type EventType =
  | 'position_created'
  | 'anchor_set'
  | 'trigger_detected'
  | 'order_submitted'
  | 'order_filled'
  | 'order_cancelled'
  | 'order_rejected'
  | 'hold'
  | 'buy'
  | 'sell'
  | 'error'
  | 'info'
  | 'dividend'
  | 'DAILY_CHECK'
  | 'PRICE_UPDATE'
  | 'TRIGGER_EVALUATED'
  | 'EXECUTION';

interface EventTypeOption {
  value: string;
  label: string;
  category?: string;
}

const defaultEventTypes: EventTypeOption[] = [
  // Position events
  { value: 'position_created', label: 'Position Created', category: 'Position' },
  { value: 'anchor_set', label: 'Anchor Set', category: 'Position' },
  // Trigger events
  { value: 'trigger_detected', label: 'Trigger Detected', category: 'Trigger' },
  { value: 'TRIGGER_EVALUATED', label: 'Trigger Evaluated', category: 'Trigger' },
  // Order events
  { value: 'order_submitted', label: 'Order Submitted', category: 'Order' },
  { value: 'order_filled', label: 'Order Filled', category: 'Order' },
  { value: 'order_cancelled', label: 'Order Cancelled', category: 'Order' },
  { value: 'order_rejected', label: 'Order Rejected', category: 'Order' },
  // Action events
  { value: 'buy', label: 'Buy', category: 'Action' },
  { value: 'sell', label: 'Sell', category: 'Action' },
  { value: 'hold', label: 'Hold', category: 'Action' },
  // Evaluation types
  { value: 'DAILY_CHECK', label: 'Daily Check', category: 'Evaluation' },
  { value: 'PRICE_UPDATE', label: 'Price Update', category: 'Evaluation' },
  { value: 'EXECUTION', label: 'Execution', category: 'Evaluation' },
  // Other
  { value: 'dividend', label: 'Dividend', category: 'Other' },
  { value: 'error', label: 'Error', category: 'Other' },
  { value: 'info', label: 'Info', category: 'Other' },
];

interface EventTypeFilterProps {
  selectedTypes: string[];
  onChange: (types: string[]) => void;
  availableTypes?: EventTypeOption[];
  className?: string;
  compact?: boolean;
  placeholder?: string;
}

export default function EventTypeFilter({
  selectedTypes,
  onChange,
  availableTypes = defaultEventTypes,
  className = '',
  compact = false,
  placeholder = 'All Event Types',
}: EventTypeFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (type: string) => {
    if (selectedTypes.includes(type)) {
      onChange(selectedTypes.filter((t) => t !== type));
    } else {
      onChange([...selectedTypes, type]);
    }
  };

  const handleSelectAll = () => {
    onChange(availableTypes.map((t) => t.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const hasSelection = selectedTypes.length > 0;

  // Group types by category
  const groupedTypes = availableTypes.reduce(
    (acc, type) => {
      const category = type.category || 'Other';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(type);
      return acc;
    },
    {} as Record<string, EventTypeOption[]>
  );

  const displayText = hasSelection
    ? selectedTypes.length === 1
      ? availableTypes.find((t) => t.value === selectedTypes[0])?.label || selectedTypes[0]
      : `${selectedTypes.length} types selected`
    : placeholder;

  if (compact) {
    return (
      <div className={`relative ${className}`} ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 rounded bg-white hover:bg-gray-50"
        >
          <Filter className="h-4 w-4 text-gray-400" />
          <span className={hasSelection ? 'text-gray-900' : 'text-gray-500'}>{displayText}</span>
          {hasSelection && (
            <span className="bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded-full text-xs font-medium">
              {selectedTypes.length}
            </span>
          )}
          <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute z-50 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
            <div className="p-2 border-b border-gray-100 flex justify-between items-center">
              <span className="text-xs text-gray-500">Filter by event type</span>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="text-xs text-primary-600 hover:text-primary-700"
                >
                  Select all
                </button>
                <button
                  onClick={handleClearAll}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto p-2">
              {Object.entries(groupedTypes).map(([category, types]) => (
                <div key={category} className="mb-2">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide px-2 py-1">
                    {category}
                  </div>
                  {types.map((type) => (
                    <label
                      key={type.value}
                      className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTypes.includes(type.value)}
                        onChange={() => handleToggle(type.value)}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-gray-700">{type.label}</span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-700">Event Types</span>
          {hasSelection && (
            <span className="bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full text-xs font-medium">
              {selectedTypes.length} selected
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSelectAll}
            className="text-xs text-primary-600 hover:text-primary-700"
          >
            Select all
          </button>
          {hasSelection && (
            <button
              onClick={handleClearAll}
              className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {availableTypes.map((type) => {
          const isSelected = selectedTypes.includes(type.value);
          return (
            <button
              key={type.value}
              onClick={() => handleToggle(type.value)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full transition-colors ${
                isSelected
                  ? 'bg-primary-100 text-primary-700 border border-primary-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border border-transparent'
              }`}
            >
              {isSelected && <Check className="h-3 w-3" />}
              {type.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Helper to filter events by selected types
export function filterEventsByType<T extends { type?: string; event_type?: string; evaluation_type?: string }>(
  events: T[],
  selectedTypes: string[]
): T[] {
  if (selectedTypes.length === 0) return events;
  return events.filter((event) => {
    const type = event.type || event.event_type || event.evaluation_type || '';
    return selectedTypes.some((selected) =>
      type.toLowerCase().includes(selected.toLowerCase()) ||
      selected.toLowerCase().includes(type.toLowerCase())
    );
  });
}

// Get unique event types from a list of events
export function getUniqueEventTypes<T extends { type?: string; event_type?: string; evaluation_type?: string }>(
  events: T[]
): EventTypeOption[] {
  const types = new Set<string>();
  events.forEach((event) => {
    const type = event.type || event.event_type || event.evaluation_type;
    if (type) types.add(type);
  });
  return Array.from(types).map((t) => ({
    value: t,
    label: t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
  }));
}
