import { useWorkspace, PositionFilter } from '../../WorkspaceContext';

const filters: { value: PositionFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'paused', label: 'Paused' },
];

export default function QuickFilters() {
  const { positionFilter, setPositionFilter, positions, filteredPositions } = useWorkspace();

  const getCount = (filter: PositionFilter): number => {
    if (filter === 'all') return positions.length;
    if (filter === 'active') return positions.filter((p) => p.status === 'RUNNING').length;
    if (filter === 'paused') return positions.filter((p) => p.status === 'PAUSED').length;
    return 0;
  };

  return (
    <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
      <div className="flex items-center gap-1">
        {filters.map((filter) => {
          const count = getCount(filter.value);
          const isActive = positionFilter === filter.value;

          return (
            <button
              key={filter.value}
              onClick={() => setPositionFilter(filter.value)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-full transition-colors ${
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {filter.label}
              <span
                className={`text-[10px] ${
                  isActive ? 'text-primary-200' : 'text-gray-400'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
