import { useState } from 'react';
import { Plus, Search, Filter } from 'lucide-react';
import { usePositions, useCreatePosition } from '../hooks/usePositions';
import PositionCard from '../components/PositionCard';
import CreatePositionForm from '../components/CreatePositionForm';
import { CreatePositionRequest } from '../types';

export default function Positions() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all');

  const { data: positions = [], isLoading } = usePositions();
  const createPosition = useCreatePosition();

  const handleCreatePosition = async (data: CreatePositionRequest) => {
    try {
      await createPosition.mutateAsync(data);
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create position:', error);
    }
  };

  const filteredPositions = positions.filter((position) => {
    const matchesSearch = position.ticker.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter =
      filter === 'all' ||
      (filter === 'active' && position.anchor_price) ||
      (filter === 'inactive' && !position.anchor_price);

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Positions</h1>
          <p className="text-gray-600">Manage your volatility balancing positions</p>
        </div>
        <button onClick={() => setShowCreateForm(true)} className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Position
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search by ticker..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          <div className="flex space-x-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as 'all' | 'active' | 'inactive')}
              className="input"
            >
              <option value="all">All Positions</option>
              <option value="active">Active (with anchor)</option>
              <option value="inactive">Inactive (no anchor)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Positions Grid */}
      <div>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredPositions.length === 0 ? (
          <div className="card text-center py-12">
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Filter className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || filter !== 'all' ? 'No matching positions' : 'No positions yet'}
            </h3>
            <p className="text-gray-500 mb-4">
              {searchTerm || filter !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'Create your first position to start volatility balancing.'}
            </p>
            {!searchTerm && filter === 'all' && (
              <button onClick={() => setShowCreateForm(true)} className="btn btn-primary">
                <Plus className="w-4 h-4 mr-2" />
                Create Position
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPositions.map((position) => (
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
            <div className="relative bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <CreatePositionForm
                onSubmit={handleCreatePosition}
                onCancel={() => setShowCreateForm(false)}
                isLoading={createPosition.isPending}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


