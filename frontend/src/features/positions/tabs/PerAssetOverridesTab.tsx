import { useState, useEffect } from 'react';
import { portfolioScopedApi, PerAssetOverride } from '../../../services/portfolioScopedApi';

interface PerAssetOverridesTabProps {
  tenantId: string;
  portfolioId: string;
  onCopyTraceId: (traceId: string) => void;
  copiedTraceId: string | null;
}

export default function PerAssetOverridesTab({
  tenantId,
  portfolioId,
  onCopyTraceId,
  copiedTraceId,
}: PerAssetOverridesTabProps) {
  const [overrides, setOverrides] = useState<PerAssetOverride[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOverrides();
  }, [tenantId, portfolioId]);

  const loadOverrides = async () => {
    try {
      const data = await portfolioScopedApi.getOverrides(tenantId, portfolioId);
      setOverrides(data);
    } catch (error) {
      console.error('Error loading overrides:', error);
      setOverrides([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading overrides...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Per-Asset Overrides</h3>
        <p className="text-sm text-gray-500 mb-4">
          Override portfolio-level config for specific assets. Overrides are still portfolio-scoped.
        </p>
      </div>

      {overrides.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No overrides configured. Per-asset overrides are optional.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Override Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Values
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {overrides.map((override, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                    {override.asset}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {override.override_type}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <pre className="text-xs bg-gray-50 p-2 rounded">
                      {JSON.stringify(override.values, null, 2)}
                    </pre>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                    <button className="text-primary-600 hover:text-primary-900 mr-3">Edit</button>
                    <button className="text-red-600 hover:text-red-900">Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex justify-end">
        <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700">
          Add Override
        </button>
      </div>
    </div>
  );
}













