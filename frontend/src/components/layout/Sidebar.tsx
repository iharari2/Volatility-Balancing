import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  Settings,
  Activity,
  PlaySquare,
  BarChart3,
  FileSearch,
  Cog,
  Menu,
  X,
  ChevronDown,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { useState } from 'react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

const navigation = [
  { name: 'Workspace', href: '/', icon: LayoutDashboard },
  { name: 'Portfolios', href: '/portfolios', icon: Briefcase },
  { name: 'Simulation Lab', href: '/simulation', icon: PlaySquare },
  { name: 'Analytics & Reports', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Cog },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export default function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const location = useLocation();
  const { portfolios, selectedPortfolio, setSelectedPortfolioId, loading } = useTenantPortfolio();

  const sidebarContent = (
    <div className="flex flex-col flex-grow bg-white border-r border-gray-200 h-full overflow-y-auto">
      <div className="flex h-16 items-center px-6 border-b border-gray-100 flex-shrink-0">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="h-6 w-6 text-primary-600" />
          Volatility Balancing
        </h1>
      </div>

      {/* Portfolio Selector Section */}
      <div className="px-4 py-6 border-b border-gray-100">
        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 block px-2">
          Portfolio Selection
        </label>

        <div className="relative group px-2">
          <select
            value={selectedPortfolio?.id || ''}
            onChange={(e) => setSelectedPortfolioId(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm font-bold text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none cursor-pointer hover:bg-gray-100 transition-all"
          >
            {portfolios.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
            {portfolios.length === 0 && (
              <option value="" disabled>
                No portfolios found
              </option>
            )}
          </select>
          <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none">
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </div>
        </div>

        {/* Portfolio Summary Panel */}
        {selectedPortfolio && (
          <div className="mt-4 p-4 bg-primary-50 rounded-xl border border-primary-100 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex items-center justify-between">
              <span
                className={`badge ${
                  selectedPortfolio.autoTradingEnabled ? 'badge-success' : 'badge-warning'
                } text-[10px] py-0.5`}
              >
                {selectedPortfolio.autoTradingEnabled ? 'ACTIVE' : 'PAUSED'}
              </span>
              <span className="text-[10px] font-bold text-primary-600 bg-primary-100 px-2 py-0.5 rounded uppercase tracking-tighter">
                {selectedPortfolio.positionCount || 0} POSITIONS
              </span>
            </div>

            <div className="pt-1">
              <span className="text-[10px] text-primary-400 font-bold uppercase block tracking-wider">
                Total Value
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-black text-primary-900 leading-none">
                  ${(selectedPortfolio.totalValue || 0).toLocaleString()}
                </span>
                <span className="text-xs font-bold text-success-600">+2.4%</span>
              </div>
            </div>

            <div className="pt-1 border-t border-primary-100/50">
              <span className="text-[10px] text-primary-400 font-bold uppercase block tracking-wider">
                Strategy
              </span>
              <span className="text-xs font-bold text-primary-800 uppercase tracking-tight">
                Standard Balancing
              </span>
            </div>
          </div>
        )}
      </div>

      <nav className="flex-1 px-4 py-6 space-y-1">
        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 block px-2">
          Navigation
        </label>
        {navigation.map((item) => {
          const isActive =
            location.pathname === item.href || location.pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`group flex items-center px-4 py-2.5 text-sm font-bold rounded-xl transition-all border-l-4 ${
                isActive
                  ? 'bg-primary-600 text-white shadow-md shadow-primary-200 border-l-white transform scale-[1.02]'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900 border-l-transparent'
              }`}
              onClick={onMobileClose}
            >
              <item.icon
                className={`mr-3 h-5 w-5 ${
                  isActive ? 'text-white' : 'text-gray-400 group-hover:text-primary-600'
                }`}
              />
              {item.name}
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Branding or Version */}
      <div className="p-6 border-t border-gray-50 mt-auto flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gray-900 flex items-center justify-center text-white text-[10px] font-bold">
            VB
          </div>
          <div>
            <p className="text-xs font-bold text-gray-900">Volatility v2.0</p>
            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">
              Powered by Engine
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={onMobileClose} />
          <div className="fixed inset-y-0 left-0 flex w-64 flex-col">
            {sidebarContent}
            <button
              onClick={onMobileClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col lg:pt-16">
        {sidebarContent}
      </div>
    </>
  );
}







