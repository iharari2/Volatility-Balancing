import { useState } from 'react';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useWorkspace } from '../../WorkspaceContext';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';
import { portfolioApi } from '../../../../lib/api';
import DetailTabBar from './DetailTabBar';
import EmptyDetailState from './EmptyDetailState';
import AddPositionModal from '../../../positions/modals/AddPositionModal';
import OverviewTab from '../tabs/OverviewTab';
import TradingTab from '../tabs/TradingTab';
import EventsTab from '../tabs/EventsTab';
import StrategyTab from '../tabs/StrategyTab';
import ExplainabilityTab from '../tabs/ExplainabilityTab';
import OrdersTab from '../tabs/OrdersTab';
import DividendsTab from '../tabs/DividendsTab';

export default function RightPanel() {
  const { selectedPosition, positions, activeTab, setSelectedPositionId, portfolioId, refreshPositions } = useWorkspace();
  const { selectedTenantId, refreshPortfolios } = useTenantPortfolio();
  const [showAddModal, setShowAddModal] = useState(false);

  const handleAddPosition = async (data: {
    ticker: string;
    qty: number;
    dollarValue: number;
    inputMode: 'qty' | 'dollar';
    currentPrice: number;
    startingCash: { currency: string; amount: number };
  }) => {
    if (!selectedTenantId || !portfolioId) {
      toast.error('No portfolio selected');
      return;
    }
    const finalQty = data.inputMode === 'qty' ? data.qty : data.dollarValue / data.currentPrice;
    const result = await portfolioApi.createPosition(selectedTenantId, portfolioId, {
      asset: data.ticker,
      qty: finalQty,
      anchor_price: data.currentPrice,
      avg_cost: data.currentPrice,
      starting_cash: data.startingCash,
    });
    setShowAddModal(false);
    await refreshPositions();
    await refreshPortfolios();
    if ((result as any).position_id) {
      setSelectedPositionId((result as any).position_id);
    }
    toast.success(`${data.ticker} position added`);
  };

  // No position selected
  if (!selectedPosition) {
    return (
      <>
        <EmptyDetailState hasPositions={positions.length > 0} onAddPosition={() => setShowAddModal(true)} />
        {showAddModal && (
          <AddPositionModal onClose={() => setShowAddModal(false)} onSave={handleAddPosition} />
        )}
      </>
    );
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
        {activeTab === 'explainability' && <ExplainabilityTab />}
        {activeTab === 'orders' && <OrdersTab />}
        {activeTab === 'dividends' && <DividendsTab />}
      </div>
    </div>
  );
}
