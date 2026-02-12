import { ChevronDown, TrendingUp, Plus, Briefcase } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';

export default function PortfolioSelector() {
  const { portfolios, selectedPortfolio, setSelectedPortfolioId, loading } = useTenantPortfolio();

  return (
    <div className="p-4 border-b border-gray-200">
      {/* Logo */}
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-primary-600" />
        <span className="text-lg font-bold text-gray-900">Volatility Balancing</span>
      </div>

      {/* No portfolios - guided empty state */}
      {!loading && portfolios.length === 0 ? (
        <div className="text-center py-4">
          <Briefcase className="h-8 w-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm font-medium text-gray-700 mb-1">No portfolios yet</p>
          <p className="text-xs text-gray-500 mb-3">Create a portfolio to start trading</p>
          <Link
            to="/portfolios"
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Portfolio
          </Link>
        </div>
      ) : (
        <>
          {/* Portfolio Dropdown */}
          <div className="relative">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 block">
              Portfolio
            </label>
            <div className="relative">
              <select
                value={selectedPortfolio?.id || ''}
                onChange={(e) => setSelectedPortfolioId(e.target.value)}
                disabled={loading}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm font-semibold text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none cursor-pointer hover:bg-gray-100 transition-all disabled:opacity-50"
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-4 w-4 text-gray-400" />
              </div>
            </div>
          </div>

          {/* Portfolio Summary */}
          {selectedPortfolio && (
            <div className="mt-3 p-3 bg-primary-50 rounded-lg border border-primary-100">
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`badge ${
                    selectedPortfolio.autoTradingEnabled ? 'badge-success' : 'badge-warning'
                  } text-[10px] py-0.5`}
                >
                  {selectedPortfolio.autoTradingEnabled ? 'ACTIVE' : 'PAUSED'}
                </span>
                <span className="text-[10px] font-bold text-primary-600 bg-primary-100 px-2 py-0.5 rounded uppercase tracking-tight">
                  {selectedPortfolio.positionCount || 0} POSITIONS
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-black text-primary-900">
                  ${(selectedPortfolio.totalValue || 0).toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
