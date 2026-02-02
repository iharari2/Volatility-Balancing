import { X } from 'lucide-react';
import { useWorkspace } from '../../WorkspaceContext';
import DetailTabBar from './DetailTabBar';
import EmptyDetailState from './EmptyDetailState';
import OverviewTab from '../tabs/OverviewTab';
import TradingTab from '../tabs/TradingTab';
import EventsTab from '../tabs/EventsTab';
import StrategyTab from '../tabs/StrategyTab';

export default function RightPanel() {
  const { selectedPosition, positions, activeTab, setSelectedPositionId } = useWorkspace();

  // No position selected
  if (!selectedPosition) {
    return <EmptyDetailState hasPositions={positions.length > 0} />;
  }

  return (
    <div className="h-full flex flex-col">
      {/* Position Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-gray-900">{selectedPosition.asset_symbol}</h2>
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded-full ${
              selectedPosition.status === 'RUNNING'
                ? 'bg-success-100 text-success-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {selectedPosition.status}
          </span>
        </div>
        <button
          onClick={() => setSelectedPositionId(null)}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="Close position view"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <DetailTabBar />

      <div className="flex-1 overflow-auto">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'trading' && <TradingTab />}
        {activeTab === 'events' && <EventsTab />}
        {activeTab === 'strategy' && <StrategyTab />}
      </div>
    </div>
  );
}
