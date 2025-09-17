import { useState } from 'react';
import { Plus, TrendingUp, DollarSign, Activity, AlertTriangle } from 'lucide-react';
import { usePositions, useCreatePosition } from '../hooks/usePositions';
import PositionCard from '../components/PositionCard';
import { CreatePositionRequest } from '../types';

export default function Dashboard() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CreatePositionRequest>({
    ticker: 'AAPL',
    qty: 0,
    cash: 10000,
  });

  const { data: positions = [], isLoading } = usePositions();
  const createPosition = useCreatePosition();

  const handleCreatePosition = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPosition.mutateAsync(formData);
      setShowCreateForm(false);
      setFormData({ ticker: 'AAPL', qty: 0, cash: 10000 });
    } catch (error) {
      console.error('Failed to create position:', error);
    }
  };

  const totalValue = positions.reduce((sum, pos) => {
    const value = pos.qty * (pos.anchor_price || 0) + pos.cash;
    return sum + value;
  }, 0);

  const activePositions = positions.filter((pos) => pos.anchor_price);
  const totalCash = positions.reduce((sum, pos) => sum + pos.cash, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Monitor your volatility balancing positions</p>
        </div>
        <button onClick={() => setShowCreateForm(true)} className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Position
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Positions</p>
              <p className="text-2xl font-semibold text-gray-900">{positions.length}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Positions</p>
              <p className="text-2xl font-semibold text-gray-900">{activePositions.length}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DollarSign className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Cash</p>
              <p className="text-2xl font-semibold text-gray-900">${totalCash.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Value</p>
              <p className="text-2xl font-semibold text-gray-900">${totalValue.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Positions Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Positions</h2>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : positions.length === 0 ? (
          <div className="card text-center py-12">
            <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Positions Yet</h3>
            <p className="text-gray-500 mb-4">
              Create your first position to start volatility balancing.
            </p>
            <button onClick={() => setShowCreateForm(true)} className="btn btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              Create Position
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {positions.map((position) => (
              <PositionCard key={position.id} position={position} />
            ))}
          </div>
        )}
      </div>

      {/* Create Position Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setShowCreateForm(false)}
            />
            <div className="relative bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Position</h3>

              <form onSubmit={handleCreatePosition} className="space-y-4">
                <div>
                  <label className="label">Ticker Symbol</label>
                  <input
                    type="text"
                    value={formData.ticker}
                    onChange={(e) =>
                      setFormData({ ...formData, ticker: e.target.value.toUpperCase() })
                    }
                    className="input"
                    placeholder="e.g., AAPL"
                    required
                  />
                </div>

                <div>
                  <label className="label">Initial Cash</label>
                  <input
                    type="number"
                    value={formData.cash}
                    onChange={(e) => setFormData({ ...formData, cash: Number(e.target.value) })}
                    className="input"
                    min="0"
                    step="0.01"
                    required
                  />
                </div>

                <div>
                  <label className="label">Initial Shares (optional)</label>
                  <input
                    type="number"
                    value={formData.qty}
                    onChange={(e) => setFormData({ ...formData, qty: Number(e.target.value) })}
                    className="input"
                    min="0"
                    step="0.01"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="btn btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createPosition.isPending}
                    className="btn btn-primary flex-1"
                  >
                    {createPosition.isPending ? 'Creating...' : 'Create Position'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


