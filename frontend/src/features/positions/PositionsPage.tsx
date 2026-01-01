import { useState } from 'react';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import PositionsTable from './PositionsTable';
import CashConfigForm from './CashConfigForm';
import StrategyConfigForm from './StrategyConfigForm';
import DividendsTab from './DividendsTab';

export default function PositionsPage() {
  const { positions, loading } = usePortfolio();
  const { selectedPortfolio } = useTenantPortfolio();
  const [activeTab, setActiveTab] = useState<'positions' | 'cash' | 'strategy' | 'dividends'>(
    'positions',
  );

  const tabs = [
    { id: 'positions' as const, name: 'Positions' },
    { id: 'cash' as const, name: 'Cash & Limits' },
    { id: 'strategy' as const, name: 'Strategy Config' },
    { id: 'dividends' as const, name: 'Dividends' },
  ];

  if (!selectedPortfolio) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">Please select a portfolio to view positions</p>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Positions & Config</h1>
          <p className="text-sm text-gray-500 mt-1">{selectedPortfolio.name}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white shadow rounded-lg p-6">
        {activeTab === 'positions' && (
          <PositionsTable
            positions={positions}
            cashBalance={positions.reduce((sum, pos) => sum + (pos.cashAmount || 0), 0)}
          />
        )}
        {activeTab === 'cash' && <CashConfigForm />}
        {activeTab === 'strategy' && <StrategyConfigForm />}
        {activeTab === 'dividends' && <DividendsTab />}
      </div>
    </div>
  );
}

















