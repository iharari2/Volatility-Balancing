import { useWorkspace } from '../../WorkspaceContext';
import { useTenantPortfolio } from '../../../../contexts/TenantPortfolioContext';
import OrdersTable from '../../../../components/trading/OrdersTable';

export default function OrdersTab() {
  const { selectedPosition, portfolioId } = useWorkspace();
  const { selectedTenantId } = useTenantPortfolio();

  const effectiveTenantId = selectedTenantId || 'default';

  if (!selectedPosition || !portfolioId) {
    return (
      <div className="p-6">
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-200">
          <p className="text-sm text-gray-500">Select a position to view orders.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <OrdersTable
        tenantId={effectiveTenantId}
        portfolioId={portfolioId}
        positionId={selectedPosition.position_id}
      />
    </div>
  );
}
