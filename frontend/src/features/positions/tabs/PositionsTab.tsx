import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Download,
  Plus,
  Briefcase,
  Search,
  Activity,
  Pause,
  Settings,
  BarChart3,
  Trash2,
  Edit,
} from 'lucide-react';
import {
  portfolioScopedApi,
  PortfolioPosition,
  EffectiveConfig,
} from '../../../services/portfolioScopedApi';
import { marketApi, portfolioApi } from '../../../lib/api';
import AddPositionModal from '../modals/AddPositionModal';
import AdjustPositionModal from '../modals/AdjustPositionModal';
import SetAnchorModal from '../modals/SetAnchorModal';
import EditPositionModal from '../modals/EditPositionModal';
import PositionDetailsDrawer from '../drawers/PositionDetailsDrawer';

interface PositionsTabProps {
  tenantId: string;
  portfolioId: string;
  positions: PortfolioPosition[];
  effectiveConfig: EffectiveConfig | null;
  onRefresh: () => void;
  onCopyTraceId: (traceId: string) => void;
  onPositionClick?: (positionId: string) => void;
}

// Helper function to sanitize ticker symbols
function sanitizeTicker(ticker: string | null | undefined): string | null {
  if (!ticker) return null;
  // Remove backslashes, newlines, and other invalid characters
  // Trim whitespace and convert to uppercase
  const sanitized = ticker
    .replace(/[\\\n\r\t]/g, '') // Remove backslashes, newlines, tabs
    .trim()
    .toUpperCase();
  return sanitized.length > 0 ? sanitized : null;
}

