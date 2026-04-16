import { useState, useEffect } from 'react';
import { X, Save, Trash2, AlertTriangle } from 'lucide-react';
import { portfolioApi } from '../../lib/api';
import { portfolioScopedApi, type PortfolioConfig } from '../../services/portfolioScopedApi';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import ConfirmDialog from '../../components/shared/ConfirmDialog';
import toast from 'react-hot-toast';

interface PortfolioDetailModalProps {
  isOpen: boolean;
  portfolioId: string | null;
  onClose: () => void;
  onSave: () => void;
  onDelete?: (portfolioId: string) => void;
}

type Tab = 'general' | 'strategy';

interface PortfolioDetail {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

const FIELD_LABELS: Record<string, string> = {
  trigger_threshold_up_pct: 'Trigger Up (%)',
  trigger_threshold_down_pct: 'Trigger Down (%)',
  min_stock_pct: 'Min Stock (%)',
  max_stock_pct: 'Max Stock (%)',
  max_trade_pct_of_position: 'Max Trade Size (% of position)',
  commission_rate: 'Commission Rate (%)',
};

const FIELD_HINTS: Record<string, string> = {
  trigger_threshold_up_pct: 'Price rise that triggers a sell rebalance',
  trigger_threshold_down_pct: 'Price drop that triggers a buy rebalance',
  min_stock_pct: 'Minimum stock allocation after rebalance',
  max_stock_pct: 'Maximum stock allocation after rebalance',
  max_trade_pct_of_position: 'Cap each trade to this % of total position value',
  commission_rate: 'Brokerage commission per trade',
};

export default function PortfolioDetailModal({
  isOpen,
  portfolioId,
  onClose,
  onSave,
  onDelete,
}: PortfolioDetailModalProps) {
  const { selectedTenantId, portfolios, setSelectedPortfolioId } = useTenantPortfolio();
  const [activeTab, setActiveTab] = useState<Tab>('general');

  // General tab state
  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [loadingGeneral, setLoadingGeneral] = useState(false);
  const [savingGeneral, setSavingGeneral] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [generalForm, setGeneralForm] = useState({ name: '', description: '' });

  // Strategy tab state
  const [config, setConfig] = useState<PortfolioConfig | null>(null);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const [savingStrategy, setSavingStrategy] = useState(false);
  const [strategyError, setStrategyError] = useState<string | null>(null);
  const [strategyForm, setStrategyForm] = useState<Partial<PortfolioConfig>>({});

  // Delete confirm
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (isOpen && portfolioId) {
      setActiveTab('general');
      loadGeneral();
    }
  }, [isOpen, portfolioId]);

  useEffect(() => {
    if (isOpen && portfolioId && activeTab === 'strategy' && !config && !loadingStrategy) {
      loadStrategy();
    }
  }, [activeTab, isOpen, portfolioId]);

  const loadGeneral = async () => {
    if (!portfolioId || !selectedTenantId) return;
    setLoadingGeneral(true);
    setGeneralError(null);
    try {
      const data = await portfolioApi.get(selectedTenantId, portfolioId);
      setPortfolio(data);
      setGeneralForm({ name: data.name, description: data.description || '' });
    } catch {
      setGeneralError('Failed to load portfolio');
    } finally {
      setLoadingGeneral(false);
    }
  };

  const loadStrategy = async () => {
    if (!portfolioId || !selectedTenantId) return;
    setLoadingStrategy(true);
    setStrategyError(null);
    try {
      const data = await portfolioScopedApi.getConfig(selectedTenantId, portfolioId);
      setConfig(data);
      setStrategyForm({ ...data });
    } catch {
      setStrategyError('Failed to load strategy configuration');
    } finally {
      setLoadingStrategy(false);
    }
  };

  const handleSaveGeneral = async () => {
    if (!portfolioId || !selectedTenantId || !generalForm.name.trim()) return;
    const normalizedName = generalForm.name.trim().toLowerCase();
    const duplicate = portfolios.find(
      (p) => p.id !== portfolioId && p.name.trim().toLowerCase() === normalizedName,
    );
    if (duplicate) {
      setGeneralError(`A portfolio named "${generalForm.name}" already exists.`);
      return;
    }
    setSavingGeneral(true);
    setGeneralError(null);
    try {
      await portfolioApi.update(selectedTenantId, portfolioId, {
        name: generalForm.name.trim(),
        description: generalForm.description.trim() || undefined,
      });
      await loadGeneral();
      onSave();
      toast.success('Portfolio updated');
    } catch (err: any) {
      setGeneralError(err.message || 'Failed to save changes');
    } finally {
      setSavingGeneral(false);
    }
  };

  const handleSaveStrategy = async () => {
    if (!portfolioId || !selectedTenantId || !strategyForm) return;
    setSavingStrategy(true);
    setStrategyError(null);
    try {
      await portfolioScopedApi.updateConfig(
        selectedTenantId,
        portfolioId,
        strategyForm as PortfolioConfig,
      );
      const updated = await portfolioScopedApi.getConfig(selectedTenantId, portfolioId);
      setConfig(updated);
      setStrategyForm({ ...updated });
      toast.success('Strategy saved');
    } catch (err: any) {
      setStrategyError(err.message || 'Failed to save strategy');
    } finally {
      setSavingStrategy(false);
    }
  };

  const handleDelete = async () => {
    if (!portfolioId || !selectedTenantId) return;
    setDeleting(true);
    try {
      await portfolioApi.delete(selectedTenantId, portfolioId);
      setShowDeleteConfirm(false);
      onClose();
      if (onDelete) onDelete(portfolioId);
      onSave();
      toast.success('Portfolio deleted');
    } catch {
      toast.error('Failed to delete portfolio');
    } finally {
      setDeleting(false);
    }
  };

  const setStrategyField = (key: keyof PortfolioConfig, value: string) => {
    setStrategyForm((prev) => ({
      ...prev,
      [key]: key === 'market_hours_policy' ? value : parseFloat(value) || 0,
    }));
  };

  if (!isOpen || !portfolioId) return null;

  const portfolioName = portfolio?.name ?? portfolios.find((p) => p.id === portfolioId)?.name ?? 'Portfolio';

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/40" onClick={onClose} />
        <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh]">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h2 className="text-base font-semibold text-gray-900">{portfolioName}</h2>
              <p className="text-xs text-gray-400 mt-0.5">Portfolio settings</p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-100 px-6">
            {(['general', 'strategy'] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2.5 px-1 mr-6 text-sm font-medium border-b-2 transition-colors capitalize ${
                  activeTab === tab
                    ? 'border-primary-600 text-primary-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-6 py-5">
            {/* ── GENERAL TAB ── */}
            {activeTab === 'general' && (
              <>
                {loadingGeneral ? (
                  <div className="flex justify-center py-10">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary-600 border-t-transparent" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {generalError && (
                      <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5 text-sm text-red-700">
                        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                        {generalError}
                      </div>
                    )}

                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Portfolio Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={generalForm.name}
                        onChange={(e) => setGeneralForm({ ...generalForm, name: e.target.value })}
                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        placeholder="My Portfolio"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Description
                      </label>
                      <textarea
                        value={generalForm.description}
                        onChange={(e) =>
                          setGeneralForm({ ...generalForm, description: e.target.value })
                        }
                        rows={3}
                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                        placeholder="Optional description"
                      />
                    </div>

                    {portfolio && (
                      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100 text-xs text-gray-500">
                        <div>
                          <span className="block text-gray-400">Created</span>
                          {new Date(portfolio.created_at).toLocaleDateString()}
                        </div>
                        <div>
                          <span className="block text-gray-400">Updated</span>
                          {new Date(portfolio.updated_at).toLocaleDateString()}
                        </div>
                        <div className="col-span-2">
                          <span className="block text-gray-400">ID</span>
                          <span className="font-mono">{portfolio.id}</span>
                        </div>
                      </div>
                    )}

                    {/* Danger zone */}
                    <div className="pt-3 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-500 mb-2">Danger zone</p>
                      <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete portfolio
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* ── STRATEGY TAB ── */}
            {activeTab === 'strategy' && (
              <>
                {loadingStrategy ? (
                  <div className="flex justify-center py-10">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary-600 border-t-transparent" />
                  </div>
                ) : strategyError ? (
                  <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5 text-sm text-red-700">
                    <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                    {strategyError}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Triggers */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        Triggers
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        {(['trigger_threshold_up_pct', 'trigger_threshold_down_pct'] as const).map(
                          (key) => (
                            <div key={key}>
                              <label className="block text-xs font-medium text-gray-600 mb-1">
                                {FIELD_LABELS[key]}
                              </label>
                              <input
                                type="number"
                                step="0.1"
                                value={strategyForm[key] ?? ''}
                                onChange={(e) => setStrategyField(key, e.target.value)}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                              />
                              <p className="text-xs text-gray-400 mt-0.5">{FIELD_HINTS[key]}</p>
                            </div>
                          ),
                        )}
                      </div>
                    </div>

                    {/* Guardrails */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        Guardrails
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        {(['min_stock_pct', 'max_stock_pct'] as const).map((key) => (
                          <div key={key}>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              {FIELD_LABELS[key]}
                            </label>
                            <input
                              type="number"
                              step="1"
                              min="0"
                              max="100"
                              value={strategyForm[key] ?? ''}
                              onChange={(e) => setStrategyField(key, e.target.value)}
                              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                            <p className="text-xs text-gray-400 mt-0.5">{FIELD_HINTS[key]}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Execution */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        Execution
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        {(['max_trade_pct_of_position', 'commission_rate'] as const).map((key) => (
                          <div key={key}>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              {FIELD_LABELS[key]}
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={strategyForm[key] ?? ''}
                              onChange={(e) => setStrategyField(key, e.target.value)}
                              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                            <p className="text-xs text-gray-400 mt-0.5">{FIELD_HINTS[key]}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Market hours */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        Market Hours
                      </p>
                      <div className="flex gap-2">
                        {(
                          [
                            { value: 'market-open-only', label: 'Market hours only' },
                            { value: 'market-plus-after-hours', label: 'Include after-hours' },
                          ] as const
                        ).map((opt) => (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() =>
                              setStrategyForm((prev) => ({
                                ...prev,
                                market_hours_policy: opt.value,
                              }))
                            }
                            className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
                              strategyForm.market_hours_policy === opt.value
                                ? 'bg-primary-600 text-white border-primary-600'
                                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Cancel
            </button>
            {activeTab === 'general' && (
              <button
                onClick={handleSaveGeneral}
                disabled={savingGeneral || !generalForm.name.trim()}
                className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="h-3.5 w-3.5" />
                {savingGeneral ? 'Saving…' : 'Save'}
              </button>
            )}
            {activeTab === 'strategy' && !loadingStrategy && !strategyError && (
              <button
                onClick={handleSaveStrategy}
                disabled={savingStrategy}
                className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="h-3.5 w-3.5" />
                {savingStrategy ? 'Saving…' : 'Save strategy'}
              </button>
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete portfolio"
        message={`Delete "${portfolioName}"? All positions and history will be permanently removed.`}
        confirmLabel={deleting ? 'Deleting…' : 'Delete'}
        variant="danger"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </>
  );
}
