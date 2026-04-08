import { CheckCircle, Circle, RefreshCw, X } from 'lucide-react';

interface ChecklistStep {
  id: string;
  label: string;
  description: string;
  completed: boolean;
}

interface QuickStartChecklistProps {
  steps: ChecklistStep[];
  onDismiss: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export default function QuickStartChecklist({
  steps,
  onDismiss,
  onRefresh,
  isRefreshing = false,
}: QuickStartChecklistProps) {
  const completedCount = steps.filter((s) => s.completed).length;

  return (
    <div className="bg-white border border-primary-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-gray-900">Quick Start</h3>
          <p className="text-xs text-gray-500">
            {completedCount} of {steps.length} steps complete
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh status"
              className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          )}
          <button
            onClick={onDismiss}
            title="Dismiss"
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-gray-100 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-primary-500 rounded-full transition-all duration-500"
          style={{ width: `${(completedCount / steps.length) * 100}%` }}
        />
      </div>

      <ul className="space-y-3">
        {steps.map((step) => (
          <li key={step.id} className="flex items-start gap-3">
            {step.completed ? (
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
            ) : (
              <Circle className="h-5 w-5 text-gray-300 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p
                className={`text-sm font-medium ${
                  step.completed ? 'text-gray-400 line-through' : 'text-gray-800'
                }`}
              >
                {step.label}
              </p>
              {!step.completed && (
                <p className="text-xs text-gray-400">{step.description}</p>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
