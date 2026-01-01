import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  Copy,
  Archive,
  Trash2,
  Edit,
  Settings,
  Eye,
  ChevronDown,
  ChevronUp,
  ArrowRight,
} from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioApi } from '../../lib/api';
import CreatePortfolioWizard from './CreatePortfolioWizard';
import PortfolioDetailModal from './PortfolioDetailModal';

export default function PortfolioListPage() {
  const {
    portfolios,
    selectedPortfolioId,
    setSelectedPortfolioId,
    selectedTenantId,
    refreshPortfolios,
    loading,
  } = useTenantPortfolio();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedPortfolioForDetail, setSelectedPortfolioForDetail] = useState<string | null>(null);
  const [expandedPortfolios, setExpandedPortfolios] = useState<Set<string>>(new Set());
  const [portfolioPositions, setPortfolioPositions] = useState<Record<string, any[]>>({});
  const [loadingPositions, setLoadingPositions] = useState<Record<string, boolean>>({});

  const handleCreate = () => {
    setShowCreateModal(true);
  };

  const handleSelectPortfolio = (portfolioId: string) => {
    setSelectedPortfolioId(portfolioId);
  };

  const handleDuplicate = async (portfolioId: string) => {
    try {
      const portfolio = portfolios.find((p) => p.id === portfolioId);
      if (!portfolio) return;

      // Create a new portfolio with similar name
      const newName = `${portfolio.name} (Copy)`;
      await portfolioApi.create({
        name: newName,
        description: portfolio.description || undefined,
        user_id: portfolio.userId || 'default',
      });
      await refreshPortfolios();
    } catch (error) {
      console.error('Error duplicating portfolio:', error);
      alert('Failed to duplicate portfolio');
    }
  };

  const handleArchive = async (portfolioId: string) => {
    // Archive is not yet implemented in backend - for now just show message
    alert('Archive functionality coming soon');
  };

  const handleDelete = async (portfolioId: string) => {
    if (
      window.confirm(
        'Are you sure you want to delete this portfolio? This action cannot be undone.',
      )
    ) {
      try {
        await portfolioApi.delete(selectedTenantId, portfolioId);
        // If deleted portfolio was selected, clear selection
        if (selectedPortfolioId === portfolioId) {
          setSelectedPortfolioId(null);
        }
        await refreshPortfolios();
      } catch (error) {
        console.error('Error deleting portfolio:', error);
        alert('Failed to delete portfolio');
      }
    }
  };

  const handleEdit = (portfolioId: string) => {
    setSelectedPortfolioForDetail(portfolioId);
    setShowDetailModal(true);
  };

  const handleViewDetails = (portfolioId: string) => {
    setSelectedPortfolioForDetail(portfolioId);
    setShowDetailModal(true);
  };

  const togglePortfolioExpansion = async (portfolioId: string) => {
    const isExpanded = expandedPortfolios.has(portfolioId);
    if (isExpanded) {
      // Collapse
      setExpandedPortfolios((prev) => {
        const next = new Set(prev);
        next.delete(portfolioId);
        return next;
      });
    } else {
      // Expand - load positions if not already loaded
      setExpandedPortfolios((prev) => new Set(prev).add(portfolioId));
      if (!portfolioPositions[portfolioId] && !loadingPositions[portfolioId]) {
        await loadPortfolioPositions(portfolioId);
      }
    }
  };

  const loadPortfolioPositions = async (portfolioId: string) => {
    if (!selectedTenantId) return;

    setLoadingPositions((prev) => ({ ...prev, [portfolioId]: true }));
    try {
      const positions = await portfolioApi.getPositions(selectedTenantId, portfolioId);
      setPortfolioPositions((prev) => ({ ...prev, [portfolioId]: positions }));
    } catch (error) {
      console.error(`Error loading positions for portfolio ${portfolioId}:`, error);
      setPortfolioPositions((prev) => ({ ...prev, [portfolioId]: [] }));
    } finally {
      setLoadingPositions((prev) => ({ ...prev, [portfolioId]: false }));
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolios</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage and monitor your investment portfolios
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 shadow-md transition-colors font-medium"
        >
          <Plus className="h-5 w-5" />
          <span>Create Portfolio</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {portfolios.map((portfolio) => {
          const isExpanded = expandedPortfolios.has(portfolio.id);
          const positions = portfolioPositions[portfolio.id] || [];
          const isLoading = loadingPositions[portfolio.id];
          const isSelected = selectedPortfolioId === portfolio.id;

          return (
            <div
              key={portfolio.id}
              className={`card flex flex-col h-full transition-all border-2 ${
                isSelected ? 'border-primary-500 ring-1 ring-primary-500' : 'border-transparent'
              }`}
            >
              <div className="flex justify-between items-start mb-4">
                <div
                  className="cursor-pointer group flex-1"
                  onClick={() => handleSelectPortfolio(portfolio.id)}
                >
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {portfolio.name}
                    </h3>
                    {isSelected && <span className="badge badge-info">Active</span>}
                  </div>
                  <p className="text-sm text-gray-500 line-clamp-1 mt-1">
                    {portfolio.description || 'No description'}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(portfolio.id);
                    }}
                    className="p-1.5 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors"
                    title="Edit Portfolio"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(portfolio.id);
                    }}
                    className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
                    title="Delete Portfolio"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6 pt-4 border-t border-gray-100">
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">
                    Total Value
                  </span>
                  <p className="text-lg font-bold text-gray-900">
                    ${(portfolio.totalValue || 0).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">
                    Status
                  </span>
                  <div className="mt-1">
                    <span
                      className={`badge ${
                        portfolio.autoTradingEnabled ? 'badge-success' : 'badge-warning'
                      }`}
                    >
                      {portfolio.autoTradingEnabled ? 'Auto Trading' : 'Manual Mode'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-auto flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex -space-x-2 overflow-hidden">
                  <span className="text-sm font-medium text-gray-600">
                    {portfolio.positionCount || 0} position
                    {(portfolio.positionCount || 0) !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => togglePortfolioExpansion(portfolio.id)}
                    className="btn btn-secondary py-1 text-xs flex items-center gap-1"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp className="h-3 w-3" /> Hide Assets
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" /> View Assets
                      </>
                    )}
                  </button>
                  <Link
                    to={`/portfolios/${portfolio.id}`}
                    className="btn btn-primary py-1 text-xs flex items-center gap-1"
                  >
                    Dashboard <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>

              {/* Expanded Assets Section */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-gray-200 animate-in fade-in slide-in-from-top-2">
                  {isLoading ? (
                    <div className="text-center py-4">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mx-auto"></div>
                    </div>
                  ) : positions.length === 0 ? (
                    <div className="text-center py-4 text-xs text-gray-500">No positions found</div>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-200">
                      {positions.map((position) => (
                        <div
                          key={position.id}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs"
                        >
                          <span className="font-bold text-gray-900">
                            {position.asset || position.ticker}
                          </span>
                          <span className="text-gray-600">
                            {position.qty.toLocaleString()} shares
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <CreatePortfolioWizard
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onComplete={async (portfolioId) => {
          await refreshPortfolios();
          // Wizard handles navigation internally
        }}
      />

      <PortfolioDetailModal
        isOpen={showDetailModal}
        portfolioId={selectedPortfolioForDetail}
        onClose={() => {
          setShowDetailModal(false);
          setSelectedPortfolioForDetail(null);
        }}
        onSave={async () => {
          await refreshPortfolios();
        }}
      />
    </div>
  );
}
