import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Edit,
  Trash2,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

export interface PortfolioPosition {
  id: string;
  asset?: string;
  ticker?: string;
  qty: number;
}

export interface Portfolio {
  id: string;
  name: string;
  description?: string;
  totalValue?: number;
  autoTradingEnabled?: boolean;
  positionCount?: number;
  tradingState?: string;
  pnl?: number;
  pnlPct?: number;
}

interface PortfolioCardProps {
  portfolio: Portfolio;
  positions?: PortfolioPosition[];
  isSelected?: boolean;
  isExpanded?: boolean;
  isLoadingPositions?: boolean;
  onSelect?: (portfolioId: string) => void;
  onEdit?: (portfolioId: string) => void;
  onDelete?: (portfolioId: string) => void;
  onToggleExpand?: (portfolioId: string) => void;
  showActions?: boolean;
}

export default function PortfolioCard({
  portfolio,
  positions = [],
  isSelected = false,
  isExpanded = false,
  isLoadingPositions = false,
  onSelect,
  onEdit,
  onDelete,
  onToggleExpand,
  showActions = true,
}: PortfolioCardProps) {
  const hasPnl = portfolio.pnl !== undefined;
  const isPnlPositive = (portfolio.pnl || 0) >= 0;

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-5 flex flex-col h-full transition-all border-2 ${
        isSelected ? 'border-blue-500 ring-1 ring-blue-500' : 'border-transparent hover:shadow-lg'
      }`}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div
          className={`flex-1 ${onSelect ? 'cursor-pointer group' : ''}`}
          onClick={() => onSelect?.(portfolio.id)}
        >
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
              {portfolio.name}
            </h3>
            {isSelected && (
              <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                Active
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 line-clamp-1 mt-1">
            {portfolio.description || 'No description'}
          </p>
        </div>

        {showActions && (
          <div className="flex items-center gap-1">
            {onEdit && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(portfolio.id);
                }}
                className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Edit Portfolio"
              >
                <Edit className="h-4 w-4" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(portfolio.id);
                }}
                className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
                title="Delete Portfolio"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6 pt-4 border-t border-gray-100">
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">
            Total Value
          </span>
          <p className="text-lg font-bold text-gray-900">
            ${(portfolio.totalValue || 0).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">
            Status
          </span>
          <div className="mt-1">
            <span
              className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full ${
                portfolio.autoTradingEnabled
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {portfolio.autoTradingEnabled ? 'Auto Trading' : 'Manual Mode'}
            </span>
          </div>
        </div>
      </div>

      {/* P&L if available */}
      {hasPnl && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">
              Today's P&L
            </span>
            <div className={`flex items-center ${isPnlPositive ? 'text-green-600' : 'text-red-600'}`}>
              {isPnlPositive ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              <span className="font-bold">
                {isPnlPositive ? '+' : ''}${(portfolio.pnl || 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
              {portfolio.pnlPct !== undefined && (
                <span className="text-sm ml-1">
                  ({isPnlPositive ? '+' : ''}{portfolio.pnlPct.toFixed(2)}%)
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto flex items-center justify-between pt-4 border-t border-gray-100">
        <span className="text-sm font-medium text-gray-600">
          {portfolio.positionCount || 0} position
          {(portfolio.positionCount || 0) !== 1 ? 's' : ''}
        </span>
        <div className="flex gap-2">
          {onToggleExpand && (
            <button
              onClick={() => onToggleExpand(portfolio.id)}
              className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors flex items-center gap-1"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3" /> Hide Assets
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" /> View Assets
                </>
              )}
            </button>
          )}
          <Link
            to={`/portfolios/${portfolio.id}`}
            className="px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1"
          >
            Dashboard <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Expanded Assets Section */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {isLoadingPositions ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : positions.length === 0 ? (
            <div className="text-center py-4 text-xs text-gray-500">No positions found</div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {positions.map((position) => (
                <div
                  key={position.id}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs"
                >
                  <span className="font-bold text-gray-900">
                    {position.asset || position.ticker}
                  </span>
                  <span className="text-gray-600">
                    {position.qty.toLocaleString()} shares
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
