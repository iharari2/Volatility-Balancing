import { MousePointerClick, TrendingUp } from 'lucide-react';

interface EmptyDetailStateProps {
  hasPositions?: boolean;
}

export default function EmptyDetailState({ hasPositions = false }: EmptyDetailStateProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        {hasPositions ? (
          <>
            <MousePointerClick className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Select a Position</h3>
            <p className="text-sm text-gray-500">
              Choose a position from the list to view its details, trading activity, and strategy
              configuration.
            </p>
          </>
        ) : (
          <>
            <TrendingUp className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Positions Yet</h3>
            <p className="text-sm text-gray-500 mb-4">
              Add your first position to start trading. Positions track your holdings and apply
              volatility-based trading strategies.
            </p>
            <button
              type="button"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            >
              Add Position
            </button>
          </>
        )}
      </div>
    </div>
  );
}
