import { PortfolioPosition } from '../../../services/portfolioScopedApi';
import { useState, useEffect } from 'react';
import { portfolioScopedApi, EffectiveConfig } from '../../../services/portfolioScopedApi';

interface StrategyParametersSectionProps {
  position: PortfolioPosition;
  tenantId: string;
  portfolioId: string;
}

export default function StrategyParametersSection({
  position,
  tenantId,
  portfolioId,
}: StrategyParametersSectionProps) {
  const [config, setConfig] = useState<EffectiveConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const effectiveConfig = await portfolioScopedApi.getEffectiveConfig(tenantId, portfolioId);
        setConfig(effectiveConfig);
      } catch (error) {
        console.error('Error loading config:', error);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [tenantId, portfolioId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Parameters</h2>
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Parameters</h2>
        <div className="text-sm text-gray-500">Configuration not available</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Parameters (Read-Only)</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <dt className="text-sm text-gray-500">Trigger Down %</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {config.trigger_threshold_down_pct?.toFixed(2) || 'N/A'}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Trigger Up %</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {config.trigger_threshold_up_pct?.toFixed(2) || 'N/A'}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Min Stock Allocation %</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {(config.min_stock_pct * 100)?.toFixed(2) || 'N/A'}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Max Stock Allocation %</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {(config.max_stock_pct * 100)?.toFixed(2) || 'N/A'}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Max Trade % of Position</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {(config.max_trade_pct_of_position * 100)?.toFixed(2) || 'N/A'}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Commission Rate</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {(config.commission_rate * 100)?.toFixed(4) || 'N/A'}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Market Hours Policy</dt>
          <dd className="text-lg font-semibold text-gray-900 mt-1">
            {config.market_hours_policy || 'N/A'}
          </dd>
        </div>
      </div>
    </div>
  );
}








