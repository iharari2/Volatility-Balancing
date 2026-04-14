import { ReactNode, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { useAuth } from '../../contexts/AuthContext';
import { marketHoursService, type MarketStatus } from '../../services/marketHoursService';
import CreatePortfolioWizard from '../../features/portfolios/CreatePortfolioWizard';

const NAV_LINKS = [
  { label: '🏠 Dashboard',    path: '/' },
  { label: '📊 Analytics',    path: '/analytics' },
  { label: '🧪 Simulation',   path: '/simulation' },
  { label: '🎯 Optimization', path: '/optimization' },
  { label: '📡 Monitoring',   path: '/monitoring' },
  { label: '👤 Admin',        path: '/admin/users', adminOnly: true },
  { label: '⚙️ Settings',     path: '/settings' },
];

interface AppShellProps {
  children: ReactNode;
  /** Optional extra actions rendered in the top-bar right section */
  topBarActions?: ReactNode;
}

export default function AppShell({ children, topBarActions }: AppShellProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedPortfolio, portfolios, setSelectedPortfolioId } = useTenantPortfolio();
  const { user } = useAuth();
  const [marketStatus, setMarketStatus] = useState<MarketStatus>('CLOSED');
  const [showCreatePortfolio, setShowCreatePortfolio] = useState(false);

  useEffect(() => {
    const update = async () => setMarketStatus((await marketHoursService.getMarketState()).status);
    update();
    const id = setInterval(update, 60_000);
    return () => clearInterval(id);
  }, []);

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">

      {/* ── Top bar ── */}
      <div className="bg-slate-900 text-slate-200 flex items-center justify-between px-5 h-11 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="font-bold text-white text-sm hover:text-slate-300 transition-colors"
          >
            ⚡ Volatility Balancer
          </button>
          {portfolios.length > 1 && (
            <select
              value={selectedPortfolio?.id ?? ''}
              onChange={(e) => setSelectedPortfolioId(e.target.value)}
              className="bg-slate-800 text-slate-200 text-xs border border-slate-700 rounded px-2 py-1"
            >
              {portfolios.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
          {portfolios.length === 1 && (
            <span className="text-slate-400 text-xs">{selectedPortfolio?.name}</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1 rounded-full">
            <span className={`w-2 h-2 rounded-full ${marketStatus === 'OPEN' ? 'bg-green-400 shadow-[0_0_6px_#4ade80]' : 'bg-slate-500'}`} />
            {marketStatus === 'OPEN' ? 'Market Open' : 'Market Closed'}
          </div>
          {topBarActions}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">

        {/* ── Left sidebar ── */}
        <div className="w-52 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col py-3 px-3 gap-3">
          {/* Portfolio card */}
          {selectedPortfolio ? (
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
              <div className="text-xs font-semibold text-indigo-700 mb-1">{selectedPortfolio.name}</div>
              <div className="text-xl font-black text-slate-900">
                ${(selectedPortfolio.totalValue ?? 0).toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {selectedPortfolio.positionCount ?? 0} position{(selectedPortfolio.positionCount ?? 0) !== 1 ? 's' : ''}
              </div>
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
              <p className="text-xs text-amber-700 mb-2">No portfolio yet</p>
              <button
                onClick={() => setShowCreatePortfolio(true)}
                className="w-full text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded px-2 py-1.5 transition-colors"
              >
                + Create Portfolio
              </button>
            </div>
          )}

          {/* Nav links */}
          <nav className="flex flex-col gap-0.5 text-xs font-medium">
            {NAV_LINKS.filter(l => !l.adminOnly || user?.role === 'owner').map(({ label, path }) => (
              <a
                key={path}
                href={path}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  isActive(path)
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                {label}
              </a>
            ))}
          </nav>
        </div>

        {/* ── Main content ── */}
        <div className="flex-1 overflow-y-auto p-4">
          {children}
        </div>

      </div>

      <CreatePortfolioWizard
        isOpen={showCreatePortfolio}
        onClose={() => setShowCreatePortfolio(false)}
        onComplete={() => setShowCreatePortfolio(false)}
      />
    </div>
  );
}
