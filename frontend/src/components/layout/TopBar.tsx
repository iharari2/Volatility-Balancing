import { useState, useEffect } from 'react';
import { Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';

interface TopBarProps {
  mode?: 'Live' | 'Simulation' | 'Sandbox';
}

export default function TopBar({ mode = 'Live' }: TopBarProps) {
  const { selectedTenant, selectedPortfolio } = useTenantPortfolio();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };

    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      <div className="flex flex-1 items-center gap-x-6 self-stretch">
        {/* Breadcrumb / Current Location */}
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-400 font-medium">
            {selectedTenant?.name || 'Default Tenant'}
          </span>
          <span className="text-gray-300">/</span>
          <span className="text-gray-900 font-bold">
            {selectedPortfolio?.name || 'No Portfolio'}
          </span>
        </div>

        <div className="h-6 w-px bg-gray-200" />

        {/* Market Hours Indicator */}
        <div className="flex items-center gap-x-2">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Market</span>
          <span className={`badge ${marketHoursService.getStatusColor(marketStatus)} text-[10px]`}>
            {marketHoursService.getStatusLabel(marketStatus)}
          </span>
        </div>

        {/* Mode Indicator */}
        <div className="flex items-center gap-x-2">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">System</span>
          <span
            className={`badge ${
              mode === 'Live'
                ? 'bg-success-100 text-success-800'
                : mode === 'Simulation'
                ? 'bg-primary-100 text-primary-800'
                : 'bg-warning-100 text-warning-800'
            } text-[10px]`}
          >
            {mode} MODE
          </span>
        </div>

        <div className="flex flex-1" />
        <div className="flex items-center gap-x-4 lg:gap-x-6">
          <Link
            to="/settings"
            className="-m-2.5 p-2.5 text-gray-400 hover:text-primary-600 transition-colors"
            title="Settings"
          >
            <Settings className="h-6 w-6" />
          </Link>
        </div>
      </div>
    </div>
  );
}
