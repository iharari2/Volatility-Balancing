import { useState, useEffect } from 'react';
import { X, Save, Settings, DollarSign, PieChart } from 'lucide-react';
import { portfolioApi } from '../../lib/api';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface PortfolioDetailModalProps {
  isOpen: boolean;
  portfolioId: string | null;
  onClose: () => void;
  onSave: () => void;
}

interface PortfolioDetail {
  id: string;
  name: string;
  description: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
  total_positions?: number;
  total_cash?: number;
  total_value?: number;
  positions_by_ticker?: Record<string, any>;
}

export default function PortfolioDetailModal({
  isOpen,
  portfolioId,
  onClose,
  onSave,
}: PortfolioDetailModalProps) {
  const { selectedTenantId, portfolios } = useTenantPortfolio();
  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  useEffect(() => {
    if (isOpen && portfolioId && selectedTenantId) {
      loadPortfolio();
    }
  }, [isOpen, portfolioId, selectedTenantId]);

  const loadPortfolio = async () => {
    if (!portfolioId || !selectedTenantId) return;

    setLoading(true);
    setError(null);
    try {
      const [portfolioData, summary] = await Promise.all([
        portfolioApi.get(selectedTenantId, portfolioId),
        portfolioApi.getSummary(selectedTenantId, portfolioId).catch(() => null),
      ]);

      const portfolioDetail: PortfolioDetail = {
        ...portfolioData,
        total_positions: summary?.total_positions,
        total_cash: summary?.total_cash,
        total_value: summary?.total_value,
        positions_by_ticker: summary?.positions_by_ticker,
      };

      setPortfolio(portfolioDetail);
      setFormData({
        name: portfolioData.name,
        description: portfolioData.description || '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load portfolio details');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!portfolioId || !selectedTenantId) return;

    setSaving(true);
    setError(null);
    try {
      // Check for duplicate portfolio name (excluding current portfolio)
      if (formData.name.trim()) {
        const normalizedName = formData.name.trim().toLowerCase();
        const duplicate = portfolios.find(
          (p) => p.id !== portfolioId && p.name.trim().toLowerCase() === normalizedName,
        );
        if (duplicate) {
          setError(
            `Portfolio with name "${formData.name}" already exists. Please choose a different name.`,
          );
          setSaving(false);
          return;
        }
      }

      await portfolioApi.update(selectedTenantId, portfolioId, {
        name: formData.name,
        description: formData.description || undefined,
      });
      setEditMode(false);
      await loadPortfolio(); // Reload to get updated data
      onSave();
    } catch (err: any) {
      // Handle validation errors from backend (e.g., duplicate name)
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to update portfolio';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (portfolio) {
      setFormData({
        name: portfolio.name,
        description: portfolio.description || '',
      });
    }
    setEditMode(false);
    setError(null);
  };

  if (!isOpen || !portfolioId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Portfolio Details</h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                <p className="text-gray-500">Loading portfolio details...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                <p className="text-red-800">{error}</p>
              </div>
            ) : portfolio ? (
              <div className="space-y-6">
                {/* Portfolio Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center">
                      <DollarSign className="h-5 w-5 text-blue-600 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-blue-900">Total Value</p>
                        <p className="text-2xl font-bold text-blue-600">
                          $
                          {(portfolio.total_value || 0).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="flex items-center">
                      <DollarSign className="h-5 w-5 text-green-600 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-green-900">Total Cash</p>
                        <p className="text-2xl font-bold text-green-600">
                          $
                          {(portfolio.total_cash || 0).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="flex items-center">
                      <PieChart className="h-5 w-5 text-purple-600 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-purple-900">Positions</p>
                        <p className="text-2xl font-bold text-purple-600">
                          {portfolio.total_positions || 0}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Portfolio Information */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-md font-semibold text-gray-900">Portfolio Information</h4>
                    {!editMode && (
                      <button
                        onClick={() => setEditMode(true)}
                        className="flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-800"
                      >
                        <Settings className="h-4 w-4 mr-1" />
                        Edit
                      </button>
                    )}
                  </div>

                  {editMode ? (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Portfolio Name
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Enter portfolio name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) =>
                            setFormData({ ...formData, description: e.target.value })
                          }
                          rows={3}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Enter portfolio description (optional)"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSave}
                          disabled={saving || !formData.name.trim()}
                          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Save className="h-4 w-4 mr-2" />
                          {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                        <button
                          onClick={handleCancel}
                          disabled={saving}
                          className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div>
                        <p className="text-sm font-medium text-gray-500">Name</p>
                        <p className="text-base text-gray-900">{portfolio.name}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Description</p>
                        <p className="text-base text-gray-900">
                          {portfolio.description || (
                            <span className="text-gray-400">No description</span>
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Created</p>
                        <p className="text-base text-gray-900">
                          {new Date(portfolio.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Last Updated</p>
                        <p className="text-base text-gray-900">
                          {new Date(portfolio.updated_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Positions Summary */}
                {portfolio.positions_by_ticker &&
                  Object.keys(portfolio.positions_by_ticker).length > 0 && (
                    <div className="border-t pt-4">
                      <h4 className="text-md font-semibold text-gray-900 mb-3">
                        Positions by Ticker
                      </h4>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <div className="space-y-2">
                          {Object.entries(portfolio.positions_by_ticker).map(
                            ([ticker, data]: [string, any]) => (
                              <div key={ticker} className="flex justify-between items-center">
                                <span className="font-medium text-gray-900">{ticker}</span>
                                <span className="text-gray-600">
                                  {data.qty?.toLocaleString(undefined, {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2,
                                  }) || 0}{' '}
                                  shares
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    </div>
                  )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}







