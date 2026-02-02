import { useState } from 'react';
import { Search, Plus, RefreshCw } from 'lucide-react';
import { useWorkspace } from '../../WorkspaceContext';
import PositionCellItem from './PositionCellItem';
import LoadingSpinner from '../../../../components/shared/LoadingSpinner';

export default function PositionCellList() {
  const {
    filteredPositions,
    positionsLoading,
    selectedPositionId,
    setSelectedPositionId,
    searchQuery,
    setSearchQuery,
    refreshPositions,
  } = useWorkspace();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshPositions();
    setIsRefreshing(false);
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Search */}
      <div className="px-4 py-2 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search positions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            title="Refresh positions"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Position List */}
      <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
        {positionsLoading ? (
          <div className="p-8">
            <LoadingSpinner message="Loading positions..." />
          </div>
        ) : filteredPositions.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-gray-400 mb-2">
              {searchQuery ? 'No positions match your search' : 'No positions found'}
            </div>
            {!searchQuery && (
              <p className="text-sm text-gray-500">Add a position to get started</p>
            )}
          </div>
        ) : (
          filteredPositions.map((position) => (
            <PositionCellItem
              key={position.position_id}
              position={position}
              isSelected={position.position_id === selectedPositionId}
              onClick={() => setSelectedPositionId(position.position_id)}
            />
          ))
        )}
      </div>

      {/* Add Position Button */}
      <div className="p-4 border-t border-gray-200">
        <button
          type="button"
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold text-primary-600 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Position
        </button>
      </div>
    </div>
  );
}
