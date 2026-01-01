import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, TrendingUp, ArrowRight } from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioScopedApi, PortfolioPosition } from '../../services/portfolioScopedApi';
import LoadingSpinner from '../../components/shared/LoadingSpinner';
import EmptyState from '../../components/shared/EmptyState';

export default function TradeSelectionPage() {
  const navigate = useNavigate();
  const { selectedTenantId, portfolios } = useTenantPortfolio();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(null);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [loading, setLoading] = useState(false);

  const tenantId = selectedTenantId || 'default';

  // Auto-select first portfolio if only one exists
  useEffect(() => {
    if (portfolios.length === 1 && !selectedPortfolioId) {
      setSelectedPortfolioId(portfolios[0].id);
    }
  }, [portfolios, selectedPortfolioId]);

  // Load positions when portfolio is selected
  useEffect(() => {
    if (!selectedPortfolioId) {
      setPositions([]);
      return;
    }

    const loadPositions = async () => {
      setLoading(true);
      try {
        const posData = await portfolioScopedApi.getPositions(tenantId, selectedPortfolioId);
        setPositions(posData);
      } catch (error) {
        console.error('Error loading positions:', error);
      } finally {
        setLoading(false);
      }
    };

    loadPositions();
  }, [tenantId, selectedPortfolioId]);

  const handleGoToCockpit = (positionId: string) => {
    if (selectedPortfolioId) {
      navigate(`/trade/${selectedPortfolioId}/position/${positionId}`);
    }
  };

  if (portfolios.length === 0) {
    return (
      <EmptyState
        icon={<Briefcase className="h-16 w-16 text-gray-400" />}
        title="No Portfolios"
        description="Create a portfolio first to view position cockpits"
        action={{
          label: 'Go to Portfolios',
          to: '/portfolios',
        }}
      />
    );
  }

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Position Cockpit Selection</h1>
        <p className="text-sm text-gray-500">Select a portfolio and position to view the cockpit</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Portfolio</label>
        <select
          value={selectedPortfolioId || ''}
          onChange={(e) => setSelectedPortfolioId(e.target.value || null)}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Choose a portfolio...</option>
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {selectedPortfolioId && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <label className="block text-sm font-medium text-gray-700 mb-4">Select Position</label>
          {loading ? (
            <LoadingSpinner message="Loading positions..." />
          ) : positions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No positions in this portfolio</p>
              <p className="text-sm mt-2">Add positions to view their cockpits</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {positions.map((position) => (
                <button
                  key={position.id}
                  onClick={() => handleGoToCockpit(position.id)}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex-1 text-left">
                    <div className="font-semibold text-gray-900">
                      {position.asset || position.ticker || 'Unknown'}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {position.qty.toFixed(2)} shares
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-gray-400" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}







