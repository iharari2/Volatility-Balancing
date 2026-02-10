import { useWorkspace } from '../../WorkspaceContext';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';
import ExplainabilityTable from '../../../../components/trading/ExplainabilityTable';

export default function ExplainabilityTab() {
  const { selectedPosition, portfolioId } = useWorkspace();
  const { selectedTenantId } = useTenantPortfolio();

  // Use 'default' tenant if none selected (matches database data)
  const effectiveTenantId = selectedTenantId || 'default';

  if (!selectedPosition || !portfolioId) {
    return (
      <div className="p-6">
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-200">
          <p className="text-sm text-gray-500">Select a position to view trade tracking data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <ExplainabilityTable
        tenantId={effectiveTenantId}
        portfolioId={portfolioId}
        positionId={selectedPosition.position_id}
        mode="LIVE"
        symbol={selectedPosition.asset_symbol}
      />
    </div>
  );
}
