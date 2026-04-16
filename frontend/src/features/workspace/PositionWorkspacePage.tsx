import { useState, useEffect, useRef } from 'react';
import { Settings, PlaySquare, HelpCircle, Home, ChevronRight, Menu, Briefcase, BarChart3, X, LogOut, User } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import MasterDetailLayout from '../../layouts/MasterDetailLayout';
import { WorkspaceProvider, useWorkspace } from './WorkspaceContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';
import LeftPanel from './components/LeftPanel/LeftPanel';
import RightPanel from './components/RightPanel/RightPanel';
import { useMarketPrice } from '../../hooks/useMarketData';
import MarketDataBadge from '../../components/shared/MarketDataBadge';

function WorkspaceTopBar() {
  const { selectedPortfolio } = useTenantPortfolio();
  const { selectedPosition, setSelectedPositionId } = useWorkspace();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [mode] = useState<'Live' | 'Simulation' | 'Sandbox'>('Live');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const marketPriceQuery = useMarketPrice(selectedPosition?.asset_symbol ?? '');

  useEffect(() => {
    const updateMarketStatus = async () => {
      const state = await marketHoursService.getMarketState();
      setMarketStatus(state.status);
    };

    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleHomeClick = () => {
    setSelectedPositionId(null);
    navigate('/');
  };

  const navigationItems = [
    { name: 'Workspace', href: '/', icon: Home },
    { name: 'Portfolios', href: '/portfolios', icon: Briefcase },
    { name: 'Simulation Lab', href: '/simulation', icon: PlaySquare },
    { name: 'Analytics & Reports', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="flex-1 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Menu Button */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="flex items-center gap-2 px-2 py-1.5 text-gray-700 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Navigation Menu"
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          {/* Dropdown Menu */}
          {isMenuOpen && (
            <div className="absolute top-full left-0 mt-1 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = window.location.pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setIsMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-primary-600'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          )}
        </div>

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
          {selectedPosition && marketPriceQuery.data && (
            <MarketDataBadge
              isFresh={marketPriceQuery.data.is_fresh}
              isMarketHours={marketPriceQuery.data.is_market_hours}
              source={marketPriceQuery.data.source}
              dataUpdatedAt={marketPriceQuery.dataUpdatedAt}
              compact
            />
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Quick Links - visible on larger screens */}
        <Link
          to="/portfolios"
          className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Briefcase className="h-4 w-4" />
          <span>Portfolios</span>
        </Link>

        <Link
          to="/simulation"
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <PlaySquare className="h-4 w-4" />
          <span className="hidden sm:inline">Sim Lab</span>
        </Link>

        <Link
          to="/analytics"
          className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <BarChart3 className="h-4 w-4" />
          <span>Analytics</span>
        </Link>

        <Link
          to="/settings"
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Settings className="h-4 w-4" />
          <span className="hidden sm:inline">Settings</span>
        </Link>

        {/* User menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setIsUserMenuOpen(o => !o)}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            title="Account"
          >
            <div className="w-6 h-6 rounded-full bg-primary-600 flex items-center justify-center text-white">
              <User className="h-3.5 w-3.5" />
            </div>
            <span className="hidden sm:block text-xs font-medium max-w-[80px] truncate">
              {user?.display_name || user?.email?.split('@')[0] || 'Account'}
            </span>
          </button>
          {isUserMenuOpen && (
            <div className="absolute right-0 mt-1 w-44 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
              <div className="px-3 py-2 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-900 truncate">{user?.display_name || user?.email}</p>
                {user?.display_name && <p className="text-xs text-gray-400 truncate">{user.email}</p>}
              </div>
              <Link
                to="/settings"
                onClick={() => setIsUserMenuOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Settings className="h-4 w-4" /> Settings
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut className="h-4 w-4" /> Sign out
              </button>
            </div>
          )}
        </div>
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
