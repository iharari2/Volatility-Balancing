import { useState, useEffect } from 'react';
import { Settings, PlaySquare, HelpCircle, Home, ChevronRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import MasterDetailLayout from '../../layouts/MasterDetailLayout';
import { WorkspaceProvider, useWorkspace } from './WorkspaceContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import LeftPanel from './components/LeftPanel/LeftPanel';
import RightPanel from './components/RightPanel/RightPanel';

function WorkspaceTopBar() {
  const { selectedPortfolio } = useTenantPortfolio();
  const { selectedPosition, setSelectedPositionId } = useWorkspace();
  const navigate = useNavigate();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [mode] = useState<'Live' | 'Simulation' | 'Sandbox'>('Live');

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };

    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleHomeClick = () => {
    setSelectedPositionId(null);
    navigate('/');
  };

  return (
    <div className="flex-1 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Home Button */}
        <button
          onClick={handleHomeClick}
          className="flex items-center gap-2 px-2 py-1 text-gray-700 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="Home - Deselect position"
        >
          <Home className="h-5 w-5" />
          <span className="font-bold text-sm hidden sm:inline">VB</span>
        </button>

        <div className="h-5 w-px bg-gray-200" />

        {/* Breadcrumb */}
        <nav className="flex items-center gap-1 text-sm">
          <span className="text-gray-500">{selectedPortfolio?.name || 'Portfolio'}</span>
          {selectedPosition && (
            <>
              <ChevronRight className="h-4 w-4 text-gray-400" />
              <span className="font-semibold text-gray-900">{selectedPosition.asset_symbol}</span>
            </>
          )}
        </nav>

        <div className="h-5 w-px bg-gray-200" />

        {/* Mode Indicator */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Mode</span>
          <span
            className={`badge text-[10px] ${
              mode === 'Live'
                ? 'bg-success-100 text-success-800'
                : mode === 'Simulation'
                ? 'bg-primary-100 text-primary-800'
                : 'bg-warning-100 text-warning-800'
            }`}
          >
            {mode}
          </span>
        </div>

        <div className="h-5 w-px bg-gray-200 hidden md:block" />

        {/* Market Status - Hidden on small screens */}
        <div className="hidden md:flex items-center gap-2">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Market</span>
          <span className={`badge ${marketHoursService.getStatusColor(marketStatus)} text-[10px]`}>
            {marketHoursService.getStatusLabel(marketStatus)}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Quick Links */}
        <Link
          to="/simulation"
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <PlaySquare className="h-4 w-4" />
          <span className="hidden sm:inline">Sim Lab</span>
        </Link>

        <Link
          to="/settings"
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Settings className="h-4 w-4" />
          <span className="hidden sm:inline">Settings</span>
        </Link>

        <button
          type="button"
          className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
          title="Help"
        >
          <HelpCircle className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function WorkspaceContent() {
  return (
    <MasterDetailLayout
      topBar={<WorkspaceTopBar />}
      leftPanel={<LeftPanel />}
      rightPanel={<RightPanel />}
    />
  );
}

export default function PositionWorkspacePage() {
  return (
    <WorkspaceProvider>
      <WorkspaceContent />
    </WorkspaceProvider>
  );
}
