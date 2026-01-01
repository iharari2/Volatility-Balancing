import { useState, useEffect } from 'react';
import { PortfolioPosition } from '../../../services/portfolioScopedApi';
import PositionStateSection from './PositionStateSection';
import BaselineComparisonSection from './BaselineComparisonSection';
import RecentMarketDataSection from './RecentMarketDataSection';
import StrategyParametersSection from './StrategyParametersSection';
import EventLogSection from './EventLogSection';

interface PositionBaseline {
  baseline_price: number;
  baseline_qty: number;
  baseline_cash: number;
  baseline_total_value: number;
  baseline_stock_value: number;
  baseline_timestamp: string;
}

interface PositionSummaryPanelProps {
  position: PortfolioPosition;
  baseline: PositionBaseline | null;
  tenantId: string;
  portfolioId: string;
}

export default function PositionSummaryPanel({
  position,
  baseline,
  tenantId,
  portfolioId,
}: PositionSummaryPanelProps) {
  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {position.asset || position.ticker || 'Unknown'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Position ID: {position.id}</p>
        </div>

        {/* Section 1: Position State */}
        <PositionStateSection position={position} />

        {/* Section 2: Baseline Comparison */}
        {baseline && <BaselineComparisonSection position={position} baseline={baseline} />}

        {/* Section 3: Recent Market Data */}
        <RecentMarketDataSection position={position} />

        {/* Section 4: Strategy Parameters */}
        <StrategyParametersSection
          position={position}
          tenantId={tenantId}
          portfolioId={portfolioId}
        />

        {/* Section 5: Event Log */}
        <EventLogSection position={position} tenantId={tenantId} portfolioId={portfolioId} />
      </div>
    </div>
  );
}