export default function PositionsTab({
  tenantId,
  portfolioId,
  positions,
  effectiveConfig,
  onRefresh,
  onCopyTraceId,
  onPositionClick,
}: PositionsTabProps) {
  const navigate = useNavigate();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showAnchorModal, setShowAnchorModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailsDrawer, setShowDetailsDrawer] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<PortfolioPosition | null>(null);
  const [marketDataMap, setMarketDataMap] = useState<
    Record<string, { price: number; change?: number; changePercent?: number }>
  >({});
  const [searchQuery, setSearchBar] = useState('');

  // Filtered positions based on search
  const filteredPositions = useMemo(() => {
    if (!searchQuery) return positions;
    return positions.filter((p) =>
      (p.asset || p.ticker || '').toLowerCase().includes(searchQuery.toLowerCase()),
    );
  }, [positions, searchQuery]);

  // Calculate totals from position (cell) total values
  // Portfolio total = sum of all position (cell) total values
  // Each position total = cash + stock_value
  const totalCash = positions.reduce((sum, pos) => sum + (pos.cash || 0), 0);
  const totalStockValue = positions.reduce((sum, pos) => {
    const ticker = pos.asset || pos.ticker || '';
    const price = marketDataMap[ticker]?.price || pos.last_price || 0;
    return sum + pos.qty * price;
  }, 0);
  // Portfolio total = sum of each position's total value (cash + stock)
  const totalPortfolioValue = positions.reduce((sum, pos) => {
    const ticker = pos.asset || pos.ticker || '';
    const price = marketDataMap[ticker]?.price || pos.last_price || 0;
    const positionStockValue = pos.qty * price;
    const positionTotalValue = (pos.cash || 0) + positionStockValue;
    return sum + positionTotalValue;
  }, 0);

  // Load market prices for all positions
  useEffect(() => {
    const loadPrices = async () => {
      if (positions.length === 0) return;
      try {
        const pricePromises = positions.map(async (pos) => {
          // Get ticker/asset - backend returns 'asset', frontend may use 'ticker'
          const tickerValue = pos.asset || pos.ticker || '';
          // Sanitize ticker before making API call
          const sanitizedTicker = sanitizeTicker(tickerValue);

          // Skip price fetch if ticker is invalid
          if (!sanitizedTicker) {
            console.warn(`Invalid ticker symbol: "${tickerValue}" - skipping price fetch`);
            return { ticker: tickerValue, price: pos.last_price || 0 };
          }

          try {
            const data = await marketApi.getPrice(sanitizedTicker);
            return {
              ticker: sanitizedTicker,
              price: data.price,
              change: (data as any).change,
              changePercent: (data as any).changePercent,
            };
          } catch (error: any) {
            // Only log non-"ticker_not_found" errors to reduce console noise
            if (error.message && !error.message.includes('ticker_not_found')) {
              console.warn(`Error loading price for ${sanitizedTicker}:`, error.message);
            }
            return { ticker: sanitizedTicker, price: pos.last_price || 0 };
          }
        });
        const results = await Promise.all(pricePromises);
        const newDataMap: Record<
          string,
          { price: number; change?: number; changePercent?: number }
        > = {};
        results.forEach((r) => {
          newDataMap[r.ticker] = {
            price: r.price,
            change: (r as any).change,
            changePercent: (r as any).changePercent,
          };
        });
        setMarketDataMap(newDataMap);
      } catch (error) {
        console.error('Error loading market prices:', error);
      } finally {
        // Price loading finished
      }
    };

    loadPrices();
    // Refresh prices every 30 seconds
    const interval = setInterval(loadPrices, 30000);
    return () => clearInterval(interval);
  }, [positions]);

  const handleAddPosition = async (data: {
    ticker: string;
    qty: number;
    dollarValue: number;
    inputMode: 'qty' | 'dollar';
    currentPrice: number;
    startingCash: {
      currency: string;
      amount: number;
    };
  }) => {
    try {
      // Determine final qty
      const finalQty = data.inputMode === 'qty' ? data.qty : data.dollarValue / data.currentPrice;

      if (finalQty <= 0 || !isFinite(finalQty)) {
        alert('Invalid quantity. Please check your input values.');
        return;
      }

      const positionPayload = {
        asset: data.ticker.trim().toUpperCase(),
        qty: finalQty,
        anchor_price: data.currentPrice,
        avg_cost: data.currentPrice,
        starting_cash: {
          currency: data.startingCash.currency,
          amount: data.startingCash.amount,
        },
      };

      const result = await portfolioApi.createPosition(tenantId, portfolioId, positionPayload);
      const traceId = (result as { trace_id?: string }).trace_id;
      if (traceId) {
        onCopyTraceId(traceId);
      }
      setShowAddModal(false);
      onRefresh();
    } catch (error: any) {
      console.error('Error adding position:', error);
      const errorMessage =
        error?.message ||
        error?.detail ||
        error?.response?.data?.detail ||
        'Failed to add position';
      alert(`Failed to add position: ${errorMessage}`);
    }
  };

  const handleAdjustPosition = async (data: {
    operation: 'BUY' | 'SELL' | 'SET_QTY';
    qty: number;
    price?: number;
    reason: string;
  }) => {
    if (!selectedPosition) return;
    try {
      const ticker = selectedPosition.asset || selectedPosition.ticker || '';
      const result = await portfolioScopedApi.adjustPosition(tenantId, portfolioId, ticker, data);
      if (result.trace_id) {
        onCopyTraceId(result.trace_id);
      }
      setShowAdjustModal(false);
      setSelectedPosition(null);
      onRefresh();
    } catch (error) {
      console.error('Error adjusting position:', error);
      alert('Failed to adjust position');
    }
  };

  const handleSetAnchor = async (anchorPrice: number) => {
    if (!selectedPosition) return;
    try {
      const ticker = selectedPosition.asset || selectedPosition.ticker || '';
      const result = await portfolioScopedApi.setAnchor(tenantId, portfolioId, ticker, anchorPrice);
      if (result.trace_id) {
        onCopyTraceId(result.trace_id);
      }
      setShowAnchorModal(false);
      setSelectedPosition(null);
      onRefresh();
    } catch (error) {
      console.error('Error setting anchor:', error);
      alert('Failed to set anchor price');
    }
  };

  const handleRemovePosition = async (positionId: string, assetSymbol: string) => {
    if (
      !window.confirm(
        `Are you sure you want to remove position "${assetSymbol}" (${positionId}) from this portfolio? This action cannot be undone.`,
      )
    ) {
      return;
    }

    try {
      await portfolioScopedApi.removePosition(tenantId, portfolioId, positionId);
      onRefresh();
      // Show success message
      alert(`Position "${assetSymbol}" has been removed from the portfolio.`);
    } catch (error: any) {
      console.error('Error removing position:', error);
      const errorMessage =
        error?.message ||
        error?.detail ||
        error?.response?.data?.detail ||
        'Failed to remove position';
      alert(`Failed to remove position: ${errorMessage}`);
    }
  };

  const handleExport = () => {
    window.open(`/api/v1/excel/positions/export?portfolio_id=${portfolioId}&format=xlsx`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="card border-l-4 border-l-primary-600">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight uppercase">
              Position Cells
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                Selected Portfolio
              </span>
              <span className="text-xs font-black text-primary-600 bg-primary-50 px-2 py-0.5 rounded uppercase tracking-tight">
                {portfolioId}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search symbol..."
                value={searchQuery}
                onChange={(e) => setSearchBar(e.target.value)}
                className="input pl-10 py-2 text-sm w-64 bg-gray-50 border-gray-200"
              />
            </div>
            <button
              onClick={handleExport}
              className="btn btn-secondary py-2 px-3 flex items-center shadow-sm"
            >
              <Download className="h-4 w-4" />
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 shadow-md transition-colors font-medium"
            >
              <Plus className="h-4 w-4" />
              <span>Add Position</span>
            </button>
          </div>
        </div>

        {/* Summary Mini-Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">
              Total Value
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-black text-gray-900">
                $
                {totalPortfolioValue.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">
              Cash Balance
            </span>
            <span className="text-xl font-black text-gray-900">
              ${totalCash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">
              Stock Allocation
            </span>
            <span className="text-xl font-black text-gray-900">
              {totalPortfolioValue > 0
                ? ((totalStockValue / totalPortfolioValue) * 100).toFixed(1)
                : '0.0'}
              %
            </span>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">
              Active Assets
            </span>
            <span className="text-xl font-black text-gray-900">{positions.length}</span>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">
              Strategy
            </span>
            <span className="text-sm font-bold text-primary-600 uppercase">Per Position</span>
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="card p-0 overflow-hidden border-l-4 border-l-transparent hover:border-l-primary-600 transition-all duration-300">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-100">
            <thead>
              <tr className="bg-gray-50/50">
                <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Asset / Exchange
                </th>
                <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Status
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Quantity
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Cash
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Current Price
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Cell Total Value
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  % Stock
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  % Δ Anchor
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  % Δ Baseline
                </th>
                <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white">
              {filteredPositions.map((position) => {
                const ticker = position.asset || position.ticker || 'N/A';
                const mkt = marketDataMap[ticker];
                const lastPrice = mkt?.price || position.last_price || 0;
                const priceChange = mkt?.changePercent;

                const positionCash = position.cash || 0;
                const stockValue = position.qty * lastPrice;
                const positionTotal = positionCash + stockValue;
                const baselinePrice = position.anchor_price || position.avg_cost || lastPrice;
                const anchorPrice = position.anchor_price || lastPrice;

                const pctFromAnchor = ((lastPrice - anchorPrice) / anchorPrice) * 100;
                const baselinePositionTotal = positionCash + position.qty * baselinePrice;
                const pctVsBaseline =
                  ((positionTotal - baselinePositionTotal) / baselinePositionTotal) * 100;

                const stockPct = positionTotal > 0 ? (stockValue / positionTotal) * 100 : 0;

                // Guardrail constraints
                const minStockPct = effectiveConfig?.min_stock_pct ?? 0;
                const maxStockPct = effectiveConfig?.max_stock_pct ?? 100;
                const isOutOfGuardrails = stockPct < minStockPct || stockPct > maxStockPct;

                return (
                  <tr
                    key={position.id}
                    className="group hover:bg-primary-50/30 transition-colors cursor-pointer border-l-2 border-l-transparent hover:border-l-primary-500"
                    onClick={() => onPositionClick?.(position.id)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="text-sm font-black text-gray-900 tracking-tight">
                          {ticker}
                        </span>
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                          NASDAQ
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center">
                        <div
                          className={`p-1.5 rounded-lg ${
                            position.qty > 0
                              ? 'bg-success-100 text-success-600'
                              : 'bg-gray-100 text-gray-400'
                          }`}
                          title={position.qty > 0 ? 'Running' : 'Paused'}
                        >
                          {position.qty > 0 ? (
                            <Activity className="h-3.5 w-3.5" />
                          ) : (
                            <Pause className="h-3.5 w-3.5" />
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-sm font-bold text-gray-900">
                        {position.qty.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-sm font-bold text-gray-600">
                        ${positionCash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex flex-col items-end">
                        <span className="text-sm font-black text-gray-900">
                          ${lastPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                        {priceChange !== undefined && (
                          <span
                            className={`text-[10px] font-bold ${
                              priceChange >= 0 ? 'text-success-600' : 'text-danger-600'
                            }`}
                          >
                            {priceChange >= 0 ? '▲' : '▼'} {Math.abs(priceChange).toFixed(2)}%
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-sm font-black text-gray-900">
                        ${positionTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex flex-col items-end">
                        <span
                          className={`text-sm font-black ${
                            isOutOfGuardrails ? 'text-danger-600' : 'text-gray-900'
                          }`}
                        >
                          {stockPct.toFixed(1)}%
                        </span>
                        <span className="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">
                          Target: {minStockPct}-{maxStockPct}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span
                        className={`text-sm font-black ${
                          pctFromAnchor >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}
                      >
                        {pctFromAnchor >= 0 ? '+' : ''}
                        {pctFromAnchor.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span
                        className={`text-sm font-black ${
                          pctVsBaseline >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}
                      >
                        {pctVsBaseline >= 0 ? '+' : ''}
                        {pctVsBaseline.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => navigate(`/trade/${portfolioId}/position/${position.id}`)}
                          className="p-1.5 text-primary-600 hover:bg-primary-100 rounded-lg transition-colors opacity-70 hover:opacity-100"
                          title="Open Cockpit"
                        >
                          <Activity className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() =>
                            navigate(
                              `/portfolios/${portfolioId}/positions?tab=analytics&positionId=${position.id}`,
                            )
                          }
                          className="p-1.5 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors opacity-70 hover:opacity-100"
                          title="View Analytics"
                        >
                          <BarChart3 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() =>
                            navigate(
                              `/portfolios/${portfolioId}/positions?tab=config&positionId=${position.id}`,
                            )
                          }
                          className="p-1.5 text-purple-600 hover:bg-purple-100 rounded-lg transition-colors opacity-70 hover:opacity-100"
                          title="Edit Strategy"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedPosition(position);
                            setShowAdjustModal(true);
                          }}
                          className="p-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors opacity-70 hover:opacity-100"
                          title="Adjust Position"
                        >
                          <Settings className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemovePosition(position.id, ticker);
                          }}
                          className="p-1.5 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                          title="Remove Position from Portfolio"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filteredPositions.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-20 text-center">
                    <div className="flex flex-col items-center justify-center opacity-40">
                      <Briefcase className="h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-sm font-black text-gray-900 uppercase tracking-widest">
                        No matching assets
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      {showAddModal && (
        <AddPositionModal onClose={() => setShowAddModal(false)} onSave={handleAddPosition} />
      )}

      {showEditModal && selectedPosition && (
        <EditPositionModal
          position={selectedPosition}
          tenantId={tenantId}
          portfolioId={portfolioId}
          onClose={() => {
            setShowEditModal(false);
            setSelectedPosition(null);
          }}
          onSave={onRefresh}
        />
      )}

      {showAdjustModal && selectedPosition && (
        <AdjustPositionModal
          position={selectedPosition}
          currentPrice={
            marketDataMap[selectedPosition.asset || selectedPosition.ticker || '']?.price ||
            selectedPosition.last_price ||
            0
          }
          onClose={() => {
            setShowAdjustModal(false);
            setSelectedPosition(null);
          }}
          onSave={handleAdjustPosition}
        />
      )}

      {showAnchorModal && selectedPosition && (
        <SetAnchorModal
          position={selectedPosition}
          currentPrice={
            marketDataMap[selectedPosition.asset || selectedPosition.ticker || '']?.price ||
            selectedPosition.last_price ||
            0
          }
          onClose={() => {
            setShowAnchorModal(false);
            setSelectedPosition(null);
          }}
          onSave={handleSetAnchor}
        />
      )}

      {showDetailsDrawer && selectedPosition && (
        <PositionDetailsDrawer
          position={selectedPosition}
          portfolioId={portfolioId}
          tenantId={tenantId}
          onClose={() => {
            setShowDetailsDrawer(false);
            setSelectedPosition(null);
          }}
        />
      )}
    </div>
  );
}





