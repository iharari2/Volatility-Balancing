import PortfolioSelector from './PortfolioSelector';
import QuickFilters from './QuickFilters';
import PositionCellList from './PositionCellList';

export default function LeftPanel() {
  return (
    <div className="h-full flex flex-col bg-white">
      <PortfolioSelector />
      <QuickFilters />
      <PositionCellList />
    </div>
  );
}
