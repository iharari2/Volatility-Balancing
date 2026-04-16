import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
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
  Briefcase,
} from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioApi } from '../../lib/api';
import ConfirmDialog from '../../components/shared/ConfirmDialog';
import CreatePortfolioWizard from './CreatePortfolioWizard';
import PortfolioDetailModal from './PortfolioDetailModal';
import QuickStartChecklist from '../onboarding/QuickStartChecklist';

const QUICKSTART_DISMISSED_KEY = 'vb.quickstart.dismissed';

const getStoredChecklistPreference = () => {
  if (typeof window === 'undefined') {
    return false;
  }
  return localStorage.getItem(QUICKSTART_DISMISSED_KEY) === 'true';
};

export default function PortfolioListPage() {
  const {
    portfolios,
    selectedPortfolioId,
    setSelectedPortfolioId,
    selectedTenantId,
    refreshPortfolios,
    loading,
  } = useTenantPortfolio();
  const [searchParams, setSearchParams] = useSearchParams();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedPortfolioForDetail, setSelectedPortfolioForDetail] = useState<string | null>(null);
  const [expandedPortfolios, setExpandedPortfolios] = useState<Set<string>>(new Set());
  const [portfolioPositions, setPortfolioPositions] = useState<Record<string, any[]>>({});
  const [loadingPositions, setLoadingPositions] = useState<Record<string, boolean>>({});
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [checklistDismissed, setChecklistDismissed] = useState<boolean>(getStoredChecklistPreference);
  const [hasAnchorConfigured, setHasAnchorConfigured] = useState(false);
  const [checkingAnchors, setCheckingAnchors] = useState(false);
  const [checklistRefreshToken, setChecklistRefreshToken] = useState(0);

  useEffect(() => {
    if (searchParams.get('create') === '1') {
      setShowCreateModal(true);
      const params = new URLSearchParams(searchParams);
      params.delete('create');
      setSearchParams(params, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    let isMounted = true;

    const checkAnchorProgress = async () => {
      if (!selectedTenantId) {
        if (isMounted) {
          setHasAnchorConfigured(false);
          setCheckingAnchors(false);
        }
        return;
      }

      const portfoliosWithPositions = portfolios.filter((p) => (p.positionCount || 0) > 0);

      if (portfoliosWithPositions.length === 0) {
        if (isMounted) {
          setHasAnchorConfigured(false);
          setCheckingAnchors(false);
        }
        return;
      }

      if (isMounted) {
        setCheckingAnchors(true);
      }

      for (const portfolio of portfoliosWithPositions) {
        try {
          const positions = await portfolioApi.getPositions(selectedTenantId, portfolio.id);
          if (!isMounted) {
            return;
          }
          const anyAnchor = positions.some(
            (position) => position.anchor_price !== null && position.anchor_price !== undefined,
          );
          if (anyAnchor) {
            setHasAnchorConfigured(true);
            setCheckingAnchors(false);
            return;
          }
        } catch (error) {
          console.warn('Unable to check anchor status for portfolio ' + portfolio.id + ':', error);
        }
      }

      if (isMounted) {
        setHasAnchorConfigured(false);
        setCheckingAnchors(false);
      }
    };

    checkAnchorProgress();

    return () => {
      isMounted = false;
    };
  }, [portfolios, selectedTenantId, checklistRefreshToken]);

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
      if (!selectedTenantId) return;
      await portfolioApi.create(selectedTenantId, {
        name: newName,
        description: portfolio.description || undefined,
      });
      await refreshPortfolios();
    } catch (error) {
      console.error('Error duplicating portfolio:', error);
      toast.error('Failed to duplicate portfolio');
    }
  };

  const handleArchive = async (portfolioId: string) => {
    // Archive is not yet implemented in backend - for now just show message
    toast('Archive functionality coming soon');
  };

  const handleDelete = (portfolioId: string) => {
    setDeleteConfirmId(portfolioId);
  };

  const confirmDeletePortfolio = async () => {
    if (!deleteConfirmId || !selectedTenantId) return;
    try {
      await portfolioApi.delete(selectedTenantId, deleteConfirmId);
      if (selectedPortfolioId === deleteConfirmId) {
        setSelectedPortfolioId('');
      }
      await refreshPortfolios();
      toast.success('Portfolio deleted');
    } catch (error) {
      console.error('Error deleting portfolio:', error);
      toast.error('Failed to delete portfolio');
    } finally {
      setDeleteConfirmId(null);
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

  const handleDismissChecklist = () => {
    setChecklistDismissed(true);
    if (typeof window !== 'undefined') {
      localStorage.setItem(QUICKSTART_DISMISSED_KEY, 'true');
    }
  };

  const handleRefreshChecklist = () => {
    setChecklistRefreshToken((prev) => prev + 1);
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

  const hasAnyPortfolio = portfolios.length > 0;
  const hasAnyPosition = portfolios.some((p) => (p.positionCount || 0) > 0);
  const hasTradingEnabled = portfolios.some((p) => p.autoTradingEnabled);

  const quickStartSteps = [
    {
      id: 'portfolio',
      label: 'Create a portfolio',
      description: 'Group cash and assets under a guardrail policy.',
      completed: hasAnyPortfolio,
    },
    {
      id: 'position',
      label: 'Add a position',
      description: 'Allocate ticker, shares, and companion cash.',
      completed: hasAnyPosition,
    },
    {
      id: 'anchor',
      label: 'Set anchor price',
      description: 'Pin a baseline before allowing automation.',
      completed: hasAnchorConfigured,
    },
    {
      id: 'trading',
      label: 'Start trading',
      description: 'Enable auto-trading on any ready portfolio.',
      completed: hasTradingEnabled,
    },
  ];

  const allStepsComplete = quickStartSteps.every((step) => step.completed);
  const showQuickStart = !allStepsComplete && !checklistDismissed;
  const isEmptyState = portfolios.length === 0;

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

      {showQuickStart && (
        <QuickStartChecklist
          steps={quickStartSteps}
          onDismiss={handleDismissChecklist}
          onRefresh={hasAnyPosition ? handleRefreshChecklist : undefined}
          isRefreshing={checkingAnchors}
        />
      )}

      {isEmptyState ? (
        <div className="rounded-3xl border border-dashed border-gray-200 bg-white px-8 py-12 text-center shadow-sm">
          <Briefcase className="mx-auto mb-4 h-14 w-14 text-gray-300" />
          <h2 className="text-2xl font-bold text-gray-900">You don't have any portfolios yet</h2>
          <p className="mx-auto mt-2 max-w-2xl text-sm text-gray-600">
            Portfolios bundle your guardrail rules, available cash, and the positions you want to automate.
            Start with one, then add more as you grow confidence in the workflow.
          </p>
          <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={handleCreate}
              className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-primary-700"
            >
              <Plus className="h-4 w-4" />
              Create your first portfolio
            </button>
            <Link to="/" className="text-sm font-semibold text-primary-700 hover:text-primary-800">
              Preview the workspace
            </Link>
          </div>

          <div className="mt-10 grid gap-4 text-left sm:grid-cols-2">
            {[
              {
                title: '1. Create a portfolio',
                description: 'Name it and choose templates for guardrails and market hours.',
              },
              {
                title: '2. Add positions',
                description: 'Select each ticker with its shares and matching cash allocation.',
              },
              {
                title: '3. Set anchor price',
                description: 'Lock the reference price to define your rebalance guardrails.',
              },
              {
                title: '4. Start trading',
                description: 'Enable auto trading to let the robot execute the guardrails.',
              },
            ].map((step) => (
              <div key={step.title} className="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
                <p className="text-sm font-semibold text-gray-900">{step.title}</p>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
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
      )}

      <ConfirmDialog
        isOpen={!!deleteConfirmId}
        title="Delete Portfolio"
        message="Are you sure you want to delete this portfolio? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={confirmDeletePortfolio}
        onCancel={() => setDeleteConfirmId(null)}
      />

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
        onDelete={(deletedId) => {
          if (selectedPortfolioId === deletedId) setSelectedPortfolioId('');
          setShowDetailModal(false);
          setSelectedPortfolioForDetail(null);
          refreshPortfolios();
        }}
      />
    </div>
  );
}
