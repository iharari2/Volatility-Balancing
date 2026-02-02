import { useWorkspace } from '../../WorkspaceContext';
import DetailTabBar from './DetailTabBar';
import EmptyDetailState from './EmptyDetailState';
import OverviewTab from '../tabs/OverviewTab';
import TradingTab from '../tabs/TradingTab';
import EventsTab from '../tabs/EventsTab';
import StrategyTab from '../tabs/StrategyTab';

export default function RightPanel() {
  const { selectedPosition, positions, activeTab } = useWorkspace();

  // No position selected
  if (!selectedPosition) {
    return <EmptyDetailState hasPositions={positions.length > 0} />;
  }

  return (
    <div className="h-full flex flex-col">
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
