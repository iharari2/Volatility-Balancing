import { useState, useEffect, useRef } from 'react';
import { Settings, LogOut, ChevronDown, User } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { useAuth } from '../../contexts/AuthContext';
import { marketHoursService, MarketStatus } from '../../services/marketHoursService';

interface TopBarProps {
  mode?: 'Live' | 'Simulation' | 'Sandbox';
}

export default function TopBar({ mode = 'Live' }: TopBarProps) {
  const { selectedTenant, selectedPortfolio } = useTenantPortfolio();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

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
        {/* Brand logo — desktop only (mobile uses sidebar header) */}
        <img
          src="/logo-compact.svg"
          alt="Volatility Balancing"
          className="h-8 flex-shrink-0 hidden lg:block"
        />
        <div className="h-6 w-px bg-gray-200 hidden lg:block" />

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

          {/* User menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen(o => !o)}
              className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center text-white">
                <User className="h-4 w-4" />
              </div>
              <span className="hidden sm:block text-sm font-medium max-w-[120px] truncate">
                {user?.display_name || user?.email?.split('@')[0] || 'Account'}
              </span>
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                <div className="px-3 py-2 border-b border-gray-100">
                  <p className="text-xs font-semibold text-gray-900 truncate">{user?.display_name || user?.email}</p>
                  {user?.display_name && <p className="text-xs text-gray-400 truncate">{user.email}</p>}
                </div>
                <Link
                  to="/settings"
                  onClick={() => setMenuOpen(false)}
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
    </div>
  );
}
